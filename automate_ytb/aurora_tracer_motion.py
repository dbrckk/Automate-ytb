"""Deterministic physically authored 3D tracer trajectory sampling.

These are visual explanations of charged-particle travel, not plasma physics.
Both motion progress and path interpolation are independent of Blender and
are exercised by regression tests; actual geometry is rendered in Cycles.
"""
from __future__ import annotations

import math
from collections.abc import Sequence

TRACERS_PER_PATH = 4


def progress(beat: str, q: float, path_index: int, particle_index: int) -> tuple[float, float]:
    """Forward, staggered, wrap-safe particle movement along a 3D path.

    Returns (position, visibility): opacity cannot be updated consistently on
    all Cycles releases, so the Blender caller uses geometrical scaling. Fade
    at each boundary hides jumps when the next particle enters the path.
    """
    if (beat not in ("solar_wind", "magnetic_field")
            or not isinstance(q, (int, float)) or not math.isfinite(q)
            or not 0 <= q <= 1 or type(path_index) is not int
            or path_index < 0 or type(particle_index) is not int
            or not 0 <= particle_index < TRACERS_PER_PATH):
        raise ValueError("Invalid aurora charged particle action clock")
    speed = 1.04 if beat == "solar_wind" else .72
    stagger = (particle_index + .18 * (path_index % 4)) / TRACERS_PER_PATH
    position = (speed * q + stagger) % 1.
    visibility = min(1., position / .07, (1. - position) / .07)
    return position, max(.001, visibility)


def interpolate(points: Sequence[Sequence[float]], position: float) -> tuple[float, float, float]:
    """Linear xyz interpolation of Blender's explicitly authored 3D path."""
    if (len(points) < 2 or not isinstance(position, (int, float))
            or not math.isfinite(position) or not 0 <= position <= 1):
        raise ValueError("Invalid animated 3D particle trajectory")
    n = len(points) - 1
    location = position * n
    lower = min(n - 1, int(location))
    weight = location - lower
    a, b = points[lower], points[lower + 1]
    if len(a) < 3 or len(b) < 3:
        raise ValueError("Incomplete authored 3D curve")
    result = tuple(
        float(a[i]) * (1 - weight) + float(b[i]) * weight
        for i in range(3)
    )
    if not all(math.isfinite(x) for x in result):
        raise ValueError("Non-finite animated path coordinate")
    return result
