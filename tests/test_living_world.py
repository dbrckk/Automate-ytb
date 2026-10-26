"""Living scenery: original per-biome details and real FFmpeg rendering."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops

from automate_ytb.living_world import (
    LIVING_VERSION, draw_ambient_layers, append_ambient_overlays,
)
from automate_ytb.animated_forest import render_motion_clip


class LivingWorldTests(unittest.TestCase):
    def test_original_plates_are_reproducible_and_biome_specific(self):
        self.assertIn("two-plane", LIVING_VERSION)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a = (root / "a_far.png", root / "a_near.png")
            b = (root / "b_far.png", root / "b_near.png")
            c = (root / "c_far.png", root / "c_near.png")
            draw_ambient_layers(*a, landscape="meadow",
                                weather="day", seed="original one")
            draw_ambient_layers(*b, landscape="meadow",
                                weather="day", seed="original one")
            draw_ambient_layers(*c, landscape="river",
                                weather="night", seed="original one")
            self.assertEqual(a[0].read_bytes(), b[0].read_bytes())
            self.assertEqual(a[1].read_bytes(), b[1].read_bytes())
            self.assertNotEqual(a[1].read_bytes(), c[1].read_bytes())
            for p in a + c:
                with Image.open(p) as im:
                    self.assertEqual(im.size, (1280, 720))
                    self.assertEqual(im.mode, "RGBA")
                    self.assertEqual(im.getpixel((380, 380))[3], 0)
                    self.assertIsNotNone(im.getchannel("A").getbbox())
            with self.assertRaises(ValueError):
                draw_ambient_layers(*b, landscape="invalid",
                                    weather="day", seed="original one")
            with self.assertRaises(ValueError):
                draw_ambient_layers(*b, landscape="river",
                                    weather="day", seed="")

    def test_trusted_filter_has_two_distinct_speeds_and_stable_indices(self):
        original = ["background", "body", "effects"]
        graph, stage, names = append_ambient_overlays(
            graph="[prev]null[last]", label="last",
            names=original, weather="wind")
        self.assertEqual(original, ["background", "body", "effects"])
        self.assertEqual(names[-2:], ["ambient_far", "ambient_near"])
        self.assertEqual(stage, "ambientnear")
        self.assertIn("[last][3:v]overlay", graph)
        self.assertIn("[ambientfar][4:v]overlay", graph)
        self.assertIn("sin(t*0.459)", graph)
        self.assertIn("sin(t*1.105)", graph)
        with self.assertRaises(ValueError):
            append_ambient_overlays(graph="", label="x",
                                    names=names, weather="day")
        with self.assertRaises(ValueError):
            append_ambient_overlays(graph="", label="x",
                                    names=[], weather="thunderquake")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Requires actual offline FFmpeg and ffprobe")
    def test_river_biome_ambient_plates_encode_real_h264(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "animated-river.mp4"
            render_motion_clip(
                kind="rabbit", topic="Our original riverbank",
                narration="A little rabbit watches the river.",
                scene_index=2, scene_count=3,
                style="cartoon", duration=1.0,
                width=1280, height=720, fps=24,
                destination=destination, landscape="river",
                direction={"action": "idle", "weather": "day",
                           "emotion": "happy", "shot": "wide"})
            self.assertGreater(destination.stat().st_size, 1500)
            check = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=codec_name,width,height,nb_frames",
                 "-of", "json", str(destination)],
                capture_output=True, text=True, check=True, timeout=40)
            stream = json.loads(check.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"], "h264")
            self.assertEqual((stream["width"], stream["height"]), (1280, 720))
            self.assertEqual(int(stream["nb_frames"]), 24)


if __name__ == "__main__":
    unittest.main()
