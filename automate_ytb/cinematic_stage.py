"""Deterministic CPU cinematic reframing for 9:16 original science.

A single source-space affine crop magnifies the authored world uniformly;
the electrical channel geometry is never stretched and voice timings remain
untouched. Each topic beat gets an individual continuous camera trajectory.
"""
from __future__ import annotations
import math
from PIL import Image

CAMERA_VERSION = "science-stage-camera-v2-vertical-action-follow"
SOURCE_SIZE = (1080, 930)
OUTPUT_SIZE = (1080, 1380)
# Zoom, X and Y targets refer to the same authored lightning geometry.
# Charge separation stays wide; the descending leader pans toward the mast;
# connection holds contact in frame; return tracks the bolt upward and thunder
# pulls back to reveal its expanding shock wave. All motion is smooth, bounded
# and applied to the original moving content, not an artificially frozen card.
SHOT_PATHS = {
    "charge": (1.57, 1.69, 495.0, 535.0, 415.0, 460.0),
    "leader": (1.73, 1.92, 505.0, 602.0, 350.0, 560.0),
    "connection": (1.78, 1.90, 600.0, 655.0, 532.0, 565.0),
    "return": (1.82, 1.91, 677.0, 520.0, 570.0, 395.0),
    "thunder": (1.79, 1.56, 650.0, 570.0, 550.0, 470.0),
}


def camera_pose(beat: str, t: float, duration: float) -> tuple[float, float, float]:
    if (beat not in SHOT_PATHS
            or type(t) not in (float, int)
            or type(duration) not in (float, int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration == 0):
        raise ValueError("Invalid cinematic stage clock or beat")
    p = t / duration
    ease = p*p*(3-2*p)
    start_zoom, stop_zoom, x0, x1, y0, y1 = SHOT_PATHS[beat]
    zoom = start_zoom + (stop_zoom-start_zoom)*ease
    focus_x = x0 + (x1-x0)*ease
    focus_y = y0 + (y1-y0)*ease
    if beat == "return":
        envelope = math.exp(-((p-.23)/.09)**2)
        focus_x += 3.5*envelope*math.sin(t*27)
    half_w = OUTPUT_SIZE[0]/zoom/2
    half_h = OUTPUT_SIZE[1]/zoom/2
    focus_x = max(half_w, min(SOURCE_SIZE[0]-half_w,focus_x))
    focus_y = max(half_h, min(SOURCE_SIZE[1]-half_h,focus_y))
    return zoom, focus_x, focus_y


def camera_frame(stage: Image.Image, beat: str, t: float,
                 duration: float) -> Image.Image:
    if stage.mode != "RGBA" or stage.size != SOURCE_SIZE:
        raise ValueError("Invalid source frame for cinematic science camera")
    zoom, focus_x, focus_y = camera_pose(beat, t, duration)
    inv=1.0/zoom
    matrix=(inv,0,focus_x-OUTPUT_SIZE[0]*inv/2,
            0,inv,focus_y-OUTPUT_SIZE[1]*inv/2)
    return stage.transform(OUTPUT_SIZE,Image.Transform.AFFINE,matrix,
                           resample=Image.Resampling.BILINEAR)
