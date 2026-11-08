"""Animated, physically anchored vegetation for the original forest Short.

The previous static foreground is retained. This overlay is drawn fresh
on every source frame: independently swaying individual curved grass blades
and an outward travelling bend after the real world-space paw/flower impact.
No procedural image noise, fake contact coordinates, or outside assets.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

from .forest_contact25d import IMPACT_TIME, contact_at
from .rig25d import GROUND

VERSION = "forest-25d-causal-living-meadow-p45-v1"
SIZE = (1080, 1920)
# World-space plant roots remain stationary; only their flexible stems bend.
ROOTS = tuple(
    (36.0 + 15.0 * j, GROUND + 8 + (j * 7) % 28,
     52.0 + (j * 19) % 54)
    for j in range(68)
)
_WAVE_SPEED = 300.0


def blade_motion(t: float, root_x: float, *,
                 impact_x: float | None = None,
                 impact_time: float | None = None) -> tuple[float, float]:
    """Return wind and delayed contact-wave bends in world pixels.

    The radial wave can reach a rooted blade only after its physical travel
    time from the grounded paw. No instantaneous whole-screen reaction.
    """
    if (type(t) not in (int, float) or not math.isfinite(t)
            or not 0 <= t <= 7.2
            or type(root_x) not in (int, float) or not math.isfinite(root_x)
            or not 0 <= root_x <= SIZE[0]
            or (impact_x is None) != (impact_time is None)):
        raise ValueError("Invalid animated meadow clock or contact geometry")
    wind = (10.0 * math.sin(1.7*t + .017*root_x)
            + 4.0 * math.sin(3.3*t - .013*root_x))
    if impact_x is None:
        return wind, 0.0
    if (type(impact_x) not in (int, float)
            or not math.isfinite(impact_x) or not 0 <= impact_x <= SIZE[0]
            or type(impact_time) not in (int, float)
            or not math.isfinite(impact_time)
            or not 0 <= impact_time <= 7.2):
        raise ValueError("Invalid real paw impact")
    distance = abs(root_x-impact_x)
    age = t-impact_time-distance/_WAVE_SPEED
    if age <= 0:
        return wind, 0.0
    # Damped organic sway; attenuation and speed derive from ground distance.
    wave = (42.0 * math.exp(-2.4*age)
            * math.sin(8.5*age)
            * math.exp(-distance/320.0))
    return wind, wave


def meadow_plate(t: float, *, origin_x: float, speed: float,
                 torso_y: float, interaction: bool) -> Image.Image:
    """Draw the moving plant overlay without mutating cached world plates."""
    if (type(interaction) is not bool
            or any(type(x) not in (int, float) or not math.isfinite(x)
                   for x in (origin_x, speed, torso_y))):
        raise ValueError("Invalid original world-space vegetation")
    # Always validate contact coordinates through the existing physical rig.
    hit = (contact_at(t, origin_x=origin_x, speed=speed,
                      torso_y=torso_y) if interaction else None)
    result = Image.new("RGBA", SIZE)
    d = ImageDraw.Draw(result)
    for index, (root_x, root_y, height) in enumerate(ROOTS):
        wind, wave = blade_motion(
            t, root_x,
            impact_x=hit.x if hit else None,
            impact_time=IMPACT_TIME if hit else None)
        dx = wind + wave
        # Root x/y never moves. The tip's large response is visible even
        # after the 9:16 camera crop without sliding the grass across earth.
        tip = (root_x + dx, root_y-height)
        middle = (root_x + dx*.34 + (index%3-1)*4, root_y-height*.54)
        base = (root_x, root_y)
        tone = index % 5
        color = (37+tone*7, 114+tone*11, 67+tone*5, 165)
        d.line((base, middle, tip), fill=color, width=3 if index%3 else 4,
               joint="curve")
        # Asymmetric tapered botanical leaves, not repeated flat ellipses.
        direction = -1 if index%2 else 1
        for fraction, reach in ((.39, 22), (.68, 16)):
            anchor_x = root_x + dx*(fraction*fraction)
            anchor_y = root_y - height*fraction
            leaf_end = (anchor_x+direction*(reach+abs(wave)*.15),
                        anchor_y - 11 - index%7)
            d.polygon((
                (anchor_x-2,anchor_y+5),
                (anchor_x+direction*reach*.55,anchor_y-1),
                leaf_end,
                (anchor_x+direction*reach*.28,anchor_y-7),
            ), fill=(58+tone*8,139+tone*8,79+tone*5,134))
        if index%9 == 0:
            # Sparse distinct flower heads sway with their own rooted stems.
            x,y=tip
            d.ellipse((x-7,y-7,x+7,y+7),
                      fill=(239,191+tone*6,131,207))
            d.ellipse((x-3,y-3,x+3,y+3),fill=(255,231,162,233))
    return result
