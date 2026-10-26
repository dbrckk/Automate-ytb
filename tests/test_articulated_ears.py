"""Original animal ear articulation stays safe, independent and visibly rendered."""
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image

from automate_ytb.animated_forest import (
    COLORS, render_layers, render_motion_clip, render_character_poster)
from automate_ytb.choreography import ear_position, body_position


class ArticulatedEarTests(unittest.TestCase):
    def test_original_silhouette_is_partitioned_into_real_separate_rgba_layers(self):
        with tempfile.TemporaryDirectory() as folder:
            for kind in COLORS:
                root = Path(folder) / kind
                layers = render_layers(root, kind=kind, topic="Animaux",
                                       narration="Dans la forêt.",
                                       scene_index=1, scene_count=3)
                with Image.open(layers["body"]) as body:
                    self.assertIsNone(
                        body.convert("RGBA").crop((0, 0, 350, 100))
                        .getchannel("A").getbbox())
                for side in ("left", "right"):
                    with Image.open(layers["ear_" + side]) as ear:
                        self.assertEqual(ear.size, (350, 440))
                        self.assertIsNotNone(
                            ear.convert("RGBA").crop((0, 0, 350, 100))
                            .getchannel("A").getbbox())

    def test_ears_follow_body_with_distinct_trusted_offsets(self):
        for kind in COLORS:
            a = ear_position("walk", kind=kind, side="left")
            b = ear_position("walk", kind=kind, side="right")
            self.assertNotEqual(a, b)
            self.assertEqual(a, ear_position("walk", kind=kind, side="left"))
            self.assertIn("sin(t*", a[0])
            self.assertIn("cos(t*", a[1])
            self.assertNotIn(";", "".join(a + b))
            self.assertIn("180", a[0])
            self.assertIn("184", a[1])
        _, rest = ear_position("rest", kind="rabbit", side="left")
        self.assertIn("+7", rest)
        _, startled = ear_position("surprise", kind="fox", side="right")
        self.assertIn("exp(-2*t)", startled)
        with self.assertRaises(ValueError):
            ear_position("walk;movie=", kind="fox", side="right")
        with self.assertRaises(ValueError):
            ear_position("walk", kind="fox", side="unknown")
        with self.assertRaises(ValueError):
            ear_position("walk", kind="unknown", side="left")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Requires actual encoded FFmpeg result")
    def test_real_fox_mp4_contains_articulated_ears_without_dropping_video(self):
        with tempfile.TemporaryDirectory() as folder:
            movie = Path(folder) / "ear-motion.mp4"
            render_motion_clip(
                kind="fox", topic="Le renard bouge ses oreilles.",
                narration="Le renard marche dans la forêt.",
                scene_index=1, scene_count=2, style="cartoon",
                duration=0.8, width=1280, height=720, fps=24,
                destination=movie,
                direction={"weather":"day", "action":"walk",
                           "emotion":"happy", "shot":"wide"})
            self.assertGreater(movie.stat().st_size, 1000)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height",
                 "-of","json",str(movie)],
                capture_output=True,text=True,check=True,timeout=30)
            video=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(video["codec_name"],"h264")
            self.assertEqual((video["width"],video["height"]),(1280,720))


if __name__ == "__main__":
    unittest.main()
