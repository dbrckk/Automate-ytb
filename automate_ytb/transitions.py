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


VERSION = "hold-frame-dissolve-v3-universal-editorial-cut"
DISSOLVE_SECONDS = 0.32


def transition_clips(clips: list[Path], *, cache: Path, fps: int,
                     durations: list[float], mode: str = "dissolve",
                     render_profile: str = "preview",
                     preserve_science_ui: bool = False
                     ) -> tuple[list[Path], dict]:
    """Create resumable, original, visually transitioned *silent* scene clips."""
    video_args(render_profile)
    if type(preserve_science_ui) is not bool:
        raise ValueError("Invalid science UI preservation flag")
    if mode not in {"dissolve", "cut", "adaptive"}:
        raise ValueError("Unknown scene transition; use adaptive, dissolve or cut")
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
    boundary_reports = []
    fade_count = 0
    cut_count = 0
    for i in range(1, len(clips)):
        previous, current = clips[i - 1], clips[i]
        if not previous.is_file() or not current.is_file():
            raise ValueError("Cannot transition missing scene clips")
        blend = min(DISSOLVE_SECONDS, durations[i - 1] * 0.35,
                    durations[i] * 0.35)
        # The adaptive editor compares ACTUAL encoded frame pairs rather
        # than assuming every narrative boundary wants a double exposure.
        # An explicit dissolve always retains the requested dissolve.
        decision = None
        if mode == "adaptive":
            from .editorial_cuts import choose_transition
            from PIL import Image
            with tempfile.TemporaryDirectory(prefix="automate-ytb-cut-review-") as review_dir:
                review_path = Path(review_dir)
                outgoing = review_path / "outgoing.png"
                incoming = review_path / "incoming.png"
                _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                      "-y", "-sseof", "-0.12", "-i", str(previous),
                      "-frames:v", "1", str(outgoing)])
                _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                      "-y", "-i", str(current), "-frames:v", "1", str(incoming)])
                with Image.open(outgoing) as frame:
                    old = frame.convert("RGB")
                with Image.open(incoming) as frame:
                    new = frame.convert("RGB")
                decision = choose_transition(old, new)
        actual_mode = decision["mode"] if decision else "dissolve"
        boundary_reports.append({
            "fromScene": i,
            "toScene": i + 1,
            "transition": actual_mode,
            "analysis": decision,
            "timelineShiftMs": 0,
        })
        if actual_mode == "cut":
            result.append(current)
            cut_count += 1
            continue
        fade_count += 1
        # Never depend on a mutable clip name alone; production scene clips
        # contain approved image hashes, timing, direction and render version.
        source = f"{VERSION}|{previous.name}|{current.name}|{fps}|{blend:.6f}|{render_profile}|{preserve_science_ui}"
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
                    # Burned-in captions and titles should never be overlaid
                    # from the outgoing scene on top of the next scene's UI.
                    # Apply a feathered stage-only matte to its final frame.
                    if preserve_science_ui:
                        from PIL import Image, ImageDraw, ImageFilter
                        with Image.open(still) as source_frame:
                            old_frame = source_frame.convert("RGBA")
                        width, height = old_frame.size
                        if (width, height) != (1080, 1920):
                            raise ValueError("Science UI masking needs 1080x1920")
                        alpha = Image.new("L", (width, height))
                        pen = ImageDraw.Draw(alpha)
                        pen.rectangle((0, 530, width, 1440), fill=255)
                        old_frame.putalpha(
                            alpha.filter(ImageFilter.GaussianBlur(35)))
                        old_frame.save(still)
                    # The incoming stream retains the original duration.
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
    return result, {
        "mode": mode,
        "count": fade_count,
        "cutCount": cut_count,
        "analyzedBoundaries": len(boundary_reports),
        "boundaries": boundary_reports,
        "durationSeconds": DISSOLVE_SECONDS,
        "timelineShiftMs": 0,
        "method": VERSION,
        "publicationApproved": False,
    }
