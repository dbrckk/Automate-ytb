"""Tiny original, deterministic life details for storybook landscapes.

These RGBA layers introduce context-specific motion without external assets,
copyrighted footage, paid inference, or unverified narrative events. Distant
clouds/birds and nearby fireflies/petals/reflections drift independently.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

LIVING_VERSION = "living-biomes-v1-independent-two-plane-motion"
LANDSCAPES = ("forest", "river", "village", "meadow")
WEATHERS = ("day", "night", "cloudy", "wind", "rain", "storm")
SIZE = (1280, 720)
SCALE = 2


def _canvas():
    return Image.new("RGBA", (SIZE[0] * SCALE, SIZE[1] * SCALE), (0, 0, 0, 0))


def _ellipse(draw: ImageDraw.ImageDraw, bounds: tuple[int, int, int, int], color):
    draw.ellipse(tuple(int(v * SCALE) for v in bounds), fill=color)


def _line(draw: ImageDraw.ImageDraw, points, color, width=2):
    draw.line([(int(x * SCALE), int(y * SCALE)) for x, y in points],
              fill=color, width=width * SCALE, joint="curve")


def _polygon(draw: ImageDraw.ImageDraw, points, color):
    draw.polygon([(int(x * SCALE), int(y * SCALE)) for x, y in points], fill=color)


def _sky_activity(draw: ImageDraw.ImageDraw, rng: Random, weather: str):
    dark = weather in ("night", "storm")
    cloudy = weather in ("rain", "cloudy", "storm")
    cloud_color = (198, 211, 224, 38) if cloudy else (247, 236, 212, 26)
    for n in range(3):
        x = rng.randint(760, 1160)
        y = rng.randint(115, 305)
        w = rng.randint(38, 90)
        for dx, dy, s in ((-22, 5, 0.65), (0, -8, 1.0), (26, 6, 0.75)):
            _ellipse(draw, (x + dx - int(w * s), y + dy - 12,
                            x + dx + int(w * s), y + dy + 21), cloud_color)
    if dark:
        # Small slow-moving lights in the top-right atmosphere, safely
        # away from the animated character and from the subtitle strip.
        for _ in range(12):
            x, y = rng.randint(720, 1240), rng.randint(76, 330)
            r = rng.randint(1, 3)
            _ellipse(draw, (x-r, y-r, x+r, y+r), (242, 224, 173, 135))
    elif weather not in ("rain", "storm"):
        # Bird-like distant silhouette strokes: incidental original scenery.
        for _ in range(4):
            x, y = rng.randint(765, 1220), rng.randint(170, 365)
            r = rng.randint(7, 14)
            ink = (51, 84, 99, 125)
            _line(draw, [(x-r,y+1),(x-r//2,y-2),(x,y+2)], ink, 2)
            _line(draw, [(x,y+2),(x+r//2,y-2),(x+r,y+1)], ink, 2)


def _near_activity(draw: ImageDraw.ImageDraw, rng: Random, *,
                   landscape: str, weather: str):
    night = weather == "night"
    if landscape == "river":
        for _ in range(15):
            x, y = rng.randint(790, 1222), rng.randint(610, 682)
            length = rng.randint(8, 24)
            color = (168, 228, 235, 170) if not night else (121, 179, 202, 125)
            _line(draw, [(x, y), (x + length, y - rng.randint(0, 3))], color, 2)
        for _ in range(3):
            x, y = rng.randint(835, 1165), rng.randint(455, 550)
            _line(draw, [(x-16, y), (x+15, y)], (55, 82, 107, 160), 2)
            _ellipse(draw, (x-17,y-6,x-3,y+5),(161,211,220,133))
            _ellipse(draw, (x+3,y-6,x+17,y+5),(161,211,220,133))
    elif landscape == "meadow":
        for _ in range(9):
            x, y = rng.randint(735, 1240), rng.randint(385, 598)
            a = rng.choice([(241, 172, 124, 170), (211, 175, 233, 160),
                            (246, 226, 167, 172)])
            _ellipse(draw, (x-13, y-10, x-2, y+4), a)
            _ellipse(draw, (x+2, y-10, x+13, y+4), a)
            _ellipse(draw, (x-8, y+1, x-2, y+9), a)
            _ellipse(draw, (x+2, y+1, x+8, y+9), a)
            _line(draw, [(x,y-4),(x,y+8)],(87,72,82,180), 2)
    elif landscape == "forest":
        for _ in range(17):
            x, y = rng.randint(725, 1240), rng.randint(340, 607)
            leaf = rng.choice([(205, 159, 85, 175), (105, 159, 86, 174),
                               (228, 183, 112, 172)])
            w = rng.randint(4, 11)
            _polygon(draw, ((x-w,y),(x+2,y-w),(x+w,y),(x-2,y+w)),leaf)
            _line(draw, [(x-2,y+w-1),(x+w//2,y-w//2)],
                  (75, 89, 56, 120),1)
    else:  # village
        for _ in range(13):
            x, y = rng.randint(720, 1214), rng.randint(345, 580)
            if night:
                # Tiny distant lantern/firefly glows; not an opaque overlay.
                _ellipse(draw,(x-10,y-10,x+10,y+10),(247,198,99,25))
                _ellipse(draw,(x-3,y-3,x+3,y+3),(255,222,125,155))
            else:
                _ellipse(draw,(x-3,y-3,x+3,y+3),(230,216,174,145))
    if night and landscape in {"forest", "meadow"}:
        for _ in range(15):
            x, y = rng.randint(760, 1220), rng.randint(320, 590)
            _ellipse(draw, (x-7,y-7,x+7,y+7),(228,211,130,21))
            _ellipse(draw, (x-2,y-2,x+2,y+2),(249,233,157,156))


def draw_ambient_layers(far: Path, near: Path, *, landscape: str,
                        weather: str, seed: str) -> None:
    """Create two different transparent, reproducible 1280x720 plates."""
    if landscape not in LANDSCAPES or weather not in WEATHERS:
        raise ValueError("Unsupported storybook location or weather")
    if not isinstance(seed, str) or not 1 <= len(seed) <= 200000:
        raise ValueError("Invalid original scene key")
    entropy = hashlib.sha256((seed + "|" + landscape + "|" + weather).encode("utf-8")).digest()
    rng = Random(int.from_bytes(entropy[:8], "big"))
    sky = _canvas()
    close = _canvas()
    _sky_activity(ImageDraw.Draw(sky), rng, weather)
    _near_activity(ImageDraw.Draw(close), rng, landscape=landscape, weather=weather)
    resample = Image.Resampling.LANCZOS
    for destination, picture in ((far, sky), (near, close)):
        destination.parent.mkdir(parents=True, exist_ok=True)
        picture.resize(SIZE, resample).save(destination, format="PNG", optimize=True)


def append_ambient_overlays(*, graph: str, label: str,
                            names: list[str], weather: str
                            ) -> tuple[str, str, list[str]]:
    """Move two scene-anchored planes separately inside trusted FFmpeg graphs.

    All motion expressions are static, reviewed text; narration and user
    prompts never enter the filter expression.
    """
    if weather not in WEATHERS or not isinstance(label, str) or not label:
        raise ValueError("Invalid animation weather or stage")
    if not isinstance(graph, str) or not isinstance(names, list):
        raise ValueError("Invalid ambient overlay inputs")
    if "ambient_far" in names or "ambient_near" in names:
        raise ValueError("Ambient plane already appended")
    first = len(names)
    second = first + 1
    speed = 1.7 if weather == "wind" else 1.0
    far_x = f"6*sin(t*{0.27 * speed:.3f})"
    far_y = "2*sin(t*0.18)"
    near_x = f"15*sin(t*{0.65 * speed:.3f})"
    near_y = f"6*sin(t*{0.47 * speed:.3f})"
    graph += (f";[{label}][{first}:v]overlay=x='{far_x}':y='{far_y}':"
              "eval=frame:format=auto[ambientfar]"
              f";[ambientfar][{second}:v]overlay=x='{near_x}':y='{near_y}':"
              "eval=frame:format=auto[ambientnear]")
    return graph, "ambientnear", names + ["ambient_far", "ambient_near"]
