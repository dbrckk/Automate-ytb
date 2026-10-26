"""Within-scene gestures are authored, time-bounded and verified in MP4 frames."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.action_timeline import (
    TIMELINE_VERSION, action_phases, choreograph, timeline_report)
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_motion_clip as owl_clip
from automate_ytb.choreography import body_position, leg_position, mouth_expression


def _frame(path: Path, t: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error",
         "-ss", str(t), "-i", str(path), "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, check=True, timeout=90)
    with Image.open(io.BytesIO(result.stdout)) as im:
        return im.convert("RGB")


def _difference(first: Image.Image, second: Image.Image, bounds: tuple) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(
        first.crop(bounds), second.crop(bounds))).mean)


class StoryPhaseTests(unittest.TestCase):
    def test_script_with_three_successive_actions_is_time_bounded(self):
        narration = "Le renard marche, puis saute, puis parle."
        phases = action_phases(narration, duration=5, fallback_action="walk")
        self.assertEqual([p["action"] for p in phases],
                         ["walk", "jump", "talk"])
        self.assertEqual(phases[0]["start"], 0.0)
        self.assertEqual(phases[-1]["end"], 5)
        self.assertTrue(all(a["end"] == b["start"]
                            for a, b in zip(phases, phases[1:])))
        self.assertTrue(all(p["end"] - p["start"] >= .55 for p in phases))
        self.assertEqual(timeline_report(narration, 5, "walk")[
            "audioTimelineShiftMs"], 0)
        self.assertIn("v3", TIMELINE_VERSION)

    def test_no_invented_transitions_in_single_action_and_unsupported_clauses(self):
        one = action_phases("Le chat marche doucement.",
                            duration=5, fallback_action="walk")
        self.assertEqual(len(one), 1)
        single = choreograph("Le chat marche doucement.", duration=5,
                             fallback_action="walk",
                             pose=lambda a: body_position(a, x=180, y=184))
        self.assertEqual(single, body_position("walk", x=180, y=184))
        unknown = action_phases("Le renard marche, et il voit un arbre.",
                                duration=4, fallback_action="walk")
        self.assertEqual(len(unknown), 1)
        too_short = action_phases(
            "The cat walks, then jumps, then talks.",
            duration=1.2, fallback_action="walk")
        self.assertEqual(len(too_short), 1)
        with self.assertRaises(ValueError):
            action_phases("test", duration=-1, fallback_action="idle")
        with self.assertRaises(ValueError):
            action_phases("test", duration=5, fallback_action="hacked;movie=secret")

    def test_blended_motion_is_distinct_from_speech_only_enable(self):
        script = "The rabbit walks, then jumps, then talks."
        body = choreograph(script, duration=5, fallback_action="walk",
                           pose=lambda a: body_position(a, x=180, y=184))
        self.assertEqual(len(body), 2)
        self.assertIn("min(1,max(0", body[0])
        self.assertIn("min(1,max(0", body[1])
        self.assertIn("76", body[1])  # jump trajectory
        self.assertNotIn("movie=", body[0]+body[1])
        legs = choreograph(script, duration=5, fallback_action="walk",
                           pose=lambda a: leg_position(a, side="left"))
        self.assertEqual(len(legs), 2)
        self.assertIn("335", legs[1])
        mouth = choreograph(script, duration=5, fallback_action="walk",
                            pose=lambda a: (mouth_expression(a),),
                            blend=False)[0]
        self.assertIn("if(lt(t,", mouth)
        self.assertIn("lt(mod", mouth)
        self.assertNotIn("min(1,max", mouth)

    def test_excessive_cues_are_bounded_and_deterministic(self):
        script = ("The fox runs, then jumps, then talks, then rests, "
                  "then runs, then walks.")
        a = action_phases(script, duration=9, fallback_action="run")
        b = action_phases(script, duration=9, fallback_action="run")
        self.assertEqual(a, b)
        self.assertLessEqual(len(a), 3)
        self.assertEqual(a[-1]["end"], 9)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required to inspect actual animated frames")
    def test_encoded_fox_multi_action_scene_has_real_motion(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "multi-action-fox.mp4"
            forest_clip(
                kind="fox", topic="Original woodland actions",
                narration="Le renard marche, puis saute, puis parle.",
                scene_index=1, scene_count=3,
                style="cartoon", duration=3.4,
                width=1280, height=720, fps=24,
                destination=dest,
                direction={"weather": "day", "action": "walk",
                           "emotion": "happy", "shot": "wide"})
            self.assertGreater(dest.stat().st_size, 1000)
            a, b, c = (_frame(dest, t) for t in (.30, 1.75, 3.05))
            self.assertEqual(c.size, (1280, 720))
            self.assertGreater(_difference(a, b, (210, 290, 540, 630)), 1)
            self.assertGreater(_difference(b, c, (210, 290, 540, 630)), 1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required to inspect actual animated frames")
    def test_encoded_owl_multi_action_with_no_weather_overlay(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "multi-action-owl.mp4"
            owl_clip(topic="Original owl",
                     narration="La chouette vole puis se repose.",
                     scene_index=1, scene_count=3,
                     style="cartoon", duration=2.4,
                     width=1280, height=720, fps=24,
                     destination=dest, direction=None)
            self.assertGreater(dest.stat().st_size, 1000)
            self.assertEqual(_frame(dest, .8).size, (1280, 720))


if __name__ == "__main__":
    unittest.main()
