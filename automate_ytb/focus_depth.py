"""Static, editorial depth-of-field for original painted storybook scenes.

This is a stylised background separation, not a physical 3D lens simulation.
The environment plates are filtered once using Pillow before FFmpeg video
encoding; independently moving creatures, props, near foliage and captions
remain sharp. Only trusted camera-shot enums select the blur radii.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

FOCUS_VERSION = "storybook-optical-separation-v1"

# Base canvas: 1280x720. Wide shots must remain bitwise unchanged. Macro
# backgrounds receive a more noticeable blur after the existing crop/zoom.
# Keeping the processing offline per still image avoids per-frame gblur.
FOCUS_RADII = {
    "wide": 0.0,
    "medium": 1.2,
    "closeup": 3.6,
    "macro": 7.2,
    "low": 2.0,
    "shoulder": 2.8,
}
PLANES = {"background": 1.0, "ambient_far": 0.75}


def focus_radius(shot: str, *, plane: str = "background") -> float:
    """Return a bounded pixel radius from curated shot/layer combinations."""
    if not isinstance(shot, str) or shot not in FOCUS_RADII:
        raise ValueError("Unsupported focus shot")
    if not isinstance(plane, str) or plane not in PLANES:
        raise ValueError("Unsupported focus plane")
    return round(FOCUS_RADII[shot] * PLANES[plane], 2)


def soften_environment_plate(path: Path, *, shot: str,
                             plane: str = "background") -> bool:
    """Blur only an original static distant layer, never the actor sprites.

    Returns False for the lossless wide-shot no-op and True when processed.
    Paths refer exclusively to locally authored production temp files.
    """
    radius = focus_radius(shot, plane=plane)
    if radius == 0:
        return False
    with Image.open(path) as source:
        if source.size != (1280, 720) or source.mode not in ("RGB", "RGBA"):
            raise ValueError("Expected a native 1280x720 original RGBA/RGB plate")
        softened = source.filter(ImageFilter.GaussianBlur(radius))
    softened.save(path, "PNG")
    return True


def focus_metadata(shot: str) -> dict:
    """Serializable audit record for optical separation of still art."""
    radius = focus_radius(shot)
    return {
        "version": FOCUS_VERSION,
        "shot": shot,
        "backgroundBlurPx": radius,
        "farAmbientBlurPx": focus_radius(shot, plane="ambient_far"),
        "preservesCharacterSharpness": True,
        "precomputedOncePerScene": True,
    }

