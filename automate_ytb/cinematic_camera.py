"""Validated 2D cinematic framing for original animated scenes.

All camera movements use FFmpeg's per-frame crop expressions. The renderer
accepts only storyboard enum values, never user-supplied filter expressions.
The wide establishing view is intentionally locked for legible scenery and
to avoid artificial movement in still backgrounds.
"""
from __future__ import annotations

CAMERA_VERSION = "cinematic-camera-v1"

# Source canvas 1280x720. Crops retain approximately 16:9 framing.
# (crop width, crop height, base x, base y, horizontal drift, vertical drift)
PROFILES = {
    "wide": (1280, 720, 0, 0, 0, 0),
    "medium": (1104, 622, 62, 42, 13, 8),
    "closeup": (880, 496, 20, 112, 15, 11),
    "macro": (704, 396, 22, 140, 12, 10),
    "low": (992, 558, 20, 144, 12, 8),
    "shoulder": (1056, 594, 148, 62, 12, 9),
}


def framing_filter(shot: str, *, width: int, height: int, fps: int,
                   scene_index: int = 1) -> str:
    """Create a single trusted filter (crop, pan, scale, pixel-format).

    Scene index changes the direction of the gentle drift but never the crop
    dimensions or camera target. All expressions are constructed internally.
    """
    if shot not in PROFILES:
        raise ValueError("Unknown cinematic shot")
    if (width, height) not in ((1280, 720), (1920, 1080)):
        raise ValueError("Unsupported scene output resolution")
    if fps not in (24, 30):
        raise ValueError("Unsupported scene frame rate")
    if not isinstance(scene_index, int) or not 1 <= scene_index <= 1200:
        raise ValueError("Invalid storyboard scene index")
    cw, ch, x, y, dx, dy = PROFILES[shot]
    if not (0 <= x-dx <= x+dx <= 1280-cw and
            0 <= y-dy <= y+dy <= 720-ch):
        raise ValueError("Unsafe cinematic crop profile")
    if shot == "wide":
        return f"scale={width}:{height}:flags=lanczos,format=yuv420p"
    # Pan slowly within the safe frame. Values are not script-supplied.
    phase = "0.0" if scene_index % 2 else "1.2"
    cx = f"{x}+{dx}*sin(n/{fps}*0.77+{phase})"
    cy = f"{y}+{dy}*sin(n/{fps}*0.52+{phase})"
    return (f"crop={cw}:{ch}:x='{cx}':y='{cy}',"
            f"scale={width}:{height}:flags=lanczos,format=yuv420p")


def framing_metadata(shot: str) -> dict:
    """Export a concise, stable provenance record for render reports."""
    if shot not in PROFILES:
        raise ValueError("Unknown cinematic shot")
    w, h, _, _, dx, dy = PROFILES[shot]
    return {"shot": shot, "sourceCanvas": [1280, 720],
            "crop": [w, h], "animatedCamera": bool(dx or dy),
            "version": CAMERA_VERSION}
