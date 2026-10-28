"""Conservative sampled visual defect preflight for original MP4 previews.

Only the decoded opening window is assessed. Metrics are diagnostic, not an
objective measure of cinematic quality; intended fades/cuts can trigger review.
No network, machine-learning inference, asset uploads or video modification.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

VISUAL_QA_VERSION = "sampled-visual-preflight-v1"
SAMPLE_FPS = 2
SAMPLE_SIZE = (96, 54)
MAX_SECONDS = 18
MAX_FRAMES = SAMPLE_FPS * MAX_SECONDS


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


def inspect_video(path: Path) -> dict:
    """Decode at most 18 seconds at 2 fps with FFmpeg; no full video upload.

    The result is not a certification of the entire file's quality, content,
    frame timing, licensing or audio. Missing tools or decoding errors are
    explicit failures, never silently treated as a clean review.
    """
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Missing or empty rendered video")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required for sampled visual QA")
    w, h = SAMPLE_SIZE
    args = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-threads", "1", "-filter_threads", "1",
        "-i", str(path), "-t", str(MAX_SECONDS),
        "-vf", f"fps={SAMPLE_FPS},scale={w}:{h}:flags=fast_bilinear,format=gray",
        "-frames:v", str(MAX_FRAMES), "-an", "-c:v", "rawvideo",
        "-pix_fmt", "gray", "-f", "rawvideo", "pipe:1",
    ]
    try:
        result = subprocess.run(args, capture_output=True, check=False,
                                timeout=90)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Timed out decoding sampled preview") from exc
    if result.returncode:
        raise RuntimeError("Visual QA could not decode video: " +
                           result.stderr.decode("utf-8", "replace")[-400:])
    return analyze_samples(result.stdout, width=w, height=h, fps=SAMPLE_FPS)
