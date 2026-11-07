"""Deterministic local light response to AUTHORED 3D molecule impacts.

This is a causal visual explanation, not atmospheric spectral simulation.
The lighting model is independent of Blender for regression verification.
"""
from __future__ import annotations

import math

VERSION = "aurora-impact-lighting-v1"
PEAK_ENERGY = {"collisions": 210.0, "emission": 275.0}
DECAY_WINDOW = {"collisions": .082, "emission": .115}


def impact_light_energy(beat: str, q: float, hit: float) -> float:
    """Light turns on at the original electron impact, then fades smoothly.

    This drives a real Blender POINT light, not a brightness overlay or an
    invented pixel-movement score. q/hit are fractions of authored shot time.
    """
    if (beat not in PEAK_ENERGY or type(q) not in (int, float)
            or type(hit) not in (int, float) or not math.isfinite(q)
            or not math.isfinite(hit) or not 0 <= q <= 1
            or not 0 < hit < 1):
        raise ValueError("Invalid original collision/emission timing")
    if q < hit:
        return 0.0
    return PEAK_ENERGY[beat] * math.exp(-(q - hit) / DECAY_WINDOW[beat])


def impact_light_color(beat: str, index: int) -> tuple[float, float, float]:
    """Scene-specific explanatory colors of genuinely local light sources."""
    if beat not in PEAK_ENERGY or type(index) is not int or not 0 <= index < 10:
        raise ValueError("Invalid original collision light index")
    if beat == "collisions":
        return (.38, .78, 1.0) if index % 3 else (.74, .53, 1.0)
    return ((1.0, .28, .30), (.64, .32, 1.0),
            (.24, 1.0, .51), (.24, 1.0, .51))[index % 4]
