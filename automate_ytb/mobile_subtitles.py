"""Burn mobile-sized English/French Shorts captions from real timed SRT.

Never resynthesize voice, claim word-level alignment or overwrite the master.
Internal phrase splits use proportional text lengths; source phrase bounds are
the genuine measured narration timestamps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

MAX_SOURCE_BYTES = 250_000
MAX_DURATION_MS = 180_000
MAX_WORDS = 8
MAX_CHARS = 43
MIN_SEGMENT_MS = 320
STYLE = (
    "FontName=DejaVu Sans,FontSize=11,PrimaryColour=&H00FFFFFF,"
    "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,"
    "Alignment=2,MarginV=78"
)


def _stamp(ms: int) -> str:
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{milli:03}"


def parse_srt(text: str) -> list[tuple[int, int, str]]:
    parts = re.split(r"\n\s*\n", text.replace("\r\n", "\n").lstrip("\ufeff").strip())
    if not 1 <= len(parts) <= 400:
        raise ValueError("Unexpected original speech subtitle count")
    pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    previous, cues = 0, []
    for index, block in enumerate(parts, 1):
        lines = block.splitlines()
        if len(lines) < 3 or lines[0].strip() != str(index):
            raise ValueError("Malformed original subtitle numbering")
        time = pattern.fullmatch(lines[1].strip())
        if time is None:
            raise ValueError("Malformed original SRT timecode")
        t = tuple(map(int, time.groups()))
        if any(v > 59 for v in (t[1], t[2], t[5], t[6])):
            raise ValueError("Invalid timecode")
        start = ((t[0] * 60 + t[1]) * 60 + t[2]) * 1000 + t[3]
        end = ((t[4] * 60 + t[5]) * 60 + t[6]) * 1000 + t[7]
        if not previous <= start < end <= MAX_DURATION_MS:
            raise ValueError("Overlapping, reversed or oversized speech timing")
        content = " ".join(" ".join(lines[2:]).split())
        if not content or len(content) > 1000:
            raise ValueError("Missing or oversized narrated phrase")
        cues.append((start, end, content))
        previous = end
    return cues


def segment_cues(cues: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    output: list[tuple[int, int, str]] = []
    for start, end, content in cues:
        words = content.split()
        if any(len(word) > MAX_CHARS for word in words):
            raise ValueError("Unbreakable long word exceeds mobile subtitle width")
        groups, current = [], []
        for word in words:
            if current and (
                len(" ".join(current + [word])) > MAX_CHARS
                or len(current) >= MAX_WORDS
            ):
                groups.append(" ".join(current))
                current = []
            current.append(word)
        if current:
            groups.append(" ".join(current))
        if len(groups) * MIN_SEGMENT_MS > end - start:
            raise ValueError("Speech phrase cannot fit readable subtitle groups")
        weights = [len(group) for group in groups]
        total = sum(weights)
        cursor = start
        for i, group in enumerate(groups):
            remaining = len(groups) - i - 1
            proposed = start + round((end - start) * sum(weights[:i + 1]) / total)
            boundary = end if not remaining else max(
                cursor + MIN_SEGMENT_MS,
                min(end - remaining * MIN_SEGMENT_MS, proposed),
            )
            output.append((cursor, boundary, group))
            cursor = boundary
    if " ".join(cue[2] for cue in output) != " ".join(cue[2] for cue in cues):
        raise RuntimeError("Short subtitles lost words from original narration")
    return output


def create_mobile_srt(source: Path, destination: Path) -> dict:
    if (not source.is_file() or source.is_symlink() or
            not 0 < source.stat().st_size < MAX_SOURCE_BYTES):
        raise ValueError("Missing, unsafe or oversized original narration SRT")
    original = parse_srt(source.read_text(encoding="utf-8-sig"))
    mobile = segment_cues(original)
    rendered = "".join(
        f"{i}\n{_stamp(start)} --> {_stamp(end)}\n{text}\n\n"
        for i, (start, end, text) in enumerate(mobile, 1)
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")
    return {
        "sourceCues": len(original), "mobileCues": len(mobile),
        "sourceSrtSHA256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "mobileSrtSHA256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "timingMethod": "measured-phrase-bounds; intra-phrase proportional estimates",
        "publicationApproved": False,
    }


def _gray_at(video: Path, seconds: float) -> bytes:
    cmd = [
        "ffmpeg", "-nostdin", "-v", "error", "-ss", f"{seconds:.3f}",
        "-i", str(video), "-an", "-frames:v", "1",
        "-vf", "scale=270:480,format=gray", "-f", "rawvideo", "pipe:1",
    ]
    out = subprocess.run(cmd, capture_output=True, check=False, timeout=25)
    if out.returncode or len(out.stdout) != 270 * 480:
        raise RuntimeError("Cannot decode a real frame for caption visibility QA")
    return out.stdout


def _verify_text_pixels(master: Path, burned: Path, subtitle: Path) -> int:
    # A mere successfully encoded MP4 is not enough: a mistaken libass
    # PlayResY/MarginV value used to put all text off-screen.
    first = parse_srt(subtitle.read_text(encoding="utf-8"))[0]
    moment = (first[0] + first[1]) / 2000
    before, after = _gray_at(master, moment), _gray_at(burned, moment)
    # 270x480 sample; keep the caption safe area in the central/lower panel.
    left, right = before[255 * 270:405 * 270], after[255 * 270:405 * 270]
    changed = sum(abs(x - y) >= 35 for x, y in zip(left, right))
    if changed < 500:
        raise RuntimeError("Captions are not visibly burned into encoded pixels")
    return changed


def burn(*, video: Path, captions: Path, destination: Path) -> dict:
    if not video.is_file() or video.is_symlink() or not captions.is_file():
        raise ValueError("Missing original encoded MP4 or mobile SRT")
    if destination.exists() or destination.resolve() == video.resolve():
        raise ValueError("Refusing to overwrite the original video or an existing export")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe are required")
    source_sha = hashlib.sha256(video.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="short-burn-") as tempdir:
        folder = Path(tempdir)
        (folder / "mobile.srt").write_bytes(captions.read_bytes())
        result = folder / "burned.mp4"
        cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y",
            "-i", str(video.resolve()), "-vf",
            f"subtitles=mobile.srt:force_style='{STYLE}'",
            "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "copy",
            "-movflags", "+faststart", "-threads", "2", str(result),
        ]
        try:
            encoded = subprocess.run(
                cmd, cwd=folder, capture_output=True, text=True,
                check=False, timeout=480,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Mobile caption rendering timed out") from exc
        if (encoded.returncode or not result.is_file()
                or result.stat().st_size < 20_000):
            raise RuntimeError("Burned subtitle encoding failed: " + encoded.stderr[-600:])
        decoded = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-i", str(result),
             "-f", "null", "-"],
            capture_output=True, text=True, check=False, timeout=240,
        )
        if decoded.returncode:
            raise RuntimeError("Burned subtitle MP4 failed complete decode")
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height",
             "-of", "json", str(result)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        info = json.loads(probe.stdout)
        vids = [s for s in info["streams"] if s["codec_type"] == "video"]
        audios = [s for s in info["streams"] if s["codec_type"] == "audio"]
        if (len(vids) != 1 or len(audios) != 1
                or (vids[0]["width"], vids[0]["height"]) != (1080, 1920)
                or vids[0]["codec_name"] != "h264"
                or audios[0]["codec_name"] != "aac"):
            raise RuntimeError("Vertical H264/AAC output tracks are incomplete")
        visible = _verify_text_pixels(video, result, captions)
        if hashlib.sha256(video.read_bytes()).hexdigest() != source_sha:
            raise RuntimeError("Original MP4 changed while burning subtitles")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(result, destination)
    return {
        "video": str(destination),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "fileBytes": destination.stat().st_size,
        "durationSeconds": float(info["format"]["duration"]),
        "visibleCaptionPixels": visible,
        "videoCodec": vids[0]["codec_name"],
        "audioCodec": audios[0]["codec_name"],
        "originalVideoSHA256": source_sha,
        "originalVideoUntouched": True,
        "publicationApproved": False,
    }


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Add verified mobile-sized subtitles to a real 9:16 H264/AAC Short")
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--srt", type=Path, required=True)
    p.add_argument("--mobile-srt", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args(argv)
    metadata = create_mobile_srt(a.srt, a.mobile_srt)
    metadata.update(burn(video=a.video, captions=a.mobile_srt, destination=a.out))
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata))


if __name__ == "__main__":
    main()
