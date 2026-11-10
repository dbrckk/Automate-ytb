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
        for channel in range(11):
            slope=.059+channel*.026
            phase=rng.uniform(-1.5,1.5)
            points=[]
            for step in range(29):
                y=summit+(max_y-summit)*step/28.
                dist=y-summit
                x=(cx+side*(12+slope*dist)+
                   (2.5+dist*.015)*math.sin(dist*.019+phase)
                   +4*math.sin(dist*.047+channel*.37))
                points.append((round(x),round(y)))
            thick=3+channel%4
            draw.line(points,fill=(17,20,28,65+channel%4*8),
                      width=thick+2,joint="curve")
            upper=[(x+2,y-3) for x,y in points]
            draw.line(upper,fill=(190,163,145,24+channel%3*9),
                      width=max(1,thick//2),joint="curve")
    # Irregular depositional layers break large flat facets without adding
    # a regular grid, while the source alpha clips any crossing sky lines.
    for stratum in range(18):
        y=round(.35*h+stratum*(h*.026))
        points=[]
        for x in range(0,w+8,8):
            yy=(y+8*math.sin(x*.014+stratum*.57)
                  +3*math.sin(x*.046-stratum*.91))
            points.append((x,round(yy)))
        draw.line(points,fill=(191,158,143,13+stratum%4*5),
                  width=1+stratum%3,joint="curve")
    relief.putalpha(ImageChops.multiply(relief.getchannel("A"),alpha))
    result=Image.alpha_composite(result,relief)
    result.putalpha(alpha)
    return result
