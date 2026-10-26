"""Validated, action-driven 2D joint rotations for original character sprites.

Wing and leg images pivot independently around the sprite centre. Rotations
remain deliberately small, with a 16-pixel transparent safety margin. These
are authored layered 2D joints, NOT skeletal IK or inferred motion capture.
"""
from __future__ import annotations

import re

JOINT_VERSION = "pivoted-appendages-v1"
# (square canvas size, sprite x offset, sprite y offset). The chosen
# shoulder/hip lands at the canvas centre, so rotation uses an anatomical
# joint instead of turning the entire sprite about its own bounding box.
PIVOTS = {
    ("wing", "left"): (384, 56, 126),
    ("wing", "right"): (384, 164, 126),
    ("leg", "left"): (272, 86, 126),
    ("leg", "right"): (272, 86, 126),
}

# Radians, angular speed in radians/second, limited to small motions.
WINGS = {
    "idle": (0.030, 1.2), "walk": (0.080, 4.1),
    "run": (0.140, 8.1), "jump": (0.180, 3.6),
    "fly": (0.260, 7.4), "talk": (0.045, 2.1),
    "surprise": (0.150, 6.0), "rest": (0.012, 0.8),
}
LEGS = {
    "idle": (0.014, 1.2), "walk": (0.130, 5.1),
    "run": (0.200, 10.2), "jump": (0.130, 3.6),
    "fly": (0.040, 5.3), "talk": (0.015, 2.0),
    "surprise": (0.110, 7.5), "rest": (0.005, 0.8),
}


def joint_angle(action: str, *, joint: str, side: str) -> str:
    """Return an internally authored, bounded FFmpeg angle expression."""
    profiles = {"wing": WINGS, "leg": LEGS}
    if joint not in profiles or side not in ("left", "right"):
        raise ValueError("Unsupported original articulated joint")
    if action not in profiles[joint]:
        raise ValueError("Unsupported original character action")
    amplitude, frequency = profiles[joint][action]
    # At the start of a scene the source image has exactly its approved pose.
    # Mirrored wings/legs pivot in opposite directions, and ease smoothly.
    sign = "-" if side == "right" else ""
    return f"{sign}{amplitude:.3f}*sin(t*{frequency:.3f})"


def pivot_offset(joint: str, side: str) -> tuple[int, int]:
    """Screen correction for the padded canvas, retaining sprite placement."""
    if (joint, side) not in PIVOTS:
        raise ValueError("Unsupported original character joint")
    _, x, y = PIVOTS[(joint, side)]
    return x, y


def rotated_source(*, input_index: int, output_label: str, angle: str,
                   joint: str, side: str) -> str:
    """Rotate a joint in an alpha-padded plate about its shoulder or hip.

    Consumers must subtract pivot_offset(joint, side) from original overlay
    coordinates so the unrotated first frame matches the approved poster.
    """
    if (not isinstance(input_index, int) or isinstance(input_index, bool)
            or not 1 <= input_index <= 24):
        raise ValueError("Untrusted FFmpeg image stream index")
    if not isinstance(output_label, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]{1,24}", output_label):
        raise ValueError("Invalid FFmpeg rotated joint label")
    if (not isinstance(angle, str) or not 1 <= len(angle) <= 25000
            or not re.fullmatch(r"[a-zA-Z0-9_+*/()., \\-]+", angle)):
        raise ValueError("Untrusted FFmpeg angle expression")
    if (joint, side) not in PIVOTS:
        raise ValueError("Unsupported original character joint")
    canvas, dx, dy = PIVOTS[(joint, side)]
    return (f"[{input_index}:v]format=rgba,"
            f"pad={canvas}:{canvas}:{dx}:{dy}:color=black@0,"
            f"rotate=a='{angle}':ow=iw:oh=ih:c=none"
            f"[{output_label}];")
