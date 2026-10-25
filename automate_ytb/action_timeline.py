"""Deterministic within-scene choreography from the user's original wording.

Purely visual action phases. No narration changes, no ASR/word alignment, and
no external media. A transition only occurs between *distinct, explicitly
described* actions separated by a narrative connective or punctuation.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeVar

from .director import ACTIONS, direction_for

TIMELINE_VERSION = "speech-anchored-action-phases-v2"
# A conservative, short easing around the boundary avoids teleporting the rig.
BLEND_SECONDS = 0.24
MIN_PHASE_SECONDS = 0.55
MAX_PHASES = 3

# Leave an ordinary "and" alone: sentences such as "the owl watches the
# rain and the fox" do not justify extra animated actions.
_SEPARATORS = re.compile(
    r"(?:\s*(?:[,;]|\.(?=\s)|!(?=\s)|\?(?=\s))\s*|"
    r"\s+\b(?:puis|ensuite|alors|then|afterwards|and then)\b\s+)",
    flags=re.IGNORECASE)


def _audio_anchored_phases(narration: str, *, duration: float,
                           segments: list[dict], scene_start_ms: int
                           ) -> list[dict] | None:
    """Use *measured synthesis phrase starts*, never unmeasured word timings.

    Conservative contract: each recognized gesture belongs to a different
    synthesized caption phrase. A phrase containing two different gestures
    is ambiguous, so we keep the legacy script estimate instead.
    """
    from .captions import caption_phrases
    if not isinstance(segments, list) or not isinstance(scene_start_ms, int) \
            or isinstance(scene_start_ms, bool) or scene_start_ms < 0:
        raise ValueError("Invalid synthesized-phrase action metadata")
    expected = caption_phrases(narration)
    if len(segments) != len(expected):
        raise ValueError("Audio cue count differs from the authored script")
    previous = scene_start_ms
    stop = scene_start_ms + round(duration * 1000)
    gestures: list[dict] = []
    ambiguous = False
    for entry, original in zip(segments, expected):
        if not isinstance(entry, dict):
            raise ValueError("Invalid synthesized gesture cue")
        start, end = entry.get("startMs"), entry.get("endMs")
        if (not isinstance(start, int) or isinstance(start, bool)
                or not isinstance(end, int) or isinstance(end, bool)
                or start != previous or end <= start or end > stop):
            raise ValueError("Invalid synthesized gesture timestamps")
        if " ".join(str(entry.get("text", "")).split()) != original:
            raise ValueError("Synthesized gesture text differs from narration")
        previous = end
        # Multiple verbs within the *same* recorded phrase have no measured
        # internal boundary; they must never receive fake audio alignment.
        sub_actions = [
            direction_for(part)["action"]
            for part in _SEPARATORS.split(original) if part.strip()
        ]
        distinct = {a for a in sub_actions if a != "idle"}
        if len(distinct) > 1:
            ambiguous = True
            continue
        action = next(iter(distinct), "idle")
        if action == "idle":
            continue
        if gestures and gestures[-1]["action"] == action:
            continue
        gestures.append({"action": action,
                         "start": round((start - scene_start_ms)/1000, 4)})
    if previous != stop:
        raise ValueError("Synthesized gesture cues do not reach the scene end")
    if ambiguous or not 2 <= len(gestures) <= MAX_PHASES or gestures[0]["start"] != 0:
        return None
    boundaries = [p["start"] for p in gestures] + [float(duration)]
    if any(b-a < MIN_PHASE_SECONDS for a, b in zip(boundaries, boundaries[1:])):
        return None
    return [{"action": phase["action"], "start": boundaries[i],
             "end": boundaries[i+1]} for i, phase in enumerate(gestures)]


def action_phases(narration: str, *, duration: float,
                  fallback_action: str,
                  caption_segments: list[dict] | None = None,
                  scene_start_ms: int = 0) -> list[dict]:
    """Return approximate visual cue intervals, not word-synchronized times."""
    if not isinstance(narration, str) or len(narration) > 150_000:
        raise ValueError("Narration must be bounded original text")
    if not isinstance(duration, (int, float)) or not 0 < duration <= 3600:
        raise ValueError("Invalid original scene duration")
    if fallback_action not in ACTIONS:
        raise ValueError("Unsupported fallback action")
    if caption_segments is not None:
        from_audio = _audio_anchored_phases(
            narration, duration=duration, segments=caption_segments,
            scene_start_ms=scene_start_ms)
        if from_audio is not None:
            return from_audio
    clauses = [part.strip() for part in _SEPARATORS.split(narration) if part.strip()]
    if len(clauses) < 2:
        return [{"action": fallback_action, "start": 0.0, "end": float(duration)}]
    # Only split at up to three explicit, semantically distinct gestures. No
    # contradictory movements invented for unrecognized connective phrases.
    phases = []
    for clause in clauses:
        detected = direction_for(clause)["action"]
        if detected == "idle":
            continue
        if phases and phases[-1]["action"] == detected:
            phases[-1]["weight"] += max(len(clause), 8)
            continue
        if len(phases) >= MAX_PHASES:
            phases[-1]["weight"] += max(len(clause), 8)
            continue
        phases.append({"action": detected, "weight": max(len(clause), 8)})
    if len(phases) < 2 or duration < len(phases) * MIN_PHASE_SECONDS:
        return [{"action": fallback_action, "start": 0.0, "end": float(duration)}]
    weights = [phase["weight"] for phase in phases]
    total = sum(weights)
    boundaries = [0.0]
    consumed = 0
    for i, weight in enumerate(weights[:-1], start=1):
        consumed += weight
        estimate = duration * consumed / total
        # At least 0.55s for each phase, even in uneven sentences.
        boundary = min(max(estimate, boundaries[-1] + MIN_PHASE_SECONDS),
                       duration - (len(phases) - i) * MIN_PHASE_SECONDS)
        boundaries.append(round(boundary, 4))
    boundaries.append(float(duration))
    return [
        {"action": phase["action"],
         "start": boundaries[i], "end": boundaries[i + 1]}
        for i, phase in enumerate(phases)
    ]


def _local(expression: str, start: float) -> str:
    """Reset rhythmic phases at the beginning of each visual action."""
    if start == 0:
        return expression
    return re.sub(r"\bt\b", f"(t-{start:.4f})", expression)


def _weight(boundary: float) -> str:
    start = max(0.0, boundary - BLEND_SECONDS / 2)
    return f"min(1,max(0,(t-{start:.4f})/{BLEND_SECONDS:.4f}))"


def choreograph(narration: str, *, duration: float,
                fallback_action: str,
                pose: Callable[[str], tuple[str, ...]],
                blend: bool = True,
                caption_segments: list[dict] | None = None,
                scene_start_ms: int = 0) -> tuple[str, ...]:
    """Blend distinct authored poses within a fixed scene video interval.

    The adapter produces expressions only from reviewed action enum values.
    Do not pass user-supplied strings as pose functions. Mouth visibility
    instead switches precisely at the nearest phase boundary.
    """
    phases = action_phases(
        narration, duration=duration, fallback_action=fallback_action,
        caption_segments=caption_segments, scene_start_ms=scene_start_ms)
    if len(phases) == 1:
        return pose(phases[0]["action"])
    initial = pose(phases[0]["action"])
    if not isinstance(initial, tuple) or not initial:
        raise ValueError("Pose callback must provide expression tuple")
    combined = tuple(_local(v, phases[0]["start"]) for v in initial)
    for phase in phases[1:]:
        other = pose(phase["action"])
        if not isinstance(other, tuple) or len(other) != len(combined):
            raise ValueError("Every pose must have identical coordinates")
        other = tuple(_local(v, phase["start"]) for v in other)
        if blend:
            w = _weight(phase["start"])
            combined = tuple(
                f"({old})*(1-({w}))+({new})*({w})"
                for old, new in zip(combined, other)
            )
        else:
            combined = tuple(
                f"if(lt(t,{phase['start']:.4f}),({old}),({new}))"
                for old, new in zip(combined, other)
            )
    return combined


def timeline_report(narration: str, duration: float, fallback_action: str,
                    *, caption_segments: list[dict] | None = None,
                    scene_start_ms: int = 0) -> dict:
    measured = (_audio_anchored_phases(
        narration, duration=duration, segments=caption_segments,
        scene_start_ms=scene_start_ms)
        if caption_segments is not None else None)
    phases = measured if measured is not None else action_phases(
        narration, duration=duration, fallback_action=fallback_action)
    return {"version": TIMELINE_VERSION,
            "phases": phases, "phaseCount": len(phases),
            "timingMethod": ("measured-synthesized-phrase-onsets-not-word-aligned"
                             if measured is not None else
                             "relative-script-clause-length-not-audio-aligned"),
            "audioAnchored": measured is not None,
            "audioTimelineShiftMs": 0}
