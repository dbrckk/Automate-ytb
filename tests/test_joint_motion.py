"""Regression suite for attached animated sprite joints and real FFmpeg MP4s."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.joint_motion import AMPLITUDES, JOINT_VERSION, joint_angle
from automate_ytb.director import ACTIONS
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_motion_clip as owl_clip


class JointMotionTests(unittest.TestCase):
    def test_bounded_angles_for_every_original_action(self):
        self.assertIn("v4", JOINT_VERSION)
        self.assertEqual(set(ACTIONS), set(AMPLITUDES["wing"]))
        for part, sides in (("wing", ("left", "right")),
                            ("leg", ("left", "right")),
                            ("ear", ("left", "right")),
                            ("tail", ("tail",))):
            self.assertEqual(set(AMPLITUDES[part]), set(ACTIONS))
            for action in ACTIONS:
                self.assertLessEqual(AMPLITUDES[part][action], 0.25)
                for side in sides:
                    expr = joint_angle(action, part=part, side=side)
                    self.assertEqual(expr, joint_angle(action, part=part, side=side))
                    self.assertEqual(
                        expr.count("sin("),
                        1 if part == "leg" and action in {"walk", "run"}
                        else 3 if action == "jump" else 2)
                    self.assertNotIn(";", expr)
                    self.assertNotIn("\n", expr)
        self.assertNotEqual(joint_angle("run", part="leg", side="left"),
                            joint_angle("run", part="leg", side="right"))
        for params in (
            dict(action="unknown", part="wing", side="left"),
            dict(action="run", part="unknown", side="left"),
            dict(action="run", part="tail", side="right"),
            dict(action="run", part="wing", side="tail"),
        ):
            with self.subTest(**params), self.assertRaises(ValueError):
                joint_angle(**params)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Full video encode/decode requires FFmpeg")
    def test_owl_and_fox_joint_rotation_encode_and_decode(self):
        # Decode every frame rather than only checking the MP4 container.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shared = dict(
                topic="An original animal adventure",
                narration="An animal explores the forest.",
                scene_index=1, scene_count=3, style="cartoon",
                duration=1.05, width=1280, height=720, fps=24,
                landscape="forest")
            cases = (
                ("fox", "run", forest_clip),
                ("owl", "fly", owl_clip),
            )
            for animal, action, renderer in cases:
                with self.subTest(animal=animal, action=action):
                    output = root / (animal + ".mp4")
                    kwargs = dict(shared, destination=output,
                                  direction=dict(weather="day", action=action,
                                                 emotion="happy", shot="wide"))
                    if animal == "fox":
                        kwargs["kind"] = "fox"
                    renderer(**kwargs)
                    self.assertGreater(output.stat().st_size, 1500)
                    result = subprocess.run([
                        "ffprobe", "-v", "error", "-count_frames",
                        "-select_streams", "v:0",
                        "-show_entries",
                        "stream=codec_name,width,height,nb_read_frames",
                        "-of", "json", str(output)],
                        check=True, text=True, capture_output=True, timeout=90)
                    stream = json.loads(result.stdout)["streams"][0]
                    self.assertEqual(stream["codec_name"], "h264")
                    self.assertEqual((stream["width"], stream["height"]), (1280, 720))
                    self.assertGreaterEqual(int(stream["nb_read_frames"]), 24)


if __name__ == "__main__":
    unittest.main()
