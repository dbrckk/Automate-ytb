"""Deterministic local rotation poses for independently drawn 2D appendages.

The selected action controls angular movement; user narration never becomes a
raw FFmpeg expression. This is sprite articulation, not inverse kinematics.
"""
from __future__ import annotations

from .director import ACTIONS

JOINT_VERSION = "original-joint-rotation-v5-continuous-jump-phase"

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
    """Bounded, C1-continuous landing impulse during the last 0.36s of a jump.

    Compact pulse vanishes with zero velocity at both ends of the period:
    no abrupt leftover joint angle when modulo time wraps at 1.75s.
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
    phase = "mod(t,1.75)"
    elapsed = f"max(0,({phase}-1.39))"
    elapsed_norm = f"min(1,max(0,({elapsed})/0.36))"
    envelope = f"16*pow({elapsed_norm},2)*pow(1-({elapsed_norm}),2)"
    return (f"({angle:.4f}*({envelope})*exp(-6*({elapsed}))"
            f"*sin(26*({elapsed})))")

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
    if action == "jump":
        # Body, wing, leg, ear and tail rotations must share the exact
        # original smoothstep flight cycle. Start/end at neutral with zero
        # wrap velocity, instead of an unrelated 3.6 Hz oscillation.
        clock = "mod(t,1.75)"
        smooth = lambda v: f"(({v})*({v})*(3-2*({v})))"
        def ramp(start: str, duration: str) -> str:
            return smooth(f"min(1,max(0,(({clock})-{start})/{duration}))")
        prep = ramp("0", "0.18")
        rise = ramp("0.18", "0.57")
        fall = ramp("0.75", "0.64")
        airborne = f"({rise}-{fall})"
        anticipation = f"({prep}-{rise})"
        recoil = landing_recoil(action, part=part, side=side)
        return (f"({sign * amplitude:.4f}*({airborne})"
                f"+({-sign * amplitude * 0.18:.4f})*({anticipation})"
                f"+({recoil}))")
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
