"""One-command, no-API-cost video preview from an original scene plan.

Offline scenes use generated graphic cards and the existing FFmpeg renderer.
This does NOT produce AI illustrations, factual research or final publication.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import wave

from . import production
from .studio import make_thumbnails, render_art, synthesize_voice
from .animated_owl import render_character_poster, art_brief_sha256
from .narration import SpeechEngine


LOCAL_RIGHTS = ("Original geometric scene cards generated locally by Automate-ytb "
                "from the user's authored narrative; no third-party media imported.")


def create_local_art(plan_path: Path, *, style: str = "cartoon",
                     limit: int | None = None) -> dict:
    if style not in {"cartoon", "cinematic", "documentary"}:
        raise ValueError("Unsupported graphic style")
    data = production.load_plan(plan_path)
    scenes = data["scenes"][:limit]
    if not scenes or (limit is not None and limit < 1):
        raise ValueError("Scene limit must be positive")
    already = {s["sceneId"]: s["status"] for s in production.audit(plan_path)["details"]}
    rendered, reused = 0, 0
    character_text = data["originalCharacterBible"].casefold()
    is_owl = any(word in character_text for word in ("owl", "chouette", "hibou"))
    for i, scene in enumerate(scenes, start=1):
        state = already.get(scene["id"])
        brief_sha = art_brief_sha256(
            topic=data["topic"], narration=scene["narration"],
            character=data["originalCharacterBible"], style=style,
            scene_id=scene["id"], direction=scene.get("direction"))
        if state == "ready":
            if scene.get("renderStyle") and scene["renderStyle"] != style:
                raise ValueError("Approved artwork belongs to another style; start a new project")
            if scene.get("artBriefSha256") and scene["artBriefSha256"] != brief_sha:
                raise ValueError("Approved artwork belongs to another story/character; reapprove")
            reused += 1
            continue
        if state in ("unreviewed", "changed"):
            raise ValueError(f"Scene {scene['id']} has modified or unreviewed assets; "
                             "explicitly resolve these before re-generating")
        with tempfile.TemporaryDirectory(prefix="automate-ytb-art-") as folder:
            image = Path(folder) / "original-graphic.png"
            if style == "cartoon" and is_owl:
                render_character_poster(
                    topic=data["topic"], narration=scene["narration"],
                    scene_index=i, scene_count=len(data["scenes"]),
                    style=style, destination=image,
                    direction=scene.get("direction"))
            else:
                render_art(data["topic"], scene["narration"], i, len(data["scenes"]),
                           style, image)
            production.ingest(
                plan_path=plan_path, scene_id=scene["id"], image_path=image,
                provider="automate-local-graphics", rights_note=LOCAL_RIGHTS,
                cost_usd="0", rights_confirmed=True,
            )
            # Bind the rights-reviewed locally authored PNG to its exact
            # original narration, character and style for safe future reuse.
            current = production.load_plan(plan_path)
            current["scenes"][i-1]["renderStyle"] = style
            current["scenes"][i-1]["artBriefSha256"] = brief_sha
            if style == "cartoon" and is_owl:
                current["scenes"][i-1]["motionRig"] = "original-owl-v1"
            production._write_json(plan_path, current)
        rendered += 1
    return {"mode": "offline-graphics", "created": rendered, "reused": reused,
            "characterRig": "original-owl-v1" if style == "cartoon" and is_owl else "none",
            "apiCalls": 0, "providerCostUsd": "0.0000"}


def _narrate_scenes(plan_path: Path, voice_path: Path, language: str,
                    limit: int | None, *, engine: str = "espeak",
                    voice_name: str | None = None) -> dict:
    """Build full scene-level timing from actual speech, never clipping words.

    The scene plan remains an editable DRAFT. This does not claim word-aligned
    subtitles or accurate human pronunciation; listen before publication.
    """
    data = production.load_plan(plan_path)
    scenes = data["scenes"][:limit]
    if not scenes:
        raise ValueError("No scenes selected for narration")
    voice_path.parent.mkdir(parents=True, exist_ok=True)
    synth = SpeechEngine(engine=engine, language=language, voice=voice_name)
    utterances = [synth.audio(scene["narration"]) for scene in scenes]
    sample_rate = utterances[0][1]
    if not 8000 <= sample_rate <= 96000:
        raise ValueError("Unsupported speech sample rate")
    if any(rate != sample_rate or not frames or len(frames) % 2
           for frames, rate in utterances):
        raise RuntimeError("Invalid or mismatched PCM scene audio")

    # Use integer milliseconds for all timeline boundaries; the actual WAV
    # may differ by at most one sample due to integer sample conversion.
    durations_ms = [scene["endMs"] - scene["startMs"] for scene in data["scenes"]]
    complete_audio = []
    for i, (frames, _) in enumerate(utterances):
        actual_samples = len(frames) // 2
        min_ms = math.ceil((actual_samples / sample_rate + 0.35) * 1000)
        durations_ms[i] = max(durations_ms[i], min_ms)
        target_samples = math.ceil(durations_ms[i] * sample_rate / 1000)
        complete_audio.append(frames + b"\x00" * ((target_samples - actual_samples) * 2))
    total_ms = sum(durations_ms)
    if total_ms > 3_600_000:
        raise ValueError("Narration would exceed the one-hour scene-plan limit")
    offset = 0
    for scene, duration_ms in zip(data["scenes"], durations_ms):
        scene["startMs"] = offset
        offset += duration_ms
        scene["endMs"] = offset
    data["targetDurationSeconds"] = total_ms / 1000
    data["publicationApproved"] = False
    # Audio must be fully written before the manifest is updated.
    temp_audio = voice_path.with_name("temporary-narration.wav")
    try:
        with wave.open(str(temp_audio), "wb") as wavefile:
            wavefile.setnchannels(1)
            wavefile.setsampwidth(2)
            wavefile.setframerate(sample_rate)
            for frames in complete_audio:
                wavefile.writeframes(frames)
        os.replace(temp_audio, voice_path)
    finally:
        temp_audio.unlink(missing_ok=True)
    production._write_json(plan_path.resolve(), data)
    return {
        "voice": str(voice_path), "engine": "kokoro-natural" if engine == "kokoro"
        else "espeak-draft", "voiceId": synth.voice,
        "sceneBoundaryTiming": "audio-derived", "wordAlignment": False,
        "audioSeconds": round(sum(len(audio) for audio in complete_audio) / (2*sample_rate), 3),
        "sampleRate": sample_rate, "providerApiCalls": 0,
    }


def build_preview(*, plan_path: Path, output: Path,
                  style: str = "cartoon", language: str = "fr",
                  voice: str = "espeak", limit: int | None = None,
                  resolution: str = "720p", voice_name: str | None = None,
                  soundtrack: str = "none") -> dict:
    if voice not in {"espeak", "kokoro", "none"}:
        raise ValueError("Voice must be espeak, kokoro or none")
    if soundtrack not in {"none", "ambient"}:
        raise ValueError("Soundtrack must be none or ambient")
    plan_path = plan_path.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    art = create_local_art(plan_path, style=style, limit=limit)
    voice_file = None
    details = {"engine": "none", "wordAlignment": False}
    if voice in {"espeak", "kokoro"}:
        voice_file = output / "narration.wav"
        details = _narrate_scenes(plan_path, voice_file, language, limit,
                                  engine=voice, voice_name=voice_name)
    soundtrack_report = {"engine": "none", "externalApiCalls": 0}
    soundtrack_file = None
    if soundtrack == "ambient":
        from .soundtrack import create_bed
        soundtrack_file = output / "background-original.wav"
        soundtrack_report = create_bed(plan_path=plan_path,
                                       output=soundtrack_file, limit=limit)
    result = production.render(plan_path=plan_path, output=output,
                               audio=voice_file, limit=limit,
                               resolution=resolution, fps=24,
                               music=soundtrack_file)
    thumbs = output / "thumbnails"
    thumbs.mkdir(exist_ok=True)
    data = production.load_plan(plan_path)
    pictures = make_thumbnails(data["topic"], style, thumbs)
    summary = {
        "status": "draft", "publicationApproved": False, "factChecked": False,
        "reviewBeforePublication": True, "topic": data["topic"],
        "art": art, "voice": details, "soundtrack": soundtrack_report,
        "render": result,
        "thumbnails": [str(x) for x in pictures],
        "warnings": ["Original owl scenes have independent wing, body and blink motion; other characters/styles remain draft cards.",
                     "Narration is a provisional synthetic voice; review pronunciation and pacing.",
                     "Captions are aligned per scene, not word-by-word.",
                     "Factual and rights review required before YouTube publication."],
    }
    production._write_json(output / "episode-report.json", summary)
    return summary


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Build an original YouTube preview offline")
    p.add_argument("--plan", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--style", choices=["cartoon", "cinematic", "documentary"],
                   default="cartoon")
    p.add_argument("--language", choices=["fr", "en"], default="fr")
    p.add_argument("--voice", choices=["espeak", "kokoro", "none"], default="espeak")
    p.add_argument("--voice-name", help="Optional supported Kokoro voice ID")
    p.add_argument("--soundtrack", choices=["none", "ambient"], default="none",
                   help="Original local ambient backing track with narration ducking")
    p.add_argument("--resolution", choices=["720p", "1080p"], default="720p")
    p.add_argument("--limit", type=int)
    args = p.parse_args(argv)
    try:
        result = build_preview(plan_path=args.plan, output=args.output,
                               style=args.style, language=args.language,
                               voice=args.voice, voice_name=args.voice_name, resolution=args.resolution,
                               limit=args.limit)
        print(json.dumps({"video": result["render"]["video"],
                          "scenes": result["render"]["scenesRendered"],
                          "speech": result["voice"]["engine"],
                          "offline": True, "publicationApproved": False},
                         ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
