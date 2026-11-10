"""Reusable physically motivated, narration/event-synchronized 2.5D light cue.

Only authored event anchors are accepted. No generic, arbitrarily timed
flashes; no independent audio timing; no 3D renders or downloadable assets.
"""
from __future__ import annotations

import math

from .lightfield25d import Light25D

VERSION = "narrated-event-25d-light-director-p58-v1"


def event_envelope(t: float, duration: float, event_fraction: float | None) -> float:
    """Smooth, bounded C1 light pulse; EXACT zero outside an authored event."""
    if (type(t) not in (int, float) or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration == 0):
        raise ValueError("Invalid event lighting timeline")
    if event_fraction is None:
        return 0.0
    if (type(event_fraction) not in (int, float)
            or not math.isfinite(event_fraction)
            or not 0 <= event_fraction <= 1):
        raise ValueError("Invalid original narrated event position")
    center = max(.19, min(.81, float(event_fraction)))
    reach = min(.22, center, 1.0-center)
    distance = abs(t/duration-center)
    if distance >= reach:
        return 0.0
    q = 1.0-distance/reach
    return (q*q*(3-2*q))**2


def authored_light(*, width: int, height: int,
                   t: float, duration: float,
                   event_fraction: float | None,
                   color: tuple[int,int,int],
                   focal_x: float, focal_y: float) -> Light25D | None:
    """One general-purpose cue for the shared world renderer of any genre.

    The caller supplies a real authored audio/physical event center plus its
    established look palette, not a subject-specific effect class.
    """
    if (type(width) is not int or type(height) is not int
            or not 32 <= width <= 1920 or not 32 <= height <= 1920
            or type(focal_x) not in (float,int)
            or type(focal_y) not in (float,int)
            or not math.isfinite(focal_x) or not math.isfinite(focal_y)
            or not 0 <= focal_x <= 1 or not 0 <= focal_y <= 1):
        raise ValueError("Invalid shared 2.5D world light region")
    envelope=event_envelope(t,duration,event_fraction)
    if envelope <= 0:
        return None
    return Light25D(
        x=round(width*focal_x,3),
        y=round(height*focal_y,3),
        radius=round(max(width,height)*.67,3),
        strength=round(.58*envelope,6),
        color=color,
        ambient=1.0,
    )
