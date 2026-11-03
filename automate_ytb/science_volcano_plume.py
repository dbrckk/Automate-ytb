"""Deterministic animated ash plume and crater-sourced ballistic tephra.

Stylized, depth-layered emission is integrated with original 3D rock shading.
Billows are continuously born at the vent, expand, cool and drift in wind;
no frame is a scrolling stock texture. Tephra has independent launch times,
ballistic acceleration and motion trails. This is not a physical simulator.

All soft smoke is rendered at quarter resolution and upsampled once per
frame; reusable finite palettes avoid Gaussian blurring at 1080px/30 fps.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw

VERSION = "original-volcano-ash-v1-depth-billows-ballistic-ejecta"
SIZE = (1080, 1380)
LOW = (270, 345)
ORIGIN = (540, 345)
EMITTER_COUNT = 162


def _clock(t: float, duration: float) -> None:
    if (type(t) not in (int, float) or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration):
        raise ValueError("Nonfinite or out-of-range volcano plume clock")


@lru_cache(maxsize=320)
def _billow(radius: int, shade: int, opacity: int) -> Image.Image:
    """Low resolution shaded smoke sphere; fine irregularities are cached.

    Radius, shade, opacity are intentionally quantized so consecutive frames
    reuse most sprites rather than regenerating a costly cloud at every tick.
    """
    if (type(radius) is not int or not 4 <= radius <= 38
            or type(shade) is not int or not 0 <= shade <= 5
            or type(opacity) is not int or not 0 <= opacity <= 5):
        raise ValueError("Invalid plume sprite palette")
    side = radius * 2 + 4
    center = radius + 2
    sprite = Image.new("RGBA", (side, side))
    px = sprite.load()
    for y in range(side):
        dy=(y-center)/radius
        for x in range(side):
            dx=(x-center)/radius
            # Stable angular lobes: not a perfect blurred circular disk.
            theta=math.atan2(dy,dx)
            noise=(.085*math.sin(5*theta+shade*.9)
                   +.055*math.sin(9*theta+radius*.17))
            extent=math.hypot(dx,dy)/(1+noise)
            if extent>=1.0:
                continue
            interior=max(0.0,1.0-extent)
            phase=min(1.0, max(0.0, .5 - dx*.33 - dy*.31))
            warm=shade==0
            base=63+shade*6+round(34*phase)
            alpha=round(158 * interior**.56 * ((opacity+1)/6))
            if alpha:
                px[x,y]=(min(255,base+(12 if warm else 0)),
                         max(0,base-8 if warm else base-1),
                         max(0,base-23 if warm else base+7),alpha)
    return sprite


def _ash_overlay(t: float, duration: float) -> Image.Image:
    """Smoke and ash in a bounded offscreen emission field (one resize)."""
    mist=Image.new("RGBA", LOW)
    wind=7.5+4.5*math.sin(t*.24+.3)
    # Cloud sprites are source-anchored at the (540,345) crater.
    # Birth time is stable for any t, avoiding sudden particle teleportation.
    for i in range(EMITTER_COUNT):
        born=(i+.3)*duration/(EMITTER_COUNT+7)
        age=t-born
        if age < 0 or age > 3.55:
            continue
        lifetime=age/3.55
        grow=min(1.,age/.27)
        if grow<=0:
            continue
        spread=14+age*24
        x=(ORIGIN[0]*.25 + age*wind
           + math.sin(i*2.123+age*1.6)*spread*.38)
        y=(ORIGIN[1]*.25 - age*(24+(i%5)*1.6)
           + math.cos(i*1.77+age*.8)*3.6)
        radius=min(38, max(4, int(round((5+age*(5.8+i%4*.9))/3)*3)))
        shade=(i*7)%6
        life=min(grow, (1-lifetime)**.62)
        opacity=min(5,max(0,int(life*5.5)))
        cloud=_billow(radius,shade,opacity)
        mist.alpha_composite(cloud,(
            round(x-cloud.width/2),round(y-cloud.height/2)))
    # Fine gray ash is emitted inside the same vent column; individual
    # motes disperse and fall as the video progresses.
    d=ImageDraw.Draw(mist,"RGBA")
    for j in range(210):
        born=(j+.2)*duration/218.
        age=t-born
        if not 0<=age<=2.8:
            continue
        v=(j*29)%60
        x=135 + (1 if j%2 else -1)*(v+age*(9+j%4*4))
        y=86-age*(18+j%7*3)+age*age*2.2
        if 0<=x<270 and 0<=y<345:
            rr=1+j%3
            alpha=round(110*(1-age/3.2))
            d.ellipse((x-rr,y-rr,x+rr,y+rr),
                      fill=(133,122,116,max(0,alpha)))
    return mist


def draw_ash(stage:Image.Image,t:float,duration:float)->None:
    """Composite layered rising smoke after terrain light, before sharp tephra."""
    if stage.size!=SIZE or stage.mode!="RGBA":
        raise ValueError("Plume requires native RGBA geological stage")
    _clock(t,duration)
    if t<=0:
        return
    overlay=_ash_overlay(t,duration)
    stage.alpha_composite(overlay.resize(SIZE,Image.Resampling.BILINEAR))


def draw_ejecta(stage:Image.Image,t:float,duration:float)->None:
    """Crater-born glowing rock fragments with gravity and visible trails."""
    if stage.size!=SIZE or stage.mode!="RGBA":
        raise ValueError("Tephra requires native RGBA geological stage")
    _clock(t,duration)
    d=ImageDraw.Draw(stage,"RGBA")
    g=282.0
    for i in range(135):
        born=(i+.32)*duration/142.
        age=t-born
        if not 0<=age<=2.45:
            continue
        sign=-1 if i%2 else 1
        vx=sign*(57+(i*47)%161)
        vy=-(246+(i*71)%183)
        x=ORIGIN[0]+vx*age
        y=ORIGIN[1]+vy*age+g*age*age/2
        if not -25<=x<=1105 or not -25<=y<=1380:
            continue
        r=2+(i%6)
        # An asymmetric taper reads as airborne, high-temperature ejecta.
        travel=.082
        tail_x=x-vx*travel
        tail_y=y-(vy+g*age)*travel
        d.line((tail_x,tail_y,x,y),fill=(245,91,28,159),
               width=max(2,r//2))
        d.ellipse((x-r,y-r,x+r,y+r),
                  fill=(255,164+(i%3)*19,57,235))
        if i%5==0:
            d.ellipse((x-r*.46,y-r*.46,x+r*.46,y+r*.46),
                      fill=(255,237,153,238))
