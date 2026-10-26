"""Real scene-context atmosphere remains original, deterministic and animated."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.scenic_motion import (
    BIOMES, WEATHERS, SCENIC_MOTION_VERSION,
    draw_scenic_motion, overlay_scenic_motion)
from automate_ytb.animated_forest import render_motion_clip


class ScenicMotionTests(unittest.TestCase):
    def test_original_motion_plate_is_biome_specific_and_reproducible(self):
        self.assertIn("v1", SCENIC_MOTION_VERSION)
        self.assertEqual(BIOMES, {"forest", "river", "village", "meadow"})
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            generated = {}
            for place in sorted(BIOMES):
                path = root / (place + ".png")
                draw_scenic_motion(path, landscape=place, weather="day",
                                   seed="An original story|scene 2")
                data = path.read_bytes()
                generated[place] = data
                duplicate = root / (place + "-again.png")
                draw_scenic_motion(duplicate, landscape=place, weather="day",
                                   seed="An original story|scene 2")
                self.assertEqual(data, duplicate.read_bytes())
                with Image.open(path) as plate:
                    self.assertEqual(plate.size, (1280, 720))
                    self.assertEqual(plate.mode, "RGBA")
                    # Characters, mouth poses and held props stay clear.
                    self.assertEqual(plate.getpixel((400, 300))[3], 0)
                    self.assertIsNotNone(plate.getchannel("A").getbbox())
                    self.assertGreater(plate.getchannel("A").getbbox()[0], 650)
            self.assertEqual(len(set(generated.values())), 4)
            night = root / "night.png"
            draw_scenic_motion(night, landscape="forest", weather="night",
                               seed="An original story|scene 2")
            self.assertNotEqual(generated["forest"], night.read_bytes())
            with self.assertRaises(ValueError):
                draw_scenic_motion(night, landscape="unknown", weather="day",
                                   seed="valid")
            with self.assertRaises(ValueError):
                draw_scenic_motion(night, landscape="river", weather="sunny",
                                   seed="valid")

    def test_trusted_ffmpeg_animation_uses_weather_scaled_motion(self):
        initial = ["background", "body", "effects"]
        graph, label, names = overlay_scenic_motion(
            graph="[a]null[b]", label="b", names=initial,
            scene_index=2, weather="wind")
        self.assertEqual(label, "biomemotion")
        self.assertEqual(names[-1], "scenic_motion")
        self.assertEqual(initial, ["background", "body", "effects"])
        self.assertIn("[3:v]overlay=", graph)
        self.assertIn("-1*17*sin(t*0.63)", graph)
        self.assertIn("4*sin(t*0.47)", graph)
        self.assertNotIn("movie=", graph)
        with self.assertRaises(ValueError):
            overlay_scenic_motion(graph="x",label="x",names=names,
                                  scene_index=1,weather="day")
        with self.assertRaises(ValueError):
            overlay_scenic_motion(graph="x",label="x",names=[],
                                  scene_index=0,weather="day")
        with self.assertRaises(ValueError):
            overlay_scenic_motion(graph="x",label="x",names=[],
                                  scene_index=1,weather="not-weather")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual H264 encoded MP4 required")
    def test_real_720p_mp4_animates_independent_river_details(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "river-motion.mp4"
            render_motion_clip(
                kind="fox", topic="An original river adventure",
                narration="The fox wanders along the river.",
                scene_index=1, scene_count=3,
                style="cartoon", duration=1.55,
                width=1280, height=720, fps=24,
                landscape="river", destination=video,
                direction={"weather":"day","action":"idle",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(video.stat().st_size, 1400)
            def still(timestamp: float):
                got = subprocess.run(
                    ["ffmpeg","-nostdin","-v","error","-ss",str(timestamp),
                     "-i",str(video),"-frames:v","1","-f","image2pipe",
                     "-vcodec","png","-"],
                    check=True, capture_output=True, timeout=90)
                with Image.open(io.BytesIO(got.stdout)) as im:
                    return im.convert("RGB")
            a, b = still(0.15), still(1.15)
            self.assertEqual(a.size, (1280, 720))
            area = (795, 623, 1240, 706)
            change = ImageChops.difference(a.crop(area), b.crop(area))
            self.assertGreater(sum(ImageStat.Stat(change).mean), 0.12)


if __name__ == "__main__":
    unittest.main()
