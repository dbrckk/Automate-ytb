"""Detect missing *actual* motion in final decoded original science shots.

Sampling only one still per shot can pass numeric QA even if a static illustration
is held for its entire timeline. Decode two real positions per original segment
from the final mastered H.264 and measure the fraction of changed pixels.
"""
from __future__ import annotations

import math
from pathlib import Path
import subprocess

import numpy as np

if __package__:
    from .review_shots import timeline
else:
    from review_shots import timeline

W, H = 160, 284
MIN_MOVING_PIXEL_FRACTION = .008
MIN_MEAN_RGB_CHANGE = .55
EXPECTED_COUNT = 5


def _decode(video: Path, second: float) -> np.ndarray:
    if not math.isfinite(second) or second < 0:
        raise ValueError("Invalid original motion decode position")
    proc=subprocess.run(
        ["ffmpeg","-v","error","-ss",f"{second:.3f}","-i",str(video),
         "-frames:v","1","-vf",f"scale={W}:{H}:flags=bilinear",
         "-pix_fmt","rgb24","-f","rawvideo","pipe:1"],
        check=True,capture_output=True,timeout=35)
    expected=W*H*3
    if len(proc.stdout)!=expected:
        raise RuntimeError("Incomplete actual H.264 motion sample")
    return np.frombuffer(proc.stdout,dtype=np.uint8).reshape(H,W,3).astype(np.int16)


def inspect_original_motion(video: Path, shots: list[dict],
                            video_duration: float) -> dict:
    if not Path(video).is_file():
        raise ValueError("Final H.264 master must exist for motion QA")
    spans,_=timeline(shots,video_duration)
    # Validate authored coverage and provenance *before* opening FFmpeg.
    # This avoids needlessly decoding a corrupt or missing source in tests
    # and makes a real production failure actionable at the correct layer.
    originals=[
        (index, shot) for index,shot in enumerate(shots,start=1)
        if shot.get("original_science_animation")]
    if len(originals)!=EXPECTED_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_COUNT} original moving science shots, "
            f"found {len(originals)}")
    for index,shot in originals:
        if not str(shot.get("source","")).startswith("original_"):
            raise ValueError(
                f"Original motion source attribution invalid for shot {index}")
    findings=[]
    for index,(shot,span) in enumerate(zip(shots,spans),start=1):
        if not shot.get("original_science_animation"):
            continue
        if not str(shot.get("source","")).startswith("original_"):
            raise ValueError(f"Original motion source attribution invalid for shot {index}")
        length=span["end"]-span["start"]
        if length<.80:
            raise ValueError(f"Original animated shot {index} is too short")
        a=_decode(Path(video),span["start"]+.18*length)
        b=_decode(Path(video),span["start"]+.76*length)
        diff=np.abs(a-b)
        changed=float(np.mean(np.max(diff,axis=2)>8))
        mean=float(np.mean(diff))
        findings.append({
            "shot":index,"kind":shot["source"],
            "duration":round(length,3),
            "changed_pixel_fraction":round(changed,4),
            "mean_rgb_change":round(mean,3),
            "pass": changed>=MIN_MOVING_PIXEL_FRACTION
                    and mean>=MIN_MEAN_RGB_CHANGE,
        })
    if len(findings)!=EXPECTED_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_COUNT} original moving science shots, "
            f"found {len(findings)}")
    failed=[x["shot"] for x in findings if not x["pass"]]
    result={
        "status":"passed" if not failed else "failed",
        "source":"two frames per original shot decoded from final mastered MP4",
        "checks":"real motion across independently timed full-frame compositions",
        "original_motion_shots":len(findings),
        "min_changed_pixel_fraction":MIN_MOVING_PIXEL_FRACTION,
        "min_rgb_change":MIN_MEAN_RGB_CHANGE,
        "shots":findings,
        "editorial_approved":False,
    }
    if failed:
        raise RuntimeError(f"Encoded original animation is effectively still: {failed}")
    return result
