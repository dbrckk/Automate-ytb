"""Original shareable time-advected 2.5D mineral and water source fields.

Two sub-surface noise layers shift at different velocities over a cached,
low-resolution coherent source. This yields moving physical texture rather
than dots, rigid rotated screenshots or per-frame white-noise flicker.
Clipping to a scene-specific material source mask remains the caller's job.
No GPU, 3D, stock images, network access, image models or paid tokens.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageChops, ImageOps

VERSION = "time-advected-shared-water-magma-source25d-p518-v1"
MATERIALS = ("magma", "water")
# Colors represent original illustration materials, not measured temperature.
PALETTES = {
    "magma": ((43, 12, 19), (253, 152, 58), 49, 126),
    "water": ((13, 48, 84), (144, 218, 239), 34, 94),
}


def _validate(size: tuple[int, int], seconds: float, material: str,
              seed: int) -> None:
    if (not isinstance(size, tuple) or len(size) != 2
            or any(type(q) is not int or not 128 <= q <= 900
                   for q in size)
            or type(seconds) not in (int, float) or not math.isfinite(seconds)
            or not 0 <= seconds <= 180
            or type(material) is not str or material not in MATERIALS
            or type(seed) is not int or not 0 <= seed <= 1_000_000):
        raise ValueError("Invalid original 2.5D dynamic material source")


@lru_cache(maxsize=18)
def _source_planes(size: tuple[int, int], seed: int) -> tuple[Image.Image,...]:
    """Cached multi-frequency source space; frames never reseed their noise."""
    w,h=size
    sw=min(192,max(72,w//3))
    sh=min(160,max(56,h//3))
    rng=random.Random(seed)
    layers=[]
    for divisor in (16,7,3):
        a=max(4,sw//divisor)
        b=max(4,sh//divisor)
        raw=Image.frombytes("L",(a,b),
                            bytes(rng.randrange(256) for _ in range(a*b)))
        layers.append(raw.resize((sw,sh),Image.Resampling.BICUBIC))
    return tuple(layers)


def moving_material(size: tuple[int,int], seconds: float, *,
                    material: str, seed: int = 1701) -> Image.Image:
    """RGBA original source: continuously advected multi-scale light/shadow.

    All expensive source noise is cached. Per-frame work is only offsetting
    three small, stable material planes and resampling once to requested
    native source size. 30 FPS videos need no per-pixel Python loops.
    """
    _validate(size,seconds,material,seed)
    low,mid,high=_source_planes(size,seed)
    # Velocity differs with scale and material. This is stylized convection,
    # not a numerical fluid solver; its structure does not flicker or jump
    # because the same source planes are advected at every scene timestamp.
    direction=1 if material=="magma" else -1
    low=ImageChops.offset(low,round(seconds*1.6*direction),
                          round(seconds*.35))
    mid=ImageChops.offset(mid,round(seconds*-3.5*direction),
                          round(seconds*.9*direction))
    high=ImageChops.offset(high,round(seconds*6.1*direction),
                           round(seconds*-1.2))
    density=Image.blend(low,mid,.46)
    density=Image.blend(density,high,.21)
    dark,bright,a_min,a_max=PALETTES[material]
    color=ImageOps.colorize(density,black=dark,white=bright)
    # Deep and light source-space variation, with bounded translucency.
    opacity=density.point([
        min(255,max(0,round(a_min+(a_max-a_min)*i/255)))
        for i in range(256)
    ])
    image=Image.merge("RGBA",(*color.split(),opacity))
    return image.resize(size,Image.Resampling.BILINEAR)
