"""Deterministic original stereo ambience with seamless loops and mood changes.

A procedural bed, not an orchestral soundtrack or production-ready score.
No external samples, downloaded models, paid API, or reuse of existing music.
"""
from __future__ import annotations

from array import array
from functools import lru_cache
import math
from pathlib import Path
import sys
import wave

from .production import load_plan

SAMPLERATE = 48000
CHANNELS = 2
LOOP_SECONDS = 8
MOOD_CROSSFADE_SECONDS = 0.85
VERSION = "ambient-original-v2-continuous-stereo"

CHORDS = {
    "warm": (130.81, 164.81, 196.0),
    "wonder": (146.83, 174.61, 220.0),
    "night": (110.0, 146.83, 164.81),
    "rain": (123.47, 155.56, 185.0),
}


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


@lru_cache(maxsize=4)
def _loop(theme: str) -> array:
    """Eight-second harmonic loop with phase-continuous period boundaries.

    Rounding each oscillator to an exact integer number of cycles per loop
    avoids a hard sample discontinuity without fading the music to silence
    every eight seconds. The soft per-note envelope remains periodic too.
    """
    if theme not in CHORDS:
        raise ValueError("Unknown original musical theme")
    chord = tuple(round(f * LOOP_SECONDS) / LOOP_SECONDS for f in CHORDS[theme])
    lower = round(CHORDS[theme][0] * LOOP_SECONDS / 2) / LOOP_SECONDS
    result = array("h")
    motif = (0, 1, 2, 1)
    for k in range(SAMPLERATE * LOOP_SECONDS):
        t = k / SAMPLERATE
        part = t % 2
        note = 2 * chord[motif[int(t / 2) % 4]]
        envelope = min(1.0, part / .14, max(0.0, (2.0-part) / .44))
        pad = sum(math.sin(math.tau*f*t + .15*j)
                  for j, f in enumerate(chord))
        pad += .30 * math.sin(math.tau * lower * t)
        motif_signal = math.sin(math.tau*note*t) * envelope * .23
        swell = .63 + .10 * math.sin(math.tau*t/LOOP_SECONDS)
        sample = (pad*.19 + motif_signal) * swell
        result.append(round(max(-1.0, min(1.0, sample)) * 12000))
    return result


def _smoothstep(value: float) -> float:
    v = min(1.0, max(0.0, value))
    return v*v*(3-2*v)


def create_bed(*, plan_path: Path, output: Path,
               limit: int | None = None) -> dict:
    data = load_plan(plan_path)
    if limit is not None and (
            not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0):
        raise ValueError("Scene limit must be a positive integer")
    selected = data["scenes"][:limit]
    if not selected:
        raise ValueError("No scenes to score")
    ms = selected[-1]["endMs"]
    if ms <= 0 or ms > 3_600_000:
        raise ValueError("Soundtrack duration must be within one hour")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    moods = [_theme(scene.get("direction")) for scene in selected]
    # Avoid rendering unrequested biomes: one-scene Android previews
    # should only pay CPU time for one active musical theme.
    loops = {name: _loop(name) for name in set(moods)}
    total_frames = round(ms * SAMPLERATE / 1000)
    loop_frames = LOOP_SECONDS * SAMPLERATE
    intro_frames = round(.25 * SAMPLERATE)
    outro_frames = round(.65 * SAMPLERATE)
    blend_frames = round(MOOD_CROSSFADE_SECONDS * SAMPLERATE)
    # Small side-to-side phase variation, without making a duplicate mono WAV.
    stereo_offset = round(.009 * SAMPLERATE)
    produced = 0
    transitions = 0

    with wave.open(str(output), "wb") as dst:
        dst.setnchannels(CHANNELS)
        dst.setsampwidth(2)
        dst.setframerate(SAMPLERATE)
        for idx, (scene, mood) in enumerate(zip(selected, moods)):
            end = min(total_frames, round(scene["endMs"] * SAMPLERATE / 1000))
            if end <= produced:
                raise ValueError("Invalid non-monotonic scene timing")
            previous_mood = moods[idx-1] if idx else mood
            change = previous_mood != mood
            if change:
                transitions += 1
            current = loops[mood]
            previous = loops[previous_mood]
            cursor = produced
            scene_start = produced
            while cursor < end:
                frames = min(8192, end-cursor)
                block = array("h")
                for j in range(frames):
                    frame = cursor+j
                    phase = frame % loop_frames
                    right_phase = (frame+stereo_offset) % loop_frames
                    weight = (_smoothstep((frame-scene_start)/blend_frames)
                              if change else 1.0)
                    # A changing mood fades between two continuous loops.
                    left = (previous[phase]*(1-weight) +
                            current[phase]*weight)
                    right = (previous[right_phase]*(1-weight) +
                             current[right_phase]*weight)
                    gain = min(1.0, frame/max(1,intro_frames),
                               max(0.0, (total_frames-1-frame)/max(1,outro_frames)))
                    block.append(round(left*gain))
                    block.append(round((.88*right + .12*left)*gain))
                if sys.byteorder != "little":
                    block.byteswap()
                dst.writeframesraw(block.tobytes())
                cursor += frames
            produced = end
    return {
        "file": str(output), "engine": VERSION,
        "source": "procedural-original",
        "durationSeconds": round(total_frames/SAMPLERATE, 3),
        "sampleRate": SAMPLERATE, "channels": CHANNELS,
        "loopSeconds": LOOP_SECONDS, "seamlessHarmonicLoop": True,
        "moodCrossfadeSeconds": MOOD_CROSSFADE_SECONDS,
        "moodTransitions": transitions, "sceneThemes": moods,
        "containsThirdPartyMusic": False, "externalApiCalls": 0,
        "providerCostUsd": "0",
        "note": "Continuous synthetic stereo ambience; still requires human listening review.",
    }
