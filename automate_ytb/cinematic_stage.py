"""Deterministic CPU cinematic reframing for 9:16 original science.

A single source-space affine crop magnifies the authored world uniformly;
the electrical channel geometry is never stretched and voice timings remain
untouched. Each topic beat gets an individual continuous camera trajectory.
"""
from __future__ import annotations
import math
from PIL import Image

CAMERA_VERSION = "science-stage-camera-v4-25d-action-follow-vertical-p50-smooth"
SOURCE_SIZE = (1080, 930)
OUTPUT_SIZE = (1080, 1380)
# (start_zoom, end_zoom, start_x, end_x, start_y, end_y)
# A cloud charge is framed wide; the leader pans downward, the electrical
# contact holds the grounded tower, the return stroke travels back UP, and
# the thunder shock-wave pulls back. Author geometry in 1080x930 source
# space; camera_pose guarantees a bounded, aspect-preserving safe crop.
SHOT_PATHS = {
    "charge": (1.58, 1.68, 490.0, 525.0, 452.0, 465.0),
    "leader": (1.75, 1.92, 530.0, 590.0, 405.0, 540.0),
    "connection": (1.75, 1.91, 620.0, 660.0, 530.0, 548.0),
    "return": (1.90, 1.92, 640.0, 560.0, 544.0, 390.0),
    "thunder": (1.87, 1.58, 635.0, 560.0, 540.0, 465.0),
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
    start_zoom, stop_zoom, x0, x1, y0, y1 = SHOT_PATHS[beat]
    zoom = start_zoom + (stop_zoom-start_zoom)*ease
    focus_x = x0 + (x1-x0)*ease + focus_offset[0]
    focus_y = y0 + (y1-y0)*ease + focus_offset[1]
    # Preserve the established leader-down / return-up choreography.
    # A small event-driven optical drift adds motion without the former
    # 27 Hz return-stroke camera shake (visually perceived as frame jitter).
    # Both the offset and its velocity are zero at shot boundaries.
    drift = (p*p*(1-p)*(1-p))*16
    if beat == "return":
        focus_x += 4.2*drift*math.sin(math.pi*p)
        focus_y -= 1.4*drift*math.sin(math.pi*p)
    elif beat == "connection":
        focus_x -= 2.0*drift*math.sin(math.pi*p)
        focus_y += 1.2*drift*math.sin(math.pi*p)
    elif beat == "thunder":
        focus_x += 1.6*drift*math.sin(math.pi*p)
    half_w = OUTPUT_SIZE[0]/zoom/2
    half_h = OUTPUT_SIZE[1]/zoom/2
    focus_x = max(half_w, min(SOURCE_SIZE[0]-half_w,focus_x))
    focus_y = max(half_h, min(SOURCE_SIZE[1]-half_h,focus_y))
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
