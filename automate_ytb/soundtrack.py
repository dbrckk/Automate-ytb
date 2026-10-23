"""Original, license-independent ambient audio beds for YouTube previews.

All samples are created mathematically from scratch. No sample packs, copyrighted
melodies, internet requests, downloaded weights, or subscription services are used.
"""
from __future__ import annotations

from array import array
import hashlib
import math
from pathlib import Path
import sys
import wave

from .production import load_plan

SAMPLERATE = 16000
LOOP_SECONDS = 8
# Simple non-referential chord colors; not copies of recorded audio.
CHORDS = {
    "warm": (130.81, 164.81, 196.0),
    "wonder": (146.83, 174.61, 220.0),
    "night": (110.0, 146.83, 164.81),
    "rain": (123.47, 155.56, 185.0),
}
VERSION = "ambient-original-v1"


def _theme(direction: dict | None) -> str:
    direction = direction or {}
    weather = str(direction.get("weather", "")).lower()
    emotion = str(direction.get("emotion", "")).lower()
    if weather in ("rain", "storm"):
        return "rain"
    if weather == "night" or emotion == "worried":
        return "night"
    if emotion in ("curious", "surprised"):
        return "wonder"
    return "warm"


def _loop(theme: str) -> array:
    """A soft synthesized pad with subtle original arpeggio; fades every 8 s.

    The fade protects the repeated loop from clicks without any processing API.
    """
    chord = CHORDS[theme]
    samples = array("h")
    n = SAMPLERATE * LOOP_SECONDS
    motif = (0, 1, 2, 1)
    for k in range(n):
        t = k / SAMPLERATE
        seconds_in_note = t % 2
        note = chord[motif[int(t / 2) % 4]] * 2
        attack = min(1.0, seconds_in_note / 0.14)
        release = min(1.0, (2.0 - seconds_in_note) / 0.44)
        # Warm fundamental + airy fifth; envelope swells slowly.
        pad = sum(math.sin(math.tau * f * t + 0.15 * j) for j, f in enumerate(chord))
        pad += .30 * math.sin(math.tau * chord[0] / 2 * t)
        pluck = math.sin(math.tau * note * t) * max(0.0, attack * release) * .23
        swell = .63 + .10 * math.sin(math.tau * t / 8)
        # The loop smoothly approaches zero at each boundary.
        seam = min(1., t / .17, (LOOP_SECONDS - t) / .17)
        output = max(-1., min(1., (pad * .19 + pluck) * swell * seam))
        samples.append(int(output * 12000))
    return samples


def create_bed(*, plan_path: Path, output: Path,
               limit: int | None = None) -> dict:
    data = load_plan(plan_path)
    if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0):
        raise ValueError("Scene limit must be a positive integer")
    selected = data["scenes"][:limit]
    if not selected:
        raise ValueError("No scenes to score")
    ms = selected[-1]["endMs"]
    if ms <= 0 or ms > 3_600_000:
        raise ValueError("Soundtrack duration must be within one hour")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    loops = {name: _loop(name) for name in CHORDS}
    scene_moods = [_theme(s.get("direction")) for s in selected]
    target_samples = round(ms * SAMPLERATE / 1000)
    produced = 0
    fade_frames = int(SAMPLERATE * .22)
    with wave.open(str(output), "wb") as dst:
        dst.setnchannels(1)
        dst.setsampwidth(2)
        dst.setframerate(SAMPLERATE)
        for scene, mood in zip(selected, scene_moods):
            end = min(target_samples, round(scene["endMs"] * SAMPLERATE / 1000))
            count = end - produced
            if count <= 0:
                raise ValueError("Invalid non-monotonic scene timing")
            src = loops[mood]
            loop_length = len(src)
            cursor = 0
            while cursor < count:
                block_count = min(8192, count - cursor)
                block = array("h")
                for j in range(block_count):
                    frame = cursor + j
                    # A deterministic, click-free short fade between authored
                    # scenes and at the very beginning/end of each episode.
                    envelope = min(
                        1.0, frame / fade_frames,
                        max(0.0, (count - 1 - frame) / fade_frames))
                    block.append(round(src[frame % loop_length] * envelope))
                if sys.byteorder != "little":
                    block.byteswap()
                dst.writeframesraw(block.tobytes())
                cursor += block_count
            produced = end
    return {
        "file": str(output), "engine": VERSION, "source": "procedural-original",
        "durationSeconds": round(target_samples / SAMPLERATE, 3),
        "sampleRate": SAMPLERATE, "sceneThemes": scene_moods,
        "containsThirdPartyMusic": False, "externalApiCalls": 0,
        "providerCostUsd": "0",
        "note": "Synthetic ambient draft with scene cross-fades to silence; verify musical suitability.",
    }
