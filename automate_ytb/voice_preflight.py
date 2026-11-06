"""Measure Kokoro speech *before* optional expensive Blender rendering.

The exact synthesized WAV, adjusted scene plan, caption phrase markers and
strict pacing result are cached by SHA-256. Downstream reuses the identical
audio and plan, rather than re-synthesizing speech with potentially different
timings after rendering 3D assets.

This helper does not access a paid API, trim spoken words, invent text or
approve publication. It remains opt-in for the CPU Blender Shorts workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import wave

from . import production
from .narration_pacing import inspect as inspect_pacing


SCHEMA_VERSION = 1
MAX_WAV_BYTES = 250_000_000


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _voice_timeline_sha(path: Path) -> str:
    """Hash only author text, PCM boundaries and caption phrases.

    Art generation and production.prepare may legitimately add provenance,
    render statuses, images or prompts to the storyboard. Those changes
    must never invalidate *audio* evidence. Editing speech or timestamps
    must still fail closed.
    """
    plan = production.load_plan(path)
    rows = [
        {
            "id": scene["id"],
            "narration": scene["narration"],
            "startMs": scene["startMs"],
            "endMs": scene["endMs"],
            "captionSegments": scene.get("captionSegments"),
        }
        for scene in plan["scenes"]
    ]
    payload = {
        "topic": plan["topic"],
        "targetDurationSeconds": plan["targetDurationSeconds"],
        "sourceScriptSha256": plan.get("sourceScriptSha256"),
        "scenes": rows,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _measured_wav_ms(path: Path) -> int:
    if not path.is_file() or not 2048 <= path.stat().st_size <= MAX_WAV_BYTES:
        raise ValueError("Preflight narration WAV is missing or outside bounds")
    try:
        with wave.open(str(path), "rb") as f:
            if (f.getnchannels() != 1 or f.getsampwidth() != 2 or
                    f.getcomptype() != "NONE" or
                    not 8000 <= f.getframerate() <= 96000 or
                    f.getnframes() < f.getframerate()):
                raise ValueError("Preflight narration WAV must be nonempty mono PCM16")
            return round(f.getnframes() * 1000 / f.getframerate())
    except (wave.Error, EOFError) as error:
        raise ValueError("Preflight narration WAV could not be decoded") from error


def prepare(*, plan: Path, output_dir: Path, language: str,
            voice_style: str = "natural", voice_name: str | None = None) -> dict:
    """Create an immutable, exact-speech preflight bundle before rendering 3D.

    The caller's original plan is never modified, including when strict
    pacing fails. Failed preflights still emit a measured diagnostics file.
    """
    from .episode import _narrate_scenes

    if language not in ("en", "fr"):
        raise ValueError("Speech preflight language must be en or fr")
    from .voice_pacing import speaking_speed
    speaking_speed(style=voice_style)
    if voice_name == "auto":
        voice_name = None
    original = production.load_plan(Path(plan))
    original_ms = round(original["targetDurationSeconds"] * 1000)
    if not 30000 <= original_ms <= 3600000:
        raise ValueError("Unsupported original narration duration")
    output_dir = Path(output_dir).resolve()
    source = Path(plan).resolve()
    if source.parent == output_dir or source == output_dir / "plan.json":
        raise ValueError("Preflight directory must differ from source plan")
    output_dir.mkdir(parents=True, exist_ok=True)
    adjusted = output_dir / "plan.json"
    audio = output_dir / "narration.wav"
    manifest = output_dir / "manifest.json"
    # No stale success marker may survive a changed script or failed audio.
    manifest.unlink(missing_ok=True)
    adjusted.write_bytes(source.read_bytes())
    voice = _narrate_scenes(
        adjusted, audio, language, None, engine="kokoro",
        voice_name=voice_name, caption_timing="audio",
        narration_style=voice_style,
    )
    pacing = inspect_pacing(
        voice["measuredScenePacing"], strict=True,
        requested_duration_ms=original_ms,
    )
    production._write_json(output_dir / "narration-pacing.json", pacing)
    if pacing["status"] != "passed":
        raise ValueError(
            "Real speech does not fit the authored duration: "
            + "; ".join(pacing["errors"])
            + ". Inspect the PCM diagnostics before starting Blender."
        )
    wav_ms = _measured_wav_ms(audio)
    if abs(wav_ms - pacing["totalSceneDurationMs"]) > 3:
        raise ValueError("WAV sample duration differs from measured scene timing")
    updated = production.load_plan(adjusted)
    if abs(updated["scenes"][-1]["endMs"] - wav_ms) > 3:
        raise ValueError("Prepared scene plan does not match measured narration")
    metadata = {
        "schemaVersion": SCHEMA_VERSION,
        "status": "passed",
        "engine": "kokoro-natural",
        "voiceStyle": voice_style,
        "voiceName": voice_name,
        "language": language,
        "originalRequestedDurationMs": original_ms,
        "originalPlanSha256": _sha(source),
        "preparedPlanSha256": _sha(adjusted),
        "preparedVoiceTimelineSha256": _voice_timeline_sha(adjusted),
        "narrationSha256": _sha(audio),
        "pacingSha256": _sha(output_dir / "narration-pacing.json"),
        "speechDurationMs": wav_ms,
        "voice": voice,
        "publicationApproved": False,
        "humanListeningRequired": True,
    }
    production._write_json(manifest, metadata)
    return metadata


def consume(*, manifest: Path, plan: Path, language: str,
            voice_style: str, voice_name: str | None = None) -> tuple[dict, int, Path]:
    """Verify the full prepared bundle before reusing its WAV without TTS.

    Must fail closed if anyone edits the prepared scene text, PCM, language,
    voice, or measured pacing between synthesis and final encoding.
    """
    manifest = Path(manifest).resolve()
    if manifest.name != "manifest.json":
        raise ValueError("Expected voice-preflight manifest.json")
    if voice_name == "auto":
        voice_name = None
    if not manifest.is_file() or not 1 <= manifest.stat().st_size <= 1_000_000:
        raise ValueError("Speech preflight manifest missing or too large")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Corrupt voice-preflight manifest") from exc
    if (not isinstance(data, dict) or data.get("schemaVersion") != SCHEMA_VERSION
            or data.get("status") != "passed" or
            data.get("publicationApproved") is not False or
            data.get("engine") != "kokoro-natural" or
            data.get("language") != language or
            data.get("voiceStyle") != voice_style or
            data.get("voiceName") != voice_name):
        raise ValueError("Precomputed narration does not match the requested voice")
    directory = manifest.parent
    adjusted = Path(plan).resolve()
    audio = directory / "narration.wav"
    diagnostic = directory / "narration-pacing.json"
    if (not adjusted.is_file() or not diagnostic.is_file() or
            _voice_timeline_sha(adjusted) != data.get("preparedVoiceTimelineSha256") or
            _sha(audio) != data.get("narrationSha256") or
            _sha(diagnostic) != data.get("pacingSha256")):
        raise ValueError("Preflight WAV, plan or diagnostics changed after synthesis")
    pacing = json.loads(diagnostic.read_text(encoding="utf-8"))
    expected = data.get("originalRequestedDurationMs")
    if type(expected) is not int or not 30000 <= expected <= 3600000:
        raise ValueError("Invalid original scene duration claim")
    voice = data.get("voice")
    if not isinstance(voice, dict) or voice.get("engine") != "kokoro-natural":
        raise ValueError("Preflight voice details missing")
    measured = inspect_pacing(
        voice["measuredScenePacing"], strict=True,
        requested_duration_ms=expected,
    )
    if measured["status"] != "passed" or measured != pacing:
        raise ValueError("Preflight audio measurements failed revalidation")
    length = _measured_wav_ms(audio)
    if (length != data.get("speechDurationMs") or
            abs(length - measured["totalSceneDurationMs"]) > 3):
        raise ValueError("Prepared WAV duration does not match scene timing")
    scenes = production.load_plan(adjusted)["scenes"]
    if len(scenes) != len(voice["measuredScenePacing"]):
        raise ValueError("Prepared narration scene count differs from script")
    if (any(row["sceneId"] != scene["id"] or
            row["sceneDurationMs"] != scene["endMs"] - scene["startMs"]
            for row, scene in zip(voice["measuredScenePacing"], scenes)) or
            abs(scenes[-1]["endMs"] - length) > 3):
        raise ValueError("Prepared narration does not match scene boundaries")
    return voice, expected, audio


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Gate actual Kokoro PCM before slow Blender 3D")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--language", choices=("en", "fr"), default="en")
    parser.add_argument("--voice-style", choices=("natural", "gentle", "lively", "expressive"),
                        default="natural")
    parser.add_argument("--voice-name")
    args = parser.parse_args(argv)
    try:
        result = prepare(plan=args.plan, output_dir=args.output_dir,
                         language=args.language, voice_style=args.voice_style,
                         voice_name=args.voice_name)
        print(json.dumps({
            "status": result["status"],
            "speechDurationMs": result["speechDurationMs"],
            "originalRequestedDurationMs": result["originalRequestedDurationMs"],
            "voiceReusedAfterBlender": True,
        }))
        return 0
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
