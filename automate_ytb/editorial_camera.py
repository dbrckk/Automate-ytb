"""Subtle original source-image motion for all still-card video styles.

A stable, shot-directed 2D camera is a fallback for documentary, cinematic,
generic cartoons and other approved image scenes that have NO authored
articulated animation rig. It is not falsely described as 3D, parallax, or
a replacement for original character animation.

The source still is motion-cropped by FFmpeg with a bounded 3-7% zoom, not
the old unbounded mechanical center zoom that continued until saturation.
No voice, caption, duration, subtitle or scene-plan timing is changed.
"""
from __future__ import annotations

import math

from .director import SHOTS, validate_direction

VERSION = "approved-still-editorial-camera-v1"
ZOOM_RANGE = {
    "wide": .034,
    "medium": .049,
    "closeup": .055,
    "macro": .057,
    "low": .043,
    "shoulder": .054,
}
# Distinct, conservative shot choreography; coordinates refer to the source
# image crop and remain within the available safe pan corridor.
PATHS = (
    (.43, .57, .50, .50),
    (.57, .43, .48, .52),
    (.46, .54, .56, .44),
    (.54, .46, .44, .56),
    (.50, .50, .56, .45),
    (.49, .52, .46, .54),
)


def camera_filter(*, width: int, height: int, fps: int,
                  duration: float, scene_index: int,
                  direction: dict | None = None) -> str:
    if ((width, height) not in ((1280,720), (1920,1080), (1080,1920))
            or fps not in (24, 30)
            or type(scene_index) is not int or scene_index < 0
            or type(duration) not in (float,int) or
            not math.isfinite(duration) or not .5 <= duration <= 3600):
        raise ValueError("Unsafe image camera sizing, clock, or index")
    if direction is not None:
        validated=validate_direction(direction)
        shot=validated["shot"]
    else:
        shot="wide"
    if shot not in SHOTS:
        raise ValueError("Unrecognized editorial camera shot")
    frames=max(2,round(duration*fps))
    start_x,end_x,start_y,end_y=PATHS[scene_index%len(PATHS)]
    travel=f"min(on/{frames-1},1)"
    # Smoothstep has zero rate of change at both shot boundaries.
    ease=f"({travel}*{travel}*(3-2*{travel}))"
    zoom=.010+ZOOM_RANGE[shot]
    z=f"1.012+{zoom:.5f}*{ease}"
    x=f"(iw-iw/zoom)*({start_x:.4f}+{end_x-start_x:.4f}*{ease})"
    y=f"(ih-ih/zoom)*({start_y:.4f}+{end_y-start_y:.4f}*{ease})"
    return (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"zoompan=z='{z}':x='{x}':y='{y}':"
            f"d=1:s={width}x{height}:fps={fps},format=yuv420p")


def camera_metadata(*, scene_index: int, duration: float,
                    direction: dict | None = None) -> dict:
    if type(scene_index) is not int or scene_index < 0:
        raise ValueError("Invalid scene index")
    if type(duration) not in (int,float) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid scene duration")
    shot = validate_direction(direction)["shot"] if direction is not None else "wide"
    return {
        "version": VERSION,
        "sourceType": "approved-single-image",
        "method": "bounded-2d-ffmpeg-zoompan",
        "shot": shot,
        "zoomStart": 1.012,
        "zoomEnd": round(1.022+ZOOM_RANGE[shot], 4),
        "durationSeconds": round(duration,3),
        "changesAudioOrCaptions": False,
        "actualThreeDimensionalGeometry": False,
    }
