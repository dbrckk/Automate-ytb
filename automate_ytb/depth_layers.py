"""Original foreground silhouette plates for lightweight pseudo-parallax.

The layer is independent from the static environment and original animal rig.
Its sway is a bounded FFmpeg overlay expression; no external assets/models.
"""
from __future__ import annotations

import hashlib
import random
from pathlib import Path
from PIL import Image, ImageDraw

DEPTH_VERSION = "original-foreground-parallax-v1"
BIOMES = ("forest", "river", "village", "meadow")


def draw_foreground(destination: Path, *, landscape: str, seed: str,
                    night: bool = False) -> None:
    if landscape not in BIOMES:
        raise ValueError("Invalid original foreground landscape")
    if not isinstance(seed, str) or len(seed) > 200_000:
        raise ValueError("Invalid deterministic scene identity")
    rng = random.Random(int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16))
    im = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dark = (21, 57, 58, 213) if night else (27, 83, 61, 199)
    light = (35, 86, 81, 175) if night else (49, 113, 78, 160)
    # Foreground strictly on the side edges and lower border. Leaves and
    # grasses lend depth without obscuring a centrally placed character.
    for side in ("left", "right"):
        for i in range(15):
            anchor_x = rng.randint(0, 70) if side == "left" else rng.randint(1210, 1278)
            base_y = rng.randint(535, 750)
            length = rng.randint(31, 107)
            bend = rng.randint(12, 35) * (1 if side == "left" else -1)
            d.line((anchor_x, base_y, anchor_x+bend, base_y-length),
                   fill=dark, width=rng.randint(3, 7))
            for offset in (0.32, 0.66):
                x = anchor_x + bend*offset
                y = base_y-length*offset
                rr = rng.randint(10, 23)
                d.ellipse((x-rr, y-rr//2, x+rr, y+rr//2),
                          fill=light if i%2 else dark)
    for i in range(30):
        x = rng.randint(0, 1279)
        if 130 < x < 650:
            continue
        y = rng.randint(690, 750)
        h = rng.randint(16, 52)
        d.line((x,y,x+rng.randint(-10,10),y-h), fill=light, width=3)
    if landscape == "river":
        for x,y in ((1085, 668), (1157, 646), (1232, 684)):
            d.line((x,y,x+6,y-120), fill=(67,91,59,220), width=9)
            d.ellipse((x-20,y-145,x+23,y-94), fill=(75,100,74,196))
    elif landscape == "village":
        for x,y in ((1130,676),(1235,642)):
            d.rectangle((x,y-75,x+9,y),fill=(87,67,57,225))
            d.ellipse((x-25,y-106,x+35,y-47),fill=dark)
    elif landscape == "meadow":
        for i in range(18):
            x=rng.choice((rng.randint(0,95),rng.randint(1100,1270)))
            y=rng.randint(580,710)
            d.ellipse((x-5,y-5,x+5,y+5),
                      fill=(223,187,124,230) if not night else (145,139,171,200))
    destination.parent.mkdir(parents=True, exist_ok=True)
    im.save(destination, format="PNG")


def overlay_foreground(*, graph: str, label: str, names: list[str],
                       scene_index: int, duration: float) -> tuple[str,str,list[str]]:
    """Append a side-edge parallax plate with mild horizontal and vertical sway."""
    if not isinstance(scene_index,int) or isinstance(scene_index,bool) or not 1 <= scene_index <= 1200:
        raise ValueError("Invalid scene index")
    if not isinstance(duration,(float,int)) or isinstance(duration,bool) or not 0 < duration <= 3600:
        raise ValueError("Invalid video duration")
    if "foreground" not in names:
        names = names + ["foreground"]
    idx=names.index("foreground")
    new_label="fgdone"
    if label == new_label:
        raise ValueError("Foreground label already used")
    sign=1 if scene_index%2 else -1
    # Frame-safe overlay: 1280x720 plate, moving at most 3px on screen.
    extra=(f";[{label}][{idx}:v]overlay="
           f"x='{sign}*2*sin(t*0.63)':y='2*sin(t*0.47)':"
           f"eval=frame:format=auto[{new_label}]")
    return graph+extra,new_label,names
