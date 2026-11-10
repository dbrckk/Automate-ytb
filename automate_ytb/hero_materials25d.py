"""Original cacheable volumetric-looking 2D hero art for 2.5D storyboards.

The glass and solar surfaces are hand-authored mathematical illustration
materials, not 3D renders or claims of accurate optical ray tracing.
They can be reused wherever a native renderer needs a prominent translucent
sphere or warm emitting body. No stock assets, random per-frame textures,
paid inference or external service is required.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

VERSION = "hero-optical-2p5d-original-materials-p512-v1"


def _check(diameter: int, seed: int) -> None:
    if (type(diameter) is not int or not 64 <= diameter <= 720
            or type(seed) is not int or not 0 <= seed <= 1_000_000):
        raise ValueError("Invalid bounded original hero material")


def _byte(number: float) -> int:
    return max(0, min(255, round(number)))


@lru_cache(maxsize=20)
def glass_sphere(diameter: int, *, seed: int = 173) -> Image.Image:
    """Translucent lens with internal refraction, tinted shadow and edge glints.

    The per-pixel Fresnel approximation follows the same authored sphere
    silhouette as the alpha mask; artwork is fully cached between frames.
    """
    _check(diameter,seed)
    phase=random.Random(seed).uniform(0,math.tau)
    radius=diameter/2.0
    center=(diameter-1)/2.0
    image=Image.new("RGBA",(diameter,diameter))
    pixels=image.load()
    for y in range(diameter):
        ny=(y-center)/radius
        for x in range(diameter):
            nx=(x-center)/radius
            radial=nx*nx+ny*ny
            if radial>=1:
                continue
            z=math.sqrt(1-radial)
            rim=(1-z)**3
            density=(math.sin(13*nx+7*ny+phase)+
                     .4*math.sin(33*nx-14*ny+phase*.8))
            blade=math.exp(-((ny+.30+.11*math.sin(4*nx+phase))/.13)**2)
            bright=math.exp(-((nx+.39)**2/.026+(ny+.46)**2/.042))
            deep=math.exp(-((nx-.29)**2/.092+(ny-.38)**2/.11))
            red=34+48*z+112*rim+94*bright+26*blade+4*density
            green=98+78*z+112*rim+67*bright+31*blade+7*density-13*deep
            blue=146+76*z+96*rim+32*bright+21*blade+4*density-29*deep
            optical_depth=85+135*rim+26*bright-10*z
            aa=min(1.,max(0.,(1-math.sqrt(radial))*radius))
            pixels[x,y]=(_byte(red),_byte(green),_byte(blue),
                         _byte(optical_depth*aa))
    d=ImageDraw.Draw(image,"RGBA")
    margin=round(diameter*.055)
    d.arc((margin,margin,diameter-margin,diameter-margin),
          156,283,fill=(239,254,255,215),
          width=max(2,round(diameter*.017)))
    d.arc((margin+10,margin+10,diameter-margin-10,diameter-margin-10),
          -28,71,fill=(59,193,239,136),
          width=max(2,round(diameter*.025)))
    d.arc((round(diameter*.18),round(diameter*.2),
           round(diameter*.83),round(diameter*.84)),
          34,147,fill=(157,233,252,67),
          width=max(2,round(diameter*.022)))
    for j in range(4):
        angle=phase+.6*j
        xx=round(diameter*(.30+.08*j)+math.sin(angle)*diameter*.035)
        yy=round(diameter*(.27+.07*j))
        rr=max(1,round(diameter*(.009+j*.001)))
        d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),
                  fill=(246,255,255,135-17*j))
    # Composited arc strokes cannot spill outside the curved lens mask.
    rim_mask=Image.new("L",(diameter,diameter))
    ImageDraw.Draw(rim_mask).ellipse(
        (0,0,diameter-1,diameter-1),fill=255)
    rim_mask=rim_mask.filter(ImageFilter.GaussianBlur(.6))
    image.putalpha(ImageChops.multiply(image.getchannel("A"),rim_mask))
    return image


@lru_cache(maxsize=20)
def solar_disc(diameter: int, *, seed: int = 71) -> Image.Image:
    """Layered emitting solar painting with a soft halo and surface granules."""
    _check(diameter,seed)
    pad=round(diameter*.36)
    width=diameter+2*pad
    radius=diameter/2.0
    center=(width-1)/2.0
    field=Image.new("RGBA",(width,width))
    px=field.load()
    rng=random.Random(seed)
    phases=[rng.random()*math.tau for _ in range(4)]
    for y in range(width):
        yy=(y-center)/radius
        for x in range(width):
            xx=(x-center)/radius
            radial=math.hypot(xx,yy)
            if radial>1.7:
                continue
            if radial>1:
                halo=math.exp(-((radial-1)/.3)**2)
                px[x,y]=(255,154+round(35*halo),
                         87+round(50*halo),_byte(22*halo))
                continue
            z=math.sqrt(max(0.,1-radial*radial))
            granules=(.5*math.sin(xx*38+phases[0])*
                       math.sin(yy*29+phases[1])
                      +.27*math.sin((xx+yy)*72+phases[2])
                      +.16*math.cos(xx*105-yy*68+phases[3]))
            warm=math.exp(-((xx+.25)**2/.21+(yy+.43)**2/.25))
            grain=36*z+10*granules
            rgb=(_byte(247+8*warm+grain*.06),
                 _byte(151+72*z+19*warm+grain*.21),
                 _byte(67+85*z+21*warm+grain*.32))
            aa=min(1.,max(0.,(1-radial)*radius))
            px[x,y]=(*rgb,_byte(255*aa))
    painter=ImageDraw.Draw(field,"RGBA")
    a=pad+round(diameter*.07)
    b=pad+round(diameter*.93)
    painter.arc((a,a,b,b),183,274,
                fill=(255,251,207,170),
                width=max(2,round(diameter*.02)))
    return field



@lru_cache(maxsize=24)
def thermal_pool(size: tuple[int,int], *, kind: str, seed: int = 129) -> Image.Image:
    """Cacheable original warm/cool material with organic painted edge."""
    if (not isinstance(size,tuple) or len(size)!=2 or
            any(type(n) is not int or not 96<=n<=720 for n in size)
            or kind not in ("warm","cool") or type(seed) is not int
            or not 0<=seed<=1_000_000):
        raise ValueError("Invalid original temperature material")
    width,height=size
    image=Image.new("RGBA",size)
    pixels=image.load()
    phase=random.Random(seed).uniform(0,math.tau)
    base=(253,211,159) if kind=="warm" else (174,222,247)
    for y in range(height):
        ny=(y-(height-1)*.5)/(height*.49)
        for x in range(width):
            nx=(x-(width-1)*.5)/(width*.49)
            # Organic superellipse: no flat rectangles or hard card rails.
            radius=(abs(nx)**4+abs(ny)**4)**.25
            radius+=.026*math.sin(nx*8.3+phase)*math.cos(ny*7.7-phase*.7)
            alpha=max(0.,min(1.,(1.03-radius)/.15))
            alpha=alpha*alpha*(3-2*alpha)
            if alpha<=0:continue
            detail=(math.sin(nx*12.8+ny*5.1+phase)
                    +.46*math.sin(nx*29.4-ny*16.9-phase*.7)
                    +.21*math.sin(nx*63.8+ny*32.4+phase*.4))
            stripe=math.exp(-((ny-.24*math.sin(nx*5+phase))/.11)**2)
            light=(1-radius)*12+detail*7+stripe*8
            pixels[x,y]=(
                _byte(base[0]+light*.4),_byte(base[1]+light*.8),
                _byte(base[2]+light*.4),_byte((226+10*stripe)*alpha))
    return image


@lru_cache(maxsize=12)
def ice_floe(size: tuple[int,int], *, seed: int = 75) -> Image.Image:
    """Original polar waterline material with above/below-water strata."""
    if (not isinstance(size,tuple) or len(size)!=2
            or any(type(n) is not int or not 96<=n<=420 for n in size)
            or type(seed) is not int or not 0<=seed<=1_000_000):
        raise ValueError("Invalid original floating ice")
    w,h=size
    im=Image.new("RGBA",size)
    d=ImageDraw.Draw(im,"RGBA")
    def poly(points, color):
        d.polygon([(round(x*w),round(y*h)) for x,y in points],fill=color)
    top=[(.07,.58),(.16,.45),(.20,.34),(.31,.22),(.38,.29),
         (.46,.14),(.53,.28),(.64,.19),(.71,.39),(.83,.42),(.91,.58)]
    poly(top+[(.84,.67),(.12,.67)],(212,239,250,241))
    poly([(.12,.61),(.84,.61),(.73,.90),(.47,.99),(.30,.85)],
         (66,157,206,135))
    poly([(.20,.39),(.31,.22),(.39,.31),(.39,.56),(.13,.60)],
         (245,252,255,237))
    poly([(.46,.15),(.53,.28),(.64,.19),(.70,.42),(.61,.52),(.42,.54)],
         (174,213,239,221))
    poly([(.39,.57),(.62,.52),(.72,.63),(.46,.89)],
         (111,196,232,139))
    rng=random.Random(seed)
    for j in range(11):
        x=rng.uniform(.16,.82); y=rng.uniform(.52,.7)
        d.line((round(x*w),round(y*h),
                round((x+rng.uniform(-.03,.03))*w),round((y+.04)*h)),
                fill=(217,245,254,120+j*8),width=1+j%2)
    d.line([(round(x*w),round(y*h)) for x,y in
           ((.07,.59),(.28,.58),(.48,.60),(.71,.57),(.91,.59))],
           fill=(241,253,255,222),width=max(2,round(w*.017)))
    return im
