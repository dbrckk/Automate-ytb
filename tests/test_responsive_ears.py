"""Independent ears: original geometry, responsive poses and real MP4."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops

from automate_ytb.animated_forest import (
    _sprite_body, _sprite_ear, render_layers, render_motion_clip)
from automate_ytb.joint_motion import joint_angle


class ResponsiveEarTests(unittest.TestCase):
    def test_ear_geometry_preserves_original_top_of_animal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for kind in ("fox", "rabbit", "cat"):
                with self.subTest(kind=kind):
                    whole = root / (kind + "-whole.png")
                    face = root / (kind + "-face.png")
                    _sprite_body(whole, kind=kind, blink=False,
                                 emotion="happy", gaze="forward")
                    _sprite_body(face, kind=kind, blink=False,
                                 emotion="happy", gaze="forward",
                                 include_ears=False)
                    original = Image.open(whole).convert("RGBA")
                    combined = Image.new("RGBA", (350, 440))
                    for side, x in (("left", 0), ("right", 200)):
                        p = root / (kind + "-" + side + ".png")
                        _sprite_ear(p, kind=kind, side=side)
                        first = p.read_bytes()
                        _sprite_ear(p, kind=kind, side=side)
                        self.assertEqual(first, p.read_bytes())
                        with Image.open(p) as ear:
                            self.assertEqual(ear.size, (150, 240))
                            self.assertEqual(ear.mode, "RGBA")
                            self.assertIsNotNone(ear.getchannel("A").getbbox())
                            combined.alpha_composite(ear, (x, 0))
                    with Image.open(face) as body:
                        combined.alpha_composite(body, (0, 0))
                    # Original silhouette geometry remains identical above
                    # the forehead; independently illuminated ear sprites
                    # intentionally have different RGB material response.
                    before = original.crop((0, 0, 350, 110))
                    after = combined.crop((0, 0, 350, 110))
                    self.assertEqual(before.getchannel("A").tobytes(),
                                     after.getchannel("A").tobytes())

    def test_ears_are_really_separate_motion_layers(self):
        with tempfile.TemporaryDirectory() as folder:
            layers = render_layers(
                Path(folder), kind="rabbit", topic="Original rabbit",
                narration="Le lapin est surpris.", scene_index=2,
                scene_count=3, style="cartoon")
            self.assertTrue(layers["left_ear"].is_file())
            self.assertTrue(layers["right_ear"].is_file())
            with Image.open(layers["body"]) as body:
                self.assertEqual(body.getpixel((80, 60))[3], 0)
            self.assertNotEqual(
                joint_angle("rest", part="ear", side="left"),
                joint_angle("surprise", part="ear", side="left"))
            self.assertIn("exp(-1.35*t)",
                          joint_angle("surprise", part="ear", side="left"))
            self.assertNotIn("exp(",
                             joint_angle("rest", part="ear", side="left"))
            self.assertNotEqual(
                joint_angle("run", part="ear", side="left"),
                joint_angle("run", part="ear", side="right"))
            with self.assertRaises(ValueError):
                _sprite_ear(Path(folder) / "bad.png",
                            kind="dragon", side="left")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg encode required")
    def test_rabbit_surprise_with_ears_encodes_all_frames(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "responsive-rabbit.mp4"
            render_motion_clip(
                kind="rabbit", topic="Original animated woodland",
                narration="Le lapin est surpris dans la clairière.",
                scene_index=2, scene_count=3, style="cartoon",
                duration=1.0, width=1280, height=720, fps=24,
                destination=video, landscape="meadow",
                direction={"weather": "day", "action": "surprise",
                           "emotion": "surprised", "shot": "wide"})
            self.assertGreater(video.stat().st_size, 1500)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-count_frames",
                 "-select_streams", "v:0", "-show_entries",
                 "stream=codec_name,width,height,nb_read_frames",
                 "-of", "json", str(video)],
                capture_output=True, text=True, check=True, timeout=90)
            stream = json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"], "h264")
            self.assertEqual((stream["width"], stream["height"]), (1280, 720))
            self.assertEqual(int(stream["nb_read_frames"]), 24)


if __name__ == "__main__":
    unittest.main()
