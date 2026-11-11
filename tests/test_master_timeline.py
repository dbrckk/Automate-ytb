"""The same authored object survives cuts; audio events use the same clock."""
from __future__ import annotations

import copy
import unittest

from automate_ytb.master_timeline import (
    Beat, MasterTimeline, PropertyEvent, SoundCue, WorldObject, VERSION)
from automate_ytb.scene_plan import plan as original_plan


def timeline() -> MasterTimeline:
    objects = [
        WorldObject("subject", {"x": 40, "value": 1, "opacity": 1},
                    unit="units"),
        WorldObject("camera", {"x": 0, "zoom": 1.}),
    ]
    events = [
        PropertyEvent("grow-a", "subject", "value", 30, 100, 1, 8),
        PropertyEvent("grow-b", "subject", "value", 100, 160, 8, 64),
        PropertyEvent("shift", "subject", "x", 35, 145, 40, 220),
        PropertyEvent("camera-follow", "camera", "x", 64, 160, 0, 120),
        PropertyEvent("camera-zoom", "camera", "zoom", 70, 170, 1, 1.6),
    ]
    cues = [
        SoundCue("growth-sound", "grow-a", "growth", offset_frames=2),
        SoundCue("camera-sound", "camera-follow", "whoosh", offset_frames=4),
        SoundCue("reveal-sound", "grow-b", "reveal"),
    ]
    return MasterTimeline(total_frames=180, objects=objects, events=events,
                          beats=[Beat("intro", 0, 60),
                                 Beat("rise", 60, 120),
                                 Beat("ending", 120, 180)], cues=cues)


class MasterTimelineWorldTests(unittest.TestCase):
    def test_real_world_actor_persists_across_multiple_editorial_beats(self):
        t = timeline()
        self.assertIn("master-timeline-v1", VERSION)
        self.assertEqual(t.state_at(0)["objects"]["subject"]["value"], 1)
        self.assertEqual(t.state_at(100)["objects"]["subject"]["value"], 8)
        self.assertEqual(t.state_at(160)["objects"]["subject"]["value"], 64)
        self.assertEqual(t.state_at(179)["objects"]["subject"]["value"], 64)
        self.assertEqual(t.state_at(59)["beatId"], "intro")
        self.assertEqual(t.state_at(60)["beatId"], "rise")
        self.assertEqual(t.state_at(119)["beatId"], "rise")
        self.assertEqual(t.state_at(120)["beatId"], "ending")
        for border in (60, 120):
            left, right = t.state_at(border-1), t.state_at(border)
            for key in ("value", "x"):
                self.assertLess(abs(right["objects"]["subject"][key] -
                                    left["objects"]["subject"][key]), 2)
        self.assertGreater(t.state_at(140)["objects"]["camera"]["x"], 0)

    def test_pure_absolute_frame_sampling_and_input_isolation(self):
        originals = {"x": 40, "value": 1}
        actor = WorldObject("subject", originals, unit="units")
        originals["x"] = 999
        self.assertEqual(actor.properties["x"], 40.)
        with self.assertRaises(TypeError):
            actor.properties["x"] = 500
        a = timeline()
        snapshots = [a.state_at(i) for i in (150, 25, 110, 150, 0)]
        self.assertEqual(snapshots[0], snapshots[3])
        snapshots[0]["objects"]["subject"]["x"] = -100
        self.assertNotEqual(snapshots[0], a.state_at(150))
        self.assertEqual(a.state_at(0)["timeMs"], 0)
        self.assertEqual(a.state_at(180)["timeMs"], 6000)
        self.assertEqual(a.state_at(180)["beatId"], "ending")

    def test_audio_events_are_sample_exact_and_copy_safe(self):
        t = timeline()
        cues = t.audio_events()
        self.assertEqual([c["atFrame"] for c in cues], [32, 68, 100])
        self.assertEqual([c["atSample"] for c in cues], [51200, 108800, 160000])
        self.assertEqual(cues[0]["sourceEventId"], "grow-a")
        cues[0]["atSample"] = -1
        self.assertEqual(t.audio_events()[0]["atSample"], 51200)
        self.assertEqual(t.audio_sample_rate, 48000)

    def test_linear_and_smooth_easing_share_exact_endpoints(self):
        o = [WorldObject("object", {"x": 0, "opacity": 0})]
        events = [PropertyEvent("move", "object", "x", 0, 90, 0, 900,
                                easing="linear"),
                  PropertyEvent("fade", "object", "opacity", 0, 90, 0, 1,
                                easing="smootherstep")]
        t = MasterTimeline(total_frames=100, objects=o, events=events,
                           beats=[Beat("whole", 0, 100)])
        self.assertEqual(t.state_at(0)["objects"]["object"]["x"], 0)
        self.assertEqual(t.state_at(45)["objects"]["object"]["x"], 450)
        self.assertAlmostEqual(t.state_at(45)["objects"]["object"]["opacity"], .5)
        self.assertEqual(t.state_at(90)["objects"]["object"]["x"], 900)
        self.assertEqual(t.state_at(99)["objects"]["object"]["x"], 900)


class MasterTimelineSafetyTests(unittest.TestCase):
    def setUp(self):
        self.obj = [WorldObject("item", {"x": 0, "value": 1}, unit="m")]
        self.beats = [Beat("one", 0, 60), Beat("two", 60, 120)]

    def _compile(self, events=None, beats=None, cues=None, objects=None):
        return MasterTimeline(total_frames=120,
                              objects=self.obj if objects is None else objects,
                              beats=self.beats if beats is None else beats,
                              events=[] if events is None else events, cues=cues)

    def test_reject_unsafe_ids_values_units_and_booleans(self):
        for name in ("../etc", "X", "a;exec", "__builtins__", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                WorldObject(name, {"x": 0})
        for value in (True, float("nan"), float("inf"), 2e18):
            with self.subTest(value=value), self.assertRaises(ValueError):
                WorldObject("item", {"x": value})
        for props in ({"value": 1}, {"x": 0, "danger": 3}, {}):
            with self.subTest(props=props), self.assertRaises(ValueError):
                WorldObject("object", props)
        with self.assertRaises(ValueError):
            WorldObject("item", {"value": 1}, unit="../../")
        with self.assertRaises(ValueError):
            PropertyEvent("move", "item", "x", True, 100, 0, 1)
        with self.assertRaises(ValueError):
            PropertyEvent("move", "item", "x", 0, 20, 0, 1, easing="shell")
        with self.assertRaises(ValueError):
            SoundCue("sound", "event", "unsupported")

    def test_reject_overlap_and_jump_even_at_touching_boundary(self):
        for events in (
            [PropertyEvent("first", "item", "x", 0, 60, 0, 10),
             PropertyEvent("second", "item", "x", 59, 100, 10, 20)],
            [PropertyEvent("first", "item", "x", 0, 60, 0, 10),
             PropertyEvent("second", "item", "x", 60, 100, 11, 20)],
            [PropertyEvent("first", "item", "x", 0, 60, 6, 10)],
        ):
            with self.subTest(events=events), self.assertRaises(ValueError):
                self._compile(events=events)

    def test_reject_missing_actors_beat_gaps_and_invalid_audio_source(self):
        ev = PropertyEvent("change", "item", "x", 0, 60, 0, 10)
        with self.assertRaises(ValueError):
            self._compile(objects=[self.obj[0], self.obj[0]])
        with self.assertRaises(ValueError):
            self._compile(beats=[Beat("one", 0, 59), Beat("two", 60, 120)])
        with self.assertRaises(ValueError):
            self._compile(beats=[Beat("one", 0, 61), Beat("two", 60, 120)])
        with self.assertRaises(ValueError):
            self._compile(events=[PropertyEvent("unknown", "other", "x", 0, 10, 0, 1)])
        with self.assertRaises(ValueError):
            self._compile(events=[ev], cues=[SoundCue("sfx", "not-an-event", "growth")])
        with self.assertRaises(ValueError):
            self._compile(events=[ev], cues=[SoundCue("late", "change", "reveal",
                                                     offset_frames=-30)])
        with self.assertRaises(ValueError):
            self._compile(events=[ev], cues=[SoundCue("a", "change", "growth"),
                                               SoundCue("a", "change", "reveal")])

    def test_adapts_existing_source_plan_without_mutating_or_resetting(self):
        original = original_plan(topic="Original causal world", script=(
            "This is an original idea. A measurable current flows. "
            "The signal reaches a landmark. The camera follows the change. "
            "The final state remains visible."), duration=30,
            shot_seconds=6, character="Original moving instrument")
        frozen = copy.deepcopy(original)
        t = MasterTimeline.from_scene_plan(
            original, objects=self.obj,
            events=[PropertyEvent("change", "item", "value", 30, 650, 1, 9)],
            cues=[SoundCue("ping", "change", "growth")])
        self.assertEqual(len(t.beats), 5)
        self.assertEqual(t.total_frames, 900)
        self.assertEqual(t.state_at(600)["objects"]["item"]["value"],
                         t.state_at(599)["objects"]["item"]["value"] + (
                             t.state_at(600)["objects"]["item"]["value"] -
                             t.state_at(599)["objects"]["item"]["value"]))
        self.assertGreater(t.state_at(599)["objects"]["item"]["value"], 1)
        self.assertEqual(original, frozen)
        invalid = copy.deepcopy(original)
        invalid["scenes"][1]["startMs"] += 1
        with self.assertRaises(ValueError):
            MasterTimeline.from_scene_plan(invalid, objects=self.obj, events=[])

    def test_bounded_resource_limits(self):
        with self.assertRaises(ValueError):
            MasterTimeline(total_frames=120, objects=self.obj,
                           events=[], beats=self.beats, fps=0)
        with self.assertRaises(ValueError):
            MasterTimeline(total_frames=True, objects=self.obj,
                           events=[], beats=self.beats)
        with self.assertRaises(ValueError):
            MasterTimeline(total_frames=120, objects=self.obj,
                           events=[], beats=self.beats, audio_sample_rate=0)


if __name__ == "__main__":
    unittest.main()
