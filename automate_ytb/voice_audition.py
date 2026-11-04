"""Free, local A/B listening samples for available Kokoro English voices.

These are short *different speaker* renditions of the exact authored opening;
they are not automatically ranked by a subjective algorithm. Runs only when
explicitly invoked, after the normal render, on a runner with Kokoro installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import wave

from .narration import SpeechEngine
from .voice_pacing import speaking_speed

CANDIDATES = ("af_heart", "af_bella", "af_nicole", "am_michael")


def listening_excerpt(script: str, *, max_characters: int = 240) -> str:
    """Select a complete authored sentence where possible, never fabricate one."""
    if not isinstance(script, str) or not script.strip():
        raise ValueError("An original nonempty script is required")
    flat = " ".join(script.split())
    if not 1 <= max_characters <= 1000:
        raise ValueError("Invalid audition excerpt limit")
    sentence = re.split(r"(?<=[.!?])\s+", flat, maxsplit=1)[0]
    if len(sentence) <= max_characters:
        return sentence
    # Avoid cutting a word. Do not add synthetic punctuation or factual text.
    words = sentence.split()
    chosen = []
    for word in words:
        if len(" ".join(chosen + [word])) > max_characters:
            break
        chosen.append(word)
    if not chosen:
        raise ValueError("First script token is too long for voice audition")
    return " ".join(chosen)


def generate(*, script: str, output: Path, style: str = "natural") -> dict:
    """Produce real MP3 files with auditable sample text and exact voice IDs."""
    rate = speaking_speed(style=style)
    excerpt = listening_excerpt(script)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    engine = SpeechEngine(engine="kokoro", language="en", voice=CANDIDATES[0])
    engine.speed = rate
    samples = []
    for voice in CANDIDATES:
        engine.voice = voice
        pcm, sample_rate = engine.audio(excerpt)
        if not pcm or len(pcm) % 2 or not 8000 <= sample_rate <= 96000:
            raise RuntimeError("Kokoro audition returned invalid PCM")
        wav_path = output / (voice + ".wav")
        mp3_path = output / (voice + ".mp3")
        try:
            with wave.open(str(wav_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(pcm)
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "160k",
                str(mp3_path),
            ], check=True)
            if not mp3_path.is_file() or mp3_path.stat().st_size == 0:
                raise RuntimeError("Voice audition encoder returned an empty MP3")
        finally:
            wav_path.unlink(missing_ok=True)
        samples.append({
            "voiceId": voice, "file": mp3_path.name,
            "durationSeconds": round(len(pcm) / (2 * sample_rate), 3),
            "sampleRate": sample_rate,
            "sha256": hashlib.sha256(mp3_path.read_bytes()).hexdigest(),
        })
    report = {
        "schemaVersion": 1,
        "method": "same-author-script-kokoro-speaker-comparison-v1",
        "language": "en",
        "style": style,
        "excerpt": excerpt,
        "excerptSha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        "samples": samples,
        "requiresHumanListening": True,
        "bestVoiceAutomaticallySelected": False,
        "paidApiCalls": 0,
        "publicationApproved": False,
    }
    (output / "audition-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A/B compare real Kokoro English voice samples")
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--style", default="natural",
                        choices=("natural", "gentle", "lively", "expressive"))
    args = parser.parse_args(argv)
    report = generate(
        script=args.script.read_text(encoding="utf-8"),
        output=args.output, style=args.style)
    print(json.dumps({"voices": [s["voiceId"] for s in report["samples"]],
                      "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
