"""Conservative, local cleanup of signed 16-bit mono speech fragments.

Phrase-mode TTS can append large digital-silence buffers to each fragment.
Those buffers accumulate into awkward pauses and misleading caption timing.
We preserve margins around speech, avoid cutting audio by target duration,
and apply a tiny click-prevention fade. No neural VAD or external API.
"""
from __future__ import annotations

from array import array
import sys


def compact_speech_pcm(pcm: bytes, rate: int) -> tuple[bytes, dict]:
    """Return PCM and deterministic timing diagnostics.

    Only prune *edge* silence; interior pauses always remain intact.
    A low relative threshold deliberately favors keeping quiet consonants.
    """
    if (not isinstance(pcm, bytes) or not pcm or len(pcm) % 2
            or not isinstance(rate, int) or not 8000 <= rate <= 96000):
        raise ValueError("Expected nonempty mono 16-bit PCM at a valid sample rate")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(value) for value in samples)
    if peak == 0:
        raise RuntimeError("Speech synthesizer produced a completely silent phrase")

    # Ten-millisecond windows and a deliberately conservative threshold.
    # Relative threshold remains low even for loud voices and never depends
    # on the previous speaker or scene.
    window = max(1, round(rate * 0.01))
    threshold = max(12, min(256, peak // 180))
    first, last = None, None
    for offset in range(0, len(samples), window):
        if any(abs(value) >= threshold
               for value in samples[offset:offset + window]):
            if first is None:
                first = offset
            last = min(len(samples), offset + window)
    if first is None:
        # Preserve extremely quiet but nonzero speech rather than discard it.
        first, last = 0, len(samples)

    leading_margin = round(rate * 0.04)
    trailing_margin = round(rate * 0.08)
    trim_begin = max(0, first - leading_margin)
    trim_end = min(len(samples), last + trailing_margin)
    # Do not introduce needless time shifts for already tight TTS output.
    if trim_begin < round(rate * 0.12):
        trim_begin = 0
    if len(samples) - trim_end < round(rate * 0.12):
        trim_end = len(samples)
    compact = samples[trim_begin:trim_end]

    # Abruptly concatenating nonzero PCM can produce clicks. The fade is
    # short enough not to audibly swallow the start/end of a syllable.
    fade = min(round(rate * 0.006), len(compact) // 2)
    for i in range(fade):
        gain = (i + 1) / (fade + 1)
        compact[i] = round(compact[i] * gain)
        compact[-1 - i] = round(compact[-1 - i] * gain)

    if sys.byteorder != "little":
        compact.byteswap()
    return compact.tobytes(), {
        "leadingTrimMs": round(trim_begin * 1000 / rate, 2),
        "trailingTrimMs": round((len(samples) - trim_end) * 1000 / rate, 2),
        "originalDurationMs": round(len(samples) * 1000 / rate, 2),
        "cleanDurationMs": round(len(compact) * 1000 / rate, 2),
        "nonzeroSamplePeak": peak,
        "method": "edge-silence-window-v1",
    }
