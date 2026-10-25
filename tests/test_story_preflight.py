"""Offline narrative repetition and pace preflight never invents editorial approval."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.scene_plan import plan
from automate_ytb.story_preflight import analyze, inspect, main as story_main
from automate_ytb.episode import build_preview


def prepared(script: str) -> dict:
    return plan(
        topic="An original little forest adventure",
        script=script, duration=30, shot_seconds=6,
        character="An original orange fox with a pale striped scarf")


class NarrativePreflightTests(unittest.TestCase):
    def test_original_story_reports_no_duplicate_and_human_review(self):
        script = " ".join([
            "The fox discovers a curious wooden key.",
            "He searches the garden for a forgotten gate.",
            "A friendly rabbit leads him through an orchard.",
            "They find a secret path behind the waterfall.",
            "At sunset the fox returns the key to its owner.",
        ])
        result = analyze(prepared(script))
        self.assertEqual(result["exactRepeatCount"], 0)
        self.assertEqual(result["nearRepeatNeighborCount"], 0)
        self.assertFalse(result["publicationApproved"])
        self.assertFalse(result["factChecked"])
        self.assertTrue(result["humanEditorialReviewRequired"])
        self.assertEqual(result["sceneCount"], 5)
        self.assertEqual(result["version"], "story-preflight-v1")

    def test_detect_exact_repetition_across_separated_scenes(self):
        repeated = "The fox repeats the identical boring sentence."
        script = " ".join([
            repeated, "An owl flies over a blooming field.", repeated,
            repeated, repeated,
        ])
        result = analyze(prepared(script))
        self.assertEqual(result["exactRepeatCount"], 3)
        self.assertEqual(result["status"], "needs-editorial-revision")
        self.assertEqual(result["exactRepeats"][0]["firstSeenSceneId"], "scene-001")
        self.assertTrue(any("repetition" in w.lower()
                            for w in result["warnings"]))
        self.assertFalse(result["publicationApproved"])

    def test_high_adjacent_overlap_is_a_warning_not_a_factual_claim(self):
        script = " ".join([
            "The fox crosses a glowing river in the golden forest.",
            "A fox crosses that golden river in the glowing forest.",
            "The rabbit repairs the old windmill at dawn.",
            "The fox looks for lost berries beneath the trees.",
            "The rabbit builds a new bridge near the village.",
        ])
        result = analyze(prepared(script))
        self.assertGreaterEqual(result["nearRepeatNeighborCount"], 1)
        self.assertEqual(result["exactRepeatCount"], 0)
        self.assertNotEqual(result["status"], "needs-editorial-revision")

    def test_pace_diagnostics_are_explicitly_heuristic(self):
        data = prepared(" ".join(
            f"The friend {i} tells a short original anecdote."
            for i in range(5)))
        data["scenes"][0]["narration"] = (
            " ".join(["astonishing and utterly wonderful"] * 24) + ".")
        data["scenes"][1]["narration"] = "One tiny event."
        report = analyze(data)
        self.assertGreater(report["speakingPaceWarningCount"], 0)
        self.assertIn("not audible fluency", " ".join(report["limitations"]))
        with self.assertRaises(ValueError):
            analyze({"scenes": [{"narration": "", "id": "x",
                                 "startMs": 0, "endMs": 100}]})

    def test_inspect_writes_hash_bound_report_and_cli_does_not_block_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan_file, output = root / "scene-plan.json", root / "story.json"
            data = prepared(" ".join(
                ["The same owl visits the same garden."] * 5))
            plan_file.write_text(json.dumps(data), encoding="utf8")
            report = inspect(plan=plan_file, destination=output)
            self.assertEqual(report["status"], "needs-editorial-revision")
            self.assertEqual(len(report["sourcePlanSha256"]), 64)
            self.assertEqual(json.loads(output.read_text())["status"],
                             "needs-editorial-revision")
            self.assertEqual(story_main([
                "--plan", str(plan_file), "--report", str(output)]), 0)

    def test_one_click_preview_exports_story_evidence_without_rewriting_script(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan_file = root / "plan.json"
            text = " ".join([
                "An orange fox finds a bright autumn leaf.",
                "The curious fox carries it to a hidden cottage.",
                "A clever cat studies the leaf with curiosity.",
                "The fox returns to the winding woodland trail.",
                "At night they safely return home together.",
            ])
            original = prepared(text)
            plan_file.write_text(json.dumps(original), encoding="utf8")
            report = build_preview(
                plan_path=plan_file, output=root / "video", limit=1,
                style="cartoon", voice="none", soundtrack="none")
            preflight = json.loads(
                (root / "video" / "story-preflight.json").read_text())
            self.assertEqual(report["storyPreflight"]["exactRepeatCount"], 0)
            self.assertEqual(preflight["sceneCount"], 5)
            self.assertEqual(preflight["sourcePlanSha256"],
                             inspect(plan=plan_file)["sourcePlanSha256"])
            self.assertEqual(
                [s["narration"] for s in original["scenes"]],
                [s["narration"] for s in json.loads(
                    plan_file.read_text())["scenes"]])
            self.assertTrue((root / "video" / "preview.mp4").is_file())


if __name__ == "__main__":
    unittest.main()
