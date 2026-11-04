"""Universal authored camera moves for still-image video scenes.

Applies to non-rig genres (documentary, cinematic, cartoon slides,
product/factual photo sequences) without modifying voice or timings.
Dedicated 2D/3D animated engines stay unchanged.
"""
from __future__ import annotations

import math

VERSION = "universal-shot-camera-v1"

# Positions are fractions of the available crop margin, not image pixels.
SHOT_PATHS = {
    "wide":     (.07, .14, .78, .42, .57, .43),
    "medium":   (.09, .15, .28, .58, .50, .50),
    "closeup":  (.14, .20, .48, .54, .51, .47),
    "macro":    (.18, .24, .49, .51, .50, .50),
    "low":      (.10, .17, .30, .69, .64, .43),
    "shoulder": (.11, .17, .70, .32, .47, .53),
}
ACTION_SPEED = {
    "idle": 1.0, "rest": .65, "walk": 1.0, "run": 1.4,
    "fly": 1.2, "jump": 1.15, "talk": .65, "surprise": 1.25,
}


def camera_filter(width: int, height: int, *, fps: int, duration: float,
                  direction: dict | None = None) -> str:
    """Return a bounded FFmpeg filter chain with a continuous camera path.

    Uses FFmpeg zoompan's output-frame index on to make motion independent
    of input framerate. Crop positions stay inside the available margin;
    easing has zero endpoint velocity, framing follows storyboard direction.
    """
    if (type(width) is not int or type(height) is not int or
            not 128 <= width <= 3840 or not 128 <= height <= 3840 or
            type(fps) is not int or not 1 <= fps <= 60 or
            type(duration) not in (int, float) or
            not math.isfinite(duration) or not .1 <= duration <= 3600):
        raise ValueError("Invalid universal camera resolution, FPS or duration")
    if direction is not None and not isinstance(direction, dict):
        raise ValueError("Camera direction must be a storyboard object")
    direction = direction or {}
    shot = direction.get("shot", "medium")
    action = direction.get("action", "idle")
    if shot not in SHOT_PATHS or action not in ACTION_SPEED:
        raise ValueError("Unsupported authored camera shot or action")
    zoom_start, zoom_end, x0, x1, y0, y1 = SHOT_PATHS[shot]
    speed = ACTION_SPEED[action]
    zoom_end = min(.25, zoom_start + (zoom_end-zoom_start)*speed)
    frames = max(2, round(fps*duration))
    progress = f"min(1,max(0,on/{frames-1}))"
    ease = f"(3*({progress})*({progress})-2*({progress})*({progress})*({progress}))"
    zoom = f"(1+{zoom_start:.5f}+{zoom_end-zoom_start:.5f}*{ease})"
    x = f"({x0:.5f}+{x1-x0:.5f}*{ease})"
    y = f"({y0:.5f}+{y1-y0:.5f}*{ease})"
    return (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='{zoom}':"
            f"x='(iw-iw/zoom)*{x}':"
            f"y='(ih-ih/zoom)*{y}':"
            f"d=1:s={width}x{height}:fps={fps},format=yuv420p")
