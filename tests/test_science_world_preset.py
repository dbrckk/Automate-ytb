"""Five original science domains compile into real cross-scene actor tracks."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.scene_plan import plan as original_plan
from automate_ytb.production import load_plan
from automate_ytb.science_world_preset import build_preset, attach, VERSION
from automate_ytb.master_timeline_adapter import compile_authored_science_timeline


CASES = {
    "ocean": ("How ocean currents transport heat", (
        "Sunlight warms surface waters.",
        "Strong winds push this surface water.",
        "Earth rotation bends currents into gyres.",
        "Cold salty water sinks near the poles.",
        "Connected circulation transports heat around Earth.",
    )),
    "rainbow": ("How does a rainbow appear", (
        "White sunlight meets a raindrop.",
        "The light refracts as it enters the drop.",
        "It reflects inside the drop.",
        "The light emerges and separates into colors.",
        "Each observer sees a rainbow arc.",
    )),
    "lightning": ("How lightning forms in thunderstorms", (
        "Ice crystals separate electrical charges.",
        "A stepped leader descends from the cloud.",
        "An upward streamer connects to the leader.",
        "The return stroke rapidly lights the sky.",
        "The expanding shock wave produces thunder.",
    )),
    "aurora": ("Why auroras appear", (
        "A solar wind carries particles from the sun.",
        "The magnetic field guides them toward the poles.",
        "These particles collide with atmospheric oxygen.",
        "Excited gas emits colored light.",
        "The resulting aurora curtains ripple above us.",
    )),
    "volcano": ("How volcanoes erupt", (
        "Magma collects in a chamber below ground.",
        "Trapped bubbles build enormous pressure.",
        "Molten rock moves upward toward a narrow vent.",
        "It erupts through the crater and releases ash.",
        "Lava then flows down the slope.",
    )),
}


def make_plan(domain: str) -> dict:
    topic, beats = CASES[domain]
    return original_plan(topic=topic, script=" ".join(beats),
                         duration=30, shot_seconds=6,
                         character="An original scientific concept in a moving illustrated world")


class ScienceWorldPresetTests(unittest.TestCase):
    def test_five_distinct_domain_episodes_compile_without_hardcoded_video(self):
        self.assertIn("original-five-beat", VERSION)
        for domain in CASES:
            with self.subTest(domain=domain):
                old = make_plan(domain)
                frozen = deepcopy(old)
                updated = build_preset(old)
                self.assertEqual(old, frozen)
                self.assertFalse(updated["publicationApproved"])
                self.assertEqual(updated["masterTimelinePreset"]["domain"], domain)
                self.assertTrue(updated["masterTimelinePreset"]["artisticallyIllustrative"])
                self.assertFalse(updated["masterTimelinePreset"]["physicallySimulated"])
                self.assertFalse(updated["masterTimelinePreset"]["audioIntegratedIntoFinalMix"])
                compiled = compile_authored_science_timeline(updated)
                self.assertEqual(compiled.timeline.total_frames, 900)
                self.assertEqual(len(compiled.timeline.beats), 5)
                self.assertEqual(len(compiled.timeline.audio_events()), 5)
                self.assertEqual(compiled.visual_actor_ids, ("concept-marker",))
                self.assertEqual(compiled.timeline.state_at(0)["beatId"], "scene-001")
                self.assertEqual(compiled.timeline.state_at(899)["beatId"], "scene-005")
                for boundary in (180, 360, 540, 720):
                    before = compiled.timeline.state_at(boundary-1)["objects"]["concept-marker"]
                    after = compiled.timeline.state_at(boundary)["objects"]["concept-marker"]
                    self.assertLess(abs(before["x"]-after["x"]), .01)
                    self.assertLess(abs(before["y"]-after["y"]), .01)
                    self.assertLess(abs(before["scale"]-after["scale"]), .01)

    def test_recalculates_anchors_after_actual_pcm_fractional_duration(self):
        p = build_preset(make_plan("ocean"))
        p["targetDurationSeconds"] = 34.42
        for scene, (start, end) in zip(p["scenes"], (
            (0,6860), (6860,13740), (13740,20420),
            (20420,27510), (27510,34420))):
            scene["startMs"], scene["endMs"] = start, end
        timeline = compile_authored_science_timeline(p).timeline
        self.assertEqual(timeline.total_frames, 1033)
        self.assertEqual(timeline.state_at(205)["beatId"], "scene-001")
        self.assertEqual(timeline.state_at(206)["beatId"], "scene-002")
        self.assertEqual(timeline.state_at(1032)["beatId"], "scene-005")
        self.assertEqual(len(timeline.audio_events()), 5)

    def test_cli_attaches_only_validated_original_plan_atomically(self):
        with tempfile.TemporaryDirectory(prefix="world-preset-") as root:
            path = Path(root) / "scene-plan.json"
            source = make_plan("ocean")
            path.write_text(json.dumps(source), encoding="utf-8")
            evidence = attach(plan_path=path)
            self.assertEqual(evidence["domain"], "ocean")
            self.assertEqual(evidence["actor"], "concept-marker")
            self.assertEqual(evidence["audioCues"], 5)
            result = load_plan(path)
            self.assertEqual(result["sourceScriptSha256"], source["sourceScriptSha256"])
            self.assertIsNotNone(compile_authored_science_timeline(result))
            with self.assertRaises(ValueError):
                attach(plan_path=path)

    def test_unrecognized_semantics_refused_before_writing(self):
        invalid = make_plan("ocean")
        invalid["scenes"][2]["narration"] = "An unrelated sentence with no supported physical beat."
        with self.assertRaises(ValueError):
            build_preset(invalid)
        with self.assertRaises(ValueError):
            build_preset({"topic": "unrecognized", "scenes": []})
        existing = make_plan("ocean")
        existing["masterTimeline"] = {"schemaVersion": 1}
        with self.assertRaises(ValueError):
            build_preset(existing)


if __name__ == "__main__":
    unittest.main()
