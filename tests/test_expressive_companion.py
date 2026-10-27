"""Original co-present animals have their own blink pose and ground contact."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops

from automate_ytb.animated_forest import (
    FOREST_RIG_VERSION, companion_kind, render_character_poster,
    render_layers, render_motion_clip,
)


class ExpressiveCompanionTests(unittest.TestCase):
    def test_companion_poses_and_contact_shadow_are_real_original_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            narration = "The fox and rabbit explore the forest together."
            layers = render_layers(
                base / "pair", kind="fox", topic="Friends by the grove",
                narration=narration, scene_index=1, scene_count=2,
                style="cartoon",
                direction={"weather": "day", "action": "idle",
                           "emotion": "happy", "shot": "wide"})
            self.assertIn("v27", FOREST_RIG_VERSION)
            for key in ("companion", "companion_shadow", "companion_blink"):
                self.assertTrue(layers[key].is_file())
            with Image.open(layers["companion"]) as open_eyes, \
                    Image.open(layers["companion_blink"]) as closed_eyes, \
                    Image.open(layers["companion_shadow"]) as shade:
                self.assertEqual(open_eyes.size, (247, 332))
                self.assertEqual(closed_eyes.size, (247, 332))
                self.assertEqual(shade.size, (280, 92))
                self.assertIsNotNone(shade.getchannel("A").getbbox())
                delta = ImageChops.difference(
                    open_eyes.convert("RGB"), closed_eyes.convert("RGB"))
                self.assertIsNotNone(delta.getbbox())
            still = base / "pair.png"
            render_character_poster(
                destination=still, kind="fox", topic="Friends by the grove",
                narration=narration, scene_index=1, scene_count=2,
                style="cartoon")
            with Image.open(still) as im:
                self.assertEqual(im.size, (1280, 720))

    def test_no_fabricated_companions_or_extra_video_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = render_layers(
                Path(tmp), kind="fox", topic="Original forest",
                narration="A fox explores the forest alone.",
                scene_index=1, scene_count=2, style="cartoon")
            for key in ("companion", "companion_shadow", "companion_blink"):
                self.assertNotIn(key, layers)
        self.assertIsNone(companion_kind("The fox thinks about a rabbit.",
                                         primary="fox"))
        self.assertEqual(companion_kind(
            "The fox and rabbit explore together.", primary="fox"), "rabbit")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg is required for a dual-actor scene")
    def test_actual_encoded_mp4_with_second_animated_actor(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "two-actors.mp4"
            render_motion_clip(
                kind="fox", topic="Original woodland friendship",
                narration="The fox and rabbit explore the forest together.",
                scene_index=2, scene_count=3, style="cartoon",
                duration=1.2, fps=24, width=1280, height=720,
                destination=destination,
                direction={"weather": "day", "action": "idle",
                           "emotion": "happy", "shot": "wide"})
            self.assertGreater(destination.stat().st_size, 1200)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=codec_name,width,height",
                 "-of", "json", str(destination)],
                capture_output=True, check=True, text=True, timeout=60)
            track = json.loads(probe.stdout)["streams"][0]
            self.assertEqual(track["codec_name"], "h264")
            self.assertEqual((track["width"], track["height"]), (1280, 720))


if __name__ == "__main__":
    unittest.main()
