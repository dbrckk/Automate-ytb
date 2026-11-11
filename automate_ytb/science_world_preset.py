"""Author original reusable persistent 2.5D motion plans for verified science beats.

This creates an **illustrative concept marker**, not a physics simulation or
measured quantity. Only recognized five-beat cause sequences are supported.
Changes are explicitly opted into, versioned, validated and remain editable.
No remote AI, paid credit, third-party media or copied reference assets.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

from .master_timeline_adapter import compile_authored_science_timeline

VERSION = "original-five-beat-science-world-preset-v1"

# Positions are in the visual director's safe world [0,1], not in metres.
# These ORIGINAL editorial trajectories illustrate causal progression only.
_PATHS = {
    "ocean": (
        (("solar", "wind", "coriolis", "sinking", "heat"),
         ((.18,.33),(.26,.37),(.41,.45),(.59,.52),(.66,.70),(.81,.55))),
    ),
    "rainbow": (
        (("sunlight", "refraction", "reflection", "emergence", "arc"),
         ((.14,.30),(.30,.33),(.42,.49),(.55,.56),(.73,.36),(.86,.38))),
    ),
    "lightning": (
        (("charge", "leader", "connection", "return", "thunder"),
         ((.28,.25),(.31,.37),(.43,.51),(.61,.72),(.68,.34),(.84,.57))),
    ),
    "aurora": (
        (("solar_wind", "magnetic_field", "collisions", "emission", "curtains"),
         ((.16,.28),(.36,.35),(.49,.42),(.63,.32),(.76,.43),(.88,.53))),
    ),
    "volcano": (
        (("magma", "pressure", "ascent", "eruption", "lava"),
         ((.41,.83),(.43,.78),(.44,.62),(.49,.39),(.66,.24),(.80,.68))),
    ),
}


def _domain_plan(topic: str, scenes: list[dict]) -> tuple[str, tuple]:
    if type(topic) is not str or not topic.strip() or len(scenes) != 5:
        raise ValueError("The free persistent-world preset requires five authored science beats")
    from .science_storyboards import classify as ocean
    from .science_rainbow import classify as rainbow
    from .science_lightning import classify as lightning
    from .science_aurora import classify as aurora
    from .science_volcano import classify as volcano
    classifiers = {
        "ocean": ocean, "rainbow": rainbow, "lightning": lightning,
        "aurora": aurora, "volcano": volcano,
    }
    for domain, recipes in _PATHS.items():
        if len(recipes) != 1:
            raise ValueError("Each original scientific domain requires one verified motion recipe")
        expected, points = recipes[0]
        actual = tuple(classifiers[domain](topic, s["narration"]) for s in scenes)
        if actual == expected:
            return domain, points
    raise ValueError(
        "The authored script is not an unambiguous, supported five-beat "
        "science sequence; no illustrative physics or motion is invented")


def build_preset(plan: dict) -> dict:
    """Return a validated complete plan with a causal cross-scene actor."""
    if type(plan) is not dict or type(plan.get("scenes")) is not list:
        raise ValueError("A valid V1 scene-plan is required")
    if plan.get("masterTimeline") is not None:
        raise ValueError("Existing authored world timeline cannot be overwritten")
    original = deepcopy(plan)
    domain, positions = _domain_plan(original["topic"], original["scenes"])
    events = []
    cue_types = {
        "ocean": ("growth","water","whoosh","water","reveal"),
        "rainbow": ("growth","contact","whoosh","growth","reveal"),
        "lightning": ("growth","electrical","electrical","electrical","reveal"),
        "aurora": ("growth","whoosh","contact","growth","reveal"),
        "volcano": ("growth","contact","growth","electrical","reveal"),
    }
    for i, scene in enumerate(original["scenes"]):
        sid = scene["id"]
        start = {"sceneId": sid, "fraction": 0}
        end = {"sceneId": sid, "fraction": 1}
        # Piecewise physical-story motion, continuous at EVERY beat boundary.
        # State and camera never restart when domain illustrations change.
        for axis, component in (("x", 0), ("y", 1)):
            events.append({
                "id": f"travel-{axis}-{i+1}",
                "objectId": "concept-marker", "field": axis,
                "start": start, "end": end,
                "from": positions[i][component],
                "to": positions[i+1][component],
                "easing": "smootherstep"})
    final_scene = original["scenes"][-1]["id"]
    events.extend((
        {
            "id": "camera-follow",
            "objectId": "camera", "field": "x",
            "start": {"sceneId": original["scenes"][0]["id"], "fraction": 0},
            "end": {"sceneId": final_scene, "fraction": 1},
            "from": 0, "to": .08,
            "easing": "smootherstep",
        },
        {
            "id": "marker-grow",
            "objectId": "concept-marker", "field": "scale",
            "start": {"sceneId": original["scenes"][0]["id"], "fraction": 0},
            "end": {"sceneId": final_scene, "fraction": 1},
            "from": .85, "to": 1.6,
            "easing": "smoothstep",
        },
    ))
    original["masterTimeline"] = {
        "schemaVersion": 1,
        "objects": [
            {"id": "camera", "properties": {"x": 0, "y": 0, "zoom": 1}},
            {"id": "concept-marker", "properties": {
                "x": positions[0][0], "y": positions[0][1],
                "scale": .85, "opacity": .97}},
        ],
        "cameraId": "camera",
        "visibleActors": ["concept-marker"],
        "events": events,
        # Audio cues are *authored* and timestamped, but the legacy final
        # mix does NOT consume them yet; report flags prevent false claims.
        "soundCues": [
            {"id": f"beat-{i+1}-sfx",
             "sourceEventId": f"travel-x-{i+1}",
             "family": cue_types[domain][i],
             "gainDb": -25 if i < 4 else -20}
            for i in range(5)
        ],
    }
    original["masterTimelinePreset"] = {
        "version": VERSION, "domain": domain,
        "artisticallyIllustrative": True,
        "physicallySimulated": False,
        "audioIntegratedIntoFinalMix": False,
        "reviewRequired": True,
    }
    if compile_authored_science_timeline(original) is None:
        raise RuntimeError("Unexpected missing authored world")
    return original


def attach(*, plan_path: Path) -> dict:
    """Validate first, then atomically update the existing, already authored plan."""
    from .production import load_plan, _write_json
    source = load_plan(plan_path)
    result = build_preset(source)
    # Preserve original plan's safety contract and original script hash.
    if result["sourceScriptSha256"] != source["sourceScriptSha256"]:
        raise RuntimeError("Script provenance changed unexpectedly")
    _write_json(plan_path.resolve(), result)
    return dict(result["masterTimelinePreset"],
                actor="concept-marker",
                scenes=len(result["scenes"]),
                audioCues=len(result["masterTimeline"]["soundCues"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Author an original illustrative continuous 2.5D science world (no physics invented)")
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)
    from json import dumps
    report = attach(plan_path=args.plan)
    print(dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
