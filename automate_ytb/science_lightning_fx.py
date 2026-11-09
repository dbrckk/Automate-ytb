"""Original cinematic weather staging for animated lightning science.

CPU-only layered atmosphere built from shaded, blurred cloud volumes, rolling
depth layers, deterministic foreground rain, wet-ground highlights and lightning
bloom. Frames change continuously; no static illustration/video asset reuse.
Informed by shader/VFX timing principles, not copied third-party media.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .science_lightning_art import detailed_cloud_volume, paint_industrial_detail

SIZE=(1080,930)
WHITE=(229,246,255,255)


def _smooth(v):
    v=max(0.,min(1.,v))
    return v*v*(3.-2.*v)


@lru_cache(maxsize=1)
def _sky() -> Image.Image:
    scene=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(scene)
    for y in range(SIZE[1]):
        depth=y/SIZE[1]
        # Color script: indigo-black upper storm, muted plum horizon,
        # cool slate reflection. Warmth is strongest behind the industrial
        # silhouette, not a uniform cyan wash across every material.
        horizon=math.exp(-((depth-.72)/.27)**2)
        d.line((0,y,1080,y),
               fill=(round(5+20*depth+22*horizon),
                     round(14+29*depth+7*horizon),
                     round(32+49*depth+3*horizon),255))
    glow=Image.new("RGBA",SIZE)
    ImageDraw.Draw(glow).ellipse((-100,500,1200,1080),
                                  fill=(171,115,86,30))
    scene.alpha_composite(glow.filter(ImageFilter.GaussianBlur(94)))
    return scene


@lru_cache(maxsize=9)
def cloud_volume(depth: int, variant: int) -> Image.Image:
    """Deterministic original sculpted cloud sprite, cached by Z and seed."""
    return detailed_cloud_volume(depth, variant)


@lru_cache(maxsize=1)
def _vignette() -> Image.Image:
    # A cached 2D radial alpha field, upscaled once; avoids per-frame pixels.
    smaller=Image.new("RGBA",(270,233))
    pixels=smaller.load()
    for y in range(233):
        for x in range(270):
            q=((x-134.5)/134.5)**2*.53+((y-107.)/124.)**2*.47
            strength=max(0.,min(1.,(q-.27)*1.15))
            pixels[x,y]=(0,8,18,round(strength*77))
    return smaller.resize(SIZE,Image.Resampling.BICUBIC)


def environment_plates(t: float, beat: str, duration: float
                       ) -> tuple[tuple[str, Image.Image], ...]:
    """Independently animated atmospheric planes, before perspective camera.

    Returned layers are complete original RGBA plates with true transparency.
    Nothing is inferred from a flattened screenshot; every cloud is authored
    at its own depth and animated at its own physical wind velocity.
    """
    if (type(t) not in (int, float) or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or duration <= 0 or not 0 <= t <= duration):
        raise ValueError("Unsafe storm environment")
    result = [("sky", _sky())]
    for depth, name in ((2, "clouds-far"),
                        (1, "clouds-middle"),
                        (0, "clouds-near")):
        plate = Image.new("RGBA", SIZE)
        for variant in range(3):
            sprite = cloud_volume(depth, variant)
            base = (-300 + variant * 435) + (depth - 1) * 28
            shift = round((16 + depth * 18) *
                          math.sin(t * (.20 + depth * .09) + variant))
            y = round(10 + depth * 81 +
                      12 * math.sin(t * .31 + variant + depth))
            plate.alpha_composite(sprite, (base + shift, y))
        result.append((name, plate))
    rain = Image.new("RGBA", SIZE)
    d = ImageDraw.Draw(rain)
    for depth, count in ((0, 42), (1, 61)):
        for i in range(count):
            speed = 160 + depth * 125
            x = (i * 113 + 37 * depth - t * (34 + depth * 12)) % 1240 - 80
            y = (i * 179 + depth * 81 + t * speed) % 960 - 45
            length = (17 + depth * 27) + (i % 4) * 5
            d.line((x, y, x - 12 - depth * 7, y + length),
                   fill=(137 + depth * 13, 195 + depth * 11, 227,
                         49 + depth * 25), width=1 + depth)
    result.append(("background-rain", rain))
    result.append(("vignette", _vignette()))
    return tuple(result)


def paint_environment(stage: Image.Image, t: float, beat: str,
                      duration: float) -> None:
    """Legacy flattened stage, identical ordering to new separated plates."""
    if stage.mode != "RGBA" or stage.size != SIZE:
        raise ValueError("Unsafe storm environment")
    for _, plate in environment_plates(t, beat, duration):
        stage.alpha_composite(plate)


def paint_terrain(draw: ImageDraw.ImageDraw,t: float) -> None:
    """Wet layered shoreline silhouette, perspective horizon and fixed tower."""
    # Two far layers move independently of foreground markers.
    far_shift=round(10*math.sin(t*.12))
    draw.polygon([(0,741),(110+far_shift,702),(232+far_shift,721),
                  (350+far_shift,686),(467+far_shift,728),
                  (583+far_shift,703),(730+far_shift,711),
                  (901+far_shift,694),(1080,720),(1080,930),(0,930)],
                 fill=(25,47,64,239))
    draw.polygon([(0,790),(142,778),(271,795),(381,769),
                  (530,789),(670,759),(829,789),(970,766),
                  (1080,779),(1080,930),(0,930)],
                 fill=(13,32,49,255))
    # Replace flat rectangles and wire-frame triangle with original
    # perspective architecture, material highlights and a braced 3D-read mast.
    paint_industrial_detail(draw,t)


def _flash_intensity(beat,t,duration):
    f=t/duration
    if beat=="return":
        # Brief flashes in a slowed explanatory clip rather than an
        # implausible solid white screen throughout.
        return max(0.,.88*math.exp(-((f-.20)/.085)**2)+
                   .52*math.exp(-((f-.59)/.11)**2))
    if beat=="connection":
        return .23*math.exp(-((f-.88)/.105)**2)
    if beat=="leader":
        return .12*math.exp(-((f-.78)/.20)**2)
    return 0.



@lru_cache(maxsize=1)
def _reactive_light_masks() -> tuple[Image.Image, Image.Image]:
    """Cached original cloud and wet-ground light falloff at source resolution.

    This is an illustrated spatial light field, not volumetric ray tracing.
    Separate masks avoid the flat, whole-screen white flash of older shorts.
    """
    clouds=Image.new("L",(270,233))
    cd=ImageDraw.Draw(clouds)
    cd.ellipse((12,2,263,144),fill=76)
    cd.ellipse((68,2,208,108),fill=229)
    cd.ellipse((125,30,229,121),fill=133)
    clouds=clouds.filter(ImageFilter.GaussianBlur(17))
    wet=Image.new("L",(270,233))
    wd=ImageDraw.Draw(wet)
    wd.ellipse((21,191,267,253),fill=78)
    wd.ellipse((116,184,242,244),fill=209)
    wet=wet.filter(ImageFilter.GaussianBlur(9))
    return (clouds.resize(SIZE,Image.Resampling.BICUBIC),
            wet.resize(SIZE,Image.Resampling.BICUBIC))


def paint_reactive_storm_light(stage: Image.Image, beat: str,
                               t: float, duration: float) -> None:
    """Synchronize real atmospheric/ground relighting with the existing bolt.

    The same _flash_intensity event already used by bloom drives these layers;
    it adds NO independent strobe. Always paint before the electric channel
    so the channel retains its own bright core. Transparent RGBA is supported
    for insertion between terrain and the electric action in the 2.5D stage.
    """
    if (stage.mode!="RGBA" or stage.size!=SIZE
            or beat not in ("charge","leader","connection","return","thunder")
            or type(t) not in (int,float) or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0<duration<=180 or not 0<=t<=duration):
        raise ValueError("Invalid atmospheric relighting frame")
    power=_flash_intensity(beat,t,duration)
    if power<.012:
        return
    cloud,wet=_reactive_light_masks()
    for mask,rgb,gain in (
            (cloud,(171,210,251),.48),
            (wet,(141,208,247),.62)):
        layer=Image.new("RGBA",SIZE,(*rgb,0))
        layer.putalpha(mask.point(
            lambda value: min(165,round(value*gain*power))))
        stage.alpha_composite(layer)
    if beat=="return":
        # Water highlights reflect the channel's grounded mast attachment.
        # They inherit the *same* two-pulse energy; no flashing title card.
        ripples=Image.new("RGBA",SIZE)
        d=ImageDraw.Draw(ripples)
        for i in range(20):
            y=814+i*6
            x=round(700+20*math.sin(t*2.0+i*.79))
            spread=round((19+i*2)*(1 if i%2 else -1))
            half=round(14+(i%6)*11)
            alpha=round((108-i*3)*power)
            d.line((x+spread-half,y,x+spread+half,y),
                   fill=(200,233,255,alpha),width=2+(i%3==0))
        stage.alpha_composite(ripples)


def bloom_electric_channel(stage: Image.Image,beat:str,t:float,
                           duration:float,path) -> None:
    if stage.mode!="RGBA" or stage.size!=SIZE:
        raise ValueError("Invalid bloom canvas")
    intensity=_flash_intensity(beat,t,duration)
    if intensity<.012:
        return
    fx=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(fx)
    limit=(max(2,round(len(path)*_smooth(t/duration)))
           if beat=="leader" else len(path))
    nodes=path[:limit]
    if len(nodes)>=2:
        for offset in (-13,0,13):
            d.line([(x+offset,y) for x,y in nodes],
                   fill=(124,195,252,round(67*intensity)),
                   width=34 if offset==0 else 14,joint="curve")
    blurred=fx.filter(ImageFilter.GaussianBlur(19))
    stage.alpha_composite(blurred)
    # A low-resolution soft lighting field follows the *actual* branching
    # channel, instead of brightening an unrelated fixed oval. It illuminates
    # the existing cloud/rain composites with spatially local light.
    field=Image.new("RGBA",(270,233))
    fd=ImageDraw.Draw(field)
    scaled=[(round(x/4),round(y/4)) for x,y in nodes]
    if len(scaled)>=2:
        fd.line(scaled,fill=(139,194,245,round(85*intensity)),
                width=35,joint="curve")
    field=field.filter(ImageFilter.GaussianBlur(19))
    stage.alpha_composite(field.resize(SIZE,Image.Resampling.BILINEAR))
    if beat=="return" and intensity>.3:
        # The channel terminates above the radio mast; specular streaks on
        # wet ground follow that same horizontal position and shift with
        # perspective. They are never independent decorative flashes.
        reflections=Image.new("RGBA",SIZE)
        d=ImageDraw.Draw(reflections)
        # CONNECTED_CHANNEL starts at the grounded tower and ends in sky.
        foot_x=round(path[0][0])
        for j in range(20):
            depth=j/19
            y=812+j*6
            ripple=round(9*math.sin(t*4.3+j*.81))
            spread=round((15+depth*165)*(1 if j%2 else -1))
            x=foot_x+spread+ripple
            width=round(17+depth*77)
            alpha=round((108-58*depth)*intensity)
            d.line((x-width//2,y,x+width//2,y),
                   fill=(166,225,253,alpha),width=2+(j%3==0))
        stage.alpha_composite(reflections)


def paint_foreground_weather(stage: Image.Image,t:float,beat:str) -> None:
    if stage.mode!="RGBA" or stage.size!=SIZE:
        raise ValueError("Invalid foreground weather canvas")
    layer=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(layer)
    for i in range(88):
        # Foreground rain travels faster and appears thicker than the distant
        # layers, preserving parallax over each original causal animation.
        x=(i*173+53-t*(77+i%4*8))%1210-50
        y=(i*211+t*(264+i%5*18))%1000-50
        span=31+i%5*7
        d.line((x,y,x-12,y+span),
               fill=(183,223,245,60+i%4*14),width=2+i%3)
    # Small impact rings on wet ground; phase continuous, no flashing jitter.
    for j in range(21):
        x=51+j*53
        y=808+(j*31)%108
        phase=(t*.85+j*.173)%1
        rr=4+17*phase
        opacity=round(95*(1-phase))
        d.arc((x-rr,y-rr*.37,x+rr,y+rr*.37),15,165,
              fill=(165,224,252,opacity),width=2)
    stage.alpha_composite(layer)
