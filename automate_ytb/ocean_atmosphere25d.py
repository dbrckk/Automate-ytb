"""Original star-free continuous undersea environment for science and nature.

A purely illustrated, reusable physical atmosphere plate with diffused
light shafts and organic 2.5D water/sediment sources. Static expensive art
is cached per story; moving physical details are painted by scene modules.
No starfield, outer-space conventions, downloaded bitmap, 3D or paid AI.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFilter

from .organic_environment25d import terrain_strata, water_caustics

VERSION = "star-free-original-underwater-environment-25d-p514-v2"
SIZE = (1080,1920)

# R=0..255 physical palette continuity: dark header and subtitle zones,
# brighter illustrated surface world, then depth-dependent absorption.
_STOPS = (
    (0, (6,22,43)),
    (460, (9,43,66)),
    (780, (20,94,123)),
    (1180, (10,60,91)),
    (1510, (8,40,65)),
    (1920, (5,23,43)),
)


@lru_cache(maxsize=16)
def underwater_background(seed: int) -> Image.Image:
    """An opaque 9:16 undersea world, stable across every video frame."""
    if type(seed) is not int or not 0<=seed<=2**64:
        raise ValueError("Invalid deterministic ocean atmosphere seed")
    plate=Image.new("RGBA",SIZE)
    painter=ImageDraw.Draw(plate)
    stop=0
    for y in range(SIZE[1]):
        while stop+2<len(_STOPS) and y>=_STOPS[stop+1][0]:
            stop+=1
        y0,a=_STOPS[stop]
        y1,b=_STOPS[stop+1]
        z=(y-y0)/(y1-y0)
        # Smooth radiometric transitions, no colored bands or hard cuts.
        z=z*z*(3-2*z)
        rgb=tuple(round(aa+(bb-aa)*z) for aa,bb in zip(a,b))
        painter.line((0,y,1080,y),fill=(*rgb,255))
    # Broad source-space diffuse rays: no star-like noise in the blue sea.
    rays=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(rays,"RGBA")
    for index in range(5):
        x0=120+index*183
        fan=65+index%3*23
        d.polygon(((x0-22,480),(x0+15,480),
                   (x0+125+fan,1400),(x0+10-fan,1400)),
                  fill=(135,226,238,12+index%3*5))
    plate=Image.alpha_composite(plate,rays.filter(
        ImageFilter.GaussianBlur(57)))
    material_seed=seed%900_000
    # An original, softly integrated water volume over the entire main
    # action region, instead of a disconnected postcard-like image card.
    plate.alpha_composite(water_caustics(
        (1080,800),seed=material_seed+103,
        color=(131,221,235),opacity=34),(0,570))
    # Distant seafloor is a separate true-alpha illustrated material,
    # faded into water rather than a triangular opaque horizon.
    plate.alpha_composite(terrain_strata(
        (1080,500),seed=(material_seed+2007)%1_000_000,
        color=(29,66,77),opacity=68),(0,1180))
    return plate
