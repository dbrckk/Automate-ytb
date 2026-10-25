"""Original deterministic atmospheric illumination plates for 2D story scenes.

Lighting lives in its own RGBA layer, independently composited over the
approved image and the real FFmpeg render. Subtle day/night color and
point-light halos are synthetic illustrations, not 3D ray tracing.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

LIGHT_VERSION = "storybook-lighting-v1"


def draw_lighting(path: Path, *, weather: str, landscape: str, seed: str) -> None:
    if weather not in {"day", "night", "cloudy", "rain", "wind", "storm"}:
        raise ValueError("Unsupported authored weather")
    if landscape not in {"forest", "river", "village", "meadow"}:
        raise ValueError("Unsupported authored location")
    if not isinstance(seed, str) or len(seed) > 200000:
        raise ValueError("Unsafe light plate seed")
    digest = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16)
    plate = Image.new("RGBA", (1280, 720))
    spots = Image.new("RGBA", (1280, 720))
    light = ImageDraw.Draw(spots, "RGBA")
    night = weather == "night"
    overcast = weather in {"cloudy", "rain", "storm"}
    if night:
        sources = [(970, 154, 255, 224, 177, 23),
                   (930, 525, 248, 171, 100, 15)]
        if landscape == "village":
            sources += [(746, 546, 255, 187, 92, 22),
                        (1024, 527, 255, 193, 105, 18)]
    elif overcast:
        sources = [(960, 170, 164, 193, 218, 14)]
    else:
        sources = [(969, 175, 255, 226, 161, 22),
                   (1020, 440, 252, 217, 143, 8)]
    for x, y, r, g, b, alpha in sources:
        x += (digest % 11) - 5
        # Soft elliptical atmospherics. Keep alpha faint enough that
        # silhouettes, pupils, subtitles and props remain legible.
        light.ellipse((x-220,y-155,x+220,y+155), fill=(r,g,b,alpha))
        light.ellipse((x-120,y-110,x+120,y+110),
                      fill=(r,g,b,max(1,alpha//3)))
    spots = spots.filter(ImageFilter.GaussianBlur(85))
    plate = Image.alpha_composite(plate, spots)
    path.parent.mkdir(parents=True, exist_ok=True)
    plate.save(path, format="PNG")


def overlay_lighting(*, graph: str, label: str,
                     names: list[str]) -> tuple[str, str, list[str]]:
    """Place lighting after foreground, before final camera crop."""
    if "lighting" in names:
        raise ValueError("Lighting already composited")
    if not isinstance(label, str) or not label or not isinstance(graph, str):
        raise ValueError("Invalid FFmpeg graph")
    index = len(names)
    new_label = "litframe"
    graph += (f";[{label}][{index}:v]overlay=x=0:y=0:"
              f"eval=frame:format=auto[{new_label}]")
    return graph, new_label, names + ["lighting"]
