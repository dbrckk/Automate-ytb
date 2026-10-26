"""Independent original cloth-tail illustration and reactive 2D motion.

Scarf fabric is its own sprite. Its motion follows the authored animal action
and the body's original FFmpeg coordinates, instead of duplicating a static
scarf polygon or importing a model/asset. Not a simulated cloth solver.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .choreography import body_position
from .director import ACTIONS

CLOTH_VERSION = "original-animated-scarf-v1"
SCARF_SIZE = (90, 100)
# Top-left relative to the character's full-body sprite on the 1280px stage.
ANCHORS = {"owl": (203, 298), "fox": (205, 301),
           "rabbit": (205, 301), "cat": (205, 301)}
TORSO_ORIGINS = {"owl": (204, 186), "fox": (180, 184),
                 "rabbit": (180, 184), "cat": (180, 184)}
SWAY = {
    "idle": (2, 1.1), "walk": (5, 2.3), "run": (11, 5.4),
    "jump": (14, 3.2), "fly": (13, 4.1), "talk": (2, 1.2),
    "surprise": (8, 4.2), "rest": (1, 0.7),
}


def draw_scarf_tail(path: Path, *, actor: str) -> None:
    """Draw a compact transparent fabric sprite matching the existing scarf."""
    if actor not in ANCHORS:
        raise ValueError("Unsupported original scarf character")
    im = Image.new("RGBA", SCARF_SIZE, (0, 0, 0, 0))
    brush = ImageDraw.Draw(im)
    gold = (248, 195, 79, 255) if actor == "owl" else (248, 190, 75, 255)
    shade = (202, 136, 49, 255)
    highlight = (255, 226, 135, 205)
    if actor == "owl":
        outline = [(31, 8), (72, 59), (51, 78), (4, 22)]
        fold = [(31, 13), (60, 62), (51, 69), (20, 25)]
    else:
        outline = [(40, 22), (78, 78), (55, 92), (6, 29)]
        fold = [(41, 30), (65, 78), (56, 82), (24, 37)]
    brush.polygon(outline, fill=gold)
    brush.line([outline[1], outline[2], outline[3]], fill=shade, width=3,
               joint="curve")
    brush.line(fold, fill=highlight, width=4, joint="curve")
    brush.line((outline[0], outline[3]), fill=shade, width=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="PNG", optimize=True)


def scarf_position(action: str, *, actor: str) -> tuple[str, str]:
    """Position cloth relative to the moving torso with damped follow-through."""
    if actor not in ANCHORS or action not in ACTIONS:
        raise ValueError("Unsupported scarf action or character")
    base_x, base_y = TORSO_ORIGINS[actor]
    torso_x, torso_y = body_position(action, x=base_x, y=base_y)
    anchor_x, anchor_y = ANCHORS[actor]
    amplitude, velocity = SWAY[action]
    # A slower phase-shifted sway suggests fabric lag relative to the body,
    # but remains continuous, limited and reproducible.
    return (
        f"({torso_x})+{anchor_x}+{amplitude}*sin(t*{velocity}-0.55)",
        f"({torso_y})+{anchor_y}+{max(1, amplitude // 3)}*sin(t*{velocity*.63:.3f}-0.75)",
    )


def append_scarf(*, graph: str, label: str, names: list[str],
                 x: str, y: str) -> tuple[str, str, list[str]]:
    """Attach a safe extra image after body/legs/props, before weather."""
    if not 1 <= len(label) <= 16 or not label.isalnum():
        raise ValueError("Invalid reviewed FFmpeg layer label")
    if "scarf_tail" in names or not 1 <= len(names) <= 20:
        raise ValueError("Invalid scarf input ordering")
    if not isinstance(x, str) or not isinstance(y, str) or not x or not y:
        raise ValueError("Invalid scarf pose")
    if any(char in x+y for char in ";[]'\\\"\n\r:"):
        raise ValueError("Unsafe scarf motion expression")
    next_label = "scarfcomposed"
    return (
        graph + f";[{label}][{len(names)}:v]overlay=x='{x}':y='{y}':"
                f"eval=frame:format=auto[{next_label}]",
        next_label,
        names + ["scarf_tail"],
    )
