"""Timeline-preserving cinematic dissolves between approved scene clips.

Unlike FFmpeg's overlapping xfade, a held final frame from the outgoing
scene is dissolved over the first frames of the incoming clip. The incoming
clip retains its exact frame count: speech, music, scene plan and SRT times
must never shift because of a purely visual transition.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile

from .encoding_profiles import video_args


VERSION = "hold-frame-dissolve-v1"
DISSOLVE_SECONDS = 0.32


def transition_clips(clips: list[Path], *, cache: Path, fps: int,
                     durations: list[float], mode: str = "dissolve",
                     render_profile: str = "preview"
                     ) -> tuple[list[Path], dict]:
    """Create resumable, original, visually transitioned *silent* scene clips."""
    video_args(render_profile)
    if mode not in {"dissolve", "cut"}:
        raise ValueError("Unknown scene transition; use dissolve or cut")
    if fps not in {24, 30}:
        raise ValueError("Unsupported transition frame rate")
    if not clips or len(clips) != len(durations):
        raise ValueError("Clip/duration count mismatch")
    if any(not isinstance(seconds, (int, float)) or not 0.5 <= seconds <= 3600
           for seconds in durations):
        raise ValueError("Invalid scene duration for transition")
    result = [clips[0]]
    if len(clips) == 1 or mode == "cut":
        return clips, {"mode": mode, "count": 0, "durationSeconds": 0,
                       "timelineShiftMs": 0, "method": "direct-cut"}
    from .production import _run
    cache.mkdir(parents=True, exist_ok=True)
    for i in range(1, len(clips)):
        previous, current = clips[i - 1], clips[i]
        if not previous.is_file() or not current.is_file():
            raise ValueError("Cannot transition missing scene clips")
        blend = min(DISSOLVE_SECONDS, durations[i - 1] * 0.35,
                    durations[i] * 0.35)
        # Never depend on a mutable clip name alone; production scene clips
        # contain approved image hashes, timing, direction and render version.
        source = f"{VERSION}|{previous.name}|{current.name}|{fps}|{blend:.6f}|{render_profile}"
        key = hashlib.sha256(source.encode()).hexdigest()[:20]
        dest = cache / f"scene-{i+1:03d}-dissolve-{key}.mp4"
        if not dest.is_file() or not dest.stat().st_size:
            temp = cache / f".scene-{i+1:03d}-{key}.tmp.mp4"
            try:
                with tempfile.TemporaryDirectory(prefix="automate-ytb-dissolve-") as temp_dir:
                    still = Path(temp_dir) / "outgoing-last-frame.png"
                    # Seek near the end. Every scene lasts at least 0.5s,
                    # with fps>=24, so at least one end frame is available.
                    _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                          "-y", "-sseof", "-0.12", "-i", str(previous),
                          "-frames:v", "1", str(still)])
                    # Overlay the previous last frame at full opacity and
                    # dissolve it to transparent, revealing current frames.
                    # The incoming stream defines the unmodified duration.
                    graph = (
                        "[1:v]format=rgba,"
                        f"fade=t=out:st=0:d={blend:.3f}:alpha=1[previous];"
                        "[0:v][previous]overlay=x=0:y=0:shortest=1:format=auto,"
                        "format=yuv420p[out]"
                    )
                    _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                          "-y", "-i", str(current), "-loop", "1",
                          "-framerate", str(fps), "-i", str(still),
                          "-filter_complex", graph, "-map", "[out]",
                          "-frames:v", str(round(durations[i] * fps)),
                          "-r", str(fps), *video_args(render_profile),
                          "-an", str(temp)])
                    if not temp.is_file() or not temp.stat().st_size:
                        raise RuntimeError("Empty cinematic transition clip")
                    temp.replace(dest)
            finally:
                temp.unlink(missing_ok=True)
        result.append(dest)
    return result, {"mode": mode, "count": len(clips) - 1,
                    "durationSeconds": DISSOLVE_SECONDS,
                    "timelineShiftMs": 0, "method": VERSION}
