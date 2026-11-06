"""Reusable, opt-in neural voice master for original TikTok/YouTube Shorts.

This job never substitutes eSpeak, publishes, or claims visual-voice sync.
It emits measured sentence/beat timestamps for an independent editor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import wave

from .narration import SpeechEngine, VOICE_CHOICES
from .voice_pacing import speaking_speed

SAMPLE_RATE = 24000


def synthesize(*, script_path: Path, destination: Path,
               language: str = "en", voice: str | None = None,
               style: str = "natural") -> dict:
    if language not in VOICE_CHOICES:
        raise ValueError("Only English and French are supported")
    if voice and voice not in VOICE_CHOICES[language]:
        raise ValueError("Voice ID is invalid for the selected language")
    speed = speaking_speed(style=style)
    lines = script_path.read_text(encoding="utf-8").splitlines()
    beats = [s.strip() for s in lines if s.strip()]
    if not 2 <= len(beats) <= 12 or sum(map(len, beats)) > 1800:
        raise ValueError("Provide 2–12 short lines with at most 1800 characters total")
    if any(len(text) > 350 or any(ord(c) < 32 for c in text)
           for text in beats):
        raise ValueError("Narration beat exceeds 350 characters or has control characters")

    engine = SpeechEngine(engine="kokoro", language=language, voice=voice)
    engine.speed = speed
    # Segment timing comes from actual generated PCM, never a word count guess.
    silence_before = int(.17 * SAMPLE_RATE)
    between = int(.17 * SAMPLE_RATE)
    after = int(.4 * SAMPLE_RATE)
    pcm = bytearray(b"\0\0" * silence_before)
    timestamps = []
    for index, phrase in enumerate(beats):
        start = round(len(pcm) / 2 / SAMPLE_RATE * 1000)
        frames, rate = engine.audio(phrase)
        if rate != SAMPLE_RATE or len(frames) == 0 or len(frames) % 2:
            raise RuntimeError("Kokoro returned invalid 24kHz/16-bit mono PCM")
        pcm.extend(frames)
        end = round(len(pcm) / 2 / SAMPLE_RATE * 1000)
        timestamps.append({"index": index + 1, "text": phrase,
                           "startMs": start, "endMs": end,
                           "speechDurationMs": end - start})
        pcm.extend(b"\0\0" * between)
    pcm.extend(b"\0\0" * after)
    duration = len(pcm) / 2 / SAMPLE_RATE
    if not math.isfinite(duration) or not 8 <= duration <= 90:
        raise ValueError("Synthesized speech is outside the 8–90 second short-video window")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kokoro-voice-", dir=destination.parent) as td:
        tmp = Path(td) / "narration.wav"
        with wave.open(str(tmp), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(SAMPLE_RATE)
            output.writeframes(pcm)
        sha = hashlib.sha256(tmp.read_bytes()).hexdigest()
        report = {
            "engine": "kokoro-natural",
            "voice": engine.voice,
            "language": language,
            "style": style,
            "sampleRate": SAMPLE_RATE,
            "channels": 1,
            "durationSeconds": round(duration, 3),
            "beats": timestamps,
            "sha256": sha,
            "publicationApproved": False,
            "requiresListeningReview": True,
        }
        report_file = tmp.with_suffix(".json")
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
        tmp.replace(destination)
        report_file.replace(destination.with_suffix(".json"))
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate real Kokoro narration and PCM beat times")
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--language", choices=["fr", "en"], default="en")
    p.add_argument("--voice")
    p.add_argument("--style", choices=["natural", "gentle", "lively", "expressive"],
                   default="natural")
    args = p.parse_args(argv)
    try:
        print(json.dumps(synthesize(script_path=args.script, destination=args.output,
                                    language=args.language, voice=args.voice,
                                    style=args.style), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
