"""Action cues visibly affect real animated character MP4s and preserve safety."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_owl import render_motion_clip as owl_clip
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.choreography import (
    PROFILES, CHOREOGRAPHY_VERSION, body_position,
    secondary_position, mouth_expression)
from automate_ytb.director import ACTIONS, direction_for, validate_direction


def captured_frame(video: Path, t: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(t),
         "-i", str(video), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"], capture_output=True,
        check=True, timeout=90)
    with Image.open(io.BytesIO(result.stdout)) as img:
        return img.convert("RGB")


def difference(a: Image.Image, b: Image.Image, bbox: tuple) -> float:
    a, b = a.crop(bbox), b.crop(bbox)
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean)


class ChoreographyTests(unittest.TestCase):
    def test_every_director_action_has_safe_distinct_motion(self):
        self.assertEqual(set(PROFILES), ACTIONS)
        self.assertIn("v9", CHOREOGRAPHY_VERSION)
        for action in ACTIONS:
            x, y = body_position(action, x=180, y=184)
            self.assertIn("180", x)
            self.assertIn("184", y)
            self.assertNotIn(";", x + y)
            self.assertIn("sin", x + y)
            for part in ("left", "right", "tail"):
                self.assertIn("sin(t*", secondary_position(action, base=300,
                                                          side=part))
            self.assertIn(mouth_expression(action), {
                "0", "lt(mod(t,0.50),0.28)", "lt(t,0.60)"})
        self.assertNotEqual(body_position("run", x=180, y=184),
                            body_position("walk", x=180, y=184))
        self.assertNotEqual(body_position("jump", x=180, y=184),
                            body_position("fly", x=180, y=184))
        self.assertNotEqual(mouth_expression("talk"), mouth_expression("rest"))
        with self.assertRaisesRegex(ValueError, "Unknown"):
            body_position("run;movie=/etc/passwd", x=180, y=184)
        with self.assertRaises(ValueError):
            body_position("run", x=5000, y=184)
        with self.assertRaises(ValueError):
            secondary_position("run", base=200, side="unknown")

    def test_director_recognizes_running_jumping_speaking_in_two_languages(self):
        samples = {
            "Le renard court vers le jardin.": "run",
            "The rabbit runs to the forest.": "run",
            "Le lapin saute sur une pierre.": "jump",
            "A cat jumps into the bushes.": "jump",
            "Le hibou raconte une histoire.": "talk",
            "The owl is talking quietly.": "talk",
            "Le renard marche tranquillement.": "walk",
            "The little fox rests by a tree.": "rest",
        }
        for text, wanted in samples.items():
            with self.subTest(text=text):
                self.assertEqual(direction_for(text)["action"], wanted)
        with self.assertRaises(ValueError):
            validate_direction({"weather": "day", "action": "anything",
                                "emotion": "neutral", "shot": "wide"})

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required to validate movement")
    def test_rabbit_jump_is_visually_distinct_from_walk(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            results = {}
            for action in ("walk", "jump"):
                video = root / f"{action}.mp4"
                forest_clip(
                    kind="rabbit", topic="La clairière originale",
                    narration="Le lapin explore un jardin.",
                    scene_index=1, scene_count=3, style="cartoon",
                    duration=1.4, width=1280, height=720, fps=24,
                    destination=video,
                    direction={"weather": "day", "action": action,
                               "emotion": "happy", "shot": "wide"})
                results[action] = captured_frame(video, .50)
                self.assertEqual(results[action].size, (1280, 720))
            self.assertGreater(
                difference(results["walk"], results["jump"],
                           (155, 160, 555, 625)), 2.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required to validate facial expressions")
    def test_owl_talk_uses_independent_open_and_closed_mouth_frames(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "owl-talking.mp4"
            owl_clip(
                topic="La chouette originale", narration="La chouette parle.",
                scene_index=1, scene_count=3, style="cartoon",
                duration=1.3, width=1280, height=720, fps=24,
                destination=video,
                direction={"weather": "day", "action": "talk",
                           "emotion": "neutral", "shot": "wide"})
            open_mouth = captured_frame(video, .13)
            closed_mouth = captured_frame(video, .38)
            self.assertGreater(
                difference(open_mouth, closed_mouth,
                           (325, 437, 403, 505)), 1.5)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required to validate fox motion")
    def test_fox_run_has_independently_moving_tail(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "fox-running.mp4"
            forest_clip(
                kind="fox", topic="La course originale",
                narration="Le renard court dans la forêt.",
                scene_index=1, scene_count=3, style="cartoon",
                duration=1.2, width=1280, height=720, fps=24,
                destination=video,
                direction={"weather": "day", "action": "run",
                           "emotion": "happy", "shot": "wide"})
            before = captured_frame(video, .1)
            after = captured_frame(video, .55)
            self.assertGreater(
                difference(before, after, (120, 320, 350, 570)), 1.0)


if __name__ == "__main__":
    unittest.main()
