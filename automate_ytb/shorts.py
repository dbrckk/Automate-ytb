"""Export an original, review-only vertical companion clip from a completed episode.

The vertical edit preserves the full horizontal frame in a sharp foreground
with a softly blurred vertical fill. It never fetches third-party media or
uploads content. Shot selection is currently a time-window, not AI highlights.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from .production import _sha, _write_json

TIMING = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")


def _ms(value: str) -> int:
    found = TIMING.fullmatch(value.strip())
    if found is None:
        raise ValueError("Invalid subtitle timestamp")
    hours, mins, sec, milli = map(int, found.groups())
    if mins > 59 or sec > 59:
        raise ValueError("Invalid subtitle timestamp")
    return ((hours * 60 + mins) * 60 + sec) * 1000 + milli


def _timestamp(ms: int) -> str:
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, rem = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"


def clip_srt(source: Path, target: Path, *, start_ms: int, end_ms: int) -> int:
    blocks = re.split(r"\r?\n\s*\r?\n", source.read_text(encoding="utf-8").strip())
    rendered = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3 or "-->" not in lines[1]:
            raise ValueError("Malformed source subtitles")
        first, last = (_ms(text) for text in lines[1].split("-->"))
        if last <= first:
            raise ValueError("Invalid subtitle interval")
        left, right = max(first, start_ms), min(last, end_ms)
        if left >= right:
            continue
        message = "\n".join(lines[2:]).strip()
        if not message:
            continue
        rendered.append(f"{len(rendered)+1}\n"
                        f"{_timestamp(left-start_ms)} --> {_timestamp(right-start_ms)}\n"
                        f"{message}")
    target.write_text("\n\n".join(rendered) + ("\n" if rendered else ""),
                      encoding="utf-8")
    return len(rendered)


def probe(path: Path) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe is required")
    done = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=False, timeout=45)
    if done.returncode:
        raise ValueError("Cannot inspect input video")
    try:
        info = json.loads(done.stdout)
        duration = float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError):
        raise ValueError("Invalid input video metadata") from None
    if not 0.5 <= duration <= 7200:
        raise ValueError("Invalid source video duration")
    kinds = {s.get("codec_type") for s in info.get("streams", [])}
    if "video" not in kinds:
        raise ValueError("Input does not contain a video stream")
    return {"seconds": duration, "hasAudio": "audio" in kinds}


def export_short(*, video: Path, output: Path, captions: Path | None = None,
                 start: float = 0, seconds: float = 30,
                 width: int = 720, height: int = 1280) -> dict:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required")
    if (not isinstance(start, (int, float)) or not isinstance(seconds, (int, float))
            or start < 0 or not 1 <= seconds <= 180
            or (width, height) not in {(720, 1280), (1080, 1920)}):
        raise ValueError("Use valid start/seconds (1-180 s) and vertical resolution")
    video = video.resolve(strict=True)
    if not video.is_file():
        raise ValueError("Source must be a regular file")
    details = probe(video)
    if start >= details["seconds"] - .1:
        raise ValueError("Start is beyond the end of the source")
    seconds = min(seconds, details["seconds"] - start)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    movie = output / "short-vertical.mp4"
    # Foreground fully visible; a blurred enlargement fills the 9:16 canvas.
    foreground_width = int(width * .944) // 2 * 2
    filt = (
        f"[0:v]split=2[forbg][forfg];"
        f"[forbg]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},boxblur=24:2[bg];"
        f"[forfg]scale={foreground_width}:-2:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]"
    )
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
           "-ss", f"{start:.3f}", "-i", str(video),
           "-t", f"{seconds:.3f}", "-filter_complex", filt,
           "-map", "[out]"]
    if details["hasAudio"]:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "160k"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-r", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(movie)]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            check=False, timeout=1200)
    if result.returncode or not movie.is_file():
        raise RuntimeError("Vertical export failed: " + result.stderr[-1200:])
    subs = None
    count = 0
    if captions:
        subs = output / "short-captions.srt"
        count = clip_srt(captions.resolve(strict=True), subs,
                         start_ms=round(start * 1000),
                         end_ms=round((start + seconds) * 1000))
    # Source video is already a draft; companion export is never publish-approved.
    report = {
        "video": str(movie), "sha256": _sha(movie), "source": str(video),
        "aspectRatio": "9:16", "resolution": f"{width}x{height}",
        "requestedSeconds": seconds, "startSeconds": start,
        "audioPresent": details["hasAudio"], "captions": str(subs) if subs else None,
        "captionBlocks": count, "selection": "fixed time window",
        "previewOnly": True, "publicationApproved": False,
        "note": "Review vertical legibility, caption timing and editorial value before publishing.",
    }
    _write_json(output / "short-report.json", report)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description="Export vertical Shorts from original videos")
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--captions", type=Path)
    p.add_argument("--start", type=float, default=0)
    p.add_argument("--seconds", type=float, default=30)
    p.add_argument("--size", choices=["720p", "1080p"], default="720p")
    args = p.parse_args(argv)
    try:
        w, h = (720, 1280) if args.size == "720p" else (1080, 1920)
        print(json.dumps(export_short(video=args.video, output=args.output,
                                      captions=args.captions, start=args.start,
                                      seconds=args.seconds, width=w, height=h),
                         ensure_ascii=False, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
