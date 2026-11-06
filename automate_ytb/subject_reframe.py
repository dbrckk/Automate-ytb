"""Follow real visual activity in horizontal footage when delivering vertical Shorts.

This is deliberately a cheap, deterministic optical heuristic, NOT an object
detector or a claim that the tracked activity is a specific animal. It follows
high-contrast and moving areas while limiting camera speed, with a central
fallback when the footage is too dark. No model, GPU, paid API or web access.
"""
from __future__ import annotations

import math
from pathlib import Path
import subprocess

ANALYSIS_WIDTH = 160
ANALYSIS_HEIGHT = 90
ANALYSIS_FPS = 2
MAX_FRAMES = 72
BYTES_PER_FRAME = ANALYSIS_WIDTH * ANALYSIS_HEIGHT


def _decode_samples(source: Path, start: float, seconds: float) -> list[bytes]:
    count = min(MAX_FRAMES, max(2, math.ceil(seconds * ANALYSIS_FPS)))
    args = [
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "error",
        "-threads", "1", "-filter_threads", "1",
        "-ss", f"{start:.3f}", "-i", str(source),
        "-t", f"{seconds:.3f}", "-an",
        "-vf", f"fps={ANALYSIS_FPS},scale={ANALYSIS_WIDTH}:{ANALYSIS_HEIGHT}:flags=fast_bilinear,format=gray",
        "-frames:v", str(count), "-f", "rawvideo", "-pix_fmt", "gray",
        "pipe:1",
    ]
    try:
        result = subprocess.run(args, capture_output=True, timeout=50, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Cannot decode bounded footage for portrait reframing") from exc
    raw = result.stdout
    if result.returncode or not raw or len(raw) % BYTES_PER_FRAME:
        raise ValueError("Invalid or undecodable tracking source footage")
    if len(raw) > MAX_FRAMES * BYTES_PER_FRAME:
        raise ValueError("Tracking sample exceeded its hard memory bound")
    return [raw[i:i + BYTES_PER_FRAME] for i in range(0, len(raw), BYTES_PER_FRAME)]


def _score_columns(frame: bytes, previous: bytes | None) -> list[float]:
    # Ignore footage annotation areas and the extreme top of each frame.
    # This also suppresses burned-in NOAA subtitles at the bottom.
    y0, y1 = 16, 72
    levels = sorted(frame[y * ANALYSIS_WIDTH + x]
                    for y in range(y0, y1, 2)
                    for x in range(0, ANALYSIS_WIDTH, 2))
    threshold = max(30, levels[int(len(levels) * .69)])
    energy = [0.0] * ANALYSIS_WIDTH
    for y in range(y0, y1, 2):
        offset = y * ANALYSIS_WIDTH
        for x in range(ANALYSIS_WIDTH):
            pixel = frame[offset + x]
            bright = max(0, pixel - threshold)
            motion = (max(0, abs(pixel - previous[offset + x]) - 13)
                      if previous is not None else 0)
            energy[x] += bright * bright + .32 * motion * motion
    return energy


def track_crop(*, source: Path, start: float, seconds: float,
               source_width: int, crop_width: int) -> dict:
    """Return a bounded per-shot portrait camera path in source pixels.

    Cropping is full-frame height. Times are local to the extracted shot;
    all x positions are even to preserve YUV420 pixel alignment.
    """
    if not math.isfinite(start) or start < 0 or not math.isfinite(seconds) or not 1 <= seconds <= 60:
        raise ValueError("Invalid footage start or tracking duration")
    if (type(source_width) is not int or type(crop_width) is not int or
            source_width < 320 or crop_width < 80 or crop_width > source_width or
            source_width % 2 or crop_width % 2):
        raise ValueError("Invalid tracking crop dimensions")
    frames = _decode_samples(source, start, seconds)
    sample_crop = max(1, round(crop_width * ANALYSIS_WIDTH / source_width))
    max_left = ANALYSIS_WIDTH - sample_crop
    central = max_left // 2
    prev_left = central
    smooth_left = float(central)
    velocity = 0.0
    max_step = max(1.6, max_left / (ANALYSIS_FPS * 5.0))
    max_acceleration = max(1.0, max_step * .25)
    samples = []
    low_information = 0
    previous = None
    for i, frame in enumerate(frames):
        energy = _score_columns(frame, previous)
        total = sum(energy)
        if total < 1800:
            low_information += 1
            candidate = central
        else:
            # Window prefix sum: O(frame width) not a per-pixel detector.
            prefix = [0.0]
            for val in energy:
                prefix.append(prefix[-1] + val)
            def score(left: int) -> float:
                strength = prefix[left + sample_crop] - prefix[left]
                displacement = abs(left - prev_left) / max(1, max_left)
                return strength - .12 * total * displacement
            candidate = max(range(max_left + 1), key=score)
            # Do not chase marginal frame-to-frame noise at the cost of a
            # gratuitous pan. A subject needs measurable salience.
            if score(candidate) < score(prev_left) + .017 * total:
                candidate = prev_left
        if i == 0:
            smooth_left = float(candidate)
        else:
            # Second-order camera inertia: cap both velocity and its change.
            # A suddenly changing optical target cannot whip the camera in
            # the opposite direction from one sample to the next.
            wanted_velocity = max(-max_step, min(max_step,
                                                .48 * (candidate - smooth_left)))
            velocity += max(-max_acceleration,
                            min(max_acceleration, wanted_velocity - velocity))
            next_left = max(0.0, min(float(max_left), smooth_left + velocity))
            if abs(next_left - (smooth_left + velocity)) > 1e-6:
                velocity = 0.0
            smooth_left = next_left
        prev_left = int(round(smooth_left))
        source_left = round(smooth_left * (source_width - crop_width) /
                            max(1, max_left) / 2) * 2
        source_left = max(0, min(source_width - crop_width, source_left))
        samples.append({
            "timeSeconds": round(min(seconds, i / ANALYSIS_FPS), 3),
            "cropX": int(source_left),
        })
        previous = frame
    if not samples:
        raise ValueError("No frames available for portrait tracking")
    # Ease the optical pan into the final scene cut. A fixed hold after
    # the last 2fps sample would abruptly drop camera velocity to zero.
    if seconds > samples[-1]["timeSeconds"]:
        sample_dt = (seconds - samples[-1]["timeSeconds"]) * ANALYSIS_FPS
        tail_left = max(0.0, min(float(max_left),
                                 smooth_left + .5 * velocity * sample_dt))
        tail_x = round(tail_left * (source_width - crop_width) /
                       max(1, max_left) / 2) * 2
        tail_x = max(0, min(source_width - crop_width, tail_x))
        samples.append({"timeSeconds": round(seconds, 3),
                        "cropX": int(tail_x)})
    return {
        "method": "decoded-grayscale-activity-salience-smoothed-v1",
        "sourceWidth": source_width,
        "cropWidth": crop_width,
        "sampledFrames": len(frames),
        "lowInformationFrames": low_information,
        "keyframes": samples,
        "requiresVisualReview": True,
        "limitations": [
            "Tracks visual activity, not species or human-verified animals",
            "Can prioritize moving particles or camera motion over the subject",
            "Fails back toward center when the video is almost featureless",
        ],
    }


def crop_expression(tracking: dict) -> str:
    """FFmpeg crop x expression with linear interpolation and bounded path.

    Input timestamps must be reset via setpts=PTS-STARTPTS before crop.
    """
    keys = tracking["keyframes"]
    if not keys:
        raise ValueError("No tracking keyframes")
    maximum = tracking["sourceWidth"] - tracking["cropWidth"]
    if any(not 0 <= row["cropX"] <= maximum or row["cropX"] % 2
           for row in keys):
        raise ValueError("Invalid crop path")
    parts = [str(keys[0]["cropX"])]
    previous = keys[0]
    for row in keys[1:]:
        dt = row["timeSeconds"] - previous["timeSeconds"]
        if dt <= 0:
            raise ValueError("Non-monotonic tracking keyframes")
        delta = row["cropX"] - previous["cropX"]
        if delta:
            parts.append(
                f"({delta})*min(1\\,max(0\\,(t-{previous['timeSeconds']:.3f})/{dt:.3f}))")
        previous = row
    # FFmpeg validates x per frame; expression values are clamped to valid
    # even coordinates after interpolation, including floating point noise.
    path = "+".join(parts)
    return f"2*trunc(min({maximum}\\,max(0\\,({path})))/2)"
