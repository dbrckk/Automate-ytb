"""Conservative sampled visual defect preflight for original MP4 previews.

Only bounded decoded windows are assessed across the episode. Metrics are diagnostic, not an
objective measure of cinematic quality; intended fades/cuts can trigger review.
No network, machine-learning inference, asset uploads or video modification.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

VISUAL_QA_VERSION = "sampled-visual-preflight-v2-episode-coverage"
SAMPLE_FPS = 2
SAMPLE_SIZE = (96, 54)
MAX_SECONDS = 18
MAX_FRAMES = SAMPLE_FPS * MAX_SECONDS
WINDOW_SECONDS = 6
MAX_VIDEO_SECONDS = 24 * 60 * 60


def analyze_samples(raw: bytes, *, width: int = 96, height: int = 54,
                    fps: int = 2) -> dict:
    """Inspect bounded raw 8-bit grayscale frames (no decoded-pixel allocation)."""
    if not isinstance(raw, bytes):
        raise ValueError("Raw grayscale video samples must be bytes")
    if (not isinstance(width, int) or isinstance(width, bool)
            or not isinstance(height, int) or isinstance(height, bool)
            or not 1 <= width <= 256 or not 1 <= height <= 256
            or not isinstance(fps, int) or isinstance(fps, bool)
            or not 1 <= fps <= 12):
        raise ValueError("Invalid sampled video dimensions or rate")
    pixels = width * height
    if len(raw) % pixels or len(raw) > pixels * 144:
        raise ValueError("Invalid or excessive sampled grayscale data")
    count = len(raw) // pixels
    if count == 0:
        return {
            "version": VISUAL_QA_VERSION, "status": "review",
            "sampledFrames": 0, "sampleRateFps": fps,
            "sampledDurationSeconds": 0,
            "nearBlackFrames": 0, "nearWhiteFrames": 0,
            "consecutiveNearStillFrames": 0, "largeLumaSteps": 0,
            "warnings": ["The sampled video produced no decoded frames."],
        }
    view = memoryview(raw)
    means = []
    black = white = jumps = still = longest_still = 0
    last_frame = None
    last_mean = None
    for n in range(count):
        frame = view[n * pixels:(n + 1) * pixels]
        avg = sum(frame) / pixels
        means.append(avg)
        if sum(x < 8 for x in frame) / pixels >= 0.985:
            black += 1
        if sum(x > 247 for x in frame) / pixels >= 0.985:
            white += 1
        if last_frame is not None:
            # Mean absolute difference at thumbnail resolution. A strongly
            # static illustrated scene is a review signal, not a render error.
            abs_difference = sum(abs(a - b) for a, b in zip(frame, last_frame)) / pixels
            still = still + 1 if abs_difference < 0.45 else 0
            longest_still = max(longest_still, still)
            if abs(avg - last_mean) >= 55 and abs_difference >= 55:
                jumps += 1
        last_frame, last_mean = frame, avg
    warnings = []
    if black:
        warnings.append(f"{black} near-black sampled frame(s); inspect unintended blank frames.")
    if white:
        warnings.append(f"{white} near-white sampled frame(s); inspect potential exposure clipping.")
    if longest_still >= 2 * fps:
        warnings.append("At least two seconds of almost identical sampled frames; inspect motion.")
    if jumps:
        warnings.append(f"{jumps} abrupt brightness change(s); check intentional cuts or flashes.")
    return {
        "version": VISUAL_QA_VERSION,
        "status": "review" if warnings else "no-obvious-sampled-defects",
        "sampledFrames": count, "sampleRateFps": fps,
        "sampledDurationSeconds": round(count / fps, 2),
        "meanLumaRange": [round(min(means), 2), round(max(means), 2)],
        "nearBlackFrames": black, "nearWhiteFrames": white,
        "consecutiveNearStillFrames": longest_still,
        "largeLumaSteps": jumps,
        "warnings": warnings,
    }


def sampling_windows(duration: float) -> list[tuple[float, float]]:
    """Inspect short clips fully; inspect opening, middle and ending of long clips.

    Each time interval is a bounded decoded sample *window*, not a claim that
    the unsampled minutes have been checked. Time spans do not overlap.
    """
    if (not isinstance(duration, (int, float)) or isinstance(duration, bool)
            or not math.isfinite(duration) or not 0 < duration <= MAX_VIDEO_SECONDS):
        raise ValueError("Invalid duration for episode visual sampling")
    if duration <= MAX_SECONDS:
        return [(0.0, float(duration))]
    length = float(WINDOW_SECONDS)
    return [(0.0, length),
            (round(duration / 2 - length / 2, 3), length),
            (round(duration - length, 3), length)]


def _probe_duration(path: Path) -> float:
    args = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(path)]
    try:
        result = subprocess.run(args, capture_output=True, timeout=30, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Timed out inspecting video duration") from exc
    if result.returncode:
        raise RuntimeError("Could not read video duration: " +
                           result.stderr.decode("utf-8", "replace")[-400:])
    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
        sampling_windows(duration)
        return duration
    except (KeyError, TypeError, ValueError, OverflowError, json.JSONDecodeError) as exc:
        raise RuntimeError("Invalid video duration metadata") from exc


def _decode_window(path: Path, start: float, seconds: float) -> dict:
    w, h = SAMPLE_SIZE
    args = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-threads", "1", "-filter_threads", "1",
        "-ss", f"{start:.3f}", "-i", str(path),
        "-t", f"{seconds:.3f}",
        "-vf", f"fps={SAMPLE_FPS},scale={w}:{h}:flags=fast_bilinear,format=gray",
        "-frames:v", str(min(MAX_FRAMES, math.ceil(seconds * SAMPLE_FPS))),
        "-an", "-c:v", "rawvideo", "-pix_fmt", "gray",
        "-f", "rawvideo", "pipe:1",
    ]
    try:
        result = subprocess.run(args, capture_output=True, check=False, timeout=90)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Timed out decoding sample at {start:.2f}s") from exc
    if result.returncode:
        raise RuntimeError(f"Visual QA could not decode video at {start:.2f}s: " +
                           result.stderr.decode("utf-8", "replace")[-400:])
    inspection = analyze_samples(result.stdout, width=w, height=h, fps=SAMPLE_FPS)
    if not inspection["sampledFrames"]:
        raise RuntimeError(f"No decoded sample frames at {start:.2f}s")
    return inspection


def inspect_video(path: Path) -> dict:
    """Decode at most 18 total seconds spread over the actual MP4 duration.

    Seek close to each selected window so a long episode does not require a
    complete decode. Windows are assessed separately: a deliberate shot cut
    *between* windows cannot be mistaken for a brightness flash or stutter.
    This is a bounded diagnostic, NOT full frame-by-frame certification.
    """
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Missing or empty rendered video")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe are required for sampled visual QA")
    duration = _probe_duration(path)
    windows = []
    for start, seconds in sampling_windows(duration):
        sample = _decode_window(path, start, seconds)
        windows.append({
            "startSeconds": round(start, 3),
            "endSeconds": round(min(duration, start + seconds), 3),
            "sampledFrames": sample["sampledFrames"],
            "nearBlackFrames": sample["nearBlackFrames"],
            "nearWhiteFrames": sample["nearWhiteFrames"],
            "consecutiveNearStillFrames": sample["consecutiveNearStillFrames"],
            "largeLumaSteps": sample["largeLumaSteps"],
            "status": sample["status"],
            "warnings": sample["warnings"],
            "meanLumaRange": sample.get("meanLumaRange"),
        })
    warnings = [
        f"Sample window {index + 1} at {item['startSeconds']:.2f}s: {warning}"
        for index, item in enumerate(windows)
        for warning in item["warnings"]
    ]
    ranges = [item["meanLumaRange"] for item in windows if item["meanLumaRange"]]
    return {
        "version": VISUAL_QA_VERSION,
        "status": "review" if warnings else "no-obvious-sampled-defects",
        "samplingStrategy": "opening-middle-ending" if len(windows) == 3 else "short-clip",
        "videoDurationSeconds": round(duration, 3),
        "sampledSpanSeconds": round(sum(end - start for start, end in
                                     ((w["startSeconds"], w["endSeconds"]) for w in windows)), 3),
        "sampledFrames": sum(w["sampledFrames"] for w in windows),
        "sampleRateFps": SAMPLE_FPS,
        "sampledDurationSeconds": round(sum(w["sampledFrames"] / SAMPLE_FPS for w in windows), 2),
        "meanLumaRange": [min(x[0] for x in ranges), max(x[1] for x in ranges)],
        "nearBlackFrames": sum(w["nearBlackFrames"] for w in windows),
        "nearWhiteFrames": sum(w["nearWhiteFrames"] for w in windows),
        "consecutiveNearStillFrames": max(w["consecutiveNearStillFrames"] for w in windows),
        "largeLumaSteps": sum(w["largeLumaSteps"] for w in windows),
        "sampledWindows": windows,
        "warnings": warnings,
    }
