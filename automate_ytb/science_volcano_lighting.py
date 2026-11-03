"""Causal lava and eruption light, masked to the 3D volcano's actual facets.

A cheap low-resolution warm light field is masked by the projected mesh alpha.
Moving lava sources illuminate adjacent rock but never the sky or UI. This is
stylized local illumination, not ray tracing or physically correct PBR.
"""
from __future__ import annotations
from functools import lru_cache
import math
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from .science_volcano_mesh import shaded_terrain

VERSION="volcano-causal-emission-v1-rock-masked-light"
SIZE=(1080,1380)
LOW=(270,345)

@lru_cache(maxsize=1)
def _terrain_mask() -> Image.Image:
    return shaded_terrain().getchannel("A").resize(LOW,Image.Resampling.BOX)

def illuminate_rock(stage:Image.Image,
                    sources:list[tuple[float,float,float,float]]) -> None:
    """Sources = [(screen_x,screen_y,spread_radius,energy[0..1]), ...]."""
    if stage.mode!="RGBA" or stage.size!=SIZE:
        raise ValueError("Volcano emitter requires source-sized RGBA stage")
    if not isinstance(sources,list) or len(sources)>24:
        raise ValueError("Volcano emitter list exceeds limit")
    if not sources:
        return
    light=Image.new("L",LOW)
    d=ImageDraw.Draw(light)
    for src in sources:
        if (not isinstance(src,(tuple,list)) or len(src)!=4 or any(
                type(value) not in (float,int) or not math.isfinite(value)
                for value in src)):
            raise ValueError("Nonfinite volcanic light source")
        x,y,radius,power=src
        if not (-500<=x<=1580 and -500<=y<=1880 and
                1<=radius<=750 and 0<=power<=1):
            raise ValueError("Unsafe volcanic light dimensions")
        if power<=0:
            continue
        cx,cy,rr=x*.25,y*.25,radius*.25
        d.ellipse((round(cx-rr),round(cy-rr),
                   round(cx+rr),round(cy+rr)),fill=round(153*power))
    if not light.getbbox():
        return
    spread=light.filter(ImageFilter.GaussianBlur(13))
    alpha=ImageChops.multiply(spread,_terrain_mask())
    if not alpha.getbbox():
        return
    overlay=Image.new("RGBA",SIZE,(255,116,39,0))
    overlay.putalpha(alpha.resize(SIZE,Image.Resampling.BILINEAR))
    stage.alpha_composite(overlay)
