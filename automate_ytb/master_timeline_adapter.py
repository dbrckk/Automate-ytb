"""Opt-in, schema-checked bridge from real V1 science plans to MasterTimeline.

The authored visual actions are anchored to editorial *scene boundaries*, not
invented speech word timestamps. Kokoro may change durations after synthesis;
fractional anchors are resolved against the resulting measured scene start/end.
Legacy plans with no "masterTimeline" member remain completely unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .master_timeline import (
    MasterTimeline, WorldObject, PropertyEvent, SoundCue, VERSION)

ADAPTER_VERSION = "authored-scene-relative-master-timeline-v1"
MAX_OBJECTS = 12
MAX_EVENTS = 128
MAX_CUES = 64


@dataclass(frozen=True)
class AuthoredScienceTimeline:
    timeline: MasterTimeline
    visual_actor_ids: tuple[str, ...]
    camera_id: str
    config_version: str = ADAPTER_VERSION

    def metadata(self) -> dict:
        return {
            "enabled": True,
            "version": VERSION,
            "adapter": self.config_version,
            "objects": len(self.timeline._objects),
            "visibleActors": list(self.visual_actor_ids),
            "propertyTracks": sum(len(events) for _, events in self.timeline._tracks.values()),
            "audioCueCount": len(self.timeline.audio_events()),
            "audioIntegratedIntoFinalMix": False,
            "timing": "author-controlled-scene-relative-anchors-after-synthesis",
            "publicationApproved": False,
        }


def _keys(value: Any, mandatory: set[str], optional: set[str], name: str) -> dict:
    if type(value) is not dict or not mandatory <= value.keys() or (
            set(value) - mandatory - optional):
        raise ValueError("Invalid authored timeline " + name)
    return value


def _list(value: Any, maximum: int, name: str, *, minimum: int = 0) -> list:
    if type(value) is not list or not minimum <= len(value) <= maximum:
        raise ValueError("Invalid authored timeline " + name + " count")
    return value


def _value(raw: Any, name: str) -> float:
    if type(raw) not in (int, float) or not math.isfinite(raw):
        raise ValueError("Invalid " + name)
    return float(raw)


def _frame_at(anchor: dict, scenes: dict, fps: int) -> int:
    _keys(anchor, {"sceneId", "fraction"}, set(), "anchor")
    sid = anchor["sceneId"]
    if type(sid) is not str or sid not in scenes:
        raise ValueError("Unknown scene anchor")
    fraction = _value(anchor["fraction"], "scene fraction")
    if not 0 <= fraction <= 1:
        raise ValueError("Scene fraction must be 0..1")
    scene = scenes[sid]
    ms = scene["startMs"] + round((scene["endMs"]-scene["startMs"]) * fraction)
    return (ms * fps + 500)//1000


def compile_authored_science_timeline(plan: dict, *, fps: int = 30) -> AuthoredScienceTimeline | None:
    """Read a deliberately authored V2 optional member on a valid V1 plan.

    No speculative semantic facts, new inferred values, remote code, implicit
    visual actions, or real-time services are introduced here.
    """
    if type(plan) is not dict:
        raise ValueError("Expected a trusted, validated scene plan")
    spec = plan.get("masterTimeline")
    if spec is None:
        return None
    if type(fps) is not int or fps != 30:
        raise ValueError("MasterTimeline science renderer requires 30 fps")
    _keys(spec, {"schemaVersion", "objects", "events", "visibleActors", "cameraId"},
          {"soundCues"}, "root")
    if type(spec["schemaVersion"]) is not int or spec["schemaVersion"] != 1:
        raise ValueError("Unsupported authored timeline schema")
    raw_objects = _list(spec["objects"], MAX_OBJECTS, "objects", minimum=2)
    raw_events = _list(spec["events"], MAX_EVENTS, "events", minimum=1)
    raw_cues = _list(spec.get("soundCues", []), MAX_CUES, "sound cues")
    actors = _list(spec["visibleActors"], 3, "visible actors", minimum=1)
    camera_id = spec["cameraId"]
    if type(camera_id) is not str:
        raise ValueError("Invalid camera identity")
    originals = []
    for item in raw_objects:
        _keys(item, {"id", "properties"}, {"unit"}, "object")
        originals.append(WorldObject(item["id"], item["properties"], item.get("unit")))
    by_id = {obj.id: obj for obj in originals}
    if len(by_id) != len(originals) or camera_id not in by_id:
        raise ValueError("Unknown or duplicated camera/object ID")
    camera = by_id[camera_id]
    if not {"x", "zoom"} <= camera.properties.keys():
        raise ValueError("Camera must declare x and zoom in world coordinates")
    if (not -.5 <= camera.properties["x"] <= .5
            or not .5 <= camera.properties["zoom"] <= 2.5):
        raise ValueError("Camera starts outside the safe stage")
    if len(set(actors)) != len(actors) or camera_id in actors:
        raise ValueError("Visible actor IDs must be distinct from camera")
    for actor_id in actors:
        if type(actor_id) is not str or actor_id not in by_id:
            raise ValueError("Unknown authored visible actor")
        props = by_id[actor_id].properties
        if not {"x", "y", "scale", "opacity"} <= props.keys():
            raise ValueError("Visible actor needs x, y, scale, opacity")
        if (not 0 <= props["x"] <= 1 or not 0 <= props["y"] <= 1
                or not .1 <= props["scale"] <= 4.0):
            raise ValueError("Visible actor starts outside the scene bounds")
    if type(plan.get("scenes")) is not list or not plan["scenes"]:
        raise ValueError("Missing existing scene plan")
    scenes = {item["id"]: item for item in plan["scenes"]}
    if len(scenes) != len(plan["scenes"]):
        raise ValueError("Duplicate scene IDs")
    events = []
    for entry in raw_events:
        _keys(entry, {"id", "objectId", "field", "start", "end", "from", "to"},
              {"easing"}, "event")
        actor, field = entry["objectId"], entry["field"]
        if actor not in by_id:
            raise ValueError("Unknown event actor")
        start = _frame_at(entry["start"], scenes, fps)
        stop = _frame_at(entry["end"], scenes, fps)
        if field in ("x", "y") and actor != camera_id:
            if not 0 <= _value(entry["to"], field) <= 1:
                raise ValueError("Authored x/y position outside world")
        if field == "x" and actor == camera_id:
            if not -.5 <= _value(entry["to"], field) <= .5:
                raise ValueError("Camera x outside world")
        if field == "zoom" and actor == camera_id:
            if not .5 <= _value(entry["to"], field) <= 2.5:
                raise ValueError("Camera zoom outside safe range")
        if field == "scale" and actor in actors:
            if not .1 <= _value(entry["to"], field) <= 4:
                raise ValueError("Actor scale outside safe range")
        events.append(PropertyEvent(
            entry["id"], actor, field, start, stop,
            _value(entry["from"], "event from"),
            _value(entry["to"], "event to"),
            entry.get("easing", "smoothstep")))
    cues = []
    for cue in raw_cues:
        _keys(cue, {"id", "sourceEventId", "family"},
              {"offsetFrames", "gainDb"}, "sound cue")
        cues.append(SoundCue(
            cue["id"], cue["sourceEventId"], cue["family"],
            cue.get("offsetFrames", 0), cue.get("gainDb", -18.0)))
    timeline = MasterTimeline.from_scene_plan(
        plan, objects=originals, events=events, cues=cues, fps=fps)
    # Only original artwork with native portrait composition supports this
    # carefully scoped visual overlay; reject silently unsupported outputs.
    return AuthoredScienceTimeline(timeline, tuple(actors), camera_id)
