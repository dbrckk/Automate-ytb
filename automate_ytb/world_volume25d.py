"""Original, reusable feathered environmental light volumes for 2.5D video.

World lights are not cards: one cached coherent volume mask fades radiometric
color and motion into the established environment on all sides. Broad,
seed-locked variations prevent a perfect ellipse or a rectangular matte.
The art is deterministic, CPU-only and independent of paid services/3D.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image

VERSION = "original-feathered-environmental-world-volume-p519-v1"
KINDS = ("water", "haze", "smoke")


def world_volume_alpha(size: tuple[int,int], *, kind: str = "water",
                       seed: int = 4135) -> Image.Image:
    if (not isinstance(size,tuple) or len(size)!=2 or
            any(type(x) is not int or not 128<=x<=1920 for x in size)
            or type(kind) is not str or kind not in KINDS
            or type(seed) is not int or not 0<=seed<=1_000_000):
        raise ValueError("Invalid original source-world blending geometry")
    return _cached_alpha(size,kind,seed)


@lru_cache(maxsize=20)
def _cached_alpha(size:tuple[int,int],kind:str,seed:int)->Image.Image:
    w,h=size
    sw=min(288,max(96,w//4))
    sh=min(288,max(96,h//4))
    image=Image.new("L",(sw,sh))
    pix=image.load()
    phase=random.Random(seed).uniform(-math.pi,math.pi)
    widths={"water":(.045,.034),"haze":(.072,.048),
            "smoke":(.085,.061)}
    wx,wy=widths[kind]
    for y in range(sh):
        ny=(y-(sh-1)/2)/((sh-1)/2)
        for x in range(sw):
            nx=(x-(sw-1)/2)/((sw-1)/2)
            # No frame-shaped hard edges; even the broad caustic world fades
            # as an irregular environmental source volume into base water.
            warped_x=nx+wx*math.sin(3.7*ny+phase) * (1-abs(nx)*.22)
            warped_y=ny+wy*math.cos(4.4*nx-phase*.7)
            radial=math.hypot(warped_x,warped_y)
            z=max(0.,min(1.,(1.02-radial)/.46))
            value=z*z*(3-2*z)
            # Truly empty outer pixels; zero-alpha source remains invisible.
            if x==0 or x==sw-1 or y==0 or y==sh-1:
                value=0.
            pix[x,y]=round(255*value)
    return image.resize(size,Image.Resampling.BICUBIC)
