"""Shared illustrated 2.5D volcanic conduit geometry for all cutaway beats.

The same deterministic rock-bounded path drives its rim, molten alpha mask,
advancing front, inner highlights and connected fracture origins.
This is a geological *schematic*, not a 3D reconstruction or CFD model.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw

VERSION = "curved-shared-volcanic-conduit-p516-v1"
SIZE = (1080, 1380)
VENT = (540, 345)
BASE = (540, 1028)
INNER_WIDTH = 42
OUTER_WIDTH = 66


def conduit_center_x(y: float) -> float:
    """Continuous centerline anchored exactly to vent and reservoir."""
    if (type(y) not in (int, float) or not math.isfinite(y)
            or not VENT[1] <= y <= BASE[1]):
        raise ValueError("Invalid volcanic conduit depth")
    u = (y - VENT[1]) / (BASE[1] - VENT[1])
    # Multiple slowly varying geological bends vanish at both endpoints;
    # the magma/ash vent cannot drift away from the actual crater.
    envelope = math.sin(math.pi*u)**2
    deviation = (11*math.sin(2.65*math.pi*u+.28)
                 +5*math.sin(5.1*math.pi*u-.45))
    return VENT[0] + envelope*deviation


@lru_cache(maxsize=1)
def conduit_path() -> tuple[tuple[int,int], ...]:
    ys=list(range(VENT[1],BASE[1],7))+[BASE[1]]
    return tuple((round(conduit_center_x(y)),y) for y in ys)


def conduit_mask(*, outer: bool = False) -> Image.Image:
    # Validate before the cache: Python considers True == 1 and false == 0
    # for hash keys, so a cached bool result must never bypass type checks.
    if type(outer) is not bool:
        raise ValueError("Invalid rock conduit mask selection")
    return _cached_conduit_mask(outer)


@lru_cache(maxsize=2)
def _cached_conduit_mask(outer: bool) -> Image.Image:
    mask=Image.new("L",SIZE)
    draw=ImageDraw.Draw(mask)
    draw.line(conduit_path(),fill=255,
              width=OUTER_WIDTH if outer else INNER_WIDTH,
              joint="curve")
    return mask


def draw_rock_conduit(draw: ImageDraw.ImageDraw) -> None:
    """Use precisely the same path as the moving magma and its alpha clip."""
    path=conduit_path()
    draw.line(path,fill=(94,56,47,248),width=OUTER_WIDTH,joint="curve")
    draw.line(path,fill=(22,19,27,255),width=INNER_WIDTH+5,joint="curve")
    # A material-colored shoulder follows the actual left/right boundary,
    # instead of two vertical rectangles as in the previous source.
    for i in range(0,len(path)-1,5):
        a=path[i]
        b=path[min(len(path)-1,i+4)]
        draw.line(((a[0]-OUTER_WIDTH//2+5,a[1]),
                   (b[0]-OUTER_WIDTH//2+5,b[1])),
                  fill=(175,105,65,113+i%3*12),width=3)
        draw.line(((a[0]+OUTER_WIDTH//2-6,a[1]),
                   (b[0]+OUTER_WIDTH//2-6,b[1])),
                  fill=(55,34,33,194),width=3)


def active_conduit_path(y_front: float) -> tuple[tuple[int,int], ...]:
    """The rising front always meets the same continuous bedrock channel."""
    if (type(y_front) not in (int,float) or not math.isfinite(y_front)
            or not VENT[1] <= y_front <= BASE[1]):
        raise ValueError("Invalid advancing magma front")
    yy=round(y_front)
    result=[(round(conduit_center_x(y_front)),yy)]
    result.extend((x,y) for x,y in conduit_path() if y>y_front)
    if result[-1] != BASE:
        result.append(BASE)
    return tuple(result)
