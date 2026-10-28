"""Original emotion-directed, subtly animated eyebrow plates for 2D animal rigs.

A lightweight, deterministic expression pass adds readable eyebrow poses to
script-directed characters. No facial recognition, emotion inference or 3D rig.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .director import ACTIONS, EMOTIONS

FACE_VERSION = "authored-eyebrow-acting-v1"
ACTORS = ("owl", "fox", "rabbit", "cat")
SIZES = {"owl": (322, 430), "fox": (350, 440),
         "rabbit": (350, 440), "cat": (350, 440)}
INK = {"owl": (55, 32, 91), "fox": (107, 58, 45),
       "rabbit": (119, 89, 123), "cat": (41, 76, 99)}


def draw_expression(destination: Path, *, actor: str, emotion: str) -> None:
    """Paint a small original antialiased brow pose above existing eyes."""
    if actor not in ACTORS or emotion not in EMOTIONS:
        raise ValueError("Unsupported authored character expression")
    w, h = SIZES[actor]
    scale = 3
    canvas = Image.new("RGBA", (w * scale, h * scale))
    d = ImageDraw.Draw(canvas)
    color = (*INK[actor], 236)
    highlight = (255, 237, 213, 96) if actor != "owl" else (238, 211, 255, 104)
    centers = (106, 219) if actor == "owl" else (117, 235)
    top = 102 if actor == "owl" else 165
    for side, x in enumerate(centers):
        # Preserve the iris and blink variants: every mark stays above
        # the existing eye and is narrow enough not to mask eyelids.
        if emotion == "surprised":
            rise = -13
            points = [(x - 28, top + 3 + rise),
                      (x - 12, top - 7 + rise),
                      (x + 12, top - 8 + rise),
                      (x + 28, top + 3 + rise)]
        elif emotion == "worried":
            inner = 1 if side == 0 else -1
            points = [(x - 27, top + 6 - 8 * inner),
                      (x - 10, top - 5 - 5 * inner),
                      (x + 9, top - 3 + 5 * inner),
                      (x + 27, top + 7 + 8 * inner)]
        elif emotion == "curious":
            rise = -10 if side == 0 else 1
            points = [(x - 27, top + 6 + rise),
                      (x - 7, top - 5 + rise),
                      (x + 12, top - 3 + rise),
                      (x + 27, top + 5 + rise)]
        elif emotion == "happy":
            points = [(x - 28, top + 7), (x - 8, top + 0),
                      (x + 10, top - 1), (x + 28, top + 8)]
        else:
            points = [(x - 25, top + 5), (x - 8, top + 2),
                      (x + 8, top + 2), (x + 25, top + 5)]
        stroke = [(round(px * scale), round(py * scale)) for px, py in points]
        d.line(stroke, fill=color, width=5 * scale, joint="curve")
        if emotion in {"happy", "surprised", "curious"}:
            d.line([(x * scale, (top - 3 + (-13 if emotion == "surprised" else 0)) * scale),
                    ((x + 11) * scale,
                     (top - 3 + (-13 if emotion == "surprised" else 0)) * scale)],
                   fill=highlight, width=2 * scale)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((w, h), Image.Resampling.LANCZOS).save(
        destination, format="PNG", optimize=True)


def expression_bob(*, action: str, emotion: str) -> str:
    """Small bounded vertical acting offset, neutral at t=0."""
    if action not in ACTIONS or emotion not in EMOTIONS:
        raise ValueError("Unsupported animation expression cue")
    if emotion == "surprised" or action == "surprise":
        return "-5*exp(-2.6*t)*sin(t*7.4)"
    if emotion == "worried":
        return "2*sin(t*1.05)"
    if emotion == "curious":
        return "-2*sin(t*1.7)"
    if emotion == "happy" or action == "talk":
        return "-1.5*sin(t*2.0)"
    return "0"


def append_expression(*, graph: str, label: str, names: list[str],
                      body_x: str, body_y: str, action: str,
                      emotion: str) -> tuple[str, str, list[str]]:
    """Attach the expression to the actor trajectory after weather layers."""
    if "expression" in names:
        raise ValueError("Expression plate already composited")
    if not isinstance(graph, str) or not isinstance(label, str) or not label:
        raise ValueError("Unsafe expression graph")
    for pose in (body_x, body_y):
        if (not isinstance(pose, str) or not 1 <= len(pose) <= 25000 or
                any(ch in pose for ch in ";[]'\"\\:\n\r")):
            raise ValueError("Unsafe expression pose")
    move = expression_bob(action=action, emotion=emotion)
    index = len(names)
    graph += (f";[{label}][{index}:v]overlay=x='{body_x}':"
              f"y='({body_y})+({move})':eval=frame:format=auto[faceexpressed]")
    return graph, "faceexpressed", names + ["expression"]
