"""Original narration delivery profiles for optional Kokoro neural speech.

The only French Kokoro-82M voice supported by its upstream voice catalogue
is ff_siwis. These settings do not claim to create a different speaker,
emotion cloning or phoneme-perfect audio.
"""
from __future__ import annotations

import re

STYLES = {"natural": 0.94, "gentle": 0.88, "lively": 1.04,
          "expressive": 0.95}
VERSION = "kokoro-phrasing-v3-no-artificial-mid-sentence-pauses-semantic-micro-prosody"


def speaking_speed(*, style: str) -> float:
    if not isinstance(style, str) or style not in STYLES:
        raise ValueError("Narration style must be natural, gentle, lively or expressive")
    return STYLES[style]


_ACTION = re.compile(
    r"\b(erupt\w*|explod\w*|collid\w*|crash\w*|strik\w*|"
    r"burst\w*|blast\w*|surge\w*|rush\w*|flash\w*|"
    r"plung\w*|sink\w*|suddenly|at once)\b", re.IGNORECASE)


def phrase_speed(phrase: str, *, style: str) -> float:
    """Small semantic rate variations; not synthesized emotion or word alignment.

    Used only by the opt-in expressive Kokoro mode. Existing styles preserve
    their fixed rate. Differences stay small across separately rendered phrases.
    """
    baseline = speaking_speed(style=style)
    if not isinstance(phrase, str) or not phrase.strip():
        raise ValueError("Narration phrase must not be blank")
    if style != "expressive":
        return baseline
    if _ACTION.search(phrase):
        return 1.00
    if phrase.rstrip().endswith(("?", "…", "...")):
        return 0.91
    if re.search(r"\b(because|however|instead|but|therefore|although)\b",
                 phrase, re.IGNORECASE):
        return 0.93
    return baseline


def natural_pause_ms(phrase: str, *, neural: bool) -> int:
    """Return a small authored-boundary pause without mutating read text.

    Each caption phrase is synthesized independently. The pause lies between
    phrases, appears in the measured PCM timestamps, and never alters the
    audio inside words. The old eSpeak timing is deliberately unchanged.
    """
    if not isinstance(phrase, str) or not phrase.strip():
        raise ValueError("Original narration phrase must not be blank")
    if not neural:
        return 80
    trimmed = phrase.rstrip()
    if trimmed.endswith(("...", "…")):
        return 290
    if trimmed.endswith((".", "?", "!")):
        return 190
    if trimmed.endswith((";", ":")):
        return 160
    if trimmed.endswith(","):
        return 105
    # Caption width may split a single natural sentence into several
    # synthesized pieces. A fixed 95 ms stop at every such boundary makes
    # otherwise flowing narration sound like unrelated teleprompter lines.
    # Keep only pauses justified by authored punctuation.
    return 0
