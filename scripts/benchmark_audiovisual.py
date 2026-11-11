"""Reproducible, privacy-safe measurements of real encoded video files.

The input media is NEVER copied into the report, repository or other outputs.
This measures technical properties, not animation quality or music aesthetics.
No third-party Python packages or online APIs are required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

VERSION = "av-reference-baseline-v1"
WIDTH, HEIGHT = 144, 256
SAMPLE_FPS = 4
DIFFERENCE_THRESHOLD = 8  # grayscale code values, out of 255
MAX_MEDIA_BYTES = 2_000_000_000
MAX_SAMPLE_SECONDS = 120
FRAME_BYTES = WIDTH * HEIGHT
_SUMMARY = re.compile(r"\bSummary:\s*Integrated loudness:\s*"
                      r"I:\s*([+-]?\d+(?:\.\d+)?)\s*LUFS\s*"
                      r"Threshold:.*?Loudness range:\s*"
                      r"LRA:\s*([+-]?\d+(?:\.\d+)?)\s*LU.*?"
                      r"True peak:\s*Peak:\s*([+-]?\d+(?:\.\d+)?)\s*dBFS",
                      re.DOTALL)


def _run(command: list[str], *, timeout: int) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(command, capture_output=True, check=True,
                              timeout=timeout)
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg/FFprobe is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Media analysis exceeded its bounded runtime") from exc
    except subprocess.CalledProcessError as exc:
        # Do not leak arbitrary source paths or media metadata through errors.
        raise RuntimeError("Media analysis failed (invalid or unsupported input)") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _probe(path: Path) -> dict:
    output = _run(["ffprobe", "-v", "error", "-show_entries",
                   "format=duration,size:stream=codec_type,codec_name,"
                   "width,height,r_frame_rate,sample_rate,channels,bit_rate",
                   "-of", "json", str(path)], timeout=60)
    raw = json.loads(output.stdout)
    streams = raw.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if len(videos) != 1 or len(audios) > 1:
        raise ValueError("Expected exactly one video and at most one audio stream")
    video = videos[0]
    seconds = float(raw["format"]["duration"])
    width, height = video.get("width"), video.get("height")
    if (not math.isfinite(seconds) or not 0.2 <= seconds <= 3600
            or type(width) is not int or type(height) is not int
            or not 16 <= width <= 8192 or not 16 <= height <= 8192):
        raise ValueError("Invalid media geometry or duration")
    fraction = video.get("r_frame_rate", "0/0")
    a, b = fraction.split("/")
    fps = float(a) / float(b)
    if not 1 <= fps <= 240:
        raise ValueError("Unsupported frame rate")
    audio = audios[0] if audios else {}
    return {
        "durationSeconds": round(seconds, 3),
        "width": width, "height": height,
        "portrait": height > width,
        "frameRate": round(fps, 6),
        "videoCodec": video.get("codec_name"),
        "audioCodec": audio.get("codec_name"),
        "audioSampleRateHz": int(audio["sample_rate"]) if audio.get("sample_rate") else None,
        "audioChannels": audio.get("channels"),
        "audioBitrateKbps": round(int(audio["bit_rate"]) / 1000, 1) if audio.get("bit_rate") else None,
        "hasAudio": bool(audios),
    }


def _motion_metrics(frames: bytes) -> dict:
    """Use each decoded sample once; report actual changed-pixel fractions.

    A high changed fraction is NOT an aesthetic goal: shakes/cuts can inflate it.
    This is strictly an observed diagnostic of gray-luma frame differences.
    """
    if len(frames) % FRAME_BYTES:
        raise ValueError("Decoder returned a partial grayscale frame")
    n = len(frames) // FRAME_BYTES
    if n < 2:
        raise ValueError("Too few decoded frames for meaningful motion analysis")
    previous = memoryview(frames)[:FRAME_BYTES]
    fractions = []
    near_black = 0
    max_frozen_samples = 0
    frozen_samples = 0
    for i in range(n):
        frame = memoryview(frames)[i * FRAME_BYTES:(i + 1) * FRAME_BYTES]
        if sum(frame) / FRAME_BYTES < 12:
            near_black += 1
        if i:
            changed = sum(1 for a, b in zip(previous, frame)
                          if abs(a - b) > DIFFERENCE_THRESHOLD)
            fraction = changed / FRAME_BYTES
            fractions.append(fraction)
            if fraction < 0.002:
                frozen_samples += 1
                max_frozen_samples = max(max_frozen_samples, frozen_samples)
            else:
                frozen_samples = 0
        previous = frame
    fractions.sort()
    return {
        "sampleCount": n,
        "motionPairs": len(fractions),
        "medianChangedPixelsPercent": round(statistics.median(fractions) * 100, 3),
        "meanChangedPixelsPercent": round(statistics.mean(fractions) * 100, 3),
        "p90ChangedPixelsPercent": round(fractions[min(len(fractions) - 1, math.ceil(len(fractions) * .90) - 1)] * 100, 3),
        "nearBlackSamples": near_black,
        "maxConsecutiveNearFrozenPairs": max_frozen_samples,
    }


def _sample_frames(path: Path, seconds: float) -> tuple[dict, bool]:
    analyzed = min(MAX_SAMPLE_SECONDS, seconds)
    output = _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                   "-i", str(path), "-t", f"{analyzed:.6f}", "-an", "-sn", "-dn",
                   "-vf", f"fps={SAMPLE_FPS},scale={WIDTH}:{HEIGHT}:flags=bicubic,format=gray",
                   "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"], timeout=180)
    return _motion_metrics(output.stdout), seconds > MAX_SAMPLE_SECONDS


def _audio_metrics(path: Path) -> dict:
    output = _run(["ffmpeg", "-nostdin", "-hide_banner", "-nostats",
                   "-loglevel", "info", "-i", str(path),
                   "-map", "0:a:0", "-af", "ebur128=peak=true",
                   "-f", "null", "-"], timeout=180)
    match = _SUMMARY.search(output.stderr.decode("utf-8", "replace"))
    if not match:
        raise ValueError("FFmpeg did not produce a complete EBU R128 audio summary")
    i, lra, peak = map(float, match.groups())
    if not all(math.isfinite(v) for v in (i, lra, peak)):
        raise ValueError("Audio contains invalid loudness measurements")
    return {"integratedLufs": i, "loudnessRangeLu": lra,
            "truePeakDbtp": peak, "measurement": "ffmpeg-ebur128-peak-true"}


def measure(path: Path, label: str) -> dict:
    if (not isinstance(label, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,49}", label)):
        raise ValueError("Use a safe, anonymous media label")
    path = path.resolve(strict=True)
    if not path.is_file() or not 1024 <= path.stat().st_size <= MAX_MEDIA_BYTES:
        raise ValueError("Media is missing, too small or too large")
    metadata = _probe(path)
    motion, truncated = _sample_frames(path, metadata["durationSeconds"])
    return {
        "label": label,
        "sha256": _sha256(path), "fileBytes": path.stat().st_size,
        "media": metadata,
        "motion": motion,
        "motionSampleWindowSeconds": round(min(MAX_SAMPLE_SECONDS, metadata["durationSeconds"]), 3),
        "motionWindowTruncated": truncated,
        "audio": _audio_metrics(path) if metadata["hasAudio"] else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Technical audiovisual baseline from real MP4 files; no source media is stored")
    parser.add_argument("--video", type=Path, action="append", required=True,
                        help="One or more local original MP4 sources")
    parser.add_argument("--label", action="append", required=True,
                        help="An anonymous safe label for the matching source")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if len(args.video) != len(args.label) or not 1 <= len(args.video) <= 6:
        parser.error("Supply between 1 and 6 video/label pairs")
    if len(set(args.label)) != len(args.label):
        parser.error("Labels must be unique")
    report = {
        "schemaVersion": 1, "engine": VERSION,
        "sample": {"fps": SAMPLE_FPS, "width": WIDTH, "height": HEIGHT,
                   "lumaChangeThreshold": DIFFERENCE_THRESHOLD,
                   "maxSeconds": MAX_SAMPLE_SECONDS},
        "automatedArtisticJudgment": False,
        "humanAudioReviewCompleted": False,
        "privacy": "No source media or absolute source path stored in this report",
        "videos": [measure(p, label) for p, label in zip(args.video, args.label)],
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print("AV_BASELINE_OK " + ", ".join(f"{x['label']}={x['media']['durationSeconds']}s"
                                       for x in report["videos"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
