"""Species-specific original storybook faces: distinct shapes, not color swaps.

Painted in the native design coordinate system through the supersampled brush.
The underlying pupils, blinks, narration-driven mouth and material passes
remain fully independent across every animation frame and approved poster.
"""
from __future__ import annotations

FACE_ANATOMY_VERSION = "original-animal-anatomy-v1"

# Clean ivory, dark pigment and ear colors arrive from the original fixed
# palette; no source narration is interpreted as a drawing instruction.
def paint_anatomy_base(d, *, kind: str, fur: tuple, dark: tuple,
                       belly: tuple, ear: tuple) -> None:
    """Build the forehead, cheek and muzzle silhouette before eyes are inked."""
    if kind not in {"fox", "rabbit", "cat"}:
        raise ValueError("Unsupported original animal anatomy")
    if kind == "fox":
        # Distinct tapering white cheeks continue the fox's V-shaped snout.
        d.polygon([(55, 222), (76, 268), (114, 283),
                   (174, 327), (142, 303), (88, 293), (48, 258)],
                  fill=belly)
        d.polygon([(301, 222), (279, 268), (240, 283),
                   (178, 327), (212, 303), (268, 293), (307, 258)],
                  fill=belly)
        d.arc((84, 147, 157, 190), 193, 343, fill=dark, width=4)
        d.arc((196, 147, 269, 190), 197, 345, fill=dark, width=4)
        for x in (87, 260):
            d.polygon([(x-13, 257), (x+6, 253), (x+21, 273),
                       (x+3, 266)], fill=ear)
    elif kind == "rabbit":
        # Puffy, layered muzzle, softened cheek volume and shy brow accents.
        d.ellipse((68, 236, 139, 305), fill=fur)
        d.ellipse((215, 236, 282, 305), fill=fur)
        d.ellipse((124, 246, 182, 307), fill=belly)
        d.ellipse((176, 246, 235, 307), fill=belly)
        d.arc((84, 151, 151, 187), 195, 350, fill=dark, width=3)
        d.arc((201, 151, 268, 187), 192, 351, fill=dark, width=3)
        for x in (73, 274):
            d.arc((x-13, 253, x+16, 293), 95, 222,
                  fill=belly, width=5)
    else:
        # Angular feline face, expressive temple tufts and real tabby marks.
        d.polygon([(61, 221), (37, 257), (60, 267), (49, 286),
                   (116, 306), (132, 280)], fill=fur)
        d.polygon([(291, 221), (317, 257), (294, 267), (307, 286),
                   (238, 306), (224, 280)], fill=fur)
        d.ellipse((137, 254, 180, 297), fill=belly)
        d.ellipse((176, 254, 219, 297), fill=belly)
        for dx in (-37, 0, 37):
            x=178+dx
            d.polygon([(x-11, 128), (x+7, 136),
                       (x+3, 166), (x-6, 158)], fill=dark)
        for pts in (
            [(52, 218), (84, 227), (72, 236), (49, 231)],
            [(53, 247), (80, 249), (67, 260), (50, 258)],
            [(300, 218), (268, 227), (280, 236), (303, 231)],
            [(301, 247), (274, 249), (287, 260), (304, 258)],
        ):
            d.polygon(pts,fill=dark)


def paint_anatomy_accents(d, *, kind: str, dark: tuple, ear: tuple) -> None:
    """Species-specific finishing touches, kept away from blink/speech poses."""
    if kind not in {"fox", "rabbit", "cat"}:
        raise ValueError("Unsupported original animal anatomy")
    if kind == "fox":
        for x in (148, 157, 200, 209):
            d.ellipse((x-2, 276, x+2, 280), fill=dark)
        d.arc((169, 246, 189, 262), 193, 342,
              fill=(255, 226, 200, 255),width=2)
    elif kind == "rabbit":
        d.polygon([(173, 248), (190, 248), (182, 259)],
                  fill=ear)
        for x in (151, 160, 203, 212):
            d.ellipse((x-2, 273, x+2, 277), fill=dark)
        d.line([(182, 258), (182, 269)], fill=dark, width=2)
    else:
        d.polygon([(167, 249), (193, 249), (181, 264)],
                  fill=ear)
        for x in (142, 151, 209, 218):
            d.ellipse((x-2, 273, x+2, 277), fill=dark)
        d.line([(181, 264), (181, 278)], fill=dark, width=2)
