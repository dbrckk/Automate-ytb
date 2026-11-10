"""Original weathered rock relief for 2D/2.5D source-layer illustrations.

Only the supplied authored RGBA silhouette can receive a material. Cached
low-frequency coherent mineral grain plus branching erosion grooves preserve
the artist's original face normals, original alpha and distinct geologic
contours; no tiled bitmap, reconstruction of 3D meshes, model or paid API.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageChops, ImageDraw

VERSION = "shared-weathered-rock-p515-v1"


def _validate(source: Image.Image, seed: int) -> None:
    if (not isinstance(source, Image.Image) or source.mode != "RGBA"
            or not 128 <= source.width <= 1920
            or not 128 <= source.height <= 1920
            or type(seed) is not int or not 0 <= seed <= 1_000_000):
        raise ValueError("Invalid original 2.5D rock source")


@lru_cache(maxsize=12)
def _mineral_grain(size: tuple[int, int], seed: int) -> Image.Image:
    """One reusable multiscale mineral-density field at source resolution."""
    w,h=size
    rng=random.Random(seed)
    levels=[]
    for divisor in (81,23,7):
        sw,sh=max(4,w//divisor),max(4,h//divisor)
        raw=Image.frombytes("L",(sw,sh),
                            bytes(rng.randrange(256) for _ in range(sw*sh)))
        levels.append(raw.resize(size,Image.Resampling.BICUBIC))
    broad=Image.blend(levels[0],levels[1],.48)
    return Image.blend(broad,levels[2],.19)


def weathered_rock(source: Image.Image, *, seed: int = 45083
                   ) -> Image.Image:
    """Overlay deterministic original erosion only inside existing geology.

    This operation is called once while generating reusable base art, never
    once per 30fps encoded frame. It does not redraw faces or change the
    original source's opacity, dimensions or opaque pixel boundary.
    """
    _validate(source,seed)
    alpha=source.getchannel("A")
    if alpha.getextrema()==(0,0):
        return source.copy()
    w,h=source.size
    grain=_mineral_grain(source.size,seed)
    # Narrow tonal excursions add fine material structure but retain lit
    # polygon face normals and shadow modeling from the source terrain.
    multiplier=grain.point(
        lambda value: max(183,min(255,round(240+(value-128)*.26))))
    factor=Image.merge("RGB",(multiplier,multiplier,multiplier))
    lit=Image.blend(source.convert("RGB"),
                    ImageChops.multiply(source.convert("RGB"),factor),.67)
    result=lit.convert("RGBA")
    result.putalpha(alpha)

    # Rock-carved radiating gullies and strata are tied to source
    # coordinates. Unlike loose decorative dots, they remain fixed on the
    # cliff while the camera, smoke and lava move independently.
    relief=Image.new("RGBA",source.size)
    draw=ImageDraw.Draw(relief,"RGBA")
    rng=random.Random(seed+17)
    cx=.5*w
    summit=.251*h
    max_y=min(h-1,round(.76*h))
    for side in (-1,1):
        for channel in range(7):
            # Independent onset, bending, length and occasional forks
            # avoid parallel scratch marks resembling synthetic rainfall.
            slope=.062+channel*.049
            phase=rng.uniform(-2.,2.)
            onset=summit+13+rng.randrange(0,100)
            ending=max_y-rng.randrange(0,160)
            points=[]
            for step in range(29):
                y=onset+(ending-onset)*step/28.
                dist=y-summit
                meander=(4+dist*.029)*math.sin(dist*.016+phase)
                meander+=3.5*math.sin(dist*.041+channel*.63)
                x=cx+side*(11+slope*dist)+meander
                points.append((round(x),round(y)))
            thick=3+channel%3
            draw.line(points,fill=(17,20,28,56+channel%4*11),
                      width=thick+1,joint="curve")
            upper=[(x+2,y-3) for x,y in points]
            draw.line(upper,fill=(190,163,145,18+channel%3*8),
                      width=max(1,thick//2),joint="curve")
            if channel%2:
                fork=points[8:22]
                subsidiary=[(x+side*(j*1.8),y)
                            for j,(x,y) in enumerate(fork)]
                draw.line(subsidiary,fill=(19,25,33,44),width=2,
                          joint="curve")
    # Short, staggered sediment bands follow partial depositional beds.
    # Full-width perfectly regular lines looked like a digital wireframe.
    for stratum in range(36):
        start=rng.randrange(110,w-180)
        length=65+rng.randrange(70,220)
        y=round(.37*h+rng.uniform(0,.38*h))
        phase=rng.uniform(-2.1,2.1)
        points=[]
        for x in range(start,min(w,start+length),7):
            yy=y+6*math.sin(x*.012+phase)+3*math.sin(x*.038-phase)
            points.append((x,round(yy)))
        if len(points)>2:
            draw.line(points,fill=(185,159,143,12+stratum%5*5),
                      width=1+stratum%2,joint="curve")
    relief.putalpha(ImageChops.multiply(relief.getchannel("A"),alpha))
    result=Image.alpha_composite(result,relief)
    result.putalpha(alpha)
    return result
