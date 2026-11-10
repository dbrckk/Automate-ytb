"""Reusable 2.5D original volcanic reservoir source geometry and materials.

The rock cavity, visible mineral rind, animated molten pool and pressure
waves now share one organically eroded contour, instead of unrelated
perfect ellipses. Source planes are cached, with no paid API/stock media.
The art illustrates subsurface circulation, not geophysical simulation.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageChops

VERSION = "shared-organic-reservoir-source25d-p517-v1"
SIZE = (1080,1380)
CENTER = (542,1127)
BOUNDS = (326,996,758,1257)


def reservoir_contour(scale: float = 1.) -> tuple[tuple[int,int], ...]:
    """Validated original source contour, with immutable cached geometry.

    Validate BEFORE the cache to reject 1/True aliases, the same boolean
    edge case discovered in the P5.16 conduit regression tests.
    """
    if (type(scale) not in (float,int) or not math.isfinite(scale)
            or not .2 <= scale <= 1.08):
        raise ValueError("Invalid authored volcanic reservoir scale")
    return _cached_reservoir_contour(float(scale))


@lru_cache(maxsize=12)
def _cached_reservoir_contour(scale: float) -> tuple[tuple[int,int], ...]:
    """112 band-limited samples shared by bedrock and molten materials."""
    cx,cy=CENTER
    pts=[]
    for k in range(112):
        angle=k*math.tau/112
        jagged_x=(1+.053*math.sin(7*angle+.8)
                    +.025*math.sin(13*angle-.7)
                    +.014*math.cos(19*angle+.25))
        jagged_y=(1+.052*math.sin(5*angle-.3)
                    +.029*math.cos(11*angle+.1)
                    +.015*math.cos(17*angle-.2))
        x=cx+scale*(202*math.cos(angle)*jagged_x
                    +4.1*math.sin(2*angle))
        y=cy+scale*(111*math.sin(angle)*jagged_y
                    +3.1*math.cos(3*angle))
        pts.append((round(x),round(y)))
    return tuple(pts)


@lru_cache(maxsize=1)
def reservoir_mask() -> Image.Image:
    """Native source mask reused by all gas, convection and liquid layers."""
    image=Image.new("L",SIZE)
    ImageDraw.Draw(image).polygon(reservoir_contour(),fill=255)
    return image


@lru_cache(maxsize=1)
def reservoir_rock_source() -> Image.Image:
    """One original rock-cutaway source material, drawn once per process."""
    plate=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(plate,"RGBA")
    outer=reservoir_contour()
    d.polygon(outer,fill=(111,49,37,255))
    d.line((*outer,outer[0]),fill=(165,104,78,239),width=12,
           joint="curve")
    d.polygon(reservoir_contour(.968),fill=(65,30,32,255))
    d.polygon(reservoir_contour(.91),fill=(39,20,29,255))
    # Staggered geological edges give the source cavity thickness and
    # soften the cutaway rim without constructing a flat colored card.
    inner=reservoir_contour(.88)
    for index in range(0,len(inner)-1,3):
        a=inner[index]
        b=inner[min(index+2,len(inner)-1)]
        d.line((a,b),fill=(192,120,82,38+index%5*8),width=4)
    # Internal fixed chromatic veins are subordinated to moving magma.
    for k in range(27):
        angle=k*2.39996323
        radius=38+(k*59)%124
        x=CENTER[0]+radius*math.cos(angle)
        y=CENTER[1]+radius*.57*math.sin(angle)
        length=12+(k*7)%24
        d.line((x-length,y-3,x+length,y+3),
               fill=(150,65,42,34+k%4*9),width=1+k%3)
    return plate


@lru_cache(maxsize=1)
def reservoir_molten_source() -> Image.Image:
    """Cached molten substrate, with layered metal/basalt material bands."""
    image=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(image,"RGBA")
    d.polygon(reservoir_contour(.98),fill=(145,49,31,210))
    d.polygon(reservoir_contour(.88),fill=(182,64,28,188))
    d.polygon(reservoir_contour(.69),fill=(228,88,28,137))
    d.polygon(reservoir_contour(.38),fill=(251,124,42,126))
    # Discontinuous isothermal structures, not perfectly elliptical
    # rings or pseudo-random flicker across independently generated frames.
    for lane in range(15):
        y=1033+lane*13
        x0=365+(lane*47)%122
        width=175+(lane*23)%110
        path=[]
        for segment in range(23):
            x=x0+width*segment/22
            yy=y+6*math.sin(x*.026+lane*.83)+2*math.sin(x*.067-lane*.31)
            path.append((round(x),round(yy)))
        d.line(path,fill=(251,161+lane%3*14,72,70+lane%4*15),
               width=2+lane%2,joint="curve")
    image.putalpha(ImageChops.multiply(image.getchannel("A"),
                                       reservoir_mask()))
    return image
