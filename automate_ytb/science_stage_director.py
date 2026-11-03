"""Deterministic source-space cinematography for authored science action fields.

This reusable director draws no substitute/fake imagery: individual domain
renderers still generate all original frames. It reframes *moving* 1080×1380
scene layers with independent, physically uniform camera trajectories.
Editorial captions are composed later at stationary 9:16 safe coordinates.
"""
from __future__ import annotations

import math
from PIL import Image

VERSION = "original-science-director-v2-event-paced"
FRAME_SIZE = (1080, 1380)

# Shot-dependent pacing and focal height. In underground scenes the camera
# closes in on magma; in ascent it tracks upwards; eruption follows the plume.
# x,y are source-space foci, not pixel offsets applied to a stretched image.
SHOTS: dict[str, dict[str, tuple[float, float, float, float, float, float]]] = {
    "volcano": {
        "magma": (1.37, 1.46, 541, 551, 897, 901),
        "pressure": (1.42, 1.49, 548, 532, 900, 886),
        "ascent": (1.31, 1.40, 550, 536, 901, 640),
        "eruption": (1.12, 1.23, 533, 554, 568, 556),
        "lava": (1.09, 1.18, 545, 559, 730, 708),
    },
    "aurora": {
        "solar_wind": (1.045, 1.065, 540, 540, 665, 667),
        "magnetic_field": (1.15, 1.25, 641, 628, 660, 663),
        "collisions": (1.18, 1.28, 524, 552, 677, 657),
        "emission": (1.25, 1.32, 538, 531, 671, 682),
        "curtains": (1.07, 1.14, 538, 552, 665, 649),
    },
}


# Event-driven camera progress: the subject remains framed while the causal
# animation develops, then the camera completes its move during the payoff.
# Piecewise smoothstep is C1 continuous at each knot (no velocity jump).
# Fractions are authored visual timing, not guessed from audio or fact claims.
EVENT_PROGRESS: dict[str, dict[str, tuple[tuple[float, float], ...]]] = {
    "volcano": {
        "magma": ((0.0,0.0),(.34,.12),(.78,.86),(1.0,1.0)),
        "pressure": ((0.0,0.0),(.27,.07),(.76,.91),(1.0,1.0)),
        "ascent": ((0.0,0.0),(.16,.03),(.86,.94),(1.0,1.0)),
        "eruption": ((0.0,0.0),(.20,.07),(.63,.87),(1.0,1.0)),
        "lava": ((0.0,0.0),(.23,.06),(.85,.96),(1.0,1.0)),
    },
    "aurora": {
        "solar_wind": ((0.0,0.0),(.18,.05),(.83,.93),(1.0,1.0)),
        "magnetic_field": ((0.0,0.0),(.22,.06),(.76,.90),(1.0,1.0)),
        "collisions": ((0.0,0.0),(.28,.11),(.75,.91),(1.0,1.0)),
        "emission": ((0.0,0.0),(.32,.09),(.73,.91),(1.0,1.0)),
        "curtains": ((0.0,0.0),(.16,.04),(.84,.96),(1.0,1.0)),
    },
}


def event_progress(topic: str, beat: str, fraction: float) -> float:
    """C1-continuous authored action timing with bounded output [0, 1]."""
    if (topic not in EVENT_PROGRESS or beat not in EVENT_PROGRESS[topic]
            or type(fraction) not in (float,int)
            or not math.isfinite(fraction) or not 0 <= fraction <= 1):
        raise ValueError("Invalid event-directed camera progress")
    knots=EVENT_PROGRESS[topic][beat]
    for i in range(len(knots)-1):
        x0,y0=knots[i]
        x1,y1=knots[i+1]
        if fraction<=x1:
            u=(fraction-x0)/(x1-x0)
            eased=u*u*(3-2*u)
            return y0+(y1-y0)*eased
    return 1.0


def pose(topic: str, beat: str, t: float,
         duration: float) -> tuple[float, float, float]:
    """Continuous normalized camera pose; crop stays inside authored art."""
    if (topic not in SHOTS or beat not in SHOTS.get(topic, ())
            or type(t) not in (float, int)
            or type(duration) not in (float, int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or duration <= 0 or duration > 180 or not 0 <= t <= duration):
        raise ValueError("Unsupported science camera or animation clock")
    q=t/duration
    # Smoothstep is C1 continuous at start and end, avoiding camera jumps
    # when an individual action begins or ends.
    ease=event_progress(topic,beat,q)
    start_z,end_z,start_x,end_x,start_y,end_y=SHOTS[topic][beat]
    zoom=start_z+(end_z-start_z)*ease
    cx=start_x+(end_x-start_x)*ease
    cy=start_y+(end_y-start_y)*ease
    width,height=FRAME_SIZE
    half_w=width/(2*zoom)
    half_h=height/(2*zoom)
    cx=max(half_w,min(width-half_w,cx))
    cy=max(half_h,min(height-half_h,cy))
    return zoom,cx,cy


def reframe(stage: Image.Image, topic: str, beat: str,
            t: float, duration: float) -> Image.Image:
    """One filtered uniform magnification; no white margins or sprite warp."""
    if stage.size != FRAME_SIZE or stage.mode != "RGBA":
        raise ValueError("Expected opaque 1080x1380 original RGBA stage")
    z,cx,cy=pose(topic,beat,t,duration)
    inv=1.0/z
    w,h=FRAME_SIZE
    # source=(screen / zoom) + source-world origin, same zoom on both
    # axes. BILINEAR keeps CPU-only Action renders within practical limits.
    affine=(inv,0.0,cx-w*inv/2,
            0.0,inv,cy-h*inv/2)
    return stage.transform(FRAME_SIZE,Image.Transform.AFFINE,affine,
                           resample=Image.Resampling.BILINEAR)
