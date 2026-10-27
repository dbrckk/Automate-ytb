"""Original small kinetic accents for explicitly directed animal movement.

Draws subtle dust/mist/splash plates in Pillow and animates their *placement*
with reviewed FFmpeg filter expressions. Only authored jump/run actions trigger
an accent. No particle simulation, downloads or external animation models.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFilter

KINETIC_VERSION = "original-motion-accents-v1"
KINETIC_ACTIONS = frozenset(("jump", "run"))
WEATHERS = frozenset(("day", "night", "cloudy", "rain", "wind", "storm"))
LANDSCAPES = frozenset(("forest", "river", "meadow", "village"))
SIZE = (300, 110)


def draw_motion_accent(destination: Path, *, action: str, weather: str,
                       landscape: str, seed: str) -> None:
    """Produce an understated, transparent, original 300x110 contact effect."""
    if action not in KINETIC_ACTIONS or weather not in WEATHERS:
        raise ValueError("Unsupported kinetic action or weather")
    if landscape not in LANDSCAPES:
        raise ValueError("Unsupported landscape")
    if not isinstance(seed, str) or not 1 <= len(seed) <= 200000:
        raise ValueError("Invalid deterministic motion seed")
    rnd = Random(int.from_bytes(hashlib.sha256(
        seed.encode("utf-8")).digest()[:8], "big"))
    wet = landscape == "river" or weather in {"rain", "storm"}
    color = ((117, 184, 206) if wet else
             (140, 147, 162) if weather == "night" else
             (172, 151, 110))
    plate = Image.new("RGBA", (600, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(plate, "RGBA")
    anchors = (102, 500) if action == "jump" else (72, 157)
    for center in anchors:
        for i in range(11):
            x = center + rnd.randrange(-68, 69)
            y = 145 + rnd.randrange(-26, 29)
            rx = rnd.randrange(10, 32)
            ry = rnd.randrange(4, 15)
            opacity = rnd.randrange(33, 81)
            d.ellipse((x-rx,y-ry,x+rx,y+ry), fill=(*color, opacity))
        # Clear, small line accents keep the character's feet legible.
        if wet:
            for i in range(4):
                x = center + (i-2)*23 + rnd.randrange(-7, 8)
                h = rnd.randrange(12, 31)
                d.arc((x-10, 122-h, x+13, 160), 195, 340,
                      fill=(*color, 100), width=3)
        else:
            for i in range(4):
                x = center + rnd.randrange(-60, 60)
                y = rnd.randrange(109, 146)
                d.arc((x-24, y-12, x+30, y+12), 190, 341,
                      fill=(*color, 91), width=3)
    plate = plate.resize(SIZE, Image.Resampling.LANCZOS)
    plate = plate.filter(ImageFilter.GaussianBlur(1.0))
    destination.parent.mkdir(parents=True, exist_ok=True)
    plate.save(destination, "PNG", optimize=True)


def append_motion_accent(*, graph: str, label: str, names: list[str],
                         action: str, body_x: str,
                         ground_y: int) -> tuple[str, str, list[str]]:
    """Append a safe accent over actor feet, only for a specified jump/run.

    The PNG is transparent and softly blurred; the reviewed expressions
    attach takeoff/landing to the 1.75-second choreography cycle.
    """
    if action not in KINETIC_ACTIONS:
        return graph, label, names
    if "motion" in names:
        raise ValueError("Duplicate motion plate")
    if not isinstance(body_x, str) or not 1 <= len(body_x) <= 25000:
        raise ValueError("Invalid original actor trajectory")
    if any(c in body_x for c in ";[]'\"\\:\n\r"):
        raise ValueError("Unsafe actor trajectory")
    if not isinstance(ground_y, int) or isinstance(ground_y, bool) or not 80 <= ground_y <= 680:
        raise ValueError("Invalid grounded motion level")
    if not isinstance(label, str) or not label or not isinstance(graph, str):
        raise ValueError("Invalid image graph")
    input_index = len(names)
    if action == "run":
        graph += (
            f";[{label}][{input_index}:v]overlay="
            f"x='({body_x})+24-14*mod(t,0.55)':"
            f"y='{ground_y}-12-20*mod(t,0.55)':"
            "enable='between(mod(t,0.55),0.06,0.27)':"
            "eval=frame:format=auto[motiondone]"
        )
    else:
        # A takeoff puff just after the 0.18s crouch, then a distinct
        # landing puff after the authored descent ends at 1.39s.
        graph += (
            f";[{input_index}:v]split=2[motioneffectA][motioneffectB]"
            f";[{label}][motioneffectA]overlay="
            f"x='({body_x})+17-10*mod(t,1.75)':"
            f"y='{ground_y}-15-25*mod(t,1.75)':"
            "enable='between(mod(t,1.75),0.18,0.43)':"
            "eval=frame:format=auto[motionstart]"
            ";[motionstart][motioneffectB]overlay="
            f"x='({body_x})+19+12*mod(t,1.75)':"
            f"y='{ground_y}-40+8*mod(t,1.75)':"
            "enable='between(mod(t,1.75),1.39,1.65)':"
            "eval=frame:format=auto[motiondone]"
        )
    return graph, "motiondone", names + ["motion"]
