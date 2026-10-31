"""Shot-by-shot review of actual NASA footage plus original animations.

Shot durations come from the existing encoded production report, not a synthetic
storyboard. This complements the six narration-scene review.
"""
from __future__ import annotations

import math
from pathlib import Path
import re

if __package__:
    from .review_frames import create_contact_sheet
else:
    from review_frames import create_contact_sheet


def timeline(shots: list[dict], video_duration: float) -> tuple[list[dict], list[str]]:
    if (not isinstance(shots, list) or not 2 <= len(shots) <= 24 or
            isinstance(video_duration, bool) or
            not isinstance(video_duration, (int, float)) or
            not math.isfinite(video_duration) or video_duration <= 0):
        raise ValueError("Invalid shot review input")

    segments: list[dict] = []
    labels: list[str] = []
    current = 0.0
    last_scene = -1
    for idx, shot in enumerate(shots, start=1):
        if not isinstance(shot, dict):
            raise ValueError("Invalid shot report entry")
        length = shot.get("duration")
        scene = shot.get("scene")
        source = shot.get("source")
        if (isinstance(length, bool) or not isinstance(length, (int, float)) or
                not math.isfinite(length) or not 0.80 <= length <= 25 or
                type(scene) is not int or not 0 <= scene < 12 or
                scene < last_scene or (last_scene == -1 and scene != 0) or
                (last_scene >= 0 and scene > last_scene + 1) or
                not isinstance(source, str) or
                not re.fullmatch(r"[a-z0-9_-]{1,24}", source)):
            raise ValueError(f"Invalid shot metadata for shot {idx}")
        start, end = current, current + float(length)
        segments.append({"start": start, "end": end})
        labels.append(f"SHOT {idx:02d} · {source} · {start+length/2:.1f}s")
        current = end
        last_scene = scene

    if last_scene != 5:
        raise ValueError("Solar Storm shot report must include all six narrated scenes")

    # Concat stream-copy and AAC round frame boundaries; tolerate subsecond
    # accumulated rounding but never trust a wildly wrong report timeline.
    if abs(current - float(video_duration)) > 0.75:
        raise ValueError(
            f"Shot plan/video duration mismatch: {current:.2f}s vs "
            f"{video_duration:.2f}s")
    if current > video_duration + 0.20:
        # A small rounding overrun can be tolerated only for the final shot.
        segments[-1]["end"] = min(segments[-1]["end"], video_duration)
    return segments, labels


def review_encoded_shots(video: Path, shots: list[dict], duration: float,
                         output: Path) -> dict:
    spans, labels = timeline(shots, duration)
    reviewed = create_contact_sheet(video, spans, output, labels=labels)
    if reviewed["sampled_scenes"] != len(shots):
        raise RuntimeError("Incomplete MP4 shot coverage")
    reviewed["sampled_shots"] = reviewed.pop("sampled_scenes")
    for idx, (frame, shot) in enumerate(zip(reviewed["frames"], shots)):
        frame["shot"] = idx+1
        frame["narration_scene"] = shot["scene"]+1
        frame["source"] = shot["source"]
        frame["source_type"] = shot.get("source_type", "unknown")
        frame["is_original_animation"] = bool(
            shot.get("original_science_animation"))
        frame.pop("scene", None)
    reviewed["coverage"] = "every encoded shot midpoint"
    reviewed["editorial_approved"] = False
    reviewed["note"] = (
        "Shot frames are decoded from final MP4; this is a review aid, "
        "not proof of scientific accuracy, source rights or artistic approval.")
    return reviewed
