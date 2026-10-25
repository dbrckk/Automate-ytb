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
                    voice_name: str | None = None,
                    caption_timing: str = "estimated") -> dict:
    """Compose uncut speech with optional boundaries from synthesized phrases.

    In audio mode each visible subtitle phrase is synthesized separately, so
    its start time comes from the exact PCM we write. This is NOT ASR,
    phoneme alignment or verification of how words sound in the recording.
    Legacy estimated mode keeps its full-scene speech synthesis behavior.
    """
    from .captions import caption_phrases
    from .speech_pcm import compact_speech_pcm

    if caption_timing not in ("estimated", "audio"):
        raise ValueError("Caption timing must be estimated or audio")
    data = production.load_plan(plan_path)
    scenes = data["scenes"][:limit]
    if not scenes:
        raise ValueError("No scenes selected for narration")
    synth = SpeechEngine(engine=engine, language=language, voice=voice_name)
    durations_ms = [scene["endMs"] - scene["startMs"] for scene in data["scenes"]]
    complete_audio = []
    phrase_timings = []
    sample_rate = None
    phrase_count = 0
    total_trimmed_ms = 0.0
    trimmed_phrases = 0
    for index, scene in enumerate(scenes):
        phrases = (caption_phrases(scene["narration"])
                   if caption_timing == "audio" else [scene["narration"]])
        chunks = bytearray()
        starts = [0]
        for phrase_index, phrase in enumerate(phrases):
            frames, rate = synth.audio(phrase)
            if (not isinstance(rate, int) or not 8000 <= rate <= 96000
                    or not isinstance(frames, bytes) or not frames
                    or len(frames) % 2):
                raise RuntimeError("Invalid PCM scene audio")
            if sample_rate is None:
                sample_rate = rate
            if rate != sample_rate:
                raise RuntimeError("Invalid or mismatched PCM scene audio")
            if caption_timing == "audio":
                frames, cleanup = compact_speech_pcm(frames, rate)
                saved_ms = cleanup["leadingTrimMs"] + cleanup["trailingTrimMs"]
                total_trimmed_ms += saved_ms
                if saved_ms:
                    trimmed_phrases += 1
            if phrase_index:
                chunks.extend(b"\x00" * (2 * round(rate * 0.08)))
                start_ms = round(len(chunks) * 1000 / (2 * rate))
                if start_ms <= starts[-1]:
                    raise RuntimeError("Speech phrases are too short to timestamp")
                starts.append(start_ms)
            chunks.extend(frames)
        actual_samples = len(chunks) // 2
        min_ms = math.ceil(actual_samples * 1000 / sample_rate + 350)
        durations_ms[index] = max(durations_ms[index], min_ms)
        target_samples = math.ceil(durations_ms[index] * sample_rate / 1000)
        chunks.extend(b"\x00" * (2 * (target_samples - actual_samples)))
        complete_audio.append(bytes(chunks))
        phrase_timings.append((phrases, starts))
        phrase_count += len(phrases)

    total_ms = sum(durations_ms)
    if total_ms > 3_600_000:
        raise ValueError("Narration would exceed the one-hour scene-plan limit")
    offset = 0
    for i, (scene, duration_ms) in enumerate(zip(data["scenes"], durations_ms)):
        scene["startMs"] = offset
        offset += duration_ms
        scene["endMs"] = offset
        # Never retain stale audio-boundary metadata across re-renders.
        scene.pop("captionSegments", None)
        if i < len(scenes) and caption_timing == "audio":
            phrases, starts = phrase_timings[i]
            markers = starts + [duration_ms]
            if any(b <= a for a, b in zip(markers, markers[1:])):
                raise RuntimeError("Audio-derived subtitle boundaries are invalid")
            scene["captionSegments"] = [
                {"text": phrase, "startMs": scene["startMs"] + a,
                 "endMs": scene["startMs"] + b}
                for phrase, a, b in zip(phrases, markers, markers[1:])
            ]
    data["targetDurationSeconds"] = total_ms / 1000
    data["publicationApproved"] = False
    voice_path.parent.mkdir(parents=True, exist_ok=True)
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
        "sceneBoundaryTiming": "audio-derived",
        "captionTiming": ("audio-derived-synthesized-phrases"
                          if caption_timing == "audio" else "estimated"),
        "captionPhraseCount": phrase_count,
        "phraseSilenceCleanup": {
            "enabled": caption_timing == "audio",
            "method": "edge-silence-window-v1" if caption_timing == "audio" else "none",
            "trimmedPhrases": trimmed_phrases,
            "removedSilenceMs": round(total_trimmed_ms, 2),
            "innerPausesPreserved": True,
        },
        "wordAlignment": False,
        "audioSeconds": round(sum(len(audio) for audio in complete_audio)
                              / (2 * sample_rate), 3),
        "sampleRate": sample_rate, "providerApiCalls": 0,
    }

def build_preview(*, plan_path: Path, output: Path,
                  style: str = "cartoon", language: str = "fr",
                  voice: str = "espeak", limit: int | None = None,
                  resolution: str = "720p", voice_name: str | None = None,
                  soundtrack: str = "none",
                  caption_timing: str = "estimated") -> dict:
    if voice not in {"espeak", "kokoro", "none"}:
        raise ValueError("Voice must be espeak, kokoro or none")
    if soundtrack not in {"none", "ambient"}:
        raise ValueError("Soundtrack must be none or ambient")
    if caption_timing not in {"estimated", "audio"}:
        raise ValueError("Caption timing must be estimated or audio")
    plan_path = plan_path.resolve()
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    art = create_local_art(plan_path, style=style, limit=limit)
    voice_file = None
    details = {"engine": "none", "wordAlignment": False}
    if voice in {"espeak", "kokoro"}:
        voice_file = output / "narration.wav"
        details = _narrate_scenes(plan_path, voice_file, language, limit,
                                  engine=voice, voice_name=voice_name,
                                  caption_timing=caption_timing)
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
                               music=soundtrack_file,
                               caption_timing=("audio" if voice_file is not None
                                               else "estimated") if caption_timing == "audio"
                                              else "estimated")
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
                     "Caption boundaries follow actual synthesized phrases in audio mode; "
                     "they are not verified word-by-word.",
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
    p.add_argument("--caption-timing", choices=["estimated", "audio"],
                   default="estimated",
                   help="Audio mode measures synthesized phrase boundaries; not word alignment")
    p.add_argument("--resolution", choices=["720p", "1080p"], default="720p")
    p.add_argument("--limit", type=int)
    args = p.parse_args(argv)
    try:
        result = build_preview(plan_path=args.plan, output=args.output,
                               style=args.style, language=args.language,
                               voice=args.voice, voice_name=args.voice_name, resolution=args.resolution,
                               soundtrack=args.soundtrack, limit=args.limit,
                               caption_timing=args.caption_timing)
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
