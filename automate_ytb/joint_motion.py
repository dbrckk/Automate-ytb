"""Deterministic local rotation poses for independently drawn 2D appendages.

The selected action controls angular movement; user narration never becomes a
raw FFmpeg expression. This is sprite articulation, not inverse kinematics.
"""
from __future__ import annotations

from .director import ACTIONS

JOINT_VERSION = "original-joint-rotation-v4-planted-contact"

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
    "ear": {"idle": 0.024, "walk": 0.052, "run": 0.084,
            "jump": 0.090, "fly": 0.062, "talk": 0.032,
            "surprise": 0.132, "rest": 0.010},
}
# A short, damped impulse follows a landing rather than letting ears,
# wings, feet and tails stop abruptly with the torso. Radians stay small.
IMPACT_AMPLITUDES = {
    "wing": 0.070, "leg": 0.045, "tail": 0.095, "ear": 0.084,
}
JUMP_PERIOD = 1.75
LANDING_TIME = 1.39


def landing_recoil(action: str, *, part: str, side: str) -> str:
    """Trusted FFmpeg angle impulse, zero outside the jump landing interval.

    Decaying spring correction starts at zero on ground contact, oscillates
    rapidly and settles before the next jump. Only validated action/rig enums
    are accepted; no source narration enters the filter expression.
    """
    if action not in ACTIONS or part not in IMPACT_AMPLITUDES:
        raise ValueError("Unknown original landing joint")
    if (part == "tail" and side != "tail") or (
            part != "tail" and side not in {"left", "right"}):
        raise ValueError("Unknown original landing joint side")
    if action != "jump":
        return "0"
    sign = -1 if side == "right" else 1
    angle = sign * IMPACT_AMPLITUDES[part]
    clock = "mod(t,1.75)"
    elapsed = f"({clock}-1.39)"
    return (
        f"if(gte({clock},1.39),"
        f"{angle:.4f}*exp(-9*({elapsed}))*sin(26*({elapsed})),0)"
    )


FREQUENCIES = {
    "idle": 1.6, "walk": 5.1, "run": 10.2, "jump": 3.6,
    "fly": 6.1, "talk": 2.0, "surprise": 7.5, "rest": 0.9,
}


def joint_angle(action: str, *, part: str, side: str) -> str:
    """Trusted, bounded FFmpeg rotate angle (radians) for the current action."""
    if action not in ACTIONS or part not in AMPLITUDES:
        raise ValueError("Unknown original animation joint")
    if (part == "tail" and side != "tail") or (
            part in ("wing", "leg", "ear") and side not in ("left", "right")):
        raise ValueError("Unknown sprite side")
    amplitude = AMPLITUDES[part][action]
    frequency = FREQUENCIES[action]
    sign = -1 if side == "right" else 1
    phase = 3.141593 if part == "leg" and side == "right" and action in {"run", "walk"} else 0
    if part == "leg" and action in {"walk", "run"}:
        # The paw's contact half-cycle holds a neutral angle; only the
        # lifted swing rotates. A squared half-sine eases both boundaries.
        swing = f"max(0,-sin(t*{frequency:.3f}+{phase:.6f}))"
        return f"({sign * amplitude:.4f}*pow({swing},2))"
    # Two small harmonics rather than a perfectly repeated back-and-forth.
    # A surprised animal briefly flicks the ears and settles instead of
    # indefinitely repeating an exaggerated alarm pose.
    envelope = "exp(-1.35*t)*" if part == "ear" and action == "surprise" else ""
    recoil = landing_recoil(action, part=part, side=side)
    return (f"({envelope}({sign * amplitude:.4f}*sin(t*{frequency:.3f}+{phase:.6f})"
            f"+{sign * amplitude * .14:.4f}*sin(t*{frequency * .46:.3f}))"
            f"+({recoil}))")
