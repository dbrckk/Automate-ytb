"""Reusable original 2.5D animated water-vortex material for science and nature.

A cached opaque-to-translucent 2D source plane is combined with independent
moving streamlines. This is a qualitative visualization of circulation, not
latitude-specific Coriolis direction, a fluid simulation, or physical 3D.
No stock photos, paid inference, stochastic frame noise or downloaded media.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageChops, ImageDraw

VERSION = "shared-animated-surface-vortex-25d-p514-v1"

PALETTES = {
    "ocean": (30, 111, 162),
    "lagoon": (25, 131, 146),
    "storm": (41, 79, 120),
}


def _validate(diameter: int, palette: str, seed: int) -> None:
    if (type(diameter) is not int or not 128 <= diameter <= 900
            or not isinstance(palette,str) or palette not in PALETTES
            or type(seed) is not int or not 0 <= seed <= 1_000_000):
        raise ValueError("Invalid original fluid-material source")


def _byte(v: float) -> int:
    return max(0, min(255, round(v)))


@lru_cache(maxsize=18)
def vortex_source(diameter: int, *, palette: str = "ocean",
                  seed: int = 385) -> Image.Image:
    """Cached source with organic rim, shaded spiral fabric and real RGBA."""
    _validate(diameter,palette,seed)
    # Low-frequency lighting is authored once on a bounded original plate;
    # high-frequency moving detail is rendered independently at full size.
    resolution=min(256,max(96,diameter//3))
    source=Image.new("RGBA",(resolution,resolution))
    px=source.load()
    rnd=random.Random(seed)
    phase=rnd.uniform(0,math.tau)
    tint=PALETTES[palette]
    mid=(resolution-1)/2
    half=resolution/2
    for y in range(resolution):
        ny=(y-mid)/half
        for x in range(resolution):
            nx=(x-mid)/half
            r=math.hypot(nx,ny)
            if r>=1:
                continue
            angle=math.atan2(ny,nx)
            edge=max(0.,min(1.,(1-r)/.065))
            edge=edge*edge*(3-2*edge)
            core=math.exp(-(r/.19)**2)
            body=math.exp(-((r-.69)/.30)**2)
            striations=(math.sin(19*r-4*angle+phase)*9
                        +math.sin(39*r+7*angle+phase*.34)*4)
            reflection=23*max(0.,-.72*nx-.5*ny)*(1-core)
            value=12*body-18*core+striations+reflection
            px[x,y]=(
                _byte(tint[0]+value*.57),
                _byte(tint[1]+value),
                _byte(tint[2]+value*.85),
                _byte((175+48*body+25*(1-r))*edge),
            )
    return source.resize((diameter,diameter),Image.Resampling.BICUBIC)


def vortex_frame(diameter: int, t: float, *,
                 palette: str = "ocean", seed: int = 385,
                 clockwise: bool = True) -> Image.Image:
    """Moving water filaments share a coherent orbit, not a spun flat image.

    Returned RGBA is independently authored at each timestamp and clipped
    to the source's exact alpha. Marker and teaching overlay are separate.
    """
    _validate(diameter,palette,seed)
    if (type(t) not in (int,float) or not math.isfinite(t)
            or not 0 <= t <= 180 or type(clockwise) is not bool):
        raise ValueError("Invalid original water animation clock")
    source=vortex_source(diameter,palette=palette,seed=seed)
    overlay=Image.new("RGBA",source.size)
    draw=ImageDraw.Draw(overlay,"RGBA")
    center=(diameter-1)/2.
    radius=diameter*.475
    direction=1 if clockwise else -1
    # Nonidentical streamline spirals add material structure; paths remain
    # smoothly moving and bounded in source space for the whole 180s clip.
    for arm in range(12):
        phase=(arm*math.tau/12+direction*t*.24
               +.15*math.sin(arm*.7+seed*.01))
        points=[]
        for i in range(72):
            f=i/71
            radial=(.16+.71*f)*radius
            angle=phase+direction*(.20+f*2.4)
            angle+=.045*math.sin(f*13+arm)
            points.append((center+radial*math.cos(angle),
                           center+radial*math.sin(angle)*.93))
        shade=(119,211,233,85) if arm%3 else (208,245,254,122)
        dark=(16,56,102,52)
        draw.line([(x,y+max(1,diameter*.006)) for x,y in points],
                  fill=dark,width=max(2,round(diameter*.012)),joint="curve")
        draw.line(points,fill=shade,width=max(2,round(diameter*.006)),
                  joint="curve")
        if arm%2==0:
            tip=points[30+arm%6*5]
            r=max(2,round(diameter*.005))
            draw.ellipse((tip[0]-r,tip[1]-r,tip[0]+r,tip[1]+r),
                         fill=(226,249,255,172))
    # Clip all moving strokes to the very same original water silhouette.
    alpha=ImageChops.multiply(
        overlay.getchannel("A"),source.getchannel("A"))
    overlay.putalpha(alpha)
    return Image.alpha_composite(source,overlay)
