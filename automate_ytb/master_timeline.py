"""Deterministic cross-scene world state and audiovisual event anchors.

MasterTimeline is the engine *contract*, not a renderer or a claim of word
alignment. An object's world-space properties persist across arbitrary beats;
no local-scene clock or mutable frame history can reset them accidentally.
All times are integer frames and all audio onsets are exact PCM sample indices.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import math
import re
from types import MappingProxyType
from typing import Mapping

VERSION = "master-timeline-v1-cross-scene-world-state"
_ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
_FIELDS = {
    "x": (-1_000_000., 1_000_000.),
    "y": (-1_000_000., 1_000_000.),
    "z": (-1_000_000., 1_000_000.),
    "scale": (.001, 100_000.),
    "zoom": (.001, 100_000.),
    "rotation": (-360_000., 360_000.),
    "opacity": (0., 1.),
    "value": (-1.e15, 1.e15),
}
_EASINGS = frozenset(("linear", "smoothstep", "smootherstep"))
_SOUNDS = frozenset(("count", "growth", "contact", "whoosh", "reveal", "water",
                     "electrical", "scale-transition"))
_MAX_FRAMES = 30 * 3600
_MAX_ACTORS = 128
_MAX_EVENTS = 2048
_MAX_CUES = 1024


def _id(value: str, what: str) -> str:
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise ValueError("Invalid " + what)
    return value


def _number(value: float, what: str, *, limits: tuple[float, float]) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Invalid numeric " + what)
    n = float(value)
    if not limits[0] <= n <= limits[1]:
        raise ValueError("Out-of-bounds " + what)
    return n


def _integer(value: int, what: str, *, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Invalid integer " + what)
    return value


def _ease(value: float, method: str) -> float:
    t = min(1.0, max(0.0, value))
    if method == "linear":
        return t
    if method == "smoothstep":
        return t * t * (3 - 2 * t)
    return t * t * t * (t * (6 * t - 15) + 10)


@dataclass(frozen=True)
class WorldObject:
    """Authored initial state. Mutable input dictionaries are copied/frozen."""
    id: str
    properties: Mapping[str, float]
    unit: str | None = None

    def __post_init__(self) -> None:
        _id(self.id, "world object ID")
        if (not isinstance(self.properties, Mapping) or not self.properties
                or len(self.properties) > len(_FIELDS)):
            raise ValueError("World object requires bounded authored properties")
        copied = {}
        for field, raw in self.properties.items():
            if field not in _FIELDS:
                raise ValueError("Unsupported animated property")
            copied[field] = _number(raw, field, limits=_FIELDS[field])
        if self.unit is not None and (type(self.unit) is not str or
                                      len(self.unit) > 24 or
                                      not re.fullmatch(r"[A-Za-z%°][A-Za-z0-9%°/ -]*", self.unit)):
            raise ValueError("Unsafe physical unit")
        if "value" in copied and not self.unit:
            raise ValueError("Measured values require an explicit unit")
        object.__setattr__(self, "properties", MappingProxyType(copied))


@dataclass(frozen=True)
class Beat:
    """Contiguous editorial interval, never a local time reset."""
    id: str
    start_frame: int
    end_frame: int

    def __post_init__(self) -> None:
        _id(self.id, "beat ID")
        _integer(self.start_frame, "beat start", low=0, high=_MAX_FRAMES)
        _integer(self.end_frame, "beat end", low=1, high=_MAX_FRAMES)
        if self.end_frame <= self.start_frame:
            raise ValueError("Empty beat")


@dataclass(frozen=True)
class PropertyEvent:
    """Absolute property motion, spanning scene boundaries when needed."""
    id: str
    object_id: str
    field: str
    start_frame: int
    end_frame: int
    from_value: float
    to_value: float
    easing: str = "smoothstep"

    def __post_init__(self) -> None:
        _id(self.id, "event ID")
        _id(self.object_id, "event actor ID")
        if self.field not in _FIELDS:
            raise ValueError("Unsupported event property")
        _integer(self.start_frame, "event start", low=0, high=_MAX_FRAMES)
        _integer(self.end_frame, "event end", low=1, high=_MAX_FRAMES)
        if self.end_frame <= self.start_frame:
            raise ValueError("Empty event")
        _number(self.from_value, "from", limits=_FIELDS[self.field])
        _number(self.to_value, "to", limits=_FIELDS[self.field])
        if self.easing not in _EASINGS:
            raise ValueError("Unsupported easing")


@dataclass(frozen=True)
class SoundCue:
    """An audio event tied to a real property event, not a guessed word."""
    id: str
    source_event_id: str
    family: str
    offset_frames: int = 0
    gain_db: float = -18.0

    def __post_init__(self) -> None:
        _id(self.id, "sound cue ID")
        _id(self.source_event_id, "source event ID")
        if self.family not in _SOUNDS:
            raise ValueError("Unsupported sound family")
        _integer(self.offset_frames, "sound event offset", low=-30, high=300)
        _number(self.gain_db, "cue gain", limits=(-60., 0.))


class MasterTimeline:
    """Compile immutable event tracks; renderers query any frame in any order."""

    def __init__(self, *, total_frames: int, objects: list[WorldObject],
                 events: list[PropertyEvent], beats: list[Beat],
                 cues: list[SoundCue] | None = None, fps: int = 30,
                 audio_sample_rate: int = 48000) -> None:
        _integer(fps, "frame rate", low=1, high=60)
        _integer(audio_sample_rate, "PCM sample rate", low=8000, high=192000)
        _integer(total_frames, "timeline duration", low=2,
                 high=min(_MAX_FRAMES, fps * 3600))
        if (not isinstance(objects, (list, tuple)) or not 1 <= len(objects) <= _MAX_ACTORS
                or not isinstance(events, (list, tuple)) or len(events) > _MAX_EVENTS
                or not isinstance(beats, (list, tuple)) or not 1 <= len(beats) <= 1200
                or not isinstance(cues if cues is not None else [], (list, tuple))
                or len(cues if cues is not None else []) > _MAX_CUES):
            raise ValueError("Unsafe MasterTimeline complexity")
        if any(type(x) is not WorldObject for x in objects):
            raise ValueError("Invalid world object")
        if any(type(x) is not PropertyEvent for x in events):
            raise ValueError("Invalid property event")
        if any(type(x) is not Beat for x in beats):
            raise ValueError("Invalid editorial beat")
        cues = [] if cues is None else cues
        if any(type(x) is not SoundCue for x in cues):
            raise ValueError("Invalid sound cue")
        self.total_frames, self.fps = total_frames, fps
        self.audio_sample_rate = audio_sample_rate
        self._objects = {x.id: x for x in objects}
        if len(self._objects) != len(objects):
            raise ValueError("Duplicate world object ID")
        ordered_beats = sorted(beats, key=lambda b: b.start_frame)
        if (len({b.id for b in ordered_beats}) != len(ordered_beats)
                or ordered_beats[0].start_frame != 0
                or ordered_beats[-1].end_frame != total_frames
                or any(a.end_frame != b.start_frame for a, b in
                       zip(ordered_beats, ordered_beats[1:]))):
            raise ValueError("Editorial beats must cover the entire timeline contiguously")
        self.beats = tuple(ordered_beats)
        self._beat_starts = tuple(b.start_frame for b in self.beats)
        sources = {}
        tracks: dict[tuple[str, str], list[PropertyEvent]] = {}
        for e in events:
            if e.id in sources:
                raise ValueError("Duplicate physical event ID")
            if e.object_id not in self._objects:
                raise ValueError("Event references unknown object")
            if e.field not in self._objects[e.object_id].properties:
                raise ValueError("Animated property must have an initial state")
            if e.end_frame > total_frames:
                raise ValueError("Event runs beyond the episode")
            sources[e.id] = e
            tracks.setdefault((e.object_id, e.field), []).append(e)
        self._tracks = {}
        for (obj_id, field), track in tracks.items():
            ordered = tuple(sorted(track, key=lambda e: e.start_frame))
            previous_frame = -1
            previous_value = self._objects[obj_id].properties[field]
            for e in ordered:
                if e.start_frame < previous_frame:
                    raise ValueError("Overlapping events on the same object property")
                if not math.isclose(e.from_value, previous_value,
                                    rel_tol=1e-12, abs_tol=1e-9):
                    raise ValueError("World state would jump between authored events")
                previous_frame, previous_value = e.end_frame, e.to_value
            self._tracks[(obj_id, field)] = (
                tuple(e.start_frame for e in ordered), ordered)
        sound_ids = set()
        scheduled = []
        for cue in cues:
            if cue.id in sound_ids:
                raise ValueError("Duplicate sound cue ID")
            sound_ids.add(cue.id)
            event = sources.get(cue.source_event_id)
            if event is None:
                raise ValueError("Sound cue has no real visual source event")
            frame = event.start_frame + cue.offset_frames
            if frame < 0 or frame >= total_frames:
                raise ValueError("Sound cue is outside the rendered episode")
            scheduled.append({
                "id": cue.id, "family": cue.family,
                "sourceEventId": event.id, "sourceObjectId": event.object_id,
                "atFrame": frame,
                "atSample": (frame * audio_sample_rate + fps // 2) // fps,
                "gainDb": cue.gain_db,
            })
        self._sound_cues = tuple(sorted(scheduled, key=lambda x: (x["atSample"], x["id"])))

    def state_at(self, frame: int) -> dict:
        """Pure 30fps world-space state; no reset at an editorial beat boundary."""
        _integer(frame, "frame index", low=0, high=self.total_frames)
        states = {key: dict(obj.properties) for key, obj in self._objects.items()}
        for (obj_id, field), (starts, events) in self._tracks.items():
            selected = bisect_right(starts, frame) - 1
            if selected >= 0:
                event = events[selected]
                fraction = ((frame - event.start_frame) /
                            (event.end_frame - event.start_frame))
                weight = _ease(fraction, event.easing)
                states[obj_id][field] = (event.from_value +
                                         (event.to_value - event.from_value) * weight)
        beat = self.beats[min(bisect_right(self._beat_starts, frame) - 1, len(self.beats) - 1)]
        return {"frame": frame, "timeMs": (frame * 1000 + self.fps // 2) // self.fps,
                "beatId": beat.id, "objects": states}

    def audio_events(self) -> list[dict]:
        """Copy safe, sample-exact events for a future PCM Foley renderer."""
        return [dict(x) for x in self._sound_cues]

    @classmethod
    def from_scene_plan(cls, plan: dict, *, objects: list[WorldObject],
                        events: list[PropertyEvent],
                        cues: list[SoundCue] | None = None, fps: int = 30) -> "MasterTimeline":
        """Adapt an EXISTING scene-plan.json without changing its schema."""
        if type(plan) is not dict or type(plan.get("targetDurationSeconds")) not in (int, float):
            raise ValueError("Invalid existing scene-plan duration")
        duration = plan["targetDurationSeconds"]
        if not math.isfinite(duration) or not 1 <= duration <= 3600:
            raise ValueError("Invalid original episode duration")
        # Kokoro updates the old integer scene duration from actual PCM; the
        # production plan then uses decimal seconds and integer millisecond
        # beat boundaries. Use those authoritative recorded milliseconds.
        duration_ms = round(duration * 1000)
        if abs(duration * 1000 - duration_ms) > 0.01:
            raise ValueError("Scene duration exceeds millisecond precision")
        scenes = plan.get("scenes")
        if (not isinstance(scenes, list) or not 1 <= len(scenes) <= 1200
                or plan.get("sceneCount") != len(scenes)):
            raise ValueError("Invalid authored scene-plan list")
        beats = []
        previous_ms = 0
        for scene in scenes:
            if not isinstance(scene, dict):
                raise ValueError("Invalid authored scene")
            start, end = scene.get("startMs"), scene.get("endMs")
            if (type(start) is not int or type(end) is not int
                    or start != previous_ms or not start < end
                    or end > duration_ms):
                raise ValueError("Missing, overlapping or invalid scene times")
            beats.append(Beat(id=scene["id"],
                              start_frame=(start * fps + 500) // 1000,
                              end_frame=(end * fps + 500) // 1000))
            previous_ms = end
        if previous_ms != duration_ms:
            raise ValueError("Scene plan does not cover authored duration")
        total_frames = (duration_ms * fps + 500) // 1000
        return cls(total_frames=total_frames, objects=objects,
                   events=events, beats=beats, cues=cues, fps=fps)
