"""Shared original semantic 2.5D silhouettes: plasma, water and volcanic ash.

This is geometry *before* final finishing: multiple curved polygonal planes,
folds and transparent occlusion painted at source resolution. It does not
extrapolate depth from flat footage, invent physical simulation, or depend on
a remote image model. Every frame is deterministically sampled from a fixed
authored seed and the same finite animation clock, without frame RNG.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageChops

VERSION = "source-authored-semantic-sheets-p525-v2-feathered-geometry"
MATERIALS = ("plasma", "water", "ash")

# Fixed palette weights are intentionally material-specific, not recolored
# copies of a single generic sine ribbon.
_SHAPES = {
    # top undulation, fold count, longitudinal speed, thickness modulation
    "plasma": (0.20, 12, 0.37, 0.22),
    "water": (0.095, 6, 0.22, 0.12),
    "ash": (0.17, 9, 0.115, 0.28),
}


def _mix(a: tuple[int, int, int], b: tuple[int, int, int],
         f: float) -> tuple[int, int, int]:
    return tuple(round(x * (1-f) + y*f) for x, y in zip(a, b))


def render_material_sheet(size: tuple[int, int], *, material: str,
                          color: tuple[int, int, int], seed: int,
                          t: float, duration: float,
                          baseline: int, thickness: int,
                          opacity: int = 100) -> Image.Image:
    """Paint a morphing, independently compositable authored RGBA depth plane.

    The two *different* organic contours define a real connected silhouette;
    a handful of nested source-space folds articulate surface curvature.
    Highlight filaments follow that silhouette instead of occupying unrelated
    circles/rectangles. The transparent plane can sit behind or ahead of any
    other independently authored 2.5D layer.
    """
    if (not isinstance(size, tuple) or len(size) != 2
            or any(type(v) is not int or not 128 <= v <= 1920 for v in size)
            or type(material) is not str or material not in MATERIALS
            or not isinstance(color, tuple) or len(color) != 3
            or any(type(c) is not int or not 0 <= c <= 255 for c in color)
            or type(seed) is not int or not 0 <= seed <= 1_000_000
            or type(t) not in (int, float)
            or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration <= 0
            or type(baseline) is not int or not 0 <= baseline < size[1]
            or type(thickness) is not int or not 24 <= thickness <= size[1]
            or type(opacity) is not int or not 1 <= opacity <= 230):
        raise ValueError("Invalid original semantic 2.5D material sheet")
    w, h = size
    amp, folds, speed, modulation = _SHAPES[material]
    rng = random.Random(seed)
    shifts = tuple(rng.uniform(0, math.tau) for _ in range(5))
    phase = speed * t
    step = max(4, min(12, w // 96))
    xx = tuple(sorted(set((*range(0, w, step), w - 1))))
    upper = []
    lower = []
    for x in xx:
        q = x / (w-1)
        # Multiscale non-periodic-looking morphology from *authored* harmonics.
        # The low-frequency folds animate slowly; high-frequency edge erosion
        # stays anchored in material coordinates, preventing random shimmer.
        wav = (0.58 * math.sin(q*math.tau*1.7 + phase + shifts[0])
               + 0.25 * math.sin(q*math.tau*4.2 - .56*phase + shifts[1])
               + 0.12 * math.sin(q*math.tau*11.1 + shifts[2])
               + 0.05 * math.cos(q*math.tau*23.3 + shifts[3]))
        y0 = baseline + thickness*amp*wav
        depth = thickness*(0.84 + modulation*(
            .57*math.sin(q*math.tau*2.3 + .37*phase + shifts[4])
            + .43*math.sin(q*math.tau*6.2 - .27*phase + shifts[2])))
        lower_mod = thickness*0.045*math.sin(q*math.tau*9.7 + shifts[1])
        upper.append((x, round(y0)))
        lower.append((x, round(y0 + depth + lower_mod)))

    plane = Image.new("RGBA", size)
    painter = ImageDraw.Draw(plane, "RGBA")
    shadow = _mix(color, (4, 16, 35) if material != "ash"
                  else (30, 33, 41), .71)
    light = _mix(color, (233, 254, 245) if material == "plasma"
                 else (204, 249, 255) if material == "water"
                 else (205, 197, 188), .40)
    body = _mix(color, (9, 34, 57) if material != "ash"
                else (49, 43, 48), .27)
    # The rear occlusion bank is offset downwards from the same geometry.
    # This is an *independent material plane* with an asymmetrical underside.
    drop = max(3, round(thickness*.065))
    painter.polygon([(x,y+drop) for x,y in upper] +
                    [(x,y+drop) for x,y in reversed(lower)],
                    fill=(*shadow, round(opacity*.47)))
    painter.polygon(upper + list(reversed(lower)),
                    fill=(*body, round(opacity*.83)))

    # Source-aligned fold strips have different depths, not opaque bands.
    # The neighboring contours remain smoothly connected at every x.
    for k in range(folds):
        f = (k + .65) / (folds + .8)
        path = []
        for (x,yt),(_,yb) in zip(upper, lower):
            q = x/(w-1)
            shiver = thickness*.014*math.sin(
                q*math.tau*(6.0+k*.21) + phase*(1.0+.035*k) + k*1.17)
            path.append((x, round(yt+(yb-yt)*f + shiver)))
        warm = material == "plasma" and k%4==0
        shade = light if k%3 != 1 else shadow
        alpha = round(opacity*(.57 if warm else .29 if k%3 else .38))
        line_width = max(1, round(thickness*(.009 if material=="plasma"
                                            else .013)))
        painter.line(path, fill=(*shade,alpha), width=line_width,
                     joint="curve")

    # Vertical plasma striations follow the upper and lower shapes. Water
    # receives a restrained crest; ash only retains irregular stratum folds.
    if material == "plasma":
        for i in range(0,len(xx)-1,2):
            x = xx[i]
            yt = upper[i][1]
            yb = lower[i][1]
            offset = 6*math.sin(i*.71 + phase*.8)
            painter.line(((x,yt),(x+offset*.4,round(yt+(yb-yt)*.43)),
                          (x+offset,round(yb*.92+yt*.08))),
                         fill=(*light,round(opacity*.39)),
                         width=1 if i%3 else 2, joint="curve")
    elif material == "water":
        painter.line(upper, fill=(*light,round(opacity*.66)),
                     width=max(1,round(thickness*.025)),joint="curve")
    # Without a lateral alpha envelope, any sheet spanning a 9:16 frame
    # becomes a perfectly vertical opaque panel at both edges. Feather the
    # *geometry source alpha*, not the final video or subtitle pixels.
    edge_fraction = .18 if material=="plasma" else (.08 if material=="water" else .13)
    ramp=[]
    for x in range(w):
        q=x/(w-1)
        u=max(0.,min(1.,q/edge_fraction,(1-q)/edge_fraction))
        fade=u*u*(3-2*u)
        # Deterministic spatial density, not a new random-per-frame texture.
        density=(.72+.28*math.sin(q*math.tau*3.9+phase*.27+shifts[3])**2
                 if material=="plasma" else 1.)
        ramp.append(max(0,min(255,round(255*fade*density))))
    alpha_x=Image.new("L",(w,1))
    alpha_x.putdata(ramp)
    alpha_mask=alpha_x.resize(size,Image.Resampling.NEAREST)
    plane.putalpha(ImageChops.multiply(plane.getchannel("A"),alpha_mask))
    return plane
