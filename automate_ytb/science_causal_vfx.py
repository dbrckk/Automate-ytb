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
VERSION = "ocean-causal-interactions-v2-source-aligned-tapered-tracer"

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
    # The actual original 9:16 ocean preview exposed a large cyan capsule:
    # 11 overlapping 13px discs made the attached tracer resemble a marker
    # pen on a presentation. Use a narrow, physically connected trajectory
    # instead, with coherent smoothly tapered width/opacity along the trail.
    trail_length=.16 if beat!="sinking" else .11
    start=max(0.,phase-trail_length)
    path=[_trajectory(beat,start+(phase-start)*i/24)
          for i in range(25)]
    for i,(a,b) in enumerate(zip(path,path[1:]),start=1):
        strength=i/24.
        draw.line((a,b),
                  fill=(*main_color,round(30+140*strength)),
                  width=1+round(3*strength),joint="curve")
    x,y=_trajectory(beat,phase)
    draw.ellipse((round(x-4),round(y-4),round(x+4),round(y+4)),
                 fill=(*main_color,225))
    # Small local source response replaces three large diagram rings.
    source_opacity=round(72*math.sin(math.pi*min(1.,phase)))
    if source_opacity>1:
        sx,sy=_trajectory(beat,0.0)
        draw.ellipse((round(sx-14),round(sy-14),
                      round(sx+14),round(sy+14)),
                     fill=(*main_color,max(1,source_opacity//4)))
        draw.ellipse((round(sx-5),round(sy-5),
                      round(sx+5),round(sy+5)),
                     fill=(*main_color,source_opacity))
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
