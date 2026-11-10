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
