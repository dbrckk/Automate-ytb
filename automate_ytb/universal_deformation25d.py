"""Deterministic non-rigid secondary motion for authored RGBA 2.5D parts.

A bounded source-space horizontal mesh warp lets flexible artwork bend about
its *actual authored hinge*. All displacement is continuous, derived from
the continuous-camera frame clock and the original sprite's dimensions.
There is no neural inference, unreviewed source image, per-frame randomness,
or dynamically downloaded model. Rigid joints remain untouched.
"""
from __future__ import annotations

import math

from PIL import Image

VERSION = "bounded-hinge-anchored-rgba-sway-v1"
_REQUIRED = frozenset(("kind","amount","cycles","offset"))


def _number(value, name: str, low: float, high: float) -> float:
    if (type(value) not in (int,float) or not math.isfinite(value)
            or not low<=value<=high):
        raise ValueError(f"Invalid non-rigid {name}")
    return float(value)


def validate_deformation(raw) -> dict | None:
    """Explicit and tightly bounded motion; no guessed semantic category."""
    if raw is None:
        return None
    if type(raw) is not dict or set(raw)!=_REQUIRED or raw.get("kind")!="sway":
        raise ValueError("Deform must be a complete authored sway specification")
    return {
        "kind":"sway",
        "amount":_number(raw["amount"],"amount",.005,.12),
        "cycles":_number(raw["cycles"],"cycles",.25,3.),
        "offset":_number(raw["offset"],"offset",0.,1.),
    }


def warp_sway_sprite(sprite: Image.Image, *, pivot: list[float],
                     deform: dict, phase: float) -> tuple[Image.Image, tuple[float,float]]:
    """Warp a cached original sprite once per frame, with a fixed joint point.

    The mesh is mapped output-to-source in bounded horizontal strips.
    At pivot.y the displacement is *exactly zero*, so an attached limb
    never detaches from its inherited parent anchor. The returned pivot
    is in padded output pixels, ready for the existing rigid rotation.
    """
    if (not isinstance(sprite,Image.Image) or sprite.mode!="RGBA"
            or not 8<=sprite.width<=3072
            or not 8<=sprite.height<=3072
            or sprite.width*sprite.height>7_000_000):
        raise ValueError("Non-rigid source must be bounded RGBA")
    if (type(pivot) is not list or len(pivot)!=2):
        raise ValueError("A warped original actor requires a joint pivot")
    px=_number(pivot[0],"pivot x",0.,1.)
    py=_number(pivot[1],"pivot y",0.,1.)
    phase=_number(phase,"phase",0.,1.)
    params=validate_deformation(deform)
    if params is None:
        raise ValueError("A deformed sprite needs an authored deformation")
    w,h=sprite.size
    margin=math.ceil(params["amount"]*w)+3
    source=Image.new("RGBA",(w+2*margin,h))
    source.alpha_composite(sprite,(margin,0))
    frequency=math.sin(math.tau*(phase*params["cycles"]+params["offset"]))
    dx_max=params["amount"]*w*frequency
    def shift(y: int) -> float:
        return dx_max*(py-y/h)
    bands=max(8,min(32,round(h/30)))
    mesh=[]
    for index in range(bands):
        top=round(h*index/bands)
        bottom=round(h*(index+1)/bands)
        if bottom<=top:
            continue
        a,b=shift(top),shift(bottom)
        mesh.append(((0,top,source.width,bottom),
                     (-a,top,-b,bottom,
                      source.width-b,bottom,source.width-a,top)))
    warped=source.transform(source.size,Image.Transform.MESH,mesh,
                            resample=Image.Resampling.BICUBIC,
                            fillcolor=(0,0,0,0))
    return warped,(margin+px*w,py*h)
