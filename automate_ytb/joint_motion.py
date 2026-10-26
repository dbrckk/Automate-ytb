"""Deterministic local rotation poses for independently drawn 2D appendages.

The selected action controls angular movement; user narration never becomes a
raw FFmpeg expression. This is sprite articulation, not inverse kinematics.
"""
from __future__ import annotations

from .director import ACTIONS

JOINT_VERSION = "original-joint-rotation-v1"

# Radians, deliberately bounded: avoid disconnected or spinning sprites.
AMPLITUDES = {
    "wing": {"idle": 0.035, "walk": 0.080, "run": 0.125,
             "jump": 0.165, "fly": 0.245, "talk": 0.040,
             "surprise": 0.170, "rest": 0.012},
    "leg": {"idle": 0.014, "walk": 0.120, "run": 0.200,
            "jump": 0.180, "fly": 0.080, "talk": 0.019,
            "surprise": 0.095, "rest": 0.008},
    "tail": {"idle": 0.034, "walk": 0.105, "run": 0.160,
             "jump": 0.140, "fly": 0.115, "talk": 0.040,
             "surprise": 0.165, "rest": 0.008},
}
FREQUENCIES = {
    "idle": 1.6, "walk": 5.1, "run": 10.2, "jump": 3.6,
    "fly": 6.1, "talk": 2.0, "surprise": 7.5, "rest": 0.9,
}


def joint_angle(action: str, *, part: str, side: str) -> str:
    """Trusted, bounded FFmpeg rotate angle (radians) for the current action."""
    if action not in ACTIONS or part not in AMPLITUDES:
        raise ValueError("Unknown original animation joint")
    if (part == "tail" and side != "tail") or (
            part in ("wing", "leg") and side not in ("left", "right")):
        raise ValueError("Unknown sprite side")
    amplitude = AMPLITUDES[part][action]
    frequency = FREQUENCIES[action]
    sign = -1 if side == "right" else 1
    phase = 3.141593 if part == "leg" and side == "right" and action in {"run", "walk"} else 0
    # Two small harmonics rather than a perfectly repeated back-and-forth.
    return (f"({sign * amplitude:.4f}*sin(t*{frequency:.3f}+{phase:.6f})"
            f"+{sign * amplitude * .14:.4f}*sin(t*{frequency * .46:.3f}))")
