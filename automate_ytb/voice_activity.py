"""Conservative voice-activity mouth cues from the *actual* preview WAV.

This is amplitude-gated stylized mouth movement, NEVER phoneme alignment.
A voice-over should animate only scenes with an explicitly written talk
action. Unsupported audio formats keep the original rhythmic mouth pose.
"""
from __future__ import annotations

from array import array
from pathlib import Path
import sys
import wave

MOUTH_VERSION = "pcm-voice-activity-v1"
MAX_GATES = 80
WINDOW_MS = 80


def activity_intervals(
    audio: Path | None, *, scene_start_ms: int, scene_end_ms: int
) -> list[tuple[float, float]] | None:
    """Return scene-local speaking intervals or None for unsupported audio.

    Monophonic 16-bit PCM WAV is analyzed in 80ms energy windows. Silence
    closes the illustrated mouth. A maximum of 80 intervals bounds FFmpeg
    expression size; overly complex tracks fall back to rhythmic talking.
    """
    if audio is None:
        return None
    if not isinstance(scene_start_ms, int) or not isinstance(scene_end_ms, int) \
            or isinstance(scene_start_ms, bool) or isinstance(scene_end_ms, bool) \
            or not 0 <= scene_start_ms < scene_end_ms <= 3_600_000:
        raise ValueError("Invalid narrated scene timing")
    if not isinstance(audio, Path) or not audio.is_file():
        raise ValueError("Narration path must be an existing file")
    try:
        with wave.open(str(audio), "rb") as handle:
            rate = handle.getframerate()
            if (handle.getnchannels() != 1 or handle.getsampwidth() != 2
                    or handle.getcomptype() != "NONE" or
                    not 8000 <= rate <= 96000):
                return None
            first = round(scene_start_ms * rate / 1000)
            last = min(round(scene_end_ms * rate / 1000), handle.getnframes())
            if last - first <= 0:
                return []
            handle.setpos(first)
            window = max(1, round(rate * WINDOW_MS / 1000))
            energies = []
            while handle.tell() < last:
                chunk = handle.readframes(min(window, last-handle.tell()))
                pcm = array("h")
                pcm.frombytes(chunk)
                if sys.byteorder != "little":
                    pcm.byteswap()
                energies.append(sum(abs(sample) for sample in pcm) / max(1, len(pcm)))
    except (wave.Error, EOFError):
        return None
    if not energies:
        return []
    maximum = max(energies)
    if maximum < 160:
        return []
    threshold = max(140, maximum * 0.16)
    active = [energy >= threshold for energy in energies]
    # Fill a one-window gap, avoiding mouth flicker for a brief consonant
    # or an 80ms hesitation. Preserve longer silence in the source track.
    for i in range(1, len(active)-1):
        if active[i-1] and active[i+1]:
            active[i] = True
    windows: list[tuple[float, float]] = []
    beginning: int | None = None
    for i, on in enumerate(active + [False]):
        if on and beginning is None:
            beginning = i
        elif not on and beginning is not None:
            left = max(0.0, beginning * WINDOW_MS / 1000 - 0.04)
            right = min((scene_end_ms-scene_start_ms)/1000,
                        i * WINDOW_MS / 1000 + 0.04)
            if right - left >= 0.08:
                windows.append((round(left, 3), round(right, 3)))
            beginning = None
    if len(windows) > MAX_GATES:
        return None
    return windows


def mouth_gate_expression(intervals: list[tuple[float, float]] | None
                          ) -> str | None:
    """Return bounded FFmpeg booleans; no user-supplied expressions."""
    if intervals is None:
        return None
    if not isinstance(intervals, list) or len(intervals) > MAX_GATES:
        raise ValueError("Invalid voice activity interval count")
    if not intervals:
        return "0"
    previous = -1.0
    expressions = []
    for start, end in intervals:
        if (not isinstance(start, (float, int))
                or not isinstance(end, (float, int))
                or isinstance(start, bool) or isinstance(end, bool)
                or not 0 <= start < end <= 3600
                or start < previous):
            raise ValueError("Invalid voice activity interval")
        expressions.append(f"between(t,{start:.3f},{end:.3f})")
        previous = start
    return "gt(" + "+".join(expressions) + ",0)"
