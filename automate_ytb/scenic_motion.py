"""Original biomes gain a distinct animated atmosphere layer.

Deterministic illustration of context-aware water glints, meadow petals,
village chimney smoke and forest motes. Everything is drawn with Pillow
in a transparent plate; only a reviewed FFmpeg overlay animates that plate.
There are no downloads, licensed stock images or unbounded filter inputs.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

SCENIC_MOTION_VERSION = "authored-biome-scenery-v1"
BIOMES = frozenset({"river", "village", "meadow", "forest"})
WEATHERS = frozenset({"day", "night", "wind", "rain", "storm", "cloudy"})


def draw_scenic_motion(destination: Path, *, landscape: str,
                       weather: str, seed: str) -> None:
    """Render a scene-locked transparent atmosphere plate at 1280x720.

    Leave the left-side original character and its speech gestures unobscured.
    Site and weather are known enums from the authored story director.
    """
    if landscape not in BIOMES or weather not in WEATHERS:
        raise ValueError("Unsupported original scenic motion")
    if not isinstance(seed, str) or len(seed) > 200_000:
        raise ValueError("Invalid original scene identity")
    rng = Random(int(hashlib.sha256(
        f"{landscape}|{weather}|{seed}".encode("utf-8")
    ).hexdigest()[:16], 16))
    image = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    night = weather == "night"
    muted = weather in {"rain", "storm", "cloudy"}
    if landscape == "river":
        # Glints and nested arcs sit solely over the actual water region.
        color = (142, 202, 219, 120) if night else (
            (225, 225, 230, 105) if muted else (246, 241, 204, 190))
        for _ in range(34):
            x = rng.randrange(775, 1216)
            y = rng.randrange(630, 699)
            w = rng.randrange(13, 43)
            draw.arc((x, y, x+w, y+11), 15, 160, fill=color, width=2)
            if rng.randrange(3) == 0:
                draw.line((x+4, y+11, x+w-3, y+11),
                          fill=color[:3]+(max(45, color[3]//2),), width=2)
    elif landscape == "village":
        # Light translucent chimney puffs float above the distant roofs.
        smoke = (158, 174, 197, 93) if night else (
            (179, 188, 207, 76) if muted else (246, 239, 215, 108))
        for cx, cy in ((743, 435), (1030, 414), (1196, 442)):
            for i in range(6):
                drift = rng.randint(-13, 13) + i*4
                r = 10 + i*3
                y = cy - i*21
                draw.ellipse((cx+drift-r, y-r//2,
                              cx+drift+r, y+r//2),
                             fill=smoke[:3]+(max(12, smoke[3]-i*12),))
    elif landscape == "meadow":
        petals = (
            ((168, 150, 204, 172), (225, 197, 147, 169))
            if night else
            ((247, 229, 181, 191), (243, 183, 193, 188),
             (206, 179, 242, 182)))
        for _ in range(46):
            x = rng.randrange(672, 1235)
            y = rng.randrange(367, 661)
            r = rng.randrange(3, 8)
            color = rng.choice(petals)
            draw.ellipse((x-r, y-r//2, x+r, y+r//2), fill=color)
            draw.line((x, y+2, x+r+3, y+r+3),
                      fill=color[:3]+(max(40, color[3]//2),), width=1)
    else:
        # Small falling leaves by day, cool blue firefly motes by night.
        for _ in range(42):
            x = rng.randrange(681, 1250)
            y = rng.randrange(245, 651)
            r = rng.randrange(3, 8)
            if night:
                color = rng.choice(((178, 219, 196, 186),
                                    (165, 207, 225, 165)))
                draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
            else:
                color = rng.choice(((232, 191, 112, 182),
                                    (182, 213, 126, 165),
                                    (245, 220, 163, 174)))
                draw.ellipse((x-r, y-r//2, x+r, y+r//2), fill=color)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG")


def overlay_scenic_motion(*, graph: str, label: str, names: list[str],
                          scene_index: int, weather: str
                          ) -> tuple[str, str, list[str]]:
    """Insert an independent biome animation before camera and foreground.

    FFmpeg expressions consist only of trusted constants, not script text.
    Each scene alternates parallax direction to avoid mechanical looping.
    """
    if not isinstance(graph, str) or not graph or not isinstance(label, str) or not label:
        raise ValueError("Invalid FFmpeg scene graph")
    if not isinstance(names, list) or "scenic_motion" in names:
        raise ValueError("Scenic motion already registered")
    if not isinstance(scene_index, int) or isinstance(scene_index, bool) or not 1 <= scene_index <= 1200:
        raise ValueError("Invalid scene index")
    if weather not in WEATHERS:
        raise ValueError("Invalid scenic weather")
    index = len(names)
    sign = 1 if scene_index % 2 else -1
    amplitude = 17 if weather == "wind" else 10 if weather in {"storm", "rain"} else 7
    vertical = 4 if weather == "wind" else 2
    suffix = (f";[{label}][{index}:v]overlay="
              f"x='{sign}*{amplitude}*sin(t*0.63)':"
              f"y='{vertical}*sin(t*0.47)':eval=frame:format=auto[biomemotion]")
    return graph + suffix, "biomemotion", names + ["scenic_motion"]
