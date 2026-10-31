"""Deterministic portrait camera motion for actual NASA sources, using FFmpeg.

Every shot is driven by full motion video: 30 real output frames per second,
with gentle pan, animated push-in and a science-aware CME focal point.
No CGI asset replacements, source-image stretching or paid APIs.
"""
from __future__ import annotations

import math

WIDTH, HEIGHT, FPS = 1080, 1920, 30
# Carefully authored pan amplitudes in 1080p output pixels for 13 clips.
PANS = (70, -64, 79, -81, 67, -44, 38, -72, 85, -52, 62, -69, 64)
OFFSETS = (0, 0, 0, 0, 0, 0, 0, 100, 0, -170, 80, 0, 0)
SOURCE_TYPES = frozenset((
    "sun131", "sun171", "sun304", "cme_launch", "magnetosphere",
    "aurora", "satellite", "satellite2"
))
ENGINE = "cinematic-source-aware-v1"


def build_portrait_camera(key: str, index: int) -> str:
    """Native portrait framing and stable output rate for one authored shot.

    The order matters: normalize the source rate, scale using original pixels,
    crop into 9:16, then gently animate the portrait viewport. Feeding 60fps
    sources directly to zoompan would silently slow the playback.
    """
    if key not in SOURCE_TYPES or type(index) is not int or not 0 <= index < 13:
        raise ValueError("Unrecognized shot source or authoring index")
    pan = PANS[index]
    offset = OFFSETS[index]
    # NASA's CME animation places the launching Sun to the left of frame.
    if key == "cme_launch":
        center = "(in_w-out_w)*0.32"
        drift = 35
    elif key == "magnetosphere":
        center = "(in_w-out_w)*0.50"
        drift = 46
    else:
        center = f"(in_w-out_w)/2+{offset}"
        drift = pan
    x_position = f"max(0,min(in_w-out_w,{center}+{drift}*sin(n/52)))"
    # Keep the actual solar imagery visible, instead of pseudo-3D distortion.
    y_position = "max(0,min(in_h-out_h,(in_h-out_h)/2+20*sin(n/75)))"
    push_rate = 0.00068 if key in {"sun131", "sun171", "sun304", "cme_launch"} else 0.00045
    max_zoom = 1.085 if key in {"sun131", "sun171", "sun304", "cme_launch"} else 1.065
    return (
        f"fps={FPS},"
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={WIDTH}:{HEIGHT}:x='{x_position}':y='{y_position}',"
        f"zoompan=z='min(zoom+{push_rate:.5f},{max_zoom:.3f})':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "setsar=1,format=yuv420p"
    )


def camera_metadata(key: str, index: int) -> dict:
    filtergraph = build_portrait_camera(key, index)
    return {
        "engine": ENGINE,
        "source": key,
        "shot_number": index + 1,
        "portrait_size": [WIDTH, HEIGHT],
        "frame_rate": FPS,
        "motion_type": "source-preserving pan + gentle 9:16 push-in",
        "focal_subject": "sunward CME launch" if key == "cme_launch" else
                         "center-weighted NASA source",
        "time_stretched": False,
        "filtergraph": filtergraph,
    }
