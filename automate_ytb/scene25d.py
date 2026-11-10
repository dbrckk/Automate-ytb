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
from .surface25d import MATERIALS, relight_surface
from .lightfield25d import Light25D, illuminate
from .optical_motion25d import translate_subpixel

VERSION = "scene25d-multiz-material-depth-relight-p523-subpixel-v3"
_ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")


@dataclass(frozen=True)
class Layer25D:
    name: str
    z: int
    image: Image.Image
    parallax_x: float = 0.0
    parallax_y: float = 0.0
    mask: Image.Image | None = None
    material: str = "none"

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
        if not isinstance(self.material,str) or self.material not in MATERIALS:
            raise ValueError("Unknown authored 2.5D material")


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
        """Audit original authored 2.5D materials and real scene parallax.

        Diagnostic metadata only; never certifies aesthetics or publication.
        """
        from .visual_quality25d import analyze_scene
        return analyze_scene(self,camera_x=camera_x,camera_y=camera_y)

    def render(self, *, camera_x: float = 0.0,
               camera_y: float = 0.0,
               light: Light25D | None = None) -> Image.Image:
        if (type(camera_x) not in (int, float)
                or type(camera_y) not in (int, float)
                or not math.isfinite(camera_x) or not math.isfinite(camera_y)
                or abs(camera_x) > 180 or abs(camera_y) > 180):
            raise ValueError("Invalid bounded 2.5D camera displacement")
        if light is not None and not isinstance(light, Light25D):
            raise ValueError("Expected an authored 2.5D light field")
        if not self._layers:
            raise ValueError("Cannot render an empty 2.5D scene")
        result = Image.new("RGBA", self.size)
        for layer in sorted(self._layers, key=lambda x: x.z):
            source = relight_surface(layer.image,layer.material)
            if layer.mask is not None:
                source = source.copy()
                source.putalpha(ImageChops.multiply(
                    source.getchannel("A"), layer.mask))
            # Preserve the authentic subpixel parallax motion of EACH Z
            # plane instead of snapping coordinates to integer pixels and
            # making background clouds/hair/jets judder at video frame rate.
            dx = camera_x * layer.parallax_x
            dy = camera_y * layer.parallax_y
            if light is not None:
                # The original low-frequency light field remains quantized
                # for cache reuse; geometry moves with genuine fractional
                # precision through premultiplied-alpha interpolation.
                source = illuminate(source, light, z=layer.z,
                                    shift_x=round(dx),shift_y=round(dy))
            if (abs(dx-round(dx))<1e-10 and
                    abs(dy-round(dy))<1e-10):
                # Exact historical fast path and pixel identity for common
                # zero/integer camera motion.
                result.alpha_composite(source,(round(dx),round(dy)))
            else:
                result.alpha_composite(translate_subpixel(source,dx,dy))
        return result
