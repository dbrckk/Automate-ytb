"""Deterministic original continuous narrative score for short-form films.

The composition follows one global musical clock rather than restarting at
scene boundaries. Optional accents are tied to validated MasterTimeline visual
events. All PCM is synthesized locally in bounded blocks, with no samples,
downloaded music, remote service or third-party composition.
"""
from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
import wave

from .production import load_plan

VERSION = "score-original-continuous-v1"
RATE = 48000
BLOCK = 4096
TAU = math.tau
MODES = {"discreet": (78, .60), "documentary": (88, .80),
         "mysterious": (76, .75), "energetic": (108, 1.)}
# Original minor-pentatonic material with simple, explicitly authored voicings.
HARMONY = ((0, 3, 7), (5, 8, 12), (3, 7, 10), (7, 10, 14))
SCALE = (0, 3, 5, 7, 10, 12, 15)
MOTIF = (0, 2, 4, 3, 1, 5, 3, 2, 4, 6, 2, 1, 5, 3, 0, 2)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _interpolate(time: float, marks: tuple[tuple[float, float], ...]) -> float:
    for (a, level_a), (b, level_b) in zip(marks, marks[1:]):
        if time <= b:
            x = min(1., max(0., (time - a) / max(1.e-9, b - a)))
            x = x*x*(3.-2.*x)
            return level_a + (level_b - level_a)*x
    return marks[-1][1]


def create_score(*, plan_path: Path, output: Path,
                 mode: str = "documentary") -> dict:
    """Write 12–180 s 48kHz stereo PCM scored to the measured scene timeline.

    Visual cues are consumed only from explicitly authored MasterTimeline, never
    from guessed spoken-word timings. The resulting stem remains compatible with
    the legacy FFmpeg sidechain and Foley final AAC mixer.
    """
    if mode not in MODES:
        raise ValueError("Unsupported original score mode")
    plan = load_plan(plan_path)
    duration = plan["targetDurationSeconds"]
    if type(duration) not in (int, float) or not 12 <= duration <= 180:
        raise ValueError("Continuous score requires a 12–180-second full episode")
    samples = round(duration * RATE)
    if not 1 <= len(plan["scenes"]) <= 1200:
        raise ValueError("Invalid narrative score scene count")
    if (plan["scenes"][0]["startMs"] != 0 or
            abs(plan["scenes"][-1]["endMs"] / 1000 - duration) > .001):
        raise ValueError("Narrative score must follow complete scene timings")
    events = []
    if plan.get("masterTimeline") is not None:
        from .master_timeline_adapter import compile_authored_science_timeline
        authored = compile_authored_science_timeline(plan, fps=30)
        if authored is None:
            raise ValueError("Cannot compile authored music events")
        events = authored.timeline.audio_events()
        if any(e["atSample"] >= samples for e in events):
            raise ValueError("Score cue lies outside measured PCM duration")
    # A stable score signature, with one key and tempo selected for the whole
    # episode. It does not change with a scene transition or language.
    seed = int.from_bytes(hashlib.sha256(
        plan["topic"].encode("utf-8")).digest()[:8], "big")
    root_hz = (110., 123.47, 130.81, 146.83, 164.81)[seed % 5]
    bpm, mode_gain = MODES[mode]
    beat_seconds = 60. / bpm
    accent_events = [e for e in events if e["family"] in {
        "reveal", "growth", "scale-transition", "electrical"}]
    # An authored reveal is the dramatic pivot; without one the arc is a
    # disclosed global score heuristic, not an alleged word-level alignment.
    reveals = [e for e in accent_events if e["family"] == "reveal"]
    pivot = (reveals[0]["atSample"] / samples if reveals else .77)
    pivot = min(.88, max(.45, pivot))
    marks = ((0., .18), (.20, .36), (.51, .64),
             (max(.52, pivot-.075), .28), (pivot, .88),
             (min(.97, pivot+.11), .65), (1., .08))
    # Use a crossfade between chord voicings, rather than slicing the pad.
    # Each stereo channel gets a slightly different detuned oscillator.
    chord_frequencies = [
        [root_hz * 2. ** (semitone / 12) for semitone in triad]
        for triad in HARMONY
    ]
    motif_shift = seed % len(SCALE)
    note_frequencies = [
        root_hz * 2. ** (SCALE[(i + motif_shift) % len(SCALE)] / 12 + 1)
        for i in MOTIF
    ]
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    max_sample = 0
    # Report only real authored cues; inferred dramaturgical pivot is separate.
    cue_report = [{"id": e["id"], "sourceEventId": e["sourceEventId"],
                   "family": e["family"], "atSample": e["atSample"],
                   "atFrame": e["atFrame"]} for e in accent_events]
    with wave.open(str(output), "wb") as dest:
        dest.setnchannels(2)
        dest.setsampwidth(2)
        dest.setframerate(RATE)
        for first in range(0, samples, BLOCK):
            block = array("h")
            for index in range(first, min(samples, first + BLOCK)):
                t = index / RATE
                phase = t / beat_seconds
                beat_index = int(phase)
                local_beat = (phase - beat_index) * beat_seconds
                bar_index = beat_index // 4
                chord_index = (bar_index + seed % 4) % len(HARMONY)
                previous = chord_frequencies[(chord_index-1) % 4]
                current = chord_frequencies[chord_index]
                chord_fade = min(1., max(0., (beat_index % 4
                                             + local_beat / beat_seconds)
                                           * beat_seconds / .32))
                progress = index / max(1, samples - 1)
                density = _interpolate(progress, marks)
                # Equal musical time independent of scene boundaries.
                note = note_frequencies[(beat_index + bar_index//4) % len(MOTIF)]
                pluck = (math.sin(TAU * note * t) +
                         .28 * math.sin(TAU * note * 2 * t)) * (
                    min(1., local_beat / .012) *
                    math.exp(-3.4 * local_beat / beat_seconds))
                bass_freq = current[0] / 2
                bass = (math.sin(TAU * bass_freq * t) *
                        (.68 + .32 * math.cos(TAU * 2 * local_beat /
                                              beat_seconds)) *
                        min(1., local_beat / .025))
                pulse = (math.sin(TAU * 66 * local_beat) *
                         math.exp(-29 * local_beat) *
                         min(1., local_beat / .006))
                score_accent = 0.
                for event in accent_events:
                    elapsed = (index - event["atSample"]) / RATE
                    if 0. <= elapsed <= .5:
                        score_accent += (math.sin(TAU * (117 - 90*elapsed) *
                                                  elapsed) *
                                         math.exp(-9*elapsed) *
                                         min(1., elapsed/.01))
                attack = min(1., t / .9)
                release = min(1., (duration-t) / 1.25)
                envelope = max(0., min(attack, release))
                for channel in (0, 1):
                    spread = 1 + (.0019 if channel else -.0019)
                    # Pad never restarts at scene transitions.
                    pad = sum(
                        math.sin(TAU * freq * spread * t + j*.19)
                        for j, freq in enumerate(current)
                    ) * chord_fade
                    if chord_fade < 1:
                        pad += (1 - chord_fade) * sum(
                            math.sin(TAU * freq * spread * t + j*.19)
                            for j, freq in enumerate(previous)
                        )
                    pad /= 3.
                    signal = mode_gain * envelope * (
                        pad * (.12 + .11*density) +
                        bass * (.055 + .04*density) +
                        pluck * (.022 + .07*density) +
                        pulse * (.012 + .025*density) +
                        score_accent * .027
                    )
                    pcm = round(max(-.92, min(.92, signal)) * 32767)
                    max_sample = max(max_sample, abs(pcm))
                    block.append(pcm)
            if sys.byteorder != "little":
                block.byteswap()
            dest.writeframesraw(block.tobytes())
    report = {
        "engine": VERSION, "source": "procedural-original-no-samples",
        "file": str(output), "mode": mode, "tempoBpm": bpm,
        "durationSeconds": samples/RATE, "sceneCount": len(plan["scenes"]),
        "sampleRateHz": RATE, "channels": 2,
        "continuousGlobalClock": True, "sceneBoundaryResets": 0,
        "originalComposition": True, "containsThirdPartyMusic": False,
        "externalApiCalls": 0, "providerCostUsd": "0",
        "audiblePeakSampleDbfs": (round(20*math.log10(max_sample / 32767), 2)
                                 if max_sample else -120.),
        "musicArc": {"pivotFraction": round(pivot, 4),
                     "pivotSource": ("authored-visual-reveal" if reveals
                                     else "global-narrative-heuristic")},
        "authoredEventAccents": cue_report,
        "wavSha256": _sha(output),
        "humanReviewed": False, "publicationApproved": False,
    }
    (output.parent / "score-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return report
