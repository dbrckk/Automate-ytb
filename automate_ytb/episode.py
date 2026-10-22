"""One-command, no-API-cost video preview from an original scene plan.

Offline scenes use generated graphic cards and the existing FFmpeg renderer.
This does NOT produce AI illustrations, factual research or final publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import wave

from . import production
from .studio import make_thumbnails, render_art, synthesize_voice


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
    for i, scene in enumerate(scenes, start=1):
        state = already.get(scene["id"])
        if state == "ready":
            reused += 1
            continue
        if state in ("unreviewed", "changed"):
            raise ValueError(f"Scene {scene['id']} has modified or unreviewed assets; "
                             "explicitly resolve these before re-generating")
        with tempfile.TemporaryDirectory(prefix="automate-ytb-art-") as folder:
            image = Path(folder) / "original-graphic.png"
            render_art(data["topic"], scene["narration"], i, len(data["scenes"]),
                       style, image)
            production.ingest(
                plan_path=plan_path, scene_id=scene["id"], image_path=image,
                provider="automate-local-graphics", rights_note=LOCAL_RIGHTS,
                cost_usd="0", rights_confirmed=True,
            )
        rendered += 1
    return {"mode": "offline-graphics", "created": rendered, "reused": reused,
            "apiCalls": 0, "providerCostUsd": "0.0000"}


def _narrate_scenes(plan_path: Path, voice_path: Path, language: str,
                    limit: int | None) -> dict:
    if language not in {"fr", "en"}:
        raise ValueError("Only fr/en eSpeak drafts are supported")
    data = production.load_plan(plan_path)
    scenes = data["scenes"][:limit]
    voice_path.parent.mkdir(parents=True, exist_ok=True)
    source_duration = [(s["endMs"] - s["startMs"]) / 1000.0
                       for s in data["scenes"]]
    units = []
    with tempfile.TemporaryDirectory(prefix="automate-ytb-tts-") as temp:
        for idx, scene in enumerate(scenes):
            path = Path(temp) / f"voice-{idx:04d}.wav"
            if not synthesize_voice(scene["narration"], path, language):
                raise RuntimeError("eSpeak speech engine is unavailable")
            with wave.open(str(path), "rb") as audio:
                params = audio.getparams()
                frames = audio.readframes(audio.getnframes())
            if params.nchannels != 1 or params.sampwidth != 2 or params.comptype != "NONE":
                raise RuntimeError("Unsupported eSpeak PCM output format")
            units.append((frames, params.framerate))
    if not units:
        raise ValueError("There are no scenes to narrate")
    samplerate = units[0][1]
    if any(rate != samplerate for _, rate in units):
        raise RuntimeError("Mixed eSpeak output sample rates")
    # Never clip narration. Longer-than-planned speech expands the affected
    # scene and shifts subsequent timecodes for scene-level caption accuracy.
    new_duration = source_duration[:]
    narration_frames = []
    for idx, (frames, _) in enumerate(units):
        actual_frames = len(frames) // 2
        minimum = actual_frames + int(samplerate * 0.35)
        desired = max(round(source_duration[idx] * samplerate), minimum)
        new_duration[idx] = desired / samplerate
        narration_frames.append(frames + b"\x00" * ((desired - actual_frames) * 2))
    cumulative = 0
    for i, scene in enumerate(data["scenes"]):
        scene["startMs"] = round(cumulative * 1000)
        cumulative += new_duration[i]
        scene["endMs"] = round(cumulative * 1000)
    if cumulative > 3600:
        raise ValueError("Narration would exceed one hour; shorten the script")
    data["targetDurationSeconds"] = round(cumulative, 3)
    data["publicationApproved"] = False
    with wave.open(str(voice_path), "wb") as combined:
        combined.setnchannels(1)
        combined.setsampwidth(2)
        combined.setframerate(samplerate)
        for frames in narration_frames:
            combined.writeframes(frames)
    # Adjust scene timecodes only after the voice was rendered successfully.
    # Timecodes must remain contiguous in integer milliseconds.
    last = 0
    for scene in data["scenes"]:
        scene["startMs"] = last
        last = scene["endMs"]
    data["targetDurationSeconds"] = last / 1000
    production._write_json(plan_path.resolve(), data)
    return {"voice": str(voice_path), "engine": "espeak-draft",
            "sceneBoundaryTiming": "audio-derived", "wordAlignment": False,
            "audioSeconds": round(sum(new_duration[:len(scenes)]), 3)}


def build_preview(*, plan_path: Path, output: Path,
                  style: str = "cartoon", language: str = "fr",
                  voice: str = "espeak", limit: int | None = None,
                  resolution: str = "720p") -> dict:
    if voice not in {"espeak", "none"}:
        raise ValueError("Voice must be espeak or none")
    plan_path = plan_path.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    art = create_local_art(plan_path, style=style, limit=limit)
    voice_file = None
    details = {"engine": "none", "wordAlignment": False}
    if voice == "espeak":
        voice_file = output / "narration.wav"
        details = _narrate_scenes(plan_path, voice_file, language, limit)
    result = production.render(plan_path=plan_path, output=output,
                               audio=voice_file, limit=limit,
                               resolution=resolution, fps=24)
    thumbs = output / "thumbnails"
    thumbs.mkdir(exist_ok=True)
    data = production.load_plan(plan_path)
    pictures = make_thumbnails(data["topic"], style, thumbs)
    summary = {
        "status": "draft", "publicationApproved": False, "factChecked": False,
        "reviewBeforePublication": True, "topic": data["topic"],
        "art": art, "voice": details, "render": result,
        "thumbnails": [str(x) for x in pictures],
        "warnings": ["Graphic illustrations are procedural draft cards, not AI images.",
                     "Narration uses the basic eSpeak voice, not natural professional TTS.",
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
    p.add_argument("--voice", choices=["espeak", "none"], default="espeak")
    p.add_argument("--resolution", choices=["720p", "1080p"], default="720p")
    p.add_argument("--limit", type=int)
    args = p.parse_args(argv)
    try:
        result = build_preview(plan_path=args.plan, output=args.output,
                               style=args.style, language=args.language,
                               voice=args.voice, resolution=args.resolution,
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
