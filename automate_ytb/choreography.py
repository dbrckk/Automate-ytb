"""Small, deterministic, validated action choreography for original 2D rigs.

The original narration's classified action selects a *trusted* expression.
No user-supplied FFmpeg filters, audio-driven lip-sync or fictitious motions.
These are rhythmic poses, not skeletal inverse kinematics.
"""
from __future__ import annotations

from .director import ACTIONS

CHOREOGRAPHY_VERSION = "authored-action-choreography-v4-planted-foot-gait"

# Horizontal travel (px), horizontal Hz, vertical displacement (px),
# vertical oscillator Hz and animation kind.
PROFILES = {
    "idle": (4, 0.45, 5, 1.5, "breathe"),
    "walk": (16, 0.70, 13, 5.1, "steps"),
    "run": (27, 1.40, 24, 10.2, "steps"),
    "jump": (15, 1.10, 76, 2.2, "leap"),
    "fly": (19, 1.05, 32, 5.3, "flight"),
    "talk": (5, 0.55, 5, 2.0, "breathe"),
    "surprise": (11, 1.30, 42, 7.5, "reaction"),
    "rest": (1, 0.20, 2, 1.1, "breathe"),
}

# Foreground parts never depend on unknown text or unvalidated values.
MOUTH_ENABLE = {
    "talk": "lt(mod(t,0.50),0.28)",
    "surprise": "lt(t,0.60)",
}


def body_position(action: str, *, x: int, y: int) -> tuple[str, str]:
    """Return FFmpeg overlay x/y expressions for the same body and blink pose."""
    if action not in ACTIONS or action not in PROFILES:
        raise ValueError("Unknown original animation action")
    if not (0 <= x <= 900 and 0 <= y <= 400):
        raise ValueError("Unsafe rig origin")
    horizontal, hf, vertical, vf, kind = PROFILES[action]
    if kind == "reaction":
        xp = f"{x}+{horizontal}*exp(-1.3*t)*sin(t*8)"
        yp = f"{y}-{vertical}*exp(-1.1*t)*abs(sin(t*{vf}))"
    else:
        # Secondary low-frequency sway prevents perfectly repeated robotic arcs.
        xp = f"{x}+{horizontal}*sin(t*{hf})+1.2*sin(t*0.37)"
        if kind == "leap":
            # Repeated four-stage leap: brief crouch, eased ascent, descent,
            # soft landing. Continuous at each boundary; no external assets.
            cycle = "mod(t,1.75)"
            crouch = f"min(1,({cycle})/0.18)"
            launch = f"min(1,max(0,(({cycle})-0.18)/0.57))"
            descend = f"min(1,max(0,(({cycle})-0.75)/0.64))"
            land = f"min(1,max(0,(({cycle})-1.39)/0.36))"
            smooth = lambda u: f"(({u})*({u})*(3-2*({u})))"
            height = f"({smooth(launch)}-{smooth(descend)})"
            yp = (f"{y}+12*({smooth(crouch)})-"
                  f"({vertical}+12)*({height})-12*({smooth(land)})")
        elif kind == "steps":
            sign = "+" if kind == "steps" else "-"
            yp = f"{y}{sign}{vertical}*abs(sin(t*{vf}))"
        elif kind == "flight":
            yp = f"{y}-23+{vertical}*sin(t*{vf})"
        else:
            yp = f"{y}+{vertical}*sin(t*{vf})+1.3*sin(t*0.41)"
    return xp, yp


def secondary_position(action: str, *, base: int, side: str) -> str:
    """Independent wing/tail swish, slower on rest and faster on locomotion."""
    if action not in ACTIONS or action not in PROFILES:
        raise ValueError("Unknown secondary animation")
    if side not in ("left", "right", "tail"):
        raise ValueError("Unsafe articulated sprite")
    amplitude = {
        "idle": 8, "walk": 22, "run": 39, "jump": 52,
        "fly": 71, "talk": 6, "surprise": 62, "rest": 2,
    }[action]
    frequency = {
        "idle": 2.6, "walk": 5.2, "run": 10.5, "jump": 6.5,
        "fly": 8.0, "talk": 2.0, "surprise": 6.6, "rest": 0.9,
    }[action]
    sign = "-" if side == "right" else "+"
    # Two frequencies create gentle organic follow-through, without noise,
    # unbounded motion or non-deterministic video output.
    follow = max(1, round(amplitude * 0.13, 2))
    return (f"{base}{sign}{amplitude}*sin(t*{frequency})"
            f"{sign}{follow}*sin(t*{frequency * 0.47:.3f}+0.35)")


def mouth_expression(action: str) -> str:
    if action not in ACTIONS or action not in PROFILES:
        raise ValueError("Unknown mouth action")
    return MOUTH_ENABLE.get(action, "0")


# Relative to the moving body's origin; each limb has its own trajectory.
# The paired limbs intentionally use opposite phases only while walking or
# running. Both tuck in the same direction in jumps and during flight.
LEG_ANCHORS = {"left": 68, "right": 186}
LEG_MOTION = {
    "idle": (1, 1, 1.3),
    "walk": (12, 11, 5.1),
    "run": (21, 20, 10.2),
    "jump": (7, 32, 2.2),
    "fly": (4, 17, 5.3),
    "talk": (1, 2, 2.0),
    "surprise": (5, 21, 7.5),
    "rest": (0, 0, 1.0),
}


def leg_position(action: str, *, side: str, body_x: int = 180,
                 body_y: int = 184) -> tuple[str, str]:
    """Independent x/y pose of a visible foot layer, relative to the body.

    For locomotion, feet alternate out of phase. For jumping, both tuck
    together. There is no user-provided filter expression or arbitrary
    sprite placement; all numbers are reviewed constants.
    """
    if action not in ACTIONS or action not in LEG_MOTION:
        raise ValueError("Unknown original animation action")
    if side not in LEG_ANCHORS:
        raise ValueError("Unknown articulated leg")
    parent_x, parent_y = body_position(action, x=body_x, y=body_y)
    reach, lift, frequency = LEG_MOTION[action]
    phase = "3.141593" if side == "right" and action in {"walk", "run"} else "0"
    x = f"({parent_x})+{LEG_ANCHORS[side]}+{reach}*sin(t*{frequency}+{phase})"
    if action == "jump":
        # Feet tuck during the airborne arc, then extend before landing.
        phase_jump = "mod(t,1.75)"
        rise = f"min(1,max(0,(({phase_jump})-0.18)/0.57))"
        fall = f"min(1,max(0,(({phase_jump})-0.75)/0.64))"
        tuck = f"(({rise})*({rise})*(3-2*({rise}))-({fall})*({fall})*(3-2*({fall})))"
        y = f"({parent_y})+335-{lift}*({tuck})"
    elif action in {"walk", "run"}:
        # A planted stance occupies half of each gait cycle. The leg only
        # lifts during the other half, with zero vertical speed at toe-off
        # and touchdown. Opposite phases alternate the planted foot.
        swing = f"max(0,sin(t*{frequency}+{phase}))"
        y = f"({parent_y})+335-{lift}*({swing})*({swing})"
    elif action == "fly":
        y = f"({parent_y})+335+{lift}*sin(t*{frequency}+{phase})"
    else:
        y = f"({parent_y})+335-{lift}*(0.5+0.5*sin(t*{frequency}+{phase}))"
    return x, y

# Small, locally phase-driven ear follow-through; the ears are independent
# original RGBA layers rather than an illusion duplicated over the forehead.
EAR_MOTION_VERSION = "two-ear-follow-through-v1"


def ear_position(action: str, *, kind: str, side: str,
                 body_x: int = 180, body_y: int = 184) -> tuple[str, str]:
    """A trusted, subtle motion for each ear, following the moving head.

    All expressions are generated from strict enumerated actions, animals,
    and sides. Zero offset at t=0 keeps posters aligned with the video pose.
    """
    if kind not in {"fox", "rabbit", "cat"}:
        raise ValueError("Unknown original forest ear rig")
    if side not in {"left", "right"}:
        raise ValueError("Unknown original ear side")
    parent_x, parent_y = body_position(action, x=body_x, y=body_y)
    base = {"fox": 4, "rabbit": 10, "cat": 5}[kind]
    action_scale = {
        "idle": 0.6, "walk": 1.0, "run": 1.3, "jump": 0.9,
        "fly": 0.9, "talk": 0.35, "surprise": 1.5, "rest": 0.25,
    }[action]
    rate = {
        "idle": 1.3, "walk": 3.5, "run": 6.7, "jump": 3.0,
        "fly": 5.3, "talk": 1.6, "surprise": 8.0, "rest": 0.7,
    }[action]
    sign = 1 if side == "left" else -1
    amplitude = round(base * action_scale, 2)
    # Harmonics give the tips a delayed follow-through without clipping;
    # opposite signs ensure distinct left/right expressive movement.
    dx = (f"({parent_x})+{sign*amplitude}*sin(t*{rate})"
          f"+{sign*round(amplitude*.27,2)}*sin(t*{rate*.48:.3f})")
    droop = 7 if action == "rest" else 0
    dy = (f"({parent_y})+{droop}*(1-exp(-2.2*t))"
          f"+{round(amplitude*.45,2)}*(1-cos(t*{rate}))")
    if action == "surprise":
        dy += "-9*exp(-2*t)*abs(sin(t*8))"
    return dx, dy
