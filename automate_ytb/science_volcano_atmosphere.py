"""Volcanic ash interacts with the 3D terrain and nearby atmosphere.

Causal shot-specific VFX, not a stock-image overlay: crater-emitted ash
grows into a moving wind-driven shadow, darkening only the actual projected
rock facets. Distant settling ash is rendered as a separate foreground pass.
Both are generated on a bounded quarter-resolution canvas and upsampled once.
The trajectories are explanatory stylization, not a calibrated atmosphere model.
"""
from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .science_volcano_lighting import _terrain_mask

VERSION = "volcano-causal-atmosphere-v1-rock-shadow-foreground-ash"
SIZE = (1080, 1380)
LOW = (270, 345)
ORIGIN = (540, 345)


def _validate(stage: Image.Image, t: float, duration: float) -> None:
    if (stage.mode != "RGBA" or stage.size != SIZE
            or type(t) not in (int, float)
            or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or duration <= 0 or duration > 180 or t < 0 or t > duration):
        raise ValueError("Invalid volcanic atmosphere stage or clock")


def _smooth(value: float) -> float:
    q = max(0., min(1., value))
    return q * q * (3 - 2 * q)


def cast_plume_shadow(stage: Image.Image, t: float, duration: float) -> None:
    """Cresting ash shades the same rock mesh that the eruption illuminates.

    Do not shade the entire stage: the plume is above the summit, the rock
    terrain below is the receiver, and the caption UI is drawn later.
    """
    _validate(stage, t, duration)
    growth = _smooth((t / duration - .06) / .46)
    if growth <= 0.:
        return
    shadow = Image.new("L", LOW)
    draw = ImageDraw.Draw(shadow)
    drift = (18 * t / duration + 17 * math.sin(t * .33)) * growth
    # Connected lobes move downwind over increasingly distant rock facets;
    # their size and darkness follow the growing ash column.
    for i in range(18):
        u = i / 17.
        x = (ORIGIN[0] + 145*u + drift + 14*math.sin(t*.41 + i*.72))*.25
        y = (ORIGIN[1] + 545*u + 8*math.sin(t*.37 + i*.46))*.25
        rx = (40 + u*75 + growth*71)*.25
        ry = (32 + u*92 + growth*45)*.25
        opacity = round(growth * (98 - u*27) * (.88 + .12*math.sin(t*.65+i)))
        draw.ellipse((x-rx,y-ry,x+rx,y+ry), fill=max(0, min(110,opacity)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    rock_only = ImageChops.multiply(shadow, _terrain_mask())
    if not rock_only.getbbox():
        return
    overlay = Image.new("RGBA", SIZE, (10, 15, 25, 0))
    overlay.putalpha(rock_only.resize(SIZE, Image.Resampling.BILINEAR))
    stage.alpha_composite(overlay)


def draw_windborne_ash(stage: Image.Image, t: float, duration: float) -> None:
    """Separately advected foreground ash with lift, drift and settling.

    Individual particles start at the crater; the later downward motion
    comes from a positive quadratic settling term. This final pass gives
    depth relative to sharp ballistic tephra without obscuring all geology.
    """
    _validate(stage, t, duration)
    if t <= 0:
        return
    veil = Image.new("RGBA", LOW)
    draw = ImageDraw.Draw(veil, "RGBA")
    for index in range(190):
        born = (index + .21) * duration / 205.
        age = t - born
        if not .15 < age < 3.75:
            continue
        depth = (index % 7) / 6.
        drift = (12 + 11*depth + index % 5*1.5)*age
        x = (ORIGIN[0]*.25 + drift
             + math.sin(index*2.39 + age*.43)*(3 + 8*age))
        y = (ORIGIN[1]*.25 - age*(22 + 3*depth)
             + age*age*(10 + 3*depth)
             + math.cos(index*1.71)*7*age)
        if not 2 <= x <= LOW[0]-2 or not 2 <= y <= LOW[1]-2:
            continue
        radius = 1 + (index % 3) + depth*.6
        fade = _smooth(min(1., age/.5)) * _smooth((3.75-age)/1.35)
        alpha = round((58+37*depth)*fade)
        if alpha <= 0:
            continue
        color = (137+index%4*5, 120+index%3*6, 116+index%5*5, alpha)
        draw.ellipse((x-radius, y-radius*.72, x+radius, y+radius*.72),
                     fill=color)
    stage.alpha_composite(veil.resize(SIZE, Image.Resampling.BILINEAR))
