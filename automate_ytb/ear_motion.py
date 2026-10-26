"""Articulated outer-ear and owl-crest movement for original 2D characters.

Small independently keyed offsets follow approved locomotion beats, while
the complete character body and pupil rig keep their established timing.
"""
from __future__ import annotations

from .choreography import body_position
from .director import ACTIONS

EAR_VERSION = "original-ear-crest-motion-v1"
EAR_AMPLITUDES = {
    "idle": (1.5, 1.5, 1.2),
    "walk": (2.5, 2.5, 3.5),
    "run": (4.0, 4.0, 6.0),
    "jump": (4.0, 5.0, 4.5),
    "fly": (3.5, 3.0, 4.8),
    "talk": (1.0, 1.5, 1.6),
    "surprise": (3.0, 3.5, 5.5),
    "rest": (0.5, 0.8, 0.7),
}


def ear_position(action: str, *, body_x: int, body_y: int) -> tuple[str, str]:
    """Translate separate crest artwork by a few pixels relative to the head."""
    if action not in ACTIONS or action not in EAR_AMPLITUDES:
        raise ValueError("Invalid original actor gesture")
    px, py = body_position(action, x=body_x, y=body_y)
    amp_x, amp_y, frequency = EAR_AMPLITUDES[action]
    # Opposed phase adds inertial lag to ear tips as the body shifts.
    # Absolute movement is <5px beyond the body's validated motion.
    x = f"({px})+{amp_x}*sin(t*{frequency}+0.42)"
    y = f"({py})-{amp_y}*sin(t*{frequency}+0.91)"
    return x, y
