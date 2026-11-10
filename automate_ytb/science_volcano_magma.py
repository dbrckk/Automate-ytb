"""Moving volcanic magma cutaway: convection, pressure, fractures, ascent.

Original native-stage 2.5D graphics for the first three beats of the
English volcano science video. A chamber and throat are continuously masked
so emitted bubbles and incandescent streaks never leak into solid rock.
Pressure waves are restrained to the chamber; radiating wall fractures
appear only after sustained build-up. In ascent, magma rises through the
same conduit seen in the earlier cutaway, with fluid-advection streaks.
The geometry is illustrative, not a geomechanical or CFD simulation.

Deterministic math, Pillow, cached rock masks, quarter-resolution glow.
No API keys, neural requests, stock footage, 3D renders or paid assets.
"""
from __future__ import annotations

from functools import lru_cache
import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .volcanic_reservoir25d import (
    BOUNDS, CENTER, reservoir_mask, reservoir_contour,
    reservoir_molten_source,
)
from .volcanic_conduit25d import (
    VENT, BASE, INNER_WIDTH, conduit_mask, conduit_center_x,
    active_conduit_path,
)

SIZE=(1080,1380)
LOW=(270,345)
VERSION="magma-chamber-v4-convective-organic-reservoir-and-shared-curved-conduit"
BEATS=("magma","pressure","ascent")
CHAMBER=BOUNDS
# Legacy bounding box retained for callers; actual rock geometry is curved.
THROAT=(514,345,566,1028)


def _validate(stage: Image.Image, beat: str, t: float,
              duration: float) -> None:
    if (stage.mode!="RGBA" or stage.size!=SIZE or beat not in BEATS
            or type(t) not in (float,int) or type(duration) not in (float,int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0<duration<=180 or not 0<=t<=duration):
        raise ValueError("Invalid magma-cutaway beat/clock/stage")


@lru_cache(maxsize=1)
def _chamber_mask() -> Image.Image:
    return reservoir_mask()


@lru_cache(maxsize=1)
def _conduit_mask() -> Image.Image:
    return conduit_mask()


def _molten_plate(t: float, duration: float, beat: str) -> Image.Image:
    """Animated metallic-orange cellular magma texture inside the chamber."""
    # Static material source is shared across every frame; only convection
    # and incandescent eddies change with actual narration time.
    stage=reservoir_molten_source().copy()
    d=ImageDraw.Draw(stage,"RGBA")
    cx,cy=CENTER
    # Sweeping advected cells simulate circulating, hot molten rock.
    # Closed elliptical trajectories avoid bubbles abruptly teleporting
    # across the magma/rock boundary at scene ends.
    for k in range(94):
        angle=k*2.3999632297 + t*(.48+(.05*(k%5))) * (-1 if k%2 else 1)
        minor=(k*37%91)/100.0
        r=23+minor*173
        x=cx + r*math.cos(angle)
        y=cy + (.28+.17*minor)*r*math.sin(angle)
        rad=8+(k*7)%18
        heat=.5+.5*math.sin(k*1.713+t*.83)
        # Draw irregular molten plates with advected edges rather than
        # scores of identical circular spots resembling floating coins.
        polygon=[]
        for j in range(10):
            a=j*math.tau/10
            modulation=1+.13*math.sin(3*a+k*.41+t*.12)
            polygon.append((
                x+rad*modulation*math.cos(a),
                y+rad*.67*modulation*math.sin(a)))
        d.polygon(polygon,
                  fill=(255,round(93+110*heat),round(24+45*heat),190))
        if k%3==0:
            d.arc((x-rad*1.3,y-rad,x+rad*1.3,y+rad),
                  190,330,fill=(255,232,103,round(165*heat+55)),width=3)
    # Distinct large circulating current ribbons, curved continuously.
    for lane in range(7):
        path=[]
        eccentric=.4+.053*lane
        phase=t*(.34+lane*.038)+lane*.91
        for j in range(35):
            v=j/34
            a=phase+v*math.pi*1.24
            x=cx+156*eccentric*math.cos(a)
            y=cy+88*eccentric*math.sin(a)
            path.append((x,y))
        d.line(path,fill=(255,190+lane*6,70,190),width=3+lane%3)
    # Bright melt-rock contact follows the exact *same organic boundary* as
    # the bedrock silhouette and the gas/liquid masks. No ellipse remains.
    contour=reservoir_contour(.971)
    d.line((*contour,contour[0]),fill=(255,133,47,228),
           width=7,joint="curve")
    return stage


def _gas(stage:Image.Image,t:float,duration:float, *, pressure:bool)->None:
    d=ImageDraw.Draw(stage,"RGBA")
    # Realistic stylization: bubbles are emitted continuously from magma,
    # and rise at different speeds; no gas is drawn outside the chamber.
    clip=_chamber_mask()
    gas=Image.new("RGBA",SIZE)
    g=ImageDraw.Draw(gas,"RGBA")
    for k in range(56):
        shift=(t*(28+k%5*4)+k*17)%198
        x=542+math.sin(k*1.79+t*.66)*159
        y=1245-shift
        r=4+(k*11)%11
        if pressure:
            r+=round(2.7*min(1,t/duration*1.5))
        g.ellipse((x-r,y-r,x+r,y+r),
                  fill=(24,26,33,38),outline=(255,217,132,220),width=2)
        g.arc((x-r+2,y-r+2,x+r-2,y+r-2),194,281,
              fill=(255,246,208,186),width=2)
    gas.putalpha(ImageChops.multiply(gas.getchannel("A"),clip))
    stage.alpha_composite(gas)


def _pressure(stage:Image.Image,t:float,duration:float)->None:
    d=ImageDraw.Draw(stage,"RGBA")
    fraction=min(1.,t/duration)
    # Pressure source contours have coherent subsurface geometry and
    # are composited under a real shared liquid mask; no glowing circles
    # can wander into the surrounding rock.
    pressure=Image.new("RGBA",SIZE)
    pd=ImageDraw.Draw(pressure,"RGBA")
    for k in range(5):
        q=(t*.28+k*.24)%1
        alpha=round(154*(1-q)*(.3+.7*fraction))
        contour=reservoir_contour(.41+q*.54)
        pd.line((*contour,contour[0]),fill=(255,155,70,alpha),
                width=2+k%2,joint="curve")
    pressure.putalpha(ImageChops.multiply(
        pressure.getchannel("A"),_chamber_mask()))
    stage.alpha_composite(pressure)
    # Radial fractures propagate through the enclosing rock only during
    # the pressure scene. Growth is progressive (no preexisting crack).
    progress=max(0.,(fraction-.22)/.78)
    if progress<=0:
        return
    fractures=[
        [(361,1057),(306,1022),(263,978),(209,943)],
        [(730,1055),(786,1029),(833,983),(906,954)],
        [(375,1204),(321,1256),(289,1302)],
        [(714,1219),(770,1269),(819,1313)],
    ]
    for index,poly in enumerate(fractures):
        p=min(1.,max(0.,progress*1.7-index*.11))
        pos=(len(poly)-1)*p
        k=int(pos)
        coords=poly[:k+1]
        if k<len(poly)-1:
            a,b=poly[k:k+2];f=pos-k
            coords.append((a[0]*(1-f)+b[0]*f,a[1]*(1-f)+b[1]*f))
        if len(coords)>=2:
            d.line(coords,fill=(28,13,16,244),width=11,joint="curve")
            d.line(coords,fill=(255,105,37,round(85+100*progress)),
                   width=4,joint="curve")


def _ascent(stage:Image.Image,t:float,duration:float)->None:
    d=ImageDraw.Draw(stage,"RGBA")
    # Magma front rises through a fixed rock conduit; its advancement is
    # monotone over the scene and will not jump backwards or loop.
    progress=min(1.,max(0.,t/duration*1.18))
    y_front=BASE[1]-(BASE[1]-VENT[1])*progress
    flow=active_conduit_path(y_front)
    # Glow follows the very same physical rock path, rather than a second
    # straight vertical stripe that could detach from the advancing front.
    if progress>0:
        light=Image.new("RGBA",LOW)
        ld=ImageDraw.Draw(light,"RGBA")
        ld.line([(x*.25,y*.25) for x,y in flow],
                fill=(255,92,21,153),width=14,joint="curve")
        stage.alpha_composite(light.filter(
            ImageFilter.GaussianBlur(9)).resize(
                SIZE,Image.Resampling.BILINEAR))
    molten=Image.new("RGBA",SIZE)
    m=ImageDraw.Draw(molten,"RGBA")
    if progress>0:
        m.line(flow,fill=(238,75,20,255),
               width=INNER_WIDTH+3,joint="curve")
        m.line(flow,fill=(255,173,50,246),width=16,joint="curve")
        m.line(flow,fill=(255,238,135,225),width=5,joint="curve")
        for i in range(29):
            y=1020-((i*47+t*(89+i%5*7))%max(2,674*progress))
            if y<y_front or y>BASE[1]:
                continue
            x=conduit_center_x(y)+math.sin(i*1.73+t*.83)*8
            r=2+i%3
            m.ellipse((x-r,y-r*2,x+r,y+r*2),
                      fill=(255,244,164,223))
    molten.putalpha(ImageChops.multiply(molten.getchannel("A"),
                                       _conduit_mask()))
    stage.alpha_composite(molten)
    # Side cracks radiate from the center as the melt rises; their reach
    # increases continuously and stays inside the rock cross-section.
    splits=[
        [(conduit_center_x(845),845),(497,810),(462,760)],
        [(conduit_center_x(690),690),(588,655),(619,609)],
        [(conduit_center_x(530),530),(492,490),(464,448)],
    ]
    for k,split in enumerate(splits):
        reach=(1024-y_front-split[0][1])/155
        f=max(0.,min(1.,reach))
        if f<=0:
            continue
        pos=(len(split)-1)*f
        idx=int(pos)
        coords=split[:idx+1]
        if idx<len(split)-1:
            a,b=split[idx:idx+2];q=pos-idx
            coords.append((a[0]*(1-q)+b[0]*q,
                           a[1]*(1-q)+b[1]*q))
        if len(coords)>=2:
            d.line(coords,fill=(52,24,23,225),width=12,joint="curve")
            d.line(coords,fill=(249,112,35,231),width=5,joint="curve")


def draw_magma(stage: Image.Image, beat: str, t: float,
               duration: float) -> None:
    """Render one authored underground stage; no generic fallback art."""
    _validate(stage,beat,t,duration)
    # The cached geological cutaway is the destination background, not
    # re-rendered every frame. Reservoir emission is clipped to its mask.
    chamber=_molten_plate(t,duration,beat)
    chamber.putalpha(ImageChops.multiply(
        chamber.getchannel("A"),_chamber_mask()))
    stage.alpha_composite(chamber)
    _gas(stage,t,duration,pressure=beat=="pressure")
    if beat=="pressure":
        _pressure(stage,t,duration)
    elif beat=="ascent":
        _ascent(stage,t,duration)
