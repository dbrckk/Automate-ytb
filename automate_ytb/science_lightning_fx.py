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
        # Dark blue-black indigo at cloud altitude to humid slate by horizon.
        d.line((0,y,1080,y),
               fill=(round(5+20*depth),round(14+29*depth),
                     round(32+49*depth),255))
    return scene


@lru_cache(maxsize=9)
def cloud_volume(depth: int, variant: int) -> Image.Image:
    """Depth-dependent shaded cumulonimbus billows on a transparent surface."""
    if type(depth) is not int or depth not in (0,1,2) or type(variant) is not int or not 0<=variant<3:
        raise ValueError("Invalid cloud volume")
    width,height=(620,300) if depth==0 else (670,285) if depth==1 else (760,265)
    plate=Image.new("RGBA",(width,height))
    rng=random.Random(41+variant*97+depth*263)
    shadow=Image.new("L",(width,height))
    ds=ImageDraw.Draw(shadow)
    for j in range(13):
        radius=(width*.09)+rng.random()*width*.105
        x=round(j*(width/12)+rng.randrange(-50,45))
        y=round(height*.51+rng.randrange(-34,45))
        sy=round(radius*(.51+depth*.12))
        ds.ellipse((x-radius,y-sy,x+radius,y+sy),fill=210)
    shadow=shadow.filter(ImageFilter.GaussianBlur(17+depth*5))
    # Upper edges receive a small cool rim, lower edges retain storm shade.
    luminance=Image.new("RGBA",(width,height))
    d=ImageDraw.Draw(luminance)
    for y in range(height):
        f=y/height
        shade=(41+variant*4+depth*13)+round(51*(1.-f)**2)
        d.line((0,y,width,y),fill=(shade,shade+18,shade+39,
                                round(185-45*f)))
    luminance.putalpha(shadow)
    # Blur bright contour spots, not an opaque cartoon cloud outline.
    mist=Image.new("RGBA",(width,height))
    md=ImageDraw.Draw(mist)
    for k in range(7):
        x=round(width*(k+1)/8)
        y=round(56+16*math.sin(k+variant))
        rr=round(width*.12)
        md.ellipse((x-rr,y-31,x+rr,y+20),
                   fill=(133,194,220,28+depth*8))
    volume=Image.alpha_composite(
        luminance,mist.filter(ImageFilter.GaussianBlur(23)))
    # Hard rectangular cloud-sprite edges were visible in the encoded film.
    # Feather all four boundaries to zero, with organic opacity variation,
    # preserving actual soft cloud contours as parallax layers overlap.
    feather=Image.new("L",(width,height))
    pixels=feather.load()
    for yy in range(height):
        fy=min(1.,yy/52.,(height-1-yy)/68.)
        for xx in range(width):
            fx=min(1.,xx/67.,(width-1-xx)/76.)
            uneven=.82+.18*math.sin(xx*.047+math.sin(yy*.033)*2.)
            pixels[xx,yy]=max(0,min(255,round(
                255*max(0,min(fx,fy))**1.4*uneven)))
    volume.putalpha(ImageChops.multiply(
        volume.getchannel("A"),feather))
    return volume


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


def paint_environment(stage: Image.Image,t: float,beat: str,duration: float) -> None:
    """Perspective atmosphere; actual rain/cloud movements have depth speeds."""
    if stage.mode!="RGBA" or stage.size!=SIZE or not math.isfinite(t) or not 0<=t<=duration:
        raise ValueError("Unsafe storm environment")
    stage.alpha_composite(_sky())
    for depth in (2,1,0):
        for variant in range(3):
            sprite=cloud_volume(depth,variant)
            width=sprite.width
            base=(-300+variant*435)+(depth-1)*28
            shift=round((16+depth*18)*math.sin(t*(.20+depth*.09)+variant))
            y=round(10+depth*81+12*math.sin(t*.31+variant+depth))
            stage.alpha_composite(sprite,(base+shift,y))
    # Atmospheric rain behind subjects: deterministic movement at 3 depths.
    back=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(back)
    for depth,count in ((0,42),(1,61)):
        for i in range(count):
            speed=160+depth*125
            x=(i*113+37*depth-t*(34+depth*12))%1240-80
            y=(i*179+depth*81+t*speed)%960-45
            length=(17+depth*27)+(i%4)*5
            d.line((x,y,x-12-depth*7,y+length),
                   fill=(137+depth*13,195+depth*11,227,
                         49+depth*25),width=1+depth)
    stage.alpha_composite(back)
    stage.alpha_composite(_vignette())


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
    # City distant industrial shapes add scale, not full 3D photorealism.
    for i in range(9):
        x=45+i*128
        h=44+(i*37)%69
        draw.rectangle((x,793-h,x+31+i%3*9,811),
                       fill=(20,42,58,234))
        for yy in (804-h+12,804-h+29):
            draw.line((x+5,yy,x+16,yy),
                      fill=(108,148,156,105),width=2)
    for k in range(18):
        x=(k*83+18)%1100
        y=832+k%4*21
        draw.line((x,y,x+28,y+2),
                  fill=(67,121,144,55),width=3)
    # Water reflections with animated perspective ripples on the horizon.
    for i in range(24):
        x=(i*131+27)%1120
        y=836+(i*59)%88
        wav=12*math.sin(t*1.2+i*.8)
        draw.line((round(x+wav),y,round(x+wav)+25+i%4*14,y),
                  fill=(90,154,181,31+i%4*16),width=2)


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
    # Lightning illuminates the surrounding atmosphere and wet horizon.
    veil=Image.new("RGBA",SIZE)
    v=ImageDraw.Draw(veil)
    v.ellipse((80,8,1040,825),
              fill=(105,165,226,round(46*intensity)))
    stage.alpha_composite(veil.filter(ImageFilter.GaussianBlur(112)))
    if beat=="return" and intensity>.3:
        reflections=Image.new("RGBA",SIZE)
        d=ImageDraw.Draw(reflections)
        for j in range(15):
            y=824+j*7
            x=400+j%4*53
            d.line((x,y,x+130-j%3*19,y),
                   fill=(155,223,249,round(82*intensity)),width=3)
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
