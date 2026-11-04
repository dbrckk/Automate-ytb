"""Evidence-based editorial decisions for every video style.

The editor compares real decoded outgoing and incoming MP4 frames. It never
changes clip timing, text, source content or audio. A high image difference
suggests a clean cut rather than an overlapping double exposure.

These deterministic heuristics are *not* evidence of artistic excellence.
They are intentionally independent of science/cartoon/portrait categories.
"""
from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageOps, ImageStat

VERSION = "universal-editorial-cut-v1"
MEAN_RGB_CUT = 46.0
MEAN_LUMA_CUT = 42.0
NEAR_BLACK_MAX = 13.0
BLACK_WHITE_JUMP = 34.0


def choose_transition(outgoing: Image.Image, incoming: Image.Image) -> dict:
    """Analyze two actual decoded RGB frames; use no style/model guesses.

    All thresholds are interpreted on 8-bit pixels and deliberately
    conservative: fades remain for modest continuity, clean cuts are
    selected for significant visual discontinuities or black-to-bright jumps.
    """
    if (not isinstance(outgoing, Image.Image) or
            not isinstance(incoming, Image.Image) or
            min(*outgoing.size, *incoming.size) < 32 or
            outgoing.width / outgoing.height != incoming.width / incoming.height):
        raise ValueError("Transition comparison requires matching video aspect ratios")

    width, height = (160, 90) if outgoing.width >= outgoing.height else (90, 160)
    first = outgoing.convert("RGB").resize(
        (width, height), Image.Resampling.BOX)
    second = incoming.convert("RGB").resize(
        (width, height), Image.Resampling.BOX)
    rgb_diff = ImageChops.difference(first, second)
    rgb_change = sum(ImageStat.Stat(rgb_diff).mean) / 3
    gray_first = ImageOps.grayscale(first)
    gray_second = ImageOps.grayscale(second)
    first_luma = ImageStat.Stat(gray_first).mean[0]
    second_luma = ImageStat.Stat(gray_second).mean[0]
    light_jump = abs(first_luma - second_luma)
    near_black_jump = (
        (min(first_luma, second_luma) <= NEAR_BLACK_MAX
         and max(first_luma, second_luma) >= BLACK_WHITE_JUMP))

    if near_black_jump:
        reason = "dark-to-bright-scene-change"
    elif rgb_change >= MEAN_RGB_CUT:
        reason = "large-rgb-discontinuity"
    elif light_jump >= MEAN_LUMA_CUT:
        reason = "large-exposure-discontinuity"
    else:
        reason = "visual-continuity"

    choice = "cut" if reason != "visual-continuity" else "dissolve"
    return {
        "algorithm": VERSION,
        "mode": choice,
        "reason": reason,
        "meanRgbPixelChange": round(rgb_change, 3),
        "meanLuminanceChange": round(light_jump, 3),
        "outgoingMeanLuminance": round(first_luma, 3),
        "incomingMeanLuminance": round(second_luma, 3),
        "sampleDimensions": [width, height],
        "noAudioOrSubtitleShift": True,
        "editorialApproved": False,
    }
