"""Original second forest animal only when explicitly present in the story."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_forest import (
    companion_kind, render_layers, render_motion_clip, render_character_poster)


class MultiCharacterScenesTests(unittest.TestCase):
    def test_two_species_require_both_names_and_co_presence(self):
        self.assertEqual(companion_kind("The fox meets a rabbit.", primary="fox"), "rabbit")
        self.assertEqual(companion_kind("The fox and a cat walk together.", primary="fox"), "cat")
        self.assertEqual(companion_kind("Le lapin rencontre un renard.", primary="rabbit"), "fox")
        self.assertEqual(companion_kind("A rabbit and a cat share the forest.", primary="rabbit"), "cat")
        self.assertIsNone(companion_kind("The fox dreamed of a rabbit.", primary="fox"))
        self.assertIsNone(companion_kind("The rabbit rests alone in the woods.", primary="rabbit"))
        self.assertIsNone(companion_kind("The fox meets an owl.", primary="fox"))
        self.assertIsNone(companion_kind("A cat and another cat.", primary="cat"))
        with self.assertRaises(ValueError):
            companion_kind("The fox and rabbit", primary="unknown")

    def test_secondary_rig_is_real_rgba_and_poster_contains_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shared = dict(kind="fox", topic="Two friends in the woods",
                          narration="The fox meets a rabbit in the forest.",
                          scene_index=1, scene_count=2, style="cartoon",
                          direction={"weather":"day","action":"idle",
                                     "emotion":"happy","shot":"wide"},
                          landscape="forest")
            layers = render_layers(root / "layers", **shared)
            self.assertIn("companion", layers)
            with Image.open(layers["companion"]) as companion:
                self.assertEqual(companion.size, (247,332))
                self.assertEqual(companion.mode, "RGBA")
                self.assertIsNotNone(companion.getchannel("A").getbbox())
            poster = root / "poster.png"
            render_character_poster(destination=poster, **shared)
            with Image.open(poster) as picture, Image.open(layers["background"]) as bg:
                self.assertEqual(picture.size,(1280,720))
                diff = ImageChops.difference(
                    picture.convert("RGB").crop((813,265,1060,597)),
                    bg.convert("RGB").crop((813,265,1060,597)))
                self.assertGreater(sum(ImageStat.Stat(diff).mean), 5.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg needed for ensemble MP4")
    def test_two_actor_scene_encodes_actual_h264(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "two-animals.mp4"
            render_motion_clip(
                kind="fox", topic="An original friendship",
                narration="The fox and rabbit meet together in the forest.",
                scene_index=1, scene_count=2, style="cartoon",
                duration=0.9, width=1280, height=720, fps=24,
                destination=path, landscape="forest",
                direction={"weather":"day", "action":"idle",
                           "emotion":"happy", "shot":"wide"})
            self.assertGreater(path.stat().st_size, 1500)
            result = subprocess.run([
                "ffprobe","-v","error","-count_frames",
                "-select_streams","v:0",
                "-show_entries","stream=codec_name,width,height,nb_read_frames",
                "-of","json",str(path)],
                capture_output=True,text=True,check=True,timeout=90)
            video = json.loads(result.stdout)["streams"][0]
            self.assertEqual(video["codec_name"],"h264")
            self.assertEqual((video["width"],video["height"]),(1280,720))
            self.assertGreaterEqual(int(video["nb_read_frames"]),20)


if __name__ == "__main__":
    unittest.main()
