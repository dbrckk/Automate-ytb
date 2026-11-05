"""Non-publishing technical preflight for TikTok and YouTube Shorts exports.

This validates the encoded MP4, but cannot approve music/asset rights,
safe zones, factual claims, platform policy, or publication consent.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess

SHORTS_MAX_SECONDS = 180.0
PREFERRED_FPS = 30


def _inspect(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size < 2048:
        raise ValueError("A nonempty local video file is required")
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration,format_name,size:"
             "stream=index,codec_type,codec_name,width,height,avg_frame_rate,"
             "sample_rate,channels,nb_frames,duration",
             "-of", "json", str(path)],
            capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Could not inspect the video with ffprobe") from exc
    if p.returncode:
        raise ValueError("Unreadable video media: " + p.stderr[-200:])
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid ffprobe data") from exc


def validate_short(path: Path, *, require_audio: bool = False) -> dict:
    """Validate actual encoded content; never claim platform publication."""
    if type(require_audio) is not bool:
        raise ValueError("require_audio must be a boolean")
    path = Path(path).resolve()
    info = _inspect(path)
    vids = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    audios = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    errors, warnings = [], []
    if len(vids) != 1 or len(audios) > 1:
        errors.append("Exactly one video and at most one audio stream required")
    v = vids[0] if len(vids) == 1 else {}
    a = audios[0] if len(audios) == 1 else {}
    fmt = info.get("format", {})
    try:
        duration = float(fmt.get("duration", 0))
        width, height = int(v.get("width", 0)), int(v.get("height", 0))
        fps = float(Fraction(str(v.get("avg_frame_rate", "0/1"))))
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        duration, width, height, fps = 0.0, 0, 0, 0.0
    if not math.isfinite(duration) or not 0 < duration <= SHORTS_MAX_SECONDS:
        errors.append("Shared YouTube Shorts export must be <=180 seconds")
    if width * 16 != height * 9 or width < 720 or height < 1280:
        errors.append("Use vertical 9:16 footage of at least 720x1280")
    if v.get("codec_name") != "h264":
        errors.append("Encode the video stream in H.264")
    if "mp4" not in str(fmt.get("format_name", "")):
        errors.append("Use an MP4 container")
    if not math.isfinite(fps) or fps < 23.9 or fps > 60.1:
        errors.append("Use an average frame rate between 24 and 60 FPS")
    elif abs(fps - PREFERRED_FPS) > .1:
        warnings.append("30 FPS is preferred for a consistent mobile preset")
    if width == 720:
        warnings.append("720p works; 1080x1920 is preferred for quality")
    if duration < 8 or duration > 60:
        warnings.append("Review pacing outside the suggested 8-60s edit window")
    if require_audio and not a:
        errors.append("Expected an audio track but none was found")
    if a and a.get("codec_name") != "aac":
        errors.append("Use AAC audio for the shared MP4 export")
    if a and str(a.get("sample_rate")) not in ("44100", "48000"):
        warnings.append("44.1 or 48 kHz AAC sampling preferred")
    if path.stat().st_size > 500 * 1024 * 1024:
        warnings.append("Review platform upload size limits before publication")
    return {
        "status": "failed" if errors else "passed",
        "uploadTechnicallyReady": not errors,
        "publicationApproved": False,
        "humanReviewRequired": True,
        "targetPlatforms": ["TikTok", "YouTube Shorts"],
        "media": {
            "path": str(path), "durationSeconds": round(duration, 3),
            "width": width, "height": height, "fps": round(fps, 3),
            "videoCodec": v.get("codec_name"),
            "audioCodec": a.get("codec_name"),
            "sizeBytes": path.stat().st_size,
        },
        "errors": errors, "warnings": warnings,
        "manualChecks": [
            "Review the video with each platform's mobile UI and safe zones",
            "Check asset/music rights, originality, factual accuracy and disclosures",
            "Review audio, language, cover, and platform music rules",
            "Publish only after explicit account-holder authorization",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="TikTok + YouTube Shorts MP4 preflight; does not upload")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--require-audio", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate_short(args.video, require_audio=args.require_audio)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "passed" else 2
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
