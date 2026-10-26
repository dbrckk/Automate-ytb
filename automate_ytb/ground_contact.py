"""Deterministic soft ground-contact shadows for original 2D animals.

A bounded blurred shadow sits beneath the moving rig. It follows horizontal
travel but stays on the ground during jumps and flying, making elevation
readable without misleading 3D physics or requiring downloaded textures.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

GROUND_VERSION = "original-ground-contact-v1"
ACTORS = ("owl", "fox", "rabbit", "cat")
WEATHERS = ("day", "night", "cloudy", "rain", "wind", "storm")
ACTIONS = ("idle", "walk", "run", "jump", "fly", "talk", "surprise", "rest")
SHADOW_SIZE = (280, 92)


def draw_contact_shadow(destination: Path, *, actor: str,
                        weather: str, action: str) -> None:
    """Generate an original, translucent contact halo, softly feathered."""
    if actor not in ACTORS or weather not in WEATHERS or action not in ACTIONS:
        raise ValueError("Unsupported original actor, action or weather")
    base_alpha = 58 if weather in ("night", "rain", "storm") else 85
    if action == "fly":
        base_alpha = round(base_alpha * 0.50)
    elif action == "jump":
        base_alpha = round(base_alpha * 0.74)
    shade = (16, 28, 35) if weather != "night" else (10, 18, 30)
    plate = Image.new("RGBA", SHADOW_SIZE, (0, 0, 0, 0))
    brush = ImageDraw.Draw(plate)
    brush.ellipse((23, 28, 257, 78), fill=(*shade, base_alpha))
    brush.ellipse((79, 43, 201, 69),
                  fill=(*shade, min(110, base_alpha + 17)))
    # Blur all edges to avoid a decal-like hard ellipse.
    plate = plate.filter(ImageFilter.GaussianBlur(radius=13))
    destination.parent.mkdir(parents=True, exist_ok=True)
    plate.save(destination, format="PNG", optimize=True)


def shadow_stage(*, body_x: str, ground_y: int, offset_x: int,
                 image_index: int) -> str:
    """Composite the shadow below the actor before the character layers.

    `body_x` is the internal validated pose expression from choreography,
    never external narration or an arbitrary FFmpeg filter argument.
    """
    if not isinstance(body_x, str) or not 1 <= len(body_x) <= 25000:
        raise ValueError("Invalid reviewed character pose")
    if any(ch in body_x for ch in ";[]'\"\\:") or "\n" in body_x:
        raise ValueError("Unsafe character pose expression")
    if not 0 <= ground_y <= 670 or not -200 <= offset_x <= 200:
        raise ValueError("Invalid shadow stage location")
    if not 1 <= image_index <= 24:
        raise ValueError("Invalid shadow input index")
    return (f"[0:v][{image_index}:v]overlay="
            f"x='({body_x})+{offset_x}':y={ground_y}:"
            f"eval=frame:format=auto[shadowstage];")
