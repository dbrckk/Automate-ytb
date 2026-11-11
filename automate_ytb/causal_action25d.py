"""Reusable source-space causal action clocks and continuous material selection.

An event is paced by its synthesized *phrase* cue, never guessed word timings.
Its physical sources stay at fixed world coordinates while a camera/observer
or other causal actor changes which sources contribute. Pure deterministic
geometry works in optical, oceanic and future volcanic 2.5D source scenes.
"""
from __future__ import annotations

import math

VERSION="shared-causal-source-selection-p527-v1"


def _fraction(value: float, name: str) -> float:
    if (type(value) not in (int,float) or not math.isfinite(value)
            or not 0 <= value <= 1):
        raise ValueError(f"Invalid {name}")
    return float(value)


def ease(value: float) -> float:
    """C1 smoothstep; clamped to the causal action's [0,1] progress."""
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError("Invalid physical action fraction")
    v=max(0.,min(1.,float(value)))
    return v*v*(3.-2.*v)


def action_phase(t: float, duration: float, *,
                 event_progress: float | None = None,
                 trigger: float = .45, lead: float = .16,
                 finish: float = .96) -> float:
    """Speech-derived physical action timeline shared across video genres.

    Exactly preserves the established ocean-action timeline with the default
    parameters. Domain renderers may select an earlier, explicitly authored
    trigger for an on-screen question or explanatory movement.
    """
    if (type(t) not in (int,float) or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration):
        raise ValueError("Invalid causal action animation clock")
    trigger=_fraction(trigger,"action trigger")
    lead=_fraction(lead,"action anticipation")
    finish=_fraction(finish,"action finish")
    if event_progress is not None:
        trigger=_fraction(event_progress,"speech-derived action cue")
    if finish < .75:
        raise ValueError("Action must have a valid visible finish")
    # Preserve known ocean-scene clamping to avoid action discontinuity when
    # using existing narration cues with highly variable phrase segmentation.
    start=min(.64,max(.06,trigger-lead))
    return ease(((t/duration)-start)/max(.10,finish-start))


def contributing_sources(points: tuple[float,...],
                         target: float) -> tuple[tuple[int,float],...]:
    """Blend fixed adjacent source nodes as a moving observer changes view.

    The nodes are never moved to follow the actor: weights migrate between
    physically fixed points. The two weights sum to 1; handoffs are C0
    continuous at every node, without popping or re-drawing a false particle.
    """
    if (not isinstance(points,tuple) or not 2<=len(points)<=128
            or any(type(x) not in (int,float) or not math.isfinite(x)
                   for x in points)
            or any(b-a<=1.e-8 for a,b in zip(points,points[1:]))
            or type(target) not in (int,float)
            or not math.isfinite(target)):
        raise ValueError("Invalid world-space light source array")
    if target<=points[0]:
        return ((0,1.),)
    if target>=points[-1]:
        return ((len(points)-1,1.),)
    for index,(a,b) in enumerate(zip(points,points[1:])):
        if a<=target<=b:
            mix=(target-a)/(b-a)
            return ((index,1.-mix),(index+1,mix))
    raise AssertionError("Unreachable sorted source interval")
