"""Deterministic CPU cinematic reframing for 9:16 original science.

A single source-space affine crop magnifies the authored world uniformly;
the electrical channel geometry is never stretched and voice timings remain
untouched. Each topic beat gets an individual continuous camera trajectory.
"""
from __future__ import annotations
import math
from PIL import Image

CAMERA_VERSION = "science-stage-camera-v2-25d-world-space-subject-tracking"
SOURCE_SIZE = (1080, 930)
OUTPUT_SIZE = (1080, 1380)
SHOT_PATHS = {
    "charge": (1.57, 1.69, 495.0, 540.0),
    "leader": (1.72, 1.53, 535.0, 575.0),
    "connection": (1.59, 1.65, 610.0, 650.0),
    "return": (1.58, 1.68, 665.0, 555.0),
    "thunder": (1.68, 1.51, 640.0, 575.0),
}


def camera_pose(beat: str, t: float, duration: float, *,
                focus_offset: tuple[float, float] = (0., 0.)
                ) -> tuple[float, float, float]:
    if (beat not in SHOT_PATHS
            or type(t) not in (float, int)
            or type(duration) not in (float, int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration == 0):
        raise ValueError("Invalid cinematic stage clock or beat")
    if (not isinstance(focus_offset, tuple) or len(focus_offset) != 2
            or any(type(v) not in (float, int)
                   or not math.isfinite(v) or abs(v) > 80
                   for v in focus_offset)):
        raise ValueError("Invalid bounded camera focus offset")
    p = t / duration
    ease = p*p*(3-2*p)
    start_zoom, stop_zoom, x0, x1 = SHOT_PATHS[beat]
    zoom = start_zoom + (stop_zoom-start_zoom)*ease
    focus_x = x0 + (x1-x0)*ease + focus_offset[0]
    if beat == "return":
        envelope = math.exp(-((p-.23)/.09)**2)
        focus_x += 3.5*envelope*math.sin(t*27)
    half_w = OUTPUT_SIZE[0]/zoom/2
    half_h = OUTPUT_SIZE[1]/zoom/2
    focus_x = max(half_w, min(SOURCE_SIZE[0]-half_w,focus_x))
    focus_y = max(half_h, min(SOURCE_SIZE[1]-half_h,
                              SOURCE_SIZE[1]/2 + focus_offset[1]))
    return zoom, focus_x, focus_y


def camera_frame(stage: Image.Image, beat: str, t: float,
                 duration: float, *,
                 focus_offset: tuple[float, float] = (0., 0.)
                 ) -> Image.Image:
    if stage.mode != "RGBA" or stage.size != SOURCE_SIZE:
        raise ValueError("Invalid source frame for cinematic science camera")
    zoom, focus_x, focus_y = camera_pose(
        beat, t, duration, focus_offset=focus_offset)
    inv=1.0/zoom
    matrix=(inv,0,focus_x-OUTPUT_SIZE[0]*inv/2,
            0,inv,focus_y-OUTPUT_SIZE[1]*inv/2)
    return stage.transform(OUTPUT_SIZE,Image.Transform.AFFINE,matrix,
                           resample=Image.Resampling.BILINEAR)
