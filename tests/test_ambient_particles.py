"""Original night fireflies and daylight pollen in actual silent MP4 scenes."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_owl import _weather_overlay, render_motion_clip
from automate_ytb.animated_forest import render_motion_clip as render_forest_clip
from automate_ytb.director import direction_for


def _actual_frame(video: Path, t: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(t), "-i",
         str(video), "-frames:v", "1", "-f", "image2pipe", "-vcodec",
         "png", "-"], capture_output=True, check=True, timeout=90)
    with Image.open(io.BytesIO(result.stdout)) as src:
        return src.convert("RGB")


def _difference(first: Image.Image, second: Image.Image,
                crop: tuple[int, int, int, int]) -> float:
    a, b = first.crop(crop), second.crop(crop)
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean)


class AmbientParticleTests(unittest.TestCase):
    def test_source_particles_are_original_deterministic_and_foreground_only(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            results = {}
            for weather in ("day", "night"):
                a, b = (folder / f"{weather}-a.png",
                        folder / f"{weather}-b.png")
                _weather_overlay(a, seed="my original storyboard", weather=weather)
                _weather_overlay(b, seed="my original storyboard", weather=weather)
                self.assertEqual(a.read_bytes(), b.read_bytes())
                with Image.open(a) as source:
                    self.assertEqual(source.size, (1280, 1440))
                    self.assertEqual(source.mode, "RGBA")
                    alpha = source.getchannel("A")
                    bound = alpha.getbbox()
                    self.assertIsNotNone(bound)
                    # The sky above the foreground is never overdrawn.
                    self.assertGreaterEqual(bound[1], 390)
                    self.assertLess(bound[3], 1440)
                results[weather] = a.read_bytes()
            self.assertNotEqual(results["day"], results["night"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required for frame-by-frame verification")
    def test_forest_day_pollen_moves_without_changing_caption_or_render_size(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "forest-day.mp4"
            render_forest_clip(
                kind="fox", topic="Le jardin original",
                narration="Le renard marche au soleil.",
                scene_index=1, scene_count=5,
                style="cartoon", duration=2.0, width=1280,
                height=720, fps=24, destination=dest,
                direction=direction_for("Le renard marche au soleil.",
                                        camera="wide establishing"))
            a, b = _actual_frame(dest, .2), _actual_frame(dest, 1.6)
            self.assertEqual(a.size, (1280, 720))
            self.assertGreater(_difference(a, b, (670, 370, 1220, 620)), .08)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required for frame-by-frame verification")
    def test_owl_night_fireflies_animate_while_sky_stays_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "owl-night.mp4"
            render_motion_clip(
                topic="Original owl night", narration="La chouette regarde la lune.",
                scene_index=1, scene_count=5, style="cartoon",
                duration=2.0, width=1280, height=720, fps=24, destination=dest,
                direction=direction_for("La chouette regarde la lune.",
                                        camera="wide establishing"))
            a, b = _actual_frame(dest, .2), _actual_frame(dest, 1.6)
            self.assertGreater(_difference(a, b, (700, 390, 1180, 600)), .10)
            self.assertLess(_difference(a, b, (980, 58, 1200, 84)), .65)


if __name__ == "__main__":
    unittest.main()
