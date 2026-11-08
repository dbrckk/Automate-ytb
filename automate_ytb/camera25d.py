"""Event-directed 2.5D camera for authored lightning shots.

A genuine multi-plane move: the physical lightning channel stays in the
world-space foreground while clouds at different Z depths move relative to it.
Each move has zero position AND velocity at the shot boundaries. The framing
may follow an authored world-space point, not an inferred subject detector.
No changes to synthesized narration or caption timecodes are permitted.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

VERSION = "scene25d-event-directed-camera-v1"
# Maximum excursions in SOURCE stage pixels, before final uniform reframe.
# Camera is restrained near the edges and stronger during the visible event.
SHOT_TRAVEL: dict[str, tuple[float, float]] = {
    "charge": (-46.0, -13.0),
    "leader": (-78.0, 19.0),
    "connection": (67.0, -16.0),
    "return": (-84.0, -10.0),
    "thunder": (61.0, 24.0),
}
DEFAULT_ACTION_FRACTION = {
    "charge": .53,
    "leader": .58,
    "connection": .66,
    "return": .37,
    "thunder": .55,
}
WORLD_CENTER = (540., 465.)


@dataclass(frozen=True)
class CameraMove25D:
    parallax_x: float
    parallax_y: float
    focus_dx: float
    focus_dy: float
    emphasis: float


def _smooth(value: float) -> float:
    return value * value * (3 - 2 * value)


def event_envelope(q: float, *, action_fraction: float) -> float:
    """C1 compact travel: 0 -> 1 at a spoken event -> 0, no cut velocity."""
    if (type(q) not in (float, int)
            or type(action_fraction) not in (float, int)
            or not math.isfinite(q) or not math.isfinite(action_fraction)
            or not 0 <= q <= 1 or not 0 <= action_fraction <= 1):
        raise ValueError("Invalid event-directed camera phase")
    a = max(.20, min(.80, action_fraction))
    if q <= a:
        return _smooth(q/a)
    return _smooth((1-q)/(1-a))


def shot_camera(beat: str, t: float, duration: float, *,
                event_fraction: float | None = None,
                subject: tuple[float, float] | None = None
                ) -> CameraMove25D:
    """Return independently usable parallax and subject-following crop offsets.

    Authored scene-local subjects must use the stage's 1080x930 coordinates.
    No external tracking guess is allowed. The existing safe-crop constraints
    are still enforced in cinematic_stage.camera_pose.
    """
    if (beat not in SHOT_TRAVEL
            or type(t) not in (float, int)
            or type(duration) not in (float, int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or duration <= 0 or duration > 180 or not 0 <= t <= duration):
        raise ValueError("Invalid 2.5D camera shot")
    if event_fraction is None:
        event_fraction = DEFAULT_ACTION_FRACTION[beat]
    if (type(event_fraction) not in (float, int)
            or not math.isfinite(event_fraction)
            or not 0 <= event_fraction <= 1):
        raise ValueError("Invalid narrated event fraction")
    if subject is not None and (
            not isinstance(subject, tuple) or len(subject) != 2
            or any(type(v) not in (float, int)
                   or not math.isfinite(v) for v in subject)
            or not (0 <= subject[0] <= 1080 and 0 <= subject[1] <= 930)):
        raise ValueError("Invalid authored world-space camera subject")
    q = t / duration
    pulse = event_envelope(q, action_fraction=event_fraction)
    travel_x, travel_y = SHOT_TRAVEL[beat]
    shift_x = 0.0
    shift_y = 0.0
    if subject is not None:
        # Follow 1/3 of the action's displacement instead of chasing every
        # branching lightning vertex or pinning the actor to screen center.
        shift_x = max(-65., min(65., (subject[0]-WORLD_CENTER[0]) * .34))
        shift_y = max(-45., min(45., (subject[1]-WORLD_CENTER[1]) * .20))
    return CameraMove25D(
        parallax_x=travel_x * pulse,
        parallax_y=travel_y * pulse,
        focus_dx=shift_x * pulse,
        focus_dy=shift_y * pulse,
        emphasis=pulse,
    )


def point_on_path(points: tuple[tuple[int, int], ...],
                  fraction: float) -> tuple[float, float]:
    """Sub-frame interpolation along an authored causal action path."""
    if (not isinstance(points, tuple) or not 2 <= len(points) <= 256
            or any(not isinstance(p, tuple) or len(p) != 2
                   or any(type(v) not in (int, float)
                          or not math.isfinite(v) or not 0 <= v <= 1080
                          for v in p) for p in points)
            or type(fraction) not in (int, float)
            or not math.isfinite(fraction)
            or not 0 <= fraction <= 1):
        raise ValueError("Invalid authored camera path")
    index = fraction * (len(points)-1)
    lo = int(index)
    hi = min(lo+1, len(points)-1)
    w = index - lo
    return (points[lo][0]*(1-w) + points[hi][0]*w,
            points[lo][1]*(1-w) + points[hi][1]*w)
