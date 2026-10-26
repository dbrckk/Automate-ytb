"""Subpixel-quality original character painting, with bounded CPU-only cost.

Draw source geometry at 2x its delivery resolution, then downsample by
Pillow's Lanczos filter. This antialiases arcs, eyes, fine outlines, and
rotated appendage silhouettes before their regular shading/detail passes.
The original 720p composition coordinates and animation paths never change.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

SPRITE_RENDER_VERSION = "original-sprite-2x-lanczos-v1"
RENDER_SCALE = 2
_ALLOWED = frozenset({"ellipse", "arc", "line", "polygon",
                      "rounded_rectangle", "rectangle", "pieslice"})


class ScaledBrush:
    """Restricted Pillow drawing facade for trusted authored sprite shapes."""

    def __init__(self, canvas: Image.Image, factor: int):
        if canvas.mode != "RGBA" or factor != RENDER_SCALE:
            raise ValueError("Invalid supersampled RGBA artwork")
        self._draw = ImageDraw.Draw(canvas)
        self._factor = factor

    def _xy(self, values):
        # Pillow accepts a flat 4-tuple or a sequence of point pairs.
        if not isinstance(values, (tuple, list)) or not values:
            raise ValueError("Expected trusted original sprite coordinates")
        if isinstance(values[0], (tuple, list)):
            return [(round(x*self._factor), round(y*self._factor))
                    for x,y in values]
        return tuple(round(v*self._factor) for v in values)

    def __getattr__(self, method):
        if method not in _ALLOWED:
            raise AttributeError(method)
        draw_method = getattr(self._draw, method)

        def draw(xy, *args, **kwargs):
            params = kwargs.copy()
            for attribute in ("width", "radius"):
                if attribute in params:
                    params[attribute] = round(params[attribute]*self._factor)
            # The original scripts use a positional radius nowhere, but
            # Pillow arc angles and line paths can be positional and remain
            # unchanged by design.
            return draw_method(self._xy(xy), *args, **params)
        return draw


def sprite_canvas(size: tuple[int, int]) -> tuple[Image.Image, ScaledBrush]:
    if (not isinstance(size, tuple) or len(size) != 2
            or any(not isinstance(n, int) or isinstance(n, bool) or
                   not 1 <= n <= 1024 for n in size)):
        raise ValueError("Invalid bounded original sprite dimensions")
    image = Image.new("RGBA",
                      (size[0]*RENDER_SCALE, size[1]*RENDER_SCALE),
                      (0, 0, 0, 0))
    return image, ScaledBrush(image, RENDER_SCALE)


def resolve_sprite(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Downsample authored contours before material grading or face accents."""
    if (image.mode != "RGBA" or image.size !=
            (size[0]*RENDER_SCALE, size[1]*RENDER_SCALE)):
        raise ValueError("Unexpected supersampled sprite dimensions")
    return image.resize(size, Image.Resampling.LANCZOS)
