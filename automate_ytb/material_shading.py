"""Original stylized material shading for transparent animal sprite plates.

Shape-aware alpha-clipped light, cool occlusion, delicate edge rim light,
and restrained specular falloff give the existing flat sprites more volume
without licensed textures, neural generators, ray tracing or GPU hardware.

The lighting is baked into every authored pose before PNG encoding, so the
approved still and the moving FFmpeg character share identical materials.
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageFilter
import hashlib
import random

MATERIAL_VERSION = "storybook-materials-v2-microtexture"
PALETTES = {
    "fox": ((255, 217, 156), (75, 47, 75)),
    "rabbit": ((255, 252, 247), (77, 69, 117)),
    "cat": ((165, 231, 246), (34, 67, 97)),
    "owl": ((247, 211, 255), (68, 44, 102)),
}
PARTS = {"body", "wing", "tail", "leg", "ear"}
SIZES = {
    "body": {(350, 440), (322, 430)},
    "wing": {(164, 212)},
    "tail": {(230, 240)},
    "leg": {(100, 125)},
    "ear": {(150, 240)},
}


def _gradient(size: tuple[int, int], *, vertical: bool, low: int,
              high: int) -> Image.Image:
    """Generate an 8-bit intensity ramp; no network or image model."""
    w, h = size
    ramp = Image.new("L", size)
    d = ImageDraw.Draw(ramp)
    span = h if vertical else w
    for value in range(span):
        fraction = value / max(1, span - 1)
        intensity = round(low + (high - low) * fraction)
        if vertical:
            d.line((0, value, w, value), fill=intensity)
        else:
            d.line((value, 0, value, h), fill=intensity)
    return ramp


def _tint(sprite: Image.Image, color: tuple[int, int, int],
          strength: Image.Image) -> None:
    layer = Image.new("RGBA", sprite.size, (*color, 0))
    layer.putalpha(strength)
    sprite.alpha_composite(layer)


def shade_sprite(sprite: Image.Image, *, kind: str, part: str) -> None:
    """Shade an existing original animal plate in place, preserving its alpha.

    The source silhouette is the hard clipping mask: neither blur nor
    highlighted edge may create an opaque pixel outside the original sprite.
    """
    if kind not in PALETTES or part not in PARTS:
        raise ValueError("Unknown original sprite material")
    if sprite.mode != "RGBA" or sprite.size not in SIZES[part]:
        raise ValueError("Unexpected RGBA sprite size")
    if kind != "owl" and part == "wing":
        raise ValueError("Only the original owl uses wing materials")
    if kind == "owl" and part in {"leg", "ear", "tail"}:
        raise ValueError("Invalid original owl part")
    alpha = sprite.getchannel("A")
    if alpha.getbbox() is None:
        return
    warm, cool = PALETTES[kind]
    w, h = sprite.size

    # Gradual cool occlusion from the lower-right area: darkest on the
    # belly and foot undersides, leaving the forehead and eye glints clear.
    xshade = _gradient((w, h), vertical=False, low=9, high=65)
    yshade = _gradient((w, h), vertical=True, low=0, high=47)
    shadow = ImageChops.lighter(xshade, yshade)
    if part == "body":
        shadow = shadow.point(lambda a: round(a * 0.82))
    shadow = ImageChops.multiply(shadow, alpha)
    _tint(sprite, cool, shadow)

    # Directional soft bounced light, painted broadly rather than as a flat
    # high-contrast stripe. Shoulder/forehead retain their original marks.
    xlight = _gradient((w, h), vertical=False, low=57, high=3)
    ylight = _gradient((w, h), vertical=True, low=44, high=6)
    illumination = ImageChops.lighter(xlight, ylight)
    illumination = illumination.point(lambda a: min(55, round(a * .92)))
    _tint(sprite, warm, ImageChops.multiply(illumination, alpha))

    # Beveled left/top contour and subtle opposite-side occlusion.
    # Offset creates a one-sided silhouette difference; clipping after blur
    # guarantees transparency outside even for fur/wing feather tips.
    rim = ImageChops.subtract(alpha, ImageChops.offset(alpha, 4, 3))
    rim = rim.filter(ImageFilter.GaussianBlur(2.8))
    rim = rim.point(lambda a: min(74, round(a * .58)))
    _tint(sprite, warm, ImageChops.multiply(rim, alpha))
    shade_rim = ImageChops.subtract(alpha, ImageChops.offset(alpha, -4, -3))
    shade_rim = shade_rim.filter(ImageFilter.GaussianBlur(3.3))
    shade_rim = shade_rim.point(lambda a: min(53, round(a * .40)))
    _tint(sprite, cool, ImageChops.multiply(shade_rim, alpha))

    # A wide elliptical light wrap gives the torso and wing a small sense
    # of curvature. Centered below the eyes, and never applied to mouth-only
    # overlays: expression layers stay crisp and consistent.
    if part in {"body", "wing", "tail"}:
        spot = Image.new("L", sprite.size)
        d = ImageDraw.Draw(spot)
        bounds = ((round(w*.10), round(h*.53), round(w*.53), round(h*.91))
                  if part == "body" else
                  (round(w*.11), round(h*.23), round(w*.65), round(h*.80)))
        d.ellipse(bounds, fill=100)
        spot = spot.filter(ImageFilter.GaussianBlur(max(5,round(min(w,h)*.085))))
        spot = spot.point(lambda a: round(a*.41))
        _tint(sprite, warm, ImageChops.multiply(spot, alpha))
    # Fine-scale fur / feather engraving: deterministic, sparse, and clipped
    # to the exact original silhouette. These tiny directional marks create
    # surface detail at 720p without a model, external texture or GPU.
    if part in {"body", "wing", "tail", "ear"}:
        salt = f"{kind}:{part}:{w}x{h}".encode("ascii")
        rng = random.Random(int.from_bytes(hashlib.sha256(salt).digest()[:8], "big"))
        grain = Image.new("L", sprite.size)
        brush = ImageDraw.Draw(grain)
        count = {"body": 650, "wing": 240, "tail": 190, "ear": 85}[part]
        for _ in range(count):
            gx = rng.randrange(3, w - 3)
            gy = rng.randrange(3, h - 3)
            length = rng.randint(2, 6)
            brush.line((gx, gy, gx + (1 if part == "wing" else -1),
                        min(h - 1, gy + length)), fill=rng.randint(30, 75), width=1)
        # Restrict detail to visibly opaque interior; protect antialias fringe.
        interior = alpha.point(lambda a: 255 if a >= 210 else 0)
        interior = interior.filter(ImageFilter.MinFilter(3))
        grain = ImageChops.multiply(grain, interior)
        _tint(sprite, warm, grain)
    # Alpha compositing colored light against antialiased boundaries can
    # increase partially covered pixel opacity. Restore exact source alpha
    # so blinks, pupils, feathers and limb edges never change silhouette.
    sprite.putalpha(alpha)
