"""Original transient ground reactions for authored animation beats.

Fleeting transparent puffs connect steps, takeoff and landings to the
illustrated world. No source footage, licensed sprites, physics engine,
external models, or additional audio are used.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter

RESPONSE_VERSION = "original-ground-response-v1"
BIOMES = ("forest", "river", "meadow", "village")
WEATHERS = ("day", "night", "cloudy", "rain", "storm", "wind")
REACTIONS = ("walk", "run", "jump")


def draw_ground_response(destination: Path, *, biome: str, weather: str,
                         seed: str) -> None:
    """Create a soft translucent contact puff, tinted by its location."""
    if biome not in BIOMES or weather not in WEATHERS:
        raise ValueError("Unknown original ground-response environment")
    if not isinstance(seed, str) or len(seed) > 200000:
        raise ValueError("Invalid bounded original animation identity")
    rng = Random(int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16))
    plate = Image.new("RGBA", (300, 120), (0, 0, 0, 0))
    marks = Image.new("RGBA", plate.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(marks, "RGBA")
    if biome == "river" or weather in {"rain", "storm"}:
        rgb = (150, 200, 221)  # spray and mist, not dry dust
    elif biome == "village":
        rgb = (190, 175, 154)
    elif biome == "meadow":
        rgb = (163, 204, 146)
    else:
        rgb = (188, 159, 114)
    opacity = 53 if weather == "night" else 80
    # Central soft plume near the feet with staggered distant side wisps.
    for i, (cx, cy, rx, ry) in enumerate(
            ((135, 75, 59, 17), (86, 68, 40, 15),
             (197, 71, 46, 16), (151, 55, 27, 16))):
        jx = rng.randint(-7, 7)
        jy = rng.randint(-5, 5)
        draw.ellipse((cx+jx-rx, cy+jy-ry, cx+jx+rx, cy+jy+ry),
                     fill=(*rgb, max(20, opacity-8*i)))
    softened = marks.filter(ImageFilter.GaussianBlur(radius=10))
    plate.alpha_composite(softened)
    d = ImageDraw.Draw(plate, "RGBA")
    # A handful of tiny, semi-transparent flecks keeps the puff readable.
    for _ in range(13):
        x = rng.choice((rng.randint(60, 115), rng.randint(175, 225)))
        y = rng.randint(31, 86)
        radius = rng.randint(2, 5)
        d.ellipse((x-radius, y-radius, x+radius, y+radius),
                  fill=(*rgb, rng.randint(26, 57)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    plate.save(destination, format="PNG", optimize=True)


def reaction_enable(action: str) -> str:
    """Return trusted beat gates; no arbitrary narration enters FFmpeg."""
    if action == "walk":
        return "between(mod(t,1.23),0.58,0.78)"
    if action == "run":
        return "between(mod(t,0.62),0.27,0.43)"
    if action == "jump":
        return ("max(between(mod(t,1.75),0.12,0.26),"
                "between(mod(t,1.75),1.36,1.58))")
    if action in {"idle", "fly", "talk", "surprise", "rest"}:
        return "0"
    raise ValueError("Unrecognized original ground reaction")


def response_stage(*, body_x: str, y: int, image_index: int,
                   enable: str, x_offset: int) -> str:
    """Add temporary contact art behind the animated sprite, above shadow."""
    for expression in (body_x, enable):
        if not isinstance(expression, str) or not 1 <= len(expression) <= 24000:
            raise ValueError("Invalid authored ground expression")
        if any(c in expression for c in ";[]'\"\\:\n\r"):
            raise ValueError("Unsafe ground-response filter expression")
    if not 0 <= y <= 610 or not -120 <= x_offset <= 190:
        raise ValueError("Invalid ground-effect alignment")
    if not 1 <= image_index <= 24:
        raise ValueError("Invalid ground-effect input index")
    return (f"[shadowstage][{image_index}:v]overlay="
            f"x='({body_x})+{x_offset}+3*sin(t*2.1)':y={y}:"
            f"enable='{enable}':eval=frame:format=auto[contactstage];")
