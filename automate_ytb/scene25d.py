"""Versioned, deterministic multi-Z 2.5D scene composition.

This is a compositing stage for *independently authored RGBA layers*, not a
single-image Ken Burns effect and not a 3D geometry or segmentation engine.
All layers are safe local images, sorted by Z, shifted independently using
camera depth factors, optionally clipped with validated grayscale masks.
Pillow alpha_composite performs straight-alpha correct source-over blending.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re

from PIL import Image, ImageChops

VERSION = "scene25d-multiz-alpha-parallax-v1"
_ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")


@dataclass(frozen=True)
class Layer25D:
    name: str
    z: int
    image: Image.Image
    parallax_x: float = 0.0
    parallax_y: float = 0.0
    mask: Image.Image | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not _ID.fullmatch(self.name):
            raise ValueError("Invalid 2.5D layer ID")
        if type(self.z) is not int or not 0 <= self.z <= 100:
            raise ValueError("Invalid 2.5D layer depth")
        if (not isinstance(self.image, Image.Image)
                or self.image.mode != "RGBA"
                or not 16 <= self.image.width <= 1920
                or not 16 <= self.image.height <= 1920):
            raise ValueError("Invalid 2.5D RGBA layer")
        if (type(self.parallax_x) not in (int, float)
                or type(self.parallax_y) not in (int, float)
                or not math.isfinite(self.parallax_x)
                or not math.isfinite(self.parallax_y)
                or not -2.0 <= self.parallax_x <= 2.0
                or not -2.0 <= self.parallax_y <= 2.0):
            raise ValueError("Invalid 2.5D parallax")
        if (self.mask is not None and
                (not isinstance(self.mask, Image.Image)
                 or self.mask.mode != "L"
                 or self.mask.size != self.image.size)):
            raise ValueError("2.5D mask must be a matching 8-bit alpha image")


class Scene25D:
    """Composite up to sixteen full-stage layers, behind-to-front."""

    def __init__(self, size: tuple[int, int]) -> None:
        if (not isinstance(size, tuple) or len(size) != 2
                or any(type(v) is not int or not 16 <= v <= 1920 for v in size)):
            raise ValueError("Invalid 2.5D stage dimensions")
        self.size = size
        self._layers: list[Layer25D] = []

    def add(self, layer: Layer25D) -> None:
        if not isinstance(layer, Layer25D) or layer.image.size != self.size:
            raise ValueError("2.5D layer must match stage dimensions")
        if len(self._layers) >= 16:
            raise ValueError("Too many 2.5D layers")
        if any(other.name == layer.name or other.z == layer.z
               for other in self._layers):
            raise ValueError("Duplicate 2.5D layer name or Z")
        self._layers.append(layer)

    @property
    def layer_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in sorted(self._layers, key=lambda x: x.z))

    def quality_report(self, *, camera_x: float = 32.,
                       camera_y: float = 14.) -> dict:
        """Optional reusable quality evidence for any authored 2.5D scene.

        This reports low-detail and flat-parallax risks, without falsely
        certifying subjective cinematic quality or approving publication.
        """
        from .visual_quality25d import analyze_scene
        return analyze_scene(self, camera_x=camera_x, camera_y=camera_y)

    def render(self, *, camera_x: float = 0.0,
               camera_y: float = 0.0) -> Image.Image:
        if (type(camera_x) not in (int, float)
                or type(camera_y) not in (int, float)
                or not math.isfinite(camera_x) or not math.isfinite(camera_y)
                or abs(camera_x) > 180 or abs(camera_y) > 180):
            raise ValueError("Invalid bounded 2.5D camera displacement")
        if not self._layers:
            raise ValueError("Cannot render an empty 2.5D scene")
        result = Image.new("RGBA", self.size)
        for layer in sorted(self._layers, key=lambda x: x.z):
            source = layer.image
            if layer.mask is not None:
                source = source.copy()
                source.putalpha(ImageChops.multiply(
                    source.getchannel("A"), layer.mask))
            dx = round(camera_x * layer.parallax_x)
            dy = round(camera_y * layer.parallax_y)
            result.alpha_composite(source, (dx, dy))
        return result
