"""Offline, rights-gated real-footage ingestion for mixed-media video scenes.

Normalized clips contain ONLY video. Narration and original soundtrack remain
under the editor's control; no source-camera audio is carried into export.
Everything is local FFmpeg H.264 and untrusted inputs never become shell code.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import subprocess

VIDEO_SUFFIXES = frozenset((".mp4", ".mov", ".webm", ".mkv"))
MAX_SOURCE_BYTES = 250 * 1024 * 1024
MAX_CLIP_BYTES = 120 * 1024 * 1024
VERSION = "owned-video-footage-v1-normalized-h264-no-source-audio"


def _call(args: list[str], *, timeout: int = 300) -> bytes:
    try:
        result = subprocess.run(
            args, capture_output=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("FFmpeg footage operation exceeded local time limit") from exc
    if result.returncode:
        err = result.stderr.decode("utf-8", "replace")[-650:]
        raise ValueError("Unreadable or unprocessable local video: " + err)
    return result.stdout


def probe_video(source: Path, *, start: float, seconds: float) -> dict:
    source = Path(source)
    if (not source.is_file() or source.is_symlink() or
            source.suffix.lower() not in VIDEO_SUFFIXES or
            not 1024 <= source.stat().st_size <= MAX_SOURCE_BYTES):
        raise ValueError("Footage must be a local MP4/MOV/MKV/WEBM up to 250 MiB")
    if (type(start) not in (int,float) or type(seconds) not in (int,float)
            or not math.isfinite(start) or not math.isfinite(seconds)
            or not 0 <= start <= 3600 or not .5 <= seconds <= 3600):
        raise ValueError("Invalid source-footage trim")
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        raise RuntimeError("Local FFmpeg and FFprobe are required")
    payload = _call([
        "ffprobe","-v","error","-protocol_whitelist","file,pipe",
        "-select_streams","v:0","-show_entries",
        "stream=width,height,codec_name:format=duration",
        "-of","json",str(source)], timeout=30)
    try:
        data = json.loads(payload)
        streams = data["streams"]
        stream = streams[0]
        width = stream["width"]
        height = stream["height"]
        duration = float(data["format"]["duration"])
        codec = stream["codec_name"]
    except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise ValueError("Video source has no validated video stream and duration") from exc
    if (type(width) is not int or type(height) is not int or
            not 256 <= width <= 4096 or not 256 <= height <= 4096 or
            not 1 <= width*height <= 12_000_000 or
            not math.isfinite(duration) or not .5 <= duration <= 7200 or
            start + seconds > duration + .03 or
            not isinstance(codec,str) or not 1 <= len(codec) <= 40):
        raise ValueError("Footage resolution, duration or selected trim is unsupported")
    return {"sourceWidth":width,"sourceHeight":height,
            "sourceDurationSeconds":round(duration,3),
            "sourceVideoCodec":codec,"clipStartSeconds":round(start,3),
            "clipDurationSeconds":round(seconds,3)}



def framing_filter(*, source_width: int, source_height: int,
                   width: int, height: int, fps: int) -> tuple[str,bool]:
    """Return a safe FFmpeg filter and whether it needs filter_complex.

    Cropping a landscape video into portrait often removes the main action.
    If aspect ratios differ strongly, retain all source content over a
    blurred, moving fill made from the SAME original footage.
    """
    if (any(type(v) is not int for v in (
            source_width,source_height,width,height,fps))
            or not 256 <= source_width <= 4096
            or not 256 <= source_height <= 4096
            or not 128 <= width <= 3840 or not 128 <= height <= 3840
            or fps not in (24,30)):
        raise ValueError("Invalid original footage framing geometry")
    source_ratio=source_width/source_height
    target_ratio=width/height
    disparity=max(source_ratio/target_ratio,target_ratio/source_ratio)
    if disparity < 1.36:
        return (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},fps={fps},format=yuv420p",False)
    filter_graph=(
        "[0:v]split=2[background][foreground];"
        f"[background]scale={width}:{height}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,"
        "boxblur=luma_radius=14:luma_power=1:"
        "chroma_radius=7:chroma_power=1[softbg];"
        f"[foreground]scale={width}:{height}:"
        "force_original_aspect_ratio=decrease,"
        "setsar=1[subject];"
        "[softbg][subject]overlay=(W-w)/2:(H-h)/2:shortest=1,"
        f"fps={fps},format=yuv420p[v]")
    return filter_graph,True


SMART_FRAMING_VERSION = "owned-footage-motion-reframing-v1"


def smart_framing_filter(*, source: Path, seconds: float,
                         source_width: int, source_height: int,
                         width: int, height: int, fps: int,
                         mode: str = "preserve") -> tuple[str, bool, dict]:
    """Choose a real pixel-tracked vertical crop or safe full-content framing.

    The optical mode does *not* identify an object or promise a good crop.
    Preserve remains the default so older callers keep their image geometry.
    Generic automatic montage can opt into 'auto'; users can explicitly
    force 'follow' or 'preserve' without editing the original source.
    """
    if mode not in {"auto", "follow", "preserve"}:
        raise ValueError("Portrait framing must be auto, follow or preserve")
    existing, complex_graph = framing_filter(
        source_width=source_width, source_height=source_height,
        width=width, height=height, fps=fps)
    report = {
        "version": SMART_FRAMING_VERSION,
        "requested": mode,
        "applied": "preserve",
        "reason": None,
        "tracking": None,
        "humanReviewRequired": True,
    }
    if mode == "preserve":
        report["reason"] = "User chose full-content preservation"
        return existing, complex_graph, report
    disparity = (source_width / source_height) / (width / height)
    if not (source_width > source_height and width < height and
            disparity >= 1.36):
        report["reason"] = "Moving crop is unnecessary or inappropriate for this geometry"
        return existing, complex_graph, report
    crop_width = int((source_height * width / height) // 2) * 2
    if crop_width < 80 or crop_width >= source_width:
        report["reason"] = "Moving crop geometry would be too narrow"
        return existing, complex_graph, report
    from .subject_reframe import MAX_TRACK_SECONDS, track_crop, crop_expression
    if source_width < 320:
        if mode == "follow":
            raise ValueError("Tracking requires at least 320 source pixels horizontally")
        report["reason"] = "Not enough horizontal pixels for reliable optical tracking"
        return existing, complex_graph, report
    if not math.isfinite(seconds) or not 1 <= seconds <= MAX_TRACK_SECONDS:
        if mode == "follow":
            raise ValueError(
                f"Tracking requires real clips of 1–{MAX_TRACK_SECONDS:g} seconds")
        report["reason"] = "Shot length outside fully sampled tracking window"
        return existing, complex_graph, report

    tracking = track_crop(source=source, start=0, seconds=seconds,
                          source_width=source_width, crop_width=crop_width)
    report["tracking"] = tracking
    samples = tracking["sampledFrames"]
    if mode == "auto" and tracking["lowInformationFrames"] * 2 >= samples:
        report["reason"] = "Insufficient image information: keep full original frame"
        return existing, complex_graph, report
    expression = crop_expression(tracking)
    graph = (
        "setpts=PTS-STARTPTS,"
        f"crop={crop_width}:{source_height}:x='{expression}':y=0,"
        f"scale={width}:{height}:flags=lanczos,"
        f"fps={fps},setsar=1,format=yuv420p"
    )
    report["applied"] = "follow"
    report["reason"] = "Bounded image-activity tracking on decoded source frames"
    return graph, False, report


def normalize_video(source: Path, dest: Path, poster: Path, *,
                    start: float, seconds: float) -> dict:
    """Cut a single real clip to scene length, re-encode deterministically.

    Paths must be temporary files within the managed scene asset directory.
    The caller commits both files atomically and binds hashes to the plan.
    """
    source = Path(source)
    meta = probe_video(source,start=start,seconds=seconds)
    # Limit long 4K source to at most 1920px per dimension. No upscaling.
    # Fixed 30fps and yuv420p keep H.264 decoders portable across Android.
    video_filter = (
        "scale=w='min(1920,iw)':h='min(1920,ih)':"
        "force_original_aspect_ratio=decrease:force_divisible_by=2,"
        "fps=30,format=yuv420p")
    _call(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
           "-protocol_whitelist","file,pipe",
           "-ss",f"{start:.3f}","-i",str(source),
           "-map","0:v:0","-t",f"{seconds:.3f}",
           "-vf",video_filter,
           "-threads","2","-c:v","libx264","-preset","veryfast",
           "-crf","19","-pix_fmt","yuv420p","-an",
           "-movflags","+faststart",str(dest)],timeout=600)
    if (not dest.is_file() or not 10_000 <= dest.stat().st_size <= MAX_CLIP_BYTES):
        raise ValueError("Normalized video footage is missing or oversized")
    normalized = probe_video(dest,start=0,seconds=seconds-.08
                             if seconds > 1 else seconds*.9)
    # Preview image is required for existing image approval/review UI. It is
    # drawn from the real normalized video, not generated or mocked.
    _call(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
           "-ss",f"{min(.6,seconds*.4):.3f}",
           "-i",str(dest),"-frames:v","1","-update","1",
           "-f","image2",str(poster)],timeout=45)
    if not poster.is_file() or poster.stat().st_size < 1000:
        raise ValueError("Could not extract original footage preview frame")
    from PIL import Image
    with Image.open(poster) as img:
        if img.format != "PNG" or img.width < 256 or img.height < 256:
            raise ValueError("Invalid extracted video thumbnail")
        img.verify()
    return {**meta,"normalizedWidth":normalized["sourceWidth"],
            "normalizedHeight":normalized["sourceHeight"],
            "normalizedFps":30,"sourceAudioIncluded":False}
