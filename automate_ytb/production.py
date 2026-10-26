"""Offline, provider-neutral image production, rights review and resumable video renders.

All generated image prompts are untrusted *data*. This module never invokes an external
image provider, downloads third-party media, or publishes to YouTube.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageOps, UnidentifiedImageError

SCENE_ID = re.compile(r"scene-\d{3,4}\Z")
PROVIDER = re.compile(r"[a-zA-Z0-9_.-]{2,64}\Z")
MAX_SCENES = 1200
VERSION = "render-v22-articulated-ear-crest"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".scene-plan-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(obj, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_plan(path: Path) -> dict:
    path = path.resolve()
    if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Missing or oversized scene plan")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        raise ValueError("Unsupported scene plan schema")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= MAX_SCENES:
        raise ValueError("Scene plan must contain 1-1200 scenes")
    if data.get("sceneCount") != len(scenes) or data.get("publicationApproved") is not False:
        raise ValueError("Scene count mismatch or unsafe publication approval")
    duration = data.get("targetDurationSeconds")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 1 <= duration <= 3600:
        raise ValueError("Invalid target duration")
    previous = 0
    for i, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError("Scene data must be objects")
        sid = scene.get("id")
        expected = f"scene-{i:03d}"
        if sid != expected or not SCENE_ID.fullmatch(sid):
            raise ValueError(f"Unexpected scene identifier at index {i}")
        if scene.get("imageAsset") != f"assets/{expected}.png":
            raise ValueError(f"Unsafe image path for {sid}")
        start, end = scene.get("startMs"), scene.get("endMs")
        if (not isinstance(start, int) or not isinstance(end, int) or
                isinstance(start, bool) or isinstance(end, bool) or
                start != previous or end <= start):
            raise ValueError(f"Non-contiguous scene timing for {sid}")
        previous = end
        if not isinstance(scene.get("narration"), str) or not scene["narration"].strip():
            raise ValueError(f"Missing narration for {sid}")
        if not isinstance(scene.get("imagePrompt"), str) or not 1 <= len(scene["imagePrompt"]) <= 9000:
            raise ValueError(f"Missing or oversized image prompt for {sid}")
        if "direction" in scene:
            from .director import validate_direction
            validate_direction(scene["direction"])
    if previous != round(duration * 1000):
        raise ValueError("Final timecode does not match target duration")
    return data


def _asset_path(plan_path: Path, scene: dict) -> Path:
    root = plan_path.resolve().parent
    dest = root / scene["imageAsset"]
    if not dest.resolve().is_relative_to(root):
        raise ValueError("Scene asset points outside the project")
    return dest


def prepare(plan_path: Path, output: Path, price_per_image_usd: str | None = None) -> dict:
    data = load_plan(plan_path)
    price = _money(price_per_image_usd) if price_per_image_usd is not None else None
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        for scene in data["scenes"]:
            item = {
                "sceneId": scene["id"], "prompt": scene["imagePrompt"],
                "camera": scene.get("camera", ""), "width": 1920, "height": 1080,
                "aspectRatio": "16:9", "outputAsset": scene["imageAsset"],
                "characterBible": data.get("originalCharacterBible", ""),
                "styleBible": data.get("visualStyleBible", ""),
                "startMs": scene["startMs"], "endMs": scene["endMs"],
                "requiresRightsReview": True,
            }
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    return {
        "prompts": str(output), "scenes": len(data["scenes"]),
        "quotedEstimateUsd": str(price * len(data["scenes"])) if price is not None else None,
        "providerRequestsSent": 0, "publicationApproved": False,
    }


def _money(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid dollar amount") from None
    if not result.is_finite() or result < 0 or result > 10000:
        raise ValueError("Dollar amount must be finite and between 0 and 10000")
    return result.quantize(Decimal("0.0001"))


def ingest(*, plan_path: Path, scene_id: str, image_path: Path,
           provider: str, rights_note: str, cost_usd: str,
           rights_confirmed: bool = False, replace: bool = False) -> dict:
    if not rights_confirmed:
        raise ValueError("Explicit --confirm-rights required before importing media")
    if not PROVIDER.fullmatch(provider) or not 12 <= len(rights_note.strip()) <= 1000:
        raise ValueError("Provide a valid provider and detailed source/rights note")
    cost = _money(cost_usd)
    data = load_plan(plan_path)
    match = next((s for s in data["scenes"] if s["id"] == scene_id), None)
    if match is None:
        raise ValueError("Unknown scene identifier")
    source = image_path.resolve(strict=True)
    if not source.is_file() or source.stat().st_size > 30 * 1024 * 1024:
        raise ValueError("Missing or oversized image")
    dest = _asset_path(plan_path, match)
    if dest.exists() and not replace:
        raise ValueError("Asset exists; use --replace to explicitly overwrite")
    if dest.resolve() == source:
        raise ValueError("Source must be separate from managed asset destination")
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".scene-asset-", suffix=".png", dir=dest.parent)
    os.close(fd)
    try:
        try:
            with Image.open(source) as im:
                if im.width < 256 or im.height < 256 or im.width * im.height > 40_000_000:
                    raise ValueError("Image dimensions must be >=256x256 and <=40MP")
                if im.format not in ("PNG", "JPEG", "WEBP"):
                    raise ValueError("Only PNG, JPEG or WEBP images are accepted")
                converted = ImageOps.exif_transpose(im).convert("RGB")
                converted.save(tmp_name, format="PNG", optimize=True)
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("Unreadable or unsafe image") from error
        digest = _sha(Path(tmp_name))
        os.replace(tmp_name, dest)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    match.update({
        "assetApproved": True,
        "assetLicenseEvidence": rights_note.strip(),
        "assetSha256": digest,
        "assetProvider": provider,
        "assetCostUsd": str(cost),
        "assetImportedAt": datetime.now(timezone.utc).isoformat(),
        "reviewStatus": "rights-confirmed-by-user",
    })
    # Asset rights approval does NOT approve fact checks, audio, or YouTube publication.
    data["assetUseApproved"] = all(x.get("assetApproved") for x in data["scenes"])
    data["publicationApproved"] = False
    _write_json(plan_path.resolve(), data)
    return {"sceneId": scene_id, "sha256": digest, "provider": provider,
            "recordedCostUsd": str(cost), "publicationApproved": False}


def audit(plan_path: Path, limit: int | None = None) -> dict:
    data = load_plan(plan_path)
    scenes = data["scenes"][:limit] if limit is not None else data["scenes"]
    if not scenes or (limit is not None and (not isinstance(limit, int) or limit <= 0)):
        raise ValueError("Invalid scene limit")
    counts = {"ready": 0, "missing": 0, "unreviewed": 0, "changed": 0}
    details = []
    billed = Decimal("0")
    for scene in scenes:
        dest = _asset_path(plan_path, scene)
        if not dest.is_file():
            state = "missing"
        elif (not scene.get("assetApproved") or not scene.get("assetLicenseEvidence")
              or not scene.get("assetSha256")):
            state = "unreviewed"
        elif _sha(dest) != scene["assetSha256"]:
            state = "changed"
        else:
            state = "ready"
            billed += _money(scene.get("assetCostUsd", "0"))
        counts[state] += 1
        details.append({"sceneId": scene["id"], "status": state})
    return {
        "totalScenes": len(scenes), "counts": counts,
        "readyForPreview": counts["ready"] == len(scenes),
        "recordedAssetCostUsd": str(billed.quantize(Decimal("0.0001"))),
        "details": details, "publicationApproved": False,
    }


def _quoted(path: Path) -> str:
    # ffconcat uses its own token escaping; all paths resolve to local reviewed media.
    return "'" + str(path).replace("'", "'\\''") + "'"


def _run(args: list[str]) -> None:
    done = subprocess.run(args, capture_output=True, text=True, timeout=1200, check=False)
    if done.returncode:
        raise RuntimeError(f"FFmpeg step failed ({done.returncode}): {done.stderr[-1500:]}")


def _srt_time(ms: int) -> str:
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, rem = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"


def render(*, plan_path: Path, output: Path, audio: Path | None = None,
           limit: int | None = None, resolution: str = "720p", fps: int = 24,
           music: Path | None = None, caption_timing: str = "estimated",
           transition: str = "dissolve") -> dict:
    if resolution not in {"720p", "1080p"} or fps not in {24, 30}:
        raise ValueError("Supported resolutions: 720p/1080p, FPS: 24/30")
    if caption_timing not in {"estimated", "audio"}:
        raise ValueError("Caption timing must be estimated or audio")
    if transition not in {"cut", "dissolve"}:
        raise ValueError("Transition must be cut or dissolve")
    if caption_timing == "audio" and audio is None:
        raise ValueError("Audio-derived captions require a narration audio track")
    data = load_plan(plan_path)
    scenes = data["scenes"][:limit] if limit is not None else data["scenes"]
    results = audit(plan_path, limit)
    if not results["readyForPreview"]:
        raise ValueError(f"Scene assets not ready: {results['counts']}")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required to render")
    dims = (1280, 720) if resolution == "720p" else (1920, 1080)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cache = output / ".clip-cache"
    cache.mkdir(exist_ok=True)
    from .scene_props import carried_props_for_scenes, gaze_target
    from .scenic_world import landscapes_for_scenes, WORLD_VERSION
    from .voice_activity import activity_intervals, MOUTH_VERSION
    carried_by_scene = carried_props_for_scenes(data["scenes"])
    scene_landscapes = landscapes_for_scenes(data["scenes"])
    # An external MP3 or stereo audio track remains supported; only supported
    # mono 16-bit WAV narrations enable exact voice-activity mouth cues.
    voice_activity_by_scene = [
        activity_intervals(
            audio, scene_start_ms=scene["startMs"],
            scene_end_ms=scene["endMs"])
        if audio is not None else None for scene in scenes
    ]
    clips = []
    for scene_index, scene in enumerate(scenes):
        # Posters remain bound to the narration and character-specific rig.
        rig_tag = scene.get("motionRig")
        local_art = (scene.get("assetProvider") == "automate-local-graphics"
                     and scene.get("renderStyle") == "cartoon")
        from .animated_forest import character_kind
        forest_kind = character_kind(data["originalCharacterBible"])
        expected_forest_rig = (
            f"original-forest-{forest_kind}-v1" if forest_kind else None)
        if (isinstance(rig_tag, str)
                and rig_tag.startswith("original-forest-")
                and (rig_tag != expected_forest_rig or not local_art)):
            raise ValueError("Forest rig does not match the approved character and style")
        if scene.get("assetProvider") == "automate-local-graphics" and scene.get("artBriefSha256"):
            brief_args = dict(
                topic=data["topic"], narration=scene["narration"],
                character=data["originalCharacterBible"],
                style=scene.get("renderStyle", "cartoon"),
                scene_id=scene["id"],
                direction=scene.get("direction"),
                held_prop=carried_by_scene[scene_index],
                landscape=scene_landscapes[scene_index])
            if rig_tag == expected_forest_rig and local_art:
                from .animated_forest import art_brief_sha256 as forest_hash
                actual = forest_hash(kind=forest_kind, **brief_args)
            else:
                from .animated_owl import art_brief_sha256
                actual = art_brief_sha256(**brief_args)
            if actual != scene["artBriefSha256"]:
                raise ValueError(f"Artwork brief changed for {scene['id']}; reapproval required")
        seconds = (scene["endMs"] - scene["startMs"]) / 1000
        uses_owl_rig = (rig_tag == "original-owl-v1" and local_art)
        uses_forest_rig = (expected_forest_rig is not None
                           and rig_tag == expected_forest_rig and local_art)
        uses_motion_rig = uses_owl_rig or uses_forest_rig
        stamp = json.dumps({
            "assetSha": scene["assetSha256"], "seconds": seconds,
            "dimensions": dims, "fps": fps, "renderer": VERSION,
            "rig": rig_tag if uses_motion_rig else None,
            "scene": scene["narration"] if uses_motion_rig else "",
            "topic": data["topic"] if uses_motion_rig else "",
            "character": data.get("originalCharacterBible") if uses_motion_rig else "",
            "direction": scene.get("direction") if uses_motion_rig else None,
            "carriedProp": carried_by_scene[scene_index] if uses_motion_rig else None,
            "landscape": scene_landscapes[scene_index] if uses_motion_rig else None,
            "synthesizedGestureCues": (
                scene.get("captionSegments")
                if uses_motion_rig and caption_timing == "audio" else None),
            "voiceActivityVersion": MOUTH_VERSION if uses_motion_rig else None,
            "voiceActivity": (voice_activity_by_scene[scene_index]
                              if uses_motion_rig else None),
        }, sort_keys=True, ensure_ascii=False).encode("utf-8")
        key = hashlib.sha256(stamp).hexdigest()[:18]
        clip = cache / f"{scene['id']}-{key}.mp4"
        if not clip.exists() or clip.stat().st_size == 0:
            w, h = dims
            # Subtle continuous camera push-in; avoids frozen slides.
            motion = ("scale=" + f"{w}:{h}:force_original_aspect_ratio=increase"
                      + f",crop={w}:{h},"
                      + "zoompan=z='min(zoom+0.00045,1.12)':"
                      + "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':"
                      + f"d=1:s={w}x{h}:fps={fps},format=yuv420p")
            tmp = clip.with_name(clip.stem + ".tmp.mp4")
            try:
                if uses_owl_rig:
                    from .animated_owl import render_motion_clip
                    index = int(scene["id"].split("-")[1])
                    render_motion_clip(
                        topic=data["topic"], narration=scene["narration"],
                        scene_index=index, scene_count=len(data["scenes"]),
                        style="cartoon", duration=seconds,
                        width=w, height=h, fps=fps, destination=tmp,
                        direction=scene.get("direction"),
                        held_prop=carried_by_scene[scene_index],
                        caption_segments=(scene.get("captionSegments")
                                          if caption_timing == "audio" else None),
                        scene_start_ms=scene["startMs"],
                        mouth_intervals=voice_activity_by_scene[scene_index],
                        landscape=scene_landscapes[scene_index],
                    )
                elif uses_forest_rig:
                    from .animated_forest import render_motion_clip as render_forest_clip
                    index = int(scene["id"].split("-")[1])
                    render_forest_clip(
                        kind=forest_kind,
                        topic=data["topic"], narration=scene["narration"],
                        scene_index=index, scene_count=len(data["scenes"]),
                        style="cartoon", duration=seconds,
                        width=w, height=h, fps=fps, destination=tmp,
                        direction=scene.get("direction"),
                        held_prop=carried_by_scene[scene_index],
                        caption_segments=(scene.get("captionSegments")
                                          if caption_timing == "audio" else None),
                        scene_start_ms=scene["startMs"],
                        mouth_intervals=voice_activity_by_scene[scene_index],
                        landscape=scene_landscapes[scene_index],
                    )
                else:
                    _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                          "-loop", "1", "-framerate", str(fps),
                          "-i", str(_asset_path(plan_path, scene)), "-t", f"{seconds:.3f}",
                          "-vf", motion, "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(tmp)])
                os.replace(tmp, clip)
            finally:
                tmp.unlink(missing_ok=True)
        clips.append(clip)
    # Action phases are visual-only cues: no audio/subtitle timeline changes.
    from .action_timeline import timeline_report
    action_timelines = [
        dict(sceneId=s["id"], **timeline_report(
            s["narration"], (s["endMs"] - s["startMs"])/1000,
            s.get("direction", {}).get("action", "idle"),
            caption_segments=(s.get("captionSegments")
                              if caption_timing == "audio" else None),
            scene_start_ms=s["startMs"]))
        for s in scenes
        if s.get("motionRig") in {
            "original-owl-v1", "original-forest-fox-v1",
            "original-forest-rabbit-v1", "original-forest-cat-v1"
        } and s.get("renderStyle") == "cartoon"
    ]
    # Visual transitions do not trim, overlap or shift the storyboard timeline.
    # Narration, original music and SRT timecodes retain their planned starts.
    from .transitions import transition_clips
    edited_clips, transitions_report = transition_clips(
        clips, cache=cache, fps=fps,
        durations=[(s["endMs"] - s["startMs"]) / 1000 for s in scenes],
        mode=transition)
    concat = output / "clips.ffconcat"
    concat.write_text("ffconcat version 1.0\n" +
                      "".join(f"file {_quoted(c)}\n" for c in edited_clips), encoding="utf-8")
    raw = output / "silent-video.mp4"
    _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
          "-f", "concat", "-safe", "0", "-i", str(concat),
          "-c", "copy", "-movflags", "+faststart", str(raw)])
    result = output / "preview.mp4"
    duration = scenes[-1]["endMs"] / 1000
    if audio is not None:
        audio = audio.resolve(strict=True)
        if not audio.is_file():
            raise ValueError("Narration audio must be a file")
    if music is not None:
        music = music.resolve(strict=True)
        if not music.is_file():
            raise ValueError("Soundtrack audio must be a file")
    if music is not None and audio is not None:
        # Compress the music against the narration *only while it speaks*,
        # instead of making the entire episode background unpleasantly quiet.
        # The final limiter prevents additive clipping.
        filters = (
            "[1:a]aresample=48000,highpass=f=70,"
            "acompressor=threshold=0.15:ratio=2:attack=12:release=160,"
            "asplit=2[spoken][control];"
            "[2:a]aresample=48000,highpass=f=70,volume=0.24[background];"
            "[background][control]sidechaincompress="
            "threshold=0.02:ratio=7:attack=25:release=350[ducked];"
            "[spoken][ducked]amix=inputs=2:duration=longest:normalize=0,"
            "alimiter=limit=0.92,"
            "loudnorm=I=-16:LRA=11:TP=-1.5[out]"
        )
        _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-i", str(raw), "-i", str(audio), "-i", str(music),
              "-filter_complex", filters, "-map", "0:v:0", "-map", "[out]",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
              "-t", f"{duration:.3f}", "-movflags", "+faststart", str(result)])
    elif music is not None:
        # Silent storytelling also gets a modest, faded instrumental bed.
        filters = ("[1:a]aresample=48000,volume=0.27,"
                   "afade=t=in:d=0.45,"
                   f"afade=t=out:st={max(0, duration-0.8):.3f}:d=0.8,"
                   "alimiter=limit=0.90,"
                   "loudnorm=I=-24:LRA=11:TP=-1.5[out]")
        _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-i", str(raw), "-i", str(music),
              "-filter_complex", filters, "-map", "0:v:0", "-map", "[out]",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
              "-t", f"{duration:.3f}", "-movflags", "+faststart", str(result)])
    elif audio is not None:
        _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-i", str(raw), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
              "-af", "apad,loudnorm=I=-16:LRA=11:TP=-1.5",
              "-t", f"{duration:.3f}", "-movflags", "+faststart", str(result)])
    else:
        shutil.copy2(raw, result)
    from .captions import subtitles_for_scenes
    srt = output / "draft-captions.srt"
    captions_text, captions_report = subtitles_for_scenes(
        scenes, use_audio_boundaries=(caption_timing == "audio"))
    srt.write_text(captions_text, encoding="utf-8")
    # Portable, inspectable coverage of the actual storyboard direction.
    from collections import Counter
    directed = [s["direction"] for s in scenes if "direction" in s]
    directions_report = {
        category: dict(sorted(Counter(item[category] for item in directed).items()))
        for category in ("weather", "action", "emotion", "shot")
    }
    report = {
        "director": {"version": "keyword-cues-v1", "directedScenes": len(directed),
                     "counts": directions_report,
                     "method": "conservative-keyword-match-on-user-script"},
        "video": str(result), "videoSha256": _sha(result),
        "scenesRendered": len(scenes), "resolution": resolution, "fps": fps,
        "targetDurationSeconds": scenes[-1]["endMs"] / 1000,
        "hasNarrationAudio": audio is not None,
        "hasBackgroundMusic": music is not None,
        "audioMastering": ("ffmpeg-loudnorm-ebu-r128-single-pass"
                           if audio is not None or music is not None else "none"),
        "targetIntegratedLufs": (-16 if audio is not None else
                                 -24 if music is not None else None),
        "targetTruePeakDbtp": (-1.5 if audio is not None or music is not None
                               else None),
        "audioMixMode": ("ducked-narration-plus-original-bed" if music is not None and audio is not None
                         else "original-bed-only" if music is not None else "narration-only" if audio is not None
                         else "silent"),
        "transitions": transitions_report,
        "objectGaze": {
            "version": "prop-eye-pose-v1",
            "method": "static-original-2d-eye-offset-toward-scripted-object",
            "scenes": [
                {"sceneId": scene["id"], "direction": gaze_target(
                    scene["narration"], held_prop=carried_by_scene[i])}
                for i, scene in enumerate(scenes)
                if scene.get("motionRig") in {
                    "original-owl-v1", "original-forest-fox-v1",
                    "original-forest-rabbit-v1", "original-forest-cat-v1"
                } and scene.get("renderStyle") == "cartoon"
            ],
            "audioTimelineShiftMs": 0,
        },
        "speechMouth": {
            "version": MOUTH_VERSION,
            "method": "mono-pcm-80ms-voice-activity-not-phonetic",
            "audioTimelineShiftMs": 0,
            "analyzedScenes": sum(x is not None for x in voice_activity_by_scene),
            "activeIntervals": sum(len(x) for x in voice_activity_by_scene
                                   if x is not None),
            "fallbackScenes": sum(x is None for x in voice_activity_by_scene),
        },
        "landscapes": {
            "version": WORLD_VERSION,
            "source": "script-derived-persistent-original-scenes",
            "sceneCount": len(scenes),
            "distinctSettings": sorted(set(scene_landscapes[:len(scenes)])),
            "byScene": [
                {"sceneId": scene["id"], "setting": scene_landscapes[i]}
                for i, scene in enumerate(scenes)
            ],
            "audioTimelineShiftMs": 0,
        },
        "actionTimeline": {
            "version": "script-action-phases-v1",
            "multiActionScenes": sum(t["phaseCount"] > 1 for t in action_timelines),
            "audioAnchoredScenes": sum(t["audioAnchored"] for t in action_timelines),
            "scenes": action_timelines,
            "audioTimelineShiftMs": 0,
        },
        "propContinuity": {
            "version": "scene-props-v2-continuity",
            "carriedScenes": sum(1 for p in carried_by_scene[:len(scenes)]
                                if p is not None),
            "carriedByScene": [
                {"sceneId": scene["id"], "prop": carried_by_scene[i]}
                for i, scene in enumerate(scenes)
                if carried_by_scene[i] is not None
            ],
            "source": "script-only-context-from-earlier-pickups",
            "timelineShiftMs": 0,
        },
        "captions": str(srt),
        "animatedOwlScenes": sum(
            1 for s in scenes
            if s.get("motionRig") == "original-owl-v1"
            and s.get("assetProvider") == "automate-local-graphics"
            and s.get("renderStyle") == "cartoon"
        ),
        "animatedForestScenes": sum(
            1 for s in scenes
            if s.get("motionRig") in {
                "original-forest-fox-v1",
                "original-forest-rabbit-v1",
                "original-forest-cat-v1",
            }
            and s.get("assetProvider") == "automate-local-graphics"
            and s.get("renderStyle") == "cartoon"
        ),
        "captionsPreciselyAligned": False,
        "captionCueAlignment": captions_report["method"],
        "captionGeneration": captions_report,
        "previewOnly": True,
        "publicationApproved": False, "assetCostUsd": results["recordedAssetCostUsd"],
        "warning": "Draft scene timecodes are not forced alignment against final audio.",
    }
    _write_json(output / "render-report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Reviewable image-to-video production pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="Export original prompts for provider-agnostic generation")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--quote-per-image-usd", default=None)
    p = sub.add_parser("ingest", help="Import a generated/owned image with explicit rights declaration")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--scene", required=True)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--provider", required=True)
    p.add_argument("--rights-note", required=True)
    p.add_argument("--cost-usd", default="0")
    p.add_argument("--confirm-rights", action="store_true")
    p.add_argument("--replace", action="store_true")
    p = sub.add_parser("audit", help="Verify completeness, checksums, review and recorded image costs")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)
    p = sub.add_parser("render", help="Build resumable, animated FFmpeg video preview")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--audio", type=Path)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--resolution", choices=["720p", "1080p"], default="720p")
    p.add_argument("--fps", type=int, choices=[24, 30], default=24)
    p.add_argument("--transition", choices=["dissolve", "cut"], default="dissolve")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.plan, args.output, args.quote_per_image_usd)
        elif args.command == "ingest":
            result = ingest(plan_path=args.plan, scene_id=args.scene,
                            image_path=args.image, provider=args.provider,
                            rights_note=args.rights_note, cost_usd=args.cost_usd,
                            rights_confirmed=args.confirm_rights, replace=args.replace)
        elif args.command == "audit":
            result = audit(args.plan, args.limit)
        else:
            result = render(plan_path=args.plan, output=args.output,
                            audio=args.audio, limit=args.limit,
                            resolution=args.resolution, fps=args.fps,
                            transition=args.transition)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
