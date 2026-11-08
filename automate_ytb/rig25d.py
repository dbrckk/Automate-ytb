"""Deterministic two-bone inverse-kinematic character legs for 2.5D scenes.

Unlike periodic displacement of a flat foot sprite, the solver keeps a paw in
WORLD space through its planted stance while solving knee position from the
moving hip. Between steps, the paw follows a bounded smooth swing. This module
is independent of a species' artwork and uses no network, rig engine or mocks.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

VERSION = "original-25d-two-bone-world-locked-feet-v1"
PERIOD = 1.45
SUPPORT = .62
UPPER = 72.0
LOWER = 72.0
GROUND = 1361.0
HIPS = {"left": 104.0, "right": 237.0}


@dataclass(frozen=True)
class LegPose:
    hip: tuple[float, float]
    knee: tuple[float, float]
    foot: tuple[float, float]
    planted: bool
    phase: float


def _valid_point(point: tuple[float, float]) -> bool:
    return (isinstance(point, tuple) and len(point) == 2
            and all(type(v) in (float, int) and math.isfinite(v)
                    for v in point))


def solve_two_bone(hip: tuple[float, float],
                   target: tuple[float, float],
                   upper: float, lower: float, *,
                   bend: int) -> tuple[float, float]:
    """Analytic IK: exact upper/lower bone lengths, no stretching or teleport."""
    if (not _valid_point(hip) or not _valid_point(target)
            or type(upper) not in (float, int)
            or type(lower) not in (float, int)
            or not math.isfinite(upper) or not math.isfinite(lower)
            or not 1 <= upper <= 300 or not 1 <= lower <= 300
            or type(bend) is not int or bend not in (-1, 1)):
        raise ValueError("Invalid original 2.5D IK geometry")
    dx,dy=target[0]-hip[0],target[1]-hip[1]
    d=math.hypot(dx,dy)
    if d < abs(upper-lower)+1e-6 or d > upper+lower-1e-6:
        raise ValueError("Unreachable 2.5D paw contact; refusing stretched leg")
    along=(upper*upper-lower*lower+d*d)/(2*d)
    rise=math.sqrt(max(0.,upper*upper-along*along))
    nx,ny=dx/d,dy/d
    return (hip[0]+along*nx-bend*rise*ny,
            hip[1]+along*ny+bend*rise*nx)


def _ease(q: float) -> float:
    return q*q*(3-2*q)


def walking_leg(t: float, *, side: str, origin_x: float,
                speed: float, torso_y: float, ground_y: float = GROUND,
                period: float = PERIOD) -> LegPose:
    """Calculate a real planted foot + a two-segment articulated leg.

    World-space contact remains the same as the pelvis translates during the
    62% stance. The opposite paw is offset by half of the period and the swing
    reconnects to the next foothold at zero position and velocity.
    """
    if (type(t) not in (float, int) or not math.isfinite(t)
            or not 0 <= t <= 3600 or side not in HIPS
            or any(type(v) not in (int, float) or not math.isfinite(v)
                   for v in (origin_x,speed,torso_y,ground_y,period))
            or not 0 <= origin_x <= 1600
            or not 1 <= speed <= 100
            or not 0 <= torso_y <= 1600
            or not 0 <= ground_y <= 1920
            or not .5 <= period <= 5):
        raise ValueError("Invalid 2.5D walking clock or authoring")
    offset = 0.0 if side == "left" else period*.5
    k=math.floor((t-offset)/period)
    contact_time=offset+k*period
    phase=(t-contact_time)/period
    # At foot plant, the paw is slightly in front of the hip. The next
    # landing is one full stride ahead in *world coordinates*.
    first_x=origin_x+HIPS[side]+speed*(contact_time+.30*period)
    next_x=first_x+speed*period
    planted=phase <= SUPPORT
    if planted:
        fx,fy=first_x,ground_y
    else:
        progress=(phase-SUPPORT)/(1-SUPPORT)
        fx=first_x+(next_x-first_x)*_ease(progress)
        # Sin^2 produces zero vertical velocity at lift and landing.
        fy=ground_y-28*math.sin(math.pi*progress)**2
    # The body may bob a few px but the foot world position never follows it.
    bx=origin_x+speed*t
    by=torso_y+3.0*math.cos(2*math.pi*t/period*2)
    hip=(bx+HIPS[side],by+322.0)
    foot=(fx,fy)
    knee=solve_two_bone(hip,foot,UPPER,LOWER,
                        bend=1 if side=="left" else -1)
    return LegPose(hip,knee,foot,planted,phase)
