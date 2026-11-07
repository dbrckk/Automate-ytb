"""Shot-specific, smooth original Blender camera choreography for aurora Shorts.

All positions are authored world-space camera/aim coordinates, not inferred
subject tracking or physical science simulation. The same deterministic path
drives actual Cycles renders and provenance evidence without Blender imports.
"""
from __future__ import annotations

import math

VERSION = "aurora-beat-story-camera-v1"
SAMPLE_COUNT = 31

# Each beat has a deliberate wide -> action -> consequence/reveal camera arc.
# Time q is normalized by actual narration/shot duration in production.
# Entries: (q, camera XYZ, world-space look-at XYZ).
BEAT_CAMERA_KEYS = {
    "solar_wind": (
        (0.0, (-.42, -11.30, 4.45), (-.68, .45, 2.06)),
        (.44, (.08, -10.77, 4.30), (.08, .50, 2.12)),
        (1.0, (.70, -10.20, 4.02), (1.15, .61, 2.18)),
    ),
    "magnetic_field": (
        (0.0, (.72, -10.80, 4.40), (.05, .43, 2.04)),
        (.44, (-.44, -10.24, 4.11), (.16, .54, 2.12)),
        (1.0, (.06, -9.76, 3.90), (.55, .65, 2.35)),
    ),
    "collisions": (
        (0.0, (-.58, -10.72, 4.24), (-.75, .31, 2.24)),
        (.44, (.02, -9.88, 3.94), (.03, .46, 2.38)),
        (1.0, (.78, -9.42, 3.61), (.69, .55, 2.50)),
    ),
    "emission": (
        (0.0, (-.57, -10.80, 4.34), (-.46, .38, 2.12)),
        (.44, (.13, -9.88, 4.18), (.10, .52, 2.45)),
        (1.0, (.73, -9.26, 4.20), (.60, .64, 2.84)),
    ),
    "curtains": (
        (0.0, (.08, -9.60, 3.52), (.00, .41, 1.64)),
        (.44, (.32, -9.05, 3.35), (.14, .74, 1.87)),
        (1.0, (.62, -8.49, 3.15), (.27, 1.06, 2.11)),
    ),
}


def _tangent(keys, index: int, column: int) -> tuple[float, float, float]:
    if index == 0 or index == len(keys) - 1:
        return (0., 0., 0.)
    before = keys[index - 1]
    after = keys[index + 1]
    interval = after[0] - before[0]
    return tuple(
        (after[column][j] - before[column][j]) / interval
        for j in range(3)
    )


def _hermite(a, b, da, db, t: float, width: float):
    t2 = t*t
    t3 = t2*t
    h00 = 2*t3 - 3*t2 + 1
    h10 = t3 - 2*t2 + t
    h01 = -2*t3 + 3*t2
    h11 = t3 - t2
    return tuple(
        h00*a[i] + h10*width*da[i] +
        h01*b[i] + h11*width*db[i]
        for i in range(3)
    )


def pose(beat: str, q: float) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """C1 continuous 3D camera and action-directed focus, bounded per beat.

    Cubic Hermite interpolation makes the camera velocity continuous at the
    authored middle action, unlike hard-cut or sinusoidal global motion.
    Zero end-tangents avoid a jarring new acceleration across scene cuts.
    """
    if (beat not in BEAT_CAMERA_KEYS or type(q) not in (int, float)
            or not math.isfinite(q) or not 0 <= q <= 1):
        raise ValueError("Invalid original 3D camera action")
    keys = BEAT_CAMERA_KEYS[beat]
    if q == 1:
        return keys[-1][1], keys[-1][2]
    index = next(i for i in range(len(keys) - 1) if keys[i][0] <= q < keys[i+1][0])
    left, right = keys[index], keys[index + 1]
    width = right[0] - left[0]
    fraction = (q - left[0]) / width
    position = _hermite(
        left[1], right[1], _tangent(keys, index, 1),
        _tangent(keys, index+1, 1), fraction, width)
    look_at = _hermite(
        left[2], right[2], _tangent(keys, index, 2),
        _tangent(keys, index+1, 2), fraction, width)
    if (not all(math.isfinite(v) for v in (*position, *look_at))
            or not (-2.0 < position[0] < 2.0 and -13 < position[1] < -7.5
                    and 2.5 < position[2] < 5.5)
            or not (-2.2 < look_at[0] < 2.2 and 0 <= look_at[1] < 2.5
                    and 1.0 < look_at[2] < 3.5)):
        raise ValueError("Authored 3D action camera left safe composition bounds")
    return position, look_at


def evidence(beat: str) -> dict[str, int]:
    """Measure real authored world-space camera and focus movement.

    Distances are cumulative path lengths in thousandths of Blender units.
    They only establish non-static camera choreography, not artistic quality.
    """
    points = [pose(beat, i/(SAMPLE_COUNT-1)) for i in range(SAMPLE_COUNT)]
    travel = sum(math.dist(a[0], b[0]) for a,b in zip(points,points[1:]))
    focus = sum(math.dist(a[1], b[1]) for a,b in zip(points,points[1:]))
    result = {
        "cameraKeyframeCount": len(BEAT_CAMERA_KEYS[beat]),
        "cameraPathSampleCount": SAMPLE_COUNT,
        "cameraTravelMilliunits": round(1000 * travel),
        "cameraFocusTravelMilliunits": round(1000 * focus),
    }
    if result["cameraTravelMilliunits"] < 650 or result["cameraFocusTravelMilliunits"] < 280:
        raise ValueError("Scene lacks motivated camera/focus movement")
    return result
