"""Validated 2D cinematic framing for original animated scenes.

All camera movements use FFmpeg's per-frame crop expressions. The renderer
accepts only storyboard enum values, never user-supplied filter expressions.
The wide establishing view is intentionally locked for legible scenery and
to avoid artificial movement in still backgrounds.
"""
from __future__ import annotations

from .director import ACTIONS

CAMERA_VERSION = "cinematic-camera-v3-action-follow"

# Source canvas 1280x720. Crops retain approximately 16:9 framing.
# (crop width, crop height, base x, base y, horizontal drift, vertical drift)
PROFILES = {
    "wide": (1280, 720, 0, 0, 0, 0),
    "medium": (1104, 622, 62, 42, 13, 8),
    "closeup": (880, 496, 20, 112, 15, 11),
    "macro": (704, 396, 22, 140, 12, 10),
    "low": (992, 558, 20, 144, 12, 8),
    "shoulder": (1056, 594, 148, 62, 12, 9),
}


def framing_filter(shot: str, *, width: int, height: int, fps: int,
                   scene_index: int = 1,
                   duration: float | None = None,
                   action: str | None = None) -> str:
    """Create a single trusted filter (crop, pan, scale, pixel-format).

    Scene index changes the direction of the gentle drift but never the crop
    dimensions or camera target. All expressions are constructed internally.
    """
    if shot not in PROFILES:
        raise ValueError("Unknown cinematic shot")
    if action is not None and (not isinstance(action, str) or action not in ACTIONS):
        raise ValueError("Unknown cinematic action")
    if (width, height) not in ((1280, 720), (1920, 1080)):
        raise ValueError("Unsupported scene output resolution")
    if fps not in (24, 30):
        raise ValueError("Unsupported scene frame rate")
    if not isinstance(scene_index, int) or not 1 <= scene_index <= 1200:
        raise ValueError("Invalid storyboard scene index")
    cw, ch, x, y, dx, dy = PROFILES[shot]
    if not (0 <= x-dx <= x+dx <= 1280-cw and
            0 <= y-dy <= y+dy <= 720-ch):
        raise ValueError("Unsafe cinematic crop profile")
    if shot == "wide":
        return f"scale={width}:{height}:flags=lanczos,format=yuv420p"
    if duration is not None:
        # Smoothstep traversal: zero camera velocity at both ends prevents
        # visible jerks at edit boundaries. Camera drift is capped by each
        # validated crop profile, and only trusted numeric values are used.
        if not isinstance(duration, (float, int)) or isinstance(duration, bool) \
                or not 0 < duration <= 3600:
            raise ValueError("Invalid cinematic camera duration")
        frames = max(2, round(duration * fps))
        p = f"min(1,max(0,n/{frames-1}))"
        ease = f"(3*({p})*({p})-2*({p})*({p})*({p}))"
        # Alternate traveling direction by scene to avoid a mechanical
        # repeated left-to-right camera pattern.
        travel = f"(2*({ease})-1)" if scene_index % 2 else f"(1-2*({ease}))"
        # A bounded, soft character-follow offset reacts only to validated
        # actions. The zero-velocity envelope vanishes smoothly at scene
        # cuts: the camera never starts or ends with a sudden jerk.
        follow_x = min(5, dx // 3) if action == "run" else 0
        follow_y = min(6, dy - 1) if action == "jump" else 0
        if follow_x or follow_y:
            envelope = f"(16*({p})*({p})*(1-({p}))*(1-({p})))"
            cx = f"{x}+{dx-follow_x}*({travel})"
            cy = f"{y}+{dy-follow_y}*({travel})"
            if follow_x:
                # The tracked horizontal cadence matches the original
                # action's 1.40 Hz body oscillation.
                cx += f"+{follow_x}*({envelope})*sin(n/{fps}*1.40)"
            if follow_y:
                # Same four-beat authored jump trajectory as choreography.py:
                # crouch .18s, rise until .75s, descend until 1.39s.
                clock = f"mod(n/{fps},1.75)"
                launch = f"min(1,max(0,(({clock})-0.18)/0.57))"
                descend = f"min(1,max(0,(({clock})-0.75)/0.64))"
                smooth = lambda v: f"(({v})*({v})*(3-2*({v})))"
                arc = f"({smooth(launch)}-{smooth(descend)})"
                cy += f"-{follow_y}*({envelope})*({arc})"
        else:
            cx = f"{x}+{dx}*({travel})"
            cy = f"{y}+{dy}*({travel})"
        return (f"crop={cw}:{ch}:x='{cx}':y='{cy}',"
                f"scale={width}:{height}:flags=lanczos,format=yuv420p")
    # Pan slowly within the safe frame. Values are not script-supplied.
    phase = "0.0" if scene_index % 2 else "1.2"
    cx = f"{x}+{dx}*sin(n/{fps}*0.77+{phase})"
    cy = f"{y}+{dy}*sin(n/{fps}*0.52+{phase})"
    return (f"crop={cw}:{ch}:x='{cx}':y='{cy}',"
            f"scale={width}:{height}:flags=lanczos,format=yuv420p")


def framing_metadata(shot: str) -> dict:
    """Export a concise, stable provenance record for render reports."""
    if shot not in PROFILES:
        raise ValueError("Unknown cinematic shot")
    w, h, _, _, dx, dy = PROFILES[shot]
    return {"shot": shot, "sourceCanvas": [1280, 720],
            "crop": [w, h], "animatedCamera": bool(dx or dy),
            "version": CAMERA_VERSION,
            "easing": "smoothstep" if dx or dy else "static",
            "zeroVelocityAtSceneEdges": bool(dx or dy),
            "actionFollowing": bool(dx or dy)}
