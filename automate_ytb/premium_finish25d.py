"""Low-cost reusable optical finishing for original layered 2.5D scenes.

Designed for the shared vector asset cache: never blur a full video frame on
every 30-fps tick. The emission plate is computed once per source layer.
Neither source geometry nor rights provenance changes. Original narration,
live camera/actor interpolation, subtitles and codec pipeline remain intact.
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter, ImageOps

VERSION = "original-cached-layer-optical-bloom-v1"


def finish_vector_layer(image: Image.Image, depth: int) -> Image.Image:
    """Add spectral edge glow around bright illustrated subject details.

    A dark sky or numeric infographic must not be illuminated as a giant
    block; cache-only light is reserved for authored hero/detail layers.
    """
    if not isinstance(image, Image.Image) or image.width < 32 or image.height < 32:
        raise ValueError("Invalid source illustration for premium finishing")
    if type(depth) is not int or not 0 <= depth <= 100:
        raise ValueError("Invalid authored artwork depth")
    art=image.convert("RGBA")
    if depth < 40:
        return art
    alpha=art.getchannel("A")
    # Only bright, actually present pixels can emit. Low-contrast and
    # transparent geometry never become an invented new object.
    value=ImageOps.grayscale(art.convert("RGB"))
    emitted=value.point(lambda v: min(214,max(0,round((v-105)*1.47))))
    emitted=ImageChops.multiply(emitted,alpha)
    if emitted.getbbox() is None:
        return art
    # Downsampled Gaussian soft light is produced once at load time.
    quarter=(max(24,art.width//4),max(24,art.height//4))
    # Preserve the actual authored colors instead of a uniform fake neon tint.
    luminous=art.copy()
    luminous.putalpha(emitted)
    luminous=luminous.resize(quarter,Image.Resampling.BILINEAR)
    luminous=luminous.filter(ImageFilter.GaussianBlur(radius=4.5))
    luminous=luminous.resize(art.size,Image.Resampling.BILINEAR)
    glow_alpha=luminous.getchannel("A").point(
        lambda v: min(116,round(v*.78)))
    luminous.putalpha(glow_alpha)
    return Image.alpha_composite(luminous,art)


__all__ = ("finish_vector_layer","VERSION")
