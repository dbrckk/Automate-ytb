"""Original, unobtrusive detail passes for the existing 2D animal sprites.

These translucent paint strokes sit on already-authored artwork; they are not
third-party textures, AI inference, physical fur or a skeletal face rig.
Drawn after eye/mouth variants so each pose keeps exactly the same accents.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

DETAIL_VERSION = "storybook-character-detail-v1"
KINDS = ("fox", "rabbit", "cat", "owl")


def finish_forest_face(sprite: Image.Image, *, kind: str) -> None:
    """Paint cheek tufts, warm rim accents and restrained fur linework."""
    if kind not in KINDS[:3]:
        raise ValueError("Unsupported forest face detail")
    if sprite.size != (350, 440) or sprite.mode != "RGBA":
        raise ValueError("Expected RGBA original animal sprite")
    accent = {
        "fox": (253, 210, 144),
        "rabbit": (255, 246, 247),
        "cat": (174, 227, 238),
    }[kind]
    pigment = Image.new("RGBA", sprite.size)
    d = ImageDraw.Draw(pigment)
    # Soft illumination follows the contour. Stay outside the eyes, nose,
    # mouth, scarf and separately overlaid speech/blink animation.
    d.arc((57, 167, 293, 324), 126, 170, fill=(*accent, 105), width=5)
    d.arc((57, 167, 293, 324), 9, 51, fill=(*accent, 80), width=4)
    d.ellipse((158, 139, 191, 155), fill=(*accent, 65))
    for x, direction in ((84, -1), (271, 1)):
        for step in range(3):
            y = 252 + step * 13
            d.line((x, y, x + direction * (13 + step * 3), y + 7),
                   fill=(*accent, 100 - step * 12), width=3)
    # A sparse row of belly fur strokes below the golden scarf.
    for x in (138, 158, 179, 201, 219):
        d.arc((x-8, 345, x+8, 364), 12, 156,
              fill=(*accent, 75), width=2)
    sprite.alpha_composite(pigment)


def finish_owl_feathers(sprite: Image.Image) -> None:
    """Add secondary plumage arcs and restrained cheek/forehead accents."""
    if sprite.size != (322, 430) or sprite.mode != "RGBA":
        raise ValueError("Expected RGBA original owl sprite")
    plate = Image.new("RGBA", sprite.size)
    d = ImageDraw.Draw(plate)
    for x in (113, 139, 165, 191, 217):
        d.arc((x-11, 338, x+11, 363), 8, 169,
              fill=(108, 76, 160, 95), width=3)
        d.line((x, 353, x-5, 360),
               fill=(243, 230, 255, 88), width=2)
    d.arc((42, 95, 278, 367), 128, 167,
          fill=(238, 197, 253, 80), width=5)
    d.arc((42, 95, 278, 367), 12, 51,
          fill=(238, 197, 253, 75), width=4)
    d.ellipse((154, 109, 170, 119), fill=(243, 216, 255, 85))
    sprite.alpha_composite(plate)
