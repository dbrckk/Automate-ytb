"""Wind-deformed, rooted canopy and understory for the existing 2.5D forest.

Warp the original authored RGBA tree/understory plates instead of painting
floating duplicate foliage. Bilinear mesh deforms stems and leaves continuously;
the lower root zone remains still. Only the populated bands are transformed,
and no additional compositor Z layer is required.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image

from .forest_cinematic_world25d import plates

VERSION = "forest-25d-rooted-mesh-canopy-wind-p46-v1"
SIZE = (1080, 1920)
# Source windows enclose all visible authored geometry, not entire 1080x1920.
WINDOWS = {
    "trees": (710, 1360),
    "understory": (1190, 1555),
}
# The trees' real grounded trunks finish near 1344. The understory's foliage
# occupies the 1280-1453 region and settles to a fixed root below it.
ROOT_Y = {"trees": 1348.0, "understory": 1535.0}
REACH = {"trees": 530.0, "understory": 270.0}
AMPLITUDE = {"trees": 26.0, "understory": 16.0}
GRID_X = 180
GRID_Y = 72


def wind_offset(t: float, x: float, y: float, *, layer: str) -> float:
    """Continuous wind displacement, zero at/below the anchored root plane."""
    if (type(t) not in (int, float) or not math.isfinite(t)
            or not 0 <= t <= 7.2
            or type(x) not in (int, float) or not math.isfinite(x)
            or not 0 <= x <= SIZE[0]
            or type(y) not in (int, float) or not math.isfinite(y)
            or not 0 <= y <= SIZE[1]
            or layer not in WINDOWS):
        raise ValueError("Invalid rooted canopy time, position or layer")
    leverage = max(0.0, min(1.0, (ROOT_Y[layer]-y)/REACH[layer]))
    leverage **= 1.3
    # Two coherent but non-identical gust rhythms, varied by world position:
    # no time-discontinuous random sprites, and no camera-space sliding.
    gust = (0.70 * math.sin(1.35*t + 0.003*x + (0.45 if layer=="understory" else 0.0))
            + 0.30 * math.sin(2.55*t - 0.004*x))
    return AMPLITUDE[layer] * leverage * gust


@lru_cache(maxsize=2)
def _source(layer: str) -> Image.Image:
    if layer not in WINDOWS:
        raise ValueError("Unknown original canopy layer")
    start, end = WINDOWS[layer]
    source = plates()[layer]
    if source.mode != "RGBA" or source.size != SIZE:
        raise ValueError("Original canopy plate must be a full-size RGBA image")
    return source.crop((0, start, SIZE[0], end))


def _mesh(t: float, layer: str) -> list[tuple[tuple[int,int,int,int], tuple[float, ...]]]:
    start,end=WINDOWS[layer]
    elements=[]
    for top in range(0,end-start,GRID_Y):
        bottom=min(end-start,top+GRID_Y)
        for left in range(0,SIZE[0],GRID_X):
            right=min(SIZE[0],left+GRID_X)
            # Pillow MESH source QUAD ordering is UL, LL, LR, UR.
            # Invert displacement for destination-to-source resampling.
            xl_top=left-wind_offset(t,left,start+top,layer=layer)
            xl_bot=left-wind_offset(t,left,start+bottom,layer=layer)
            xr_bot=right-wind_offset(t,right,start+bottom,layer=layer)
            xr_top=right-wind_offset(t,right,start+top,layer=layer)
            elements.append(((left,top,right,bottom),
                             (xl_top,top,xl_bot,bottom,
                              xr_bot,bottom,xr_top,top)))
    return elements


def living_canopy(t: float, *, layer: str) -> Image.Image:
    """Return an RGBA full-stage layer for the existing 2.5D compositor."""
    if layer not in WINDOWS:
        raise ValueError("Unrecognized canopy/understory authoring layer")
    # Validate even if the source plate happens to have no pixels on a frame.
    wind_offset(t,0.0,0.0,layer=layer)
    top,end=WINDOWS[layer]
    original=_source(layer)
    deformed=original.transform(
        original.size, Image.Transform.MESH, _mesh(t,layer),
        resample=Image.Resampling.BILINEAR)
    image=Image.new("RGBA",SIZE)
    image.alpha_composite(deformed,(0,top))
    return image
