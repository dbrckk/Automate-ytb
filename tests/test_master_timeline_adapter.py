"""Optional world actors are drawn in ACTUAL science frames, without legacy reset."""
from __future__ import annotations

import copy
import unittest

from PIL import Image, ImageChops

from automate_ytb.scene_plan import plan as source_plan
from automate_ytb.master_timeline_adapter import (
    compile_authored_science_timeline, ADAPTER_VERSION)
from automate_ytb.master_timeline_art import (
    paint_persistent_actors, STAGE)


def authored_plan() -> dict:
    original = source_plan(
        topic="An original ocean heat transport explanation",
        script=("Sunlight warms surface water. Winds drive ocean currents. "
                "The rotating Earth deflects the flows. Cold water sinks. "
                "The connected circulation transports heat."),
        duration=30, shot_seconds=6,
        character="An original physical science illustration")
    original["masterTimeline"] = {
        "schemaVersion": 1,
        "objects": [
            {"id": "camera", "properties": {"x": 0, "y": 0, "zoom": 1}},
            {"id": "parcel", "properties": {
                "x": .20, "y": .48, "scale": 1, "opacity": 1}}],
        "visualActors": ["parcel"],
        "cameraId": "camera",
        "events": [
            {"id": "parcel-drift", "objectId": "parcel", "field": "x",
             "start": {"sceneId": "scene-001", "fraction": .20},
             "end": {"sceneId": "scene-004", "fraction": .75},
             "from": .20, "to": .82},
            {"id": "camera-follow", "objectId": "camera", "field": "x",
             "start": {"sceneId": "scene-002", "fraction": 0},
             "end": {"sceneId": "scene-005", "fraction": 0},
             "from": 0, "to": .12},
            {"id": "parcel-growth", "objectId": "parcel", "field": "scale",
             "start": {"sceneId": "scene-003", "fraction": 0},
             "end": {"sceneId": "scene-005", "fraction": .50},
             "from": 1, "to": 1.6},
        ],
        "soundCues": [
            {"id": "current-rises", "sourceEventId": "parcel-drift",
             "family": "water", "offsetFrames": 2},
            {"id": "camera-shift", "sourceEventId": "camera-follow",
             "family": "whoosh", "gainDb": -24},
        ],
    }
    return original


class MasterTimelineRealSceneAdapterTests(unittest.TestCase):
    def test_legacy_plan_unchanged_until_explicit_opt_in(self):
        original = authored_plan()
        del original["masterTimeline"]
        frozen = copy.deepcopy(original)
        self.assertIsNone(compile_authored_science_timeline(original))
        self.assertEqual(original, frozen)

    def test_same_object_crosses_five_beats_with_pcm_adjusted_scene_times(self):
        original = authored_plan()
        original["targetDurationSeconds"] = 34.42
        for i, scene in enumerate(original["scenes"]):
            scene["startMs"] = [0, 6860, 13740, 20420, 27510][i]
            scene["endMs"] = [6860, 13740, 20420, 27510, 34420][i]
        frozen = copy.deepcopy(original)
        authored = compile_authored_science_timeline(original)
        self.assertIn("scene-relative", ADAPTER_VERSION)
        self.assertEqual(authored.timeline.total_frames, 1033)
        self.assertEqual(len(authored.timeline.beats), 5)
        self.assertEqual(len(authored.timeline.audio_events()), 2)
        self.assertFalse(authored.metadata()["audioIntegratedIntoFinalMix"])
        self.assertEqual(original, frozen)
        for boundary in (206, 412, 613, 825):
            before = authored.timeline.state_at(boundary - 1)["objects"]["parcel"]["x"]
            after = authored.timeline.state_at(boundary)["objects"]["parcel"]["x"]
            self.assertLess(abs(after-before), .01)
        self.assertGreater(
            authored.timeline.state_at(900)["objects"]["parcel"]["x"],
            authored.timeline.state_at(75)["objects"]["parcel"]["x"])

    def test_real_rgba_world_overlay_respects_mobile_titles_and_caption_regions(self):
        authored = compile_authored_science_timeline(authored_plan())
        original = Image.new("RGBA", (1080, 1920), (10, 24, 44, 255))
        first, later = original.copy(), original.copy()
        r1 = paint_persistent_actors(first, authored, 45)
        r2 = paint_persistent_actors(later, authored, 610)
        self.assertEqual(r1["beatId"], "scene-001")
        self.assertNotEqual(r1["visibleActors"]["parcel"]["x"],
                            r2["visibleActors"]["parcel"]["x"])
        self.assertNotEqual(first.tobytes(), later.tobytes())
        for bounds in ((0,0,1080,590), (0,1495,1080,1920)):
            self.assertEqual(first.crop(bounds).tobytes(),
                             original.crop(bounds).tobytes())
            self.assertEqual(later.crop(bounds).tobytes(),
                             original.crop(bounds).tobytes())
        self.assertNotEqual(ImageChops.difference(first.crop(STAGE),
                         original.crop(STAGE)).getbbox(), None)

    def test_fail_closed_on_unsupported_units_actors_times_and_exec_data(self):
        orig = authored_plan()
        for key, mutate in (
            ("unknown-key", lambda p: p["masterTimeline"].update({"exec": "system"})),
            ("missing-camera", lambda p: p["masterTimeline"].update({"cameraId":"missing"})),
            ("unknown-actor", lambda p: p["masterTimeline"].update({"visibleActors":["ghost"]})),
            ("duplicate-actors", lambda p: p["masterTimeline"].update({"visibleActors":["parcel","parcel"]})),
            ("wrong-fraction", lambda p: p["masterTimeline"]["events"][0]["start"].update({"fraction":2})),
            ("boolean-fraction", lambda p: p["masterTimeline"]["events"][0]["start"].update({"fraction":True})),
            ("nonfinite-fraction", lambda p: p["masterTimeline"]["events"][0]["start"].update({"fraction":float("nan")})),
            ("reversed-event", lambda p: p["masterTimeline"]["events"][0]["end"].update({"sceneId":"scene-001","fraction":0})),
            ("unknown-field", lambda p: p["masterTimeline"]["events"][0].update({"field":"code"})),
            ("sfx-not-linked", lambda p: p["masterTimeline"]["soundCues"][0].update({"sourceEventId":"ghost"})),
            ("unsafe-camera", lambda p: p["masterTimeline"]["objects"][0]["properties"].update({"zoom":5000})),
            ("unsupported-schema", lambda p: p["masterTimeline"].update({"schemaVersion":2})),
        ):
            with self.subTest(key=key):
                bad = copy.deepcopy(orig)
                mutate(bad)
                with self.assertRaises(ValueError):
                    compile_authored_science_timeline(bad)
        with self.assertRaises(ValueError):
            compile_authored_science_timeline(orig, fps=24)

    def test_cue_onsets_are_deterministic_on_measured_frames(self):
        a = compile_authored_science_timeline(authored_plan())
        b = compile_authored_science_timeline(authored_plan())
        self.assertEqual(a.timeline.audio_events(), b.timeline.audio_events())
        self.assertEqual(a.timeline.audio_events()[0]["sourceEventId"], "parcel-drift")
        self.assertEqual(a.timeline.audio_events()[0]["atFrame"], 38)
        self.assertEqual(a.timeline.audio_events()[0]["atSample"], 60800)


if __name__ == "__main__":
    unittest.main()
