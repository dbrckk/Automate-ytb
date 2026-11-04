"""Event-driven interaction overlays for authored ocean science storyboards.

These are explanatory 2D trajectories, not a CFD or geophysical simulation.
The animation follows a causal path from source to consequence; its trigger
comes from the synthesized speech phrase when available. Every frame depends
only on its timestamp, so seeking and resumable renders are deterministic.
"""
from __future__ import annotations

import math
from PIL import ImageDraw

BEATS = frozenset(("solar", "wind", "coriolis", "sinking", "heat"))
VERSION = "ocean-causal-interactions-v1"

WARM = (255, 193, 98)
COOL = (122, 222, 249)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _ease(value: float) -> float:
    q = _clamp(value)
    return q * q * (3 - 2 * q)


def event_phase(t: float, duration: float,
                event_progress: float | None = None) -> float:
    """Action progression from phrase cue; no fabricated word timestamps."""
    if (type(t) not in (int, float) or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration):
        raise ValueError("Invalid ocean event animation clock")
    if event_progress is not None and (
            type(event_progress) not in (int, float)
            or not math.isfinite(event_progress)
            or not 0 <= event_progress <= 1):
        raise ValueError("Invalid speech-derived ocean event marker")
    # The keyword is somewhere inside a synthesized caption phrase. Start
    # the action slightly before its midpoint, but don't pretend to know
    # an exact word/phoneme onset or force the event into a tiny time window.
    trigger = 0.45 if event_progress is None else event_progress
    start = min(0.64, max(0.06, trigger - 0.16))
    return _ease(((t / duration) - start) / max(0.10, 0.96 - start))


def _trajectory(beat: str, fraction: float) -> tuple[float, float]:
    """Continuous source-to-target path through the existing science diagram."""
    u = _clamp(fraction)
    if beat == "solar":
        # A sunlight ray passes from the drawn Sun toward the warm latitude.
        x = 403 + (629 - 403) * u
        y = 967 - 94 * math.sin(math.pi*u) + 107*u
    elif beat == "wind":
        # Wind drives the plotted surface-current region, not a free particle.
        x = 410 + 367*u
        y = 862 + 343*_ease(u)
    elif beat == "coriolis":
        # An orbiting tracer follows the existing circular gyre.
        theta = -math.pi*.70 + math.tau*1.12*u
        radius = 212
        x = 540 + radius * math.cos(theta)
        y = 1090 + radius * math.sin(theta)
    elif beat == "sinking":
        # Travel along the surface, sink at the cold boundary, return at depth.
        if u < .30:
            a = _ease(u/.30)
            x, y = 220+583*a, 965
        elif u < .67:
            a = _ease((u-.30)/.37)
            x, y = 803, 965+331*a
        else:
            a = _ease((u-.67)/.33)
            x, y = 803-565*a, 1296
    elif beat == "heat":
        # Transfer from the warm box to the cool box already in the shot.
        x, y = 395+310*_ease(u), 993-40*math.sin(math.pi*u)
    else:
        raise ValueError("Unsupported ocean causal beat")
    return x, y


def draw_interactions(draw: ImageDraw.ImageDraw, beat: str, *,
                      t: float, duration: float,
                      event_progress: float | None = None) -> None:
    """Render primary mover, attached trail and a visible destination response.

    Particles are never randomized or detached from their causative path.
    Unlike a generic glow or repeating loop the action ends at its result.
    Coordinates lie entirely inside the science illustration safe region.
    """
    if beat not in BEATS:
        raise ValueError("Unsupported ocean interaction")
    phase = event_phase(t, duration, event_progress)
    if phase <= 0:
        return
    main_color = WARM if beat in ("solar", "sinking", "heat") else COOL
    # Leading tracer and its physically connected motion history.
    trail_length = .16 if beat != "sinking" else .11
    for index in range(10, -1, -1):
        position = phase - trail_length * index / 10
        if position < 0:
            continue
        x, y = _trajectory(beat, position)
        radius = max(3, round(13 - 8 * index / 10))
        alpha = round(230 * (1 - .79*index/10))
        draw.ellipse((round(x-radius*2), round(y-radius*2),
                      round(x+radius*2), round(y+radius*2)),
                     fill=(*main_color, max(9, alpha//6)))
        draw.ellipse((round(x-radius), round(y-radius),
                      round(x+radius), round(y+radius)),
                     fill=(*main_color, alpha))
    # Source lighting grows during energy transfer and fades after impact.
    source = _trajectory(beat, 0.0)
    source_opacity = round(78 * math.sin(math.pi * min(1.0, phase)))
    if source_opacity > 1:
        sx, sy = source
        for radius in (23, 40, 61):
            draw.ellipse((round(sx-radius), round(sy-radius),
                          round(sx+radius), round(sy+radius)),
                         outline=(*main_color, max(1, source_opacity//(radius//23))),
                         width=3)
    # The destination responds AFTER the mover arrives, never before impact.
    if phase > .75:
        impact = _ease((phase-.75)/.25)
        x, y = _trajectory(beat, 1.0)
        ring_radius = round(18 + 69*impact)
        opacity = round(170*(1-impact))
        if opacity > 1:
            draw.ellipse((round(x-ring_radius), round(y-ring_radius),
                          round(x+ring_radius), round(y+ring_radius)),
                         outline=(*(COOL if beat in ("sinking", "heat") else main_color),
                                 opacity), width=max(2, round(6*(1-impact))))
        # Small stable arrival core makes the resulting causal state legible.
        draw.ellipse((round(x-10), round(y-10), round(x+10), round(y+10)),
                     fill=(*(COOL if beat in ("sinking", "heat") else main_color),
                           round(95+130*impact)))
