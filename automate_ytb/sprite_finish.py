"""Procedural studio shading for original 2D character sprites.

Fast Pillow operations only. Preserve the exact original alpha silhouette,
ink contours, eye pose and authored colors while adding a soft directional
light gradient, a faint diffuse face/torso sheen and a subtle lit-side rim.
No downloaded textures, third-party images or 3D rendering are used.
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter

FINISH_VERSION = "original-sprite-material-v1"


def finish_sprite(sprite: Image.Image) -> Image.Image:
    """Give a static RGBA actor plate gentle volumetric-looking light.

    This is strictly *painted 2D* shading: no normal-map or physically based
    lighting claim. No change to pixel alpha or to the sprite geometry.
    """
    if sprite.mode != "RGBA" or not 32 <= sprite.width <= 2048 or not 32 <= sprite.height <= 2048:
        raise ValueError("Expected bounded original RGBA actor sprite")
    w, h = sprite.size
    alpha = sprite.getchannel("A")
    rgb = sprite.convert("RGB")

    # Warm key from upper-left and a slightly darker right-hand contour.
    # Multiply is implemented in Pillow C rather than Python pixel loops.
    gradient = Image.new("RGB", (w, h))
    brush = ImageDraw.Draw(gradient)
    for x in range(w):
        falloff = x / max(1, w - 1)
        shade = round(254 - 28 * (falloff ** 1.35))
        brush.line((x, 0, x, h), fill=(shade, min(255, shade + 1), min(255, shade + 4)))
    shaded = ImageChops.multiply(rgb, gradient)

    # Broad, very low opacity reflected light on the rounded original form.
    soft = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(soft)
    draw.ellipse((round(w * .03), round(h * .08),
                  round(w * .73), round(h * .74)), fill=54)
    soft = soft.filter(ImageFilter.GaussianBlur(max(5, round(w * .07))))
    soft = ImageChops.multiply(soft, alpha)
    warm = Image.new("RGB", (w, h), (255, 237, 206))
    shaded = Image.composite(warm, shaded, soft)

    # An extremely narrow painterly rim on the key-light side. Avoid bright
    # outlines on the dark side or on transparency outside the silhouette.
    edge = ImageChops.subtract(alpha, alpha.filter(ImageFilter.MinFilter(5)))
    left_mask = Image.new("L", (w, h))
    left_draw = ImageDraw.Draw(left_mask)
    for x in range(w):
        left_draw.line((x, 0, x, h), fill=round(65 * (1 - x / max(1, w - 1))))
    rim = ImageChops.multiply(edge, left_mask)
    shaded = Image.composite(Image.new("RGB", (w, h), (255, 226, 184)), shaded, rim)

    shaded.putalpha(alpha)
    return shaded
