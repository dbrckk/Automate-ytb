"""Small original eye-reflection plates attached to authored gaze poses.

Each plate holds two soft specular dots within the independently authored
eyes. Their motion is <=2 pixels, and the closed-eye pose is composited above
them in the renderer so a blink never leaves floating glints.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

EYE_VERSION = "authored-eye-micro-highlights-v1"
ACTORS = ("fox", "rabbit", "cat", "owl")
GAZES = {
    "forward": (0, 0),
    "right": (13, 0),
    "left": (-13, 0),
    "up": (0, -11),
    "down": (0, 10),
    "down-right": (9, 8),
}
ANIMAL_GAZES = {
    "forward": (0, 0),
    "right": (12, 1),
    "left": (-12, 1),
    "up": (0, -10),
    "down": (0, 10),
    "down-right": (8, 8),
}


def draw_eye_glints(destination: Path, *, actor: str, gaze: str) -> None:
    """Make one reproducible transparent sprite-sized plate per original rig."""
    if actor not in ACTORS or gaze not in GAZES:
        raise ValueError("Unrecognized original eye pose")
    owl = actor == "owl"
    w, h = (322, 430) if owl else (350, 440)
    canvas = Image.new("RGBA", (w*3, h*3), (0, 0, 0, 0))
    brush = ImageDraw.Draw(canvas)
    shift_x, shift_y = (GAZES if owl else ANIMAL_GAZES)[gaze]
    centers = (106, 219) if owl else (117, 235)
    base_y = 176 if owl else 219
    for center in centers:
        # Both dots remain inside the dark pupil ellipse, away from its
        # existing upper-left highlight and outside eyebrow artwork.
        x = (center + shift_x + 12)*3
        y = (base_y + shift_y)*3
        brush.ellipse((x-12,y-12,x+12,y+12), fill=(255, 248, 225, 181))
        brush.ellipse((x-4,y-4,x+4,y+4), fill=(255,255,255,225))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize((w,h), Image.Resampling.LANCZOS).save(
        destination, format="PNG", optimize=True)


def eye_overlay_expression(*, body_x: str, body_y: str,
                           input_index: int, from_label: str,
                           to_label: str = "eyeacting") -> str:
    """Reviewed overlay step; eye glints move with the entire body pose."""
    if (not isinstance(body_x,str) or not isinstance(body_y,str)
            or any(not 1 <= len(v) <= 25000 or any(
                c in v for c in ";[]'\"\\:\n\r") for v in (body_x,body_y))):
        raise ValueError("Unsafe original character trajectory")
    if not isinstance(input_index,int) or isinstance(input_index,bool) or not 7 <= input_index <= 24:
        raise ValueError("Invalid original sprite input index")
    if from_label not in {"c","d"} or to_label != "eyeacting":
        raise ValueError("Invalid original eye stage")
    # Delay micro-acting until the authored gaze cross-fade is complete.
    # Tiny quasi-periodic shifts avoid a hard mechanical eye oscillation.
    return (f"[{from_label}][{input_index}:v]overlay="
            f"x='({body_x})+1.2*sin(t*0.91)+0.6*sin(t*2.7)':"
            f"y='({body_y})+0.9*sin(t*1.13)':"
            "enable='gte(t,0.6)':eval=frame:format=auto[eyeacting];")
