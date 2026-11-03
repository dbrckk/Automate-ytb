"""Deterministic source-space cinematography for authored science action fields.

This reusable director draws no substitute/fake imagery: individual domain
renderers still generate all original frames. It reframes *moving* 1080×1380
scene layers with independent, physically uniform camera trajectories.
Editorial captions are composed later at stationary 9:16 safe coordinates.
"""
from __future__ import annotations

import math
from PIL import Image

VERSION = "original-science-director-v3-synth-phrase-synchronized-camera"
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


# Camera reactions are tied to a narrated physical action, not arbitrary
# decorative shake. Smooth compact pulses preserve the scene boundary pose.
# (event fraction, zoom emphasis, x offset, y offset, width fraction)
ACTION_CUES = {
    "volcano": {
        "magma": (.54, .014, 0, 10, .28),
        "pressure": (.69, .026, -8, 9, .24),
        "ascent": (.63, .018, 0, -15, .32),
        "eruption": (.46, .036, 0, -18, .24),
        "lava": (.71, .018, 14, 8, .29),
    },
    "aurora": {
        "solar_wind": (.60, .010, -5, 0, .28),
        "magnetic_field": (.52, .014, 7, -3, .32),
        "collisions": (.54, .019, 0, -6, .26),
        "emission": (.61, .021, 0, -6, .25),
        "curtains": (.67, .012, 9, -5, .35),
    },
}


def action_envelope(topic: str, beat: str, progress: float, *,
                    event_progress: float | None = None) -> float:
    """C1-continuous compact emphasis, zero at both scene boundaries."""
    if (topic not in ACTION_CUES or beat not in ACTION_CUES[topic]
            or type(progress) not in (int, float)
            or not math.isfinite(progress) or not 0 <= progress <= 1):
        raise ValueError("Unsupported action cue or progress")
    center, _, _, _, width = ACTION_CUES[topic][beat]
    if event_progress is not None:
        if (type(event_progress) not in (int,float)
                or not math.isfinite(event_progress)
                or not 0<=event_progress<=1):
            raise ValueError("Invalid speech-driven action position")
        # The camera pulse must vanish at the first and last frame.
        center=max(width,min(1-width,event_progress))
    # The impulse must vanish at BOTH scene boundaries. Clipping its
    # support also avoids floating-point residuals at nominal endpoints.
    support=min(width,center,1-center)
    distance=abs(progress-center)
    if distance>=support-1e-12:
        return 0.
    d=distance/support
    # Squared smoothstep gives a soft anticipation and lingering decay.
    x = 1-d
    return (x*x*(3-2*x))**2


def pose(topic: str, beat: str, t: float,
         duration: float, *, event_progress: float | None = None
         ) -> tuple[float, float, float]:
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
    ease=q*q*(3-2*q)
    start_z,end_z,start_x,end_x,start_y,end_y=SHOTS[topic][beat]
    zoom=start_z+(end_z-start_z)*ease
    cx=start_x+(end_x-start_x)*ease
    cy=start_y+(end_y-start_y)*ease
    # A physically motivated event beat (pressure build-up, vent burst,
    # collision, photon emission) gives each shot a small transient emphasis.
    # The pulse vanishes at shot boundaries: no transition jump.
    _,push,offset_x,offset_y,_=ACTION_CUES[topic][beat]
    reaction=action_envelope(topic,beat,q,event_progress=event_progress)
    zoom+=push*reaction
    cx+=offset_x*reaction
    cy+=offset_y*reaction
    width,height=FRAME_SIZE
    half_w=width/(2*zoom)
    half_h=height/(2*zoom)
    cx=max(half_w,min(width-half_w,cx))
    cy=max(half_h,min(height-half_h,cy))
    return zoom,cx,cy


def reframe(stage: Image.Image, topic: str, beat: str,
            t: float, duration: float, *,
            event_progress: float | None = None) -> Image.Image:
    """One filtered uniform magnification; no white margins or sprite warp."""
    if stage.size != FRAME_SIZE or stage.mode != "RGBA":
        raise ValueError("Expected opaque 1080x1380 original RGBA stage")
    z,cx,cy=pose(topic,beat,t,duration,event_progress=event_progress)
    inv=1.0/z
    w,h=FRAME_SIZE
    # source=(screen / zoom) + source-world origin, same zoom on both
    # axes. BILINEAR keeps CPU-only Action renders within practical limits.
    affine=(inv,0.0,cx-w*inv/2,
            0.0,inv,cy-h*inv/2)
    return stage.transform(FRAME_SIZE,Image.Transform.AFFINE,affine,
                           resample=Image.Resampling.BILINEAR)
