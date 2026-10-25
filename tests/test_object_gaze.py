"""Original characters should focus toward script-grounded scene props."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_forest import (
    render_layers as forest_layers,
    render_motion_clip as forest_clip)
from automate_ytb.animated_owl import render_layers as owl_layers
from automate_ytb.scene_props import gaze_target


def _frame(file: Path, time: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error",
         "-ss", str(time), "-i", str(file), "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, check=True, timeout=90)
    with Image.open(io.BytesIO(result.stdout)) as source:
        return source.convert("RGB")


def _delta(a: Image.Image, b: Image.Image, bounds: tuple) -> float:
    difference = ImageChops.difference(a.crop(bounds), b.crop(bounds))
    return sum(ImageStat.Stat(difference).mean)


class ObjectAwareEyePoseTests(unittest.TestCase):
    def test_only_grounded_prop_interaction_changes_gaze(self):
        self.assertEqual(gaze_target("The cat walks in a forest."), "forward")
        self.assertEqual(gaze_target("The cat sees an apple."), "forward")
        self.assertEqual(gaze_target("The cat watches an apple."), "right")
        self.assertEqual(gaze_target("Le renard ramasse une pomme."), "right")
        self.assertEqual(gaze_target("Then the fox walks.", held_prop="apple"),
                         "down-right")
        self.assertEqual(gaze_target("The owl finds a book.", held_prop="apple"),
                         "right")
        with self.assertRaises(ValueError):
            gaze_target("A cat walks.", held_prop="unapproved-object")

    def test_each_mammal_uses_distinct_transparent_eye_poses(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for kind in ("fox", "rabbit", "cat"):
                original = forest_layers(
                    root / (kind + "-forward"), kind=kind,
                    topic="Original story", narration="The animal walks.",
                    scene_index=1, scene_count=3, style="cartoon")
                focused = forest_layers(
                    root / (kind + "-focused"), kind=kind,
                    topic="Original story",
                    narration="The animal watches a flower.",
                    scene_index=1, scene_count=3, style="cartoon")
                carried = forest_layers(
                    root / (kind + "-carried"), kind=kind,
                    topic="Original story", narration="The animal walks.",
                    scene_index=1, scene_count=3, style="cartoon",
                    held_prop="flower")
                with Image.open(original["body"]) as a, \
                     Image.open(focused["body"]) as b, \
                     Image.open(carried["body"]) as c:
                    self.assertEqual(a.size, (350, 440))
                    self.assertGreater(_delta(a.convert("RGB"), b.convert("RGB"),
                                              (85, 177, 157, 250)), 2)
                    self.assertGreater(_delta(b.convert("RGB"), c.convert("RGB"),
                                              (85, 177, 157, 250)), 1)
                # Blink sprites still render, regardless of the eye target.
                self.assertTrue(focused["blink"].is_file())

    def test_owl_eyes_respond_to_a_written_object(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            forward = owl_layers(
                root / "neutral", topic="Original night",
                narration="The owl listens to the wind.",
                scene_index=1, scene_count=3, style="cartoon")
            focused = owl_layers(
                root / "focused", topic="Original night",
                narration="The owl watches a flower.",
                scene_index=1, scene_count=3, style="cartoon")
            with Image.open(forward["body"]) as f, \
                 Image.open(focused["body"]) as g:
                self.assertGreater(
                    _delta(f.convert("RGB"), g.convert("RGB"),
                           (73, 127, 160, 210)), 2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required for eye pose verification")
    def test_encoded_cat_looks_at_flower_when_explicitly_observed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = dict(kind="cat", topic="Original woods",
                          scene_index=1, scene_count=3,
                          style="cartoon", duration=1.2,
                          width=1280, height=720, fps=24,
                          direction={"weather": "day", "action": "idle",
                                     "emotion": "curious", "shot": "wide"})
            focused, neutral = root / "focused.mp4", root / "neutral.mp4"
            forest_clip(
                narration="The cat watches a flower.",
                destination=focused, **common)
            forest_clip(
                narration="The cat looks at the horizon.",
                destination=neutral, **common)
            self.assertGreater(focused.stat().st_size, 1000)
            self.assertEqual(_frame(focused, .5).size, (1280, 720))
            self.assertGreater(
                _delta(_frame(focused, .5), _frame(neutral, .5),
                       (265, 362, 337, 434)), 1.5)


if __name__ == "__main__":
    unittest.main()
