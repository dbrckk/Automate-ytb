"""V2 animated camera is smooth, bounded, deterministic and encoded into MP4."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image, ImageChops, ImageStat

from automate_ytb.cinematic_camera import (
    CAMERA_VERSION, PROFILES, framing_filter, framing_metadata)
from automate_ytb.animated_forest import render_motion_clip


def image_at(video: Path, t: float) -> Image.Image:
    out = subprocess.run(["ffmpeg", "-nostdin", "-v", "error",
                          "-ss", str(t), "-i", str(video), "-frames:v", "1",
                          "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True, timeout=90)
    with Image.open(io.BytesIO(out.stdout)) as image:
        return image.convert("RGB")


class SmoothCinematicTests(unittest.TestCase):
    def test_eased_camera_has_safe_boundaries_and_opposite_directions(self):
        self.assertIn("v3", CAMERA_VERSION)
        for shot, (_, _, _, _, dx, dy) in PROFILES.items():
            for idx in (1, 2):
                expr = framing_filter(shot, width=1280, height=720,
                                      fps=24, scene_index=idx, duration=4.2)
                self.assertIn("format=yuv420p", expr)
                self.assertNotIn("movie=", expr)
                if dx or dy:
                    self.assertIn("min(1,max(0,n/", expr)
                    self.assertIn("crop=", expr)
                    self.assertEqual(framing_metadata(shot)["easing"], "smoothstep")
                else:
                    self.assertEqual(expr, "scale=1280:720:flags=lanczos,format=yuv420p")
            if dx or dy:
                first = framing_filter(shot, width=1280, height=720,
                                       fps=24, scene_index=1, duration=4.2)
                other = framing_filter(shot, width=1280, height=720,
                                       fps=24, scene_index=2, duration=4.2)
                self.assertNotEqual(first, other)

    def test_easing_input_rejects_unsafe_non_numeric_duration(self):
        for bad in (-2, 0, 3601, True, "2;movie=/etc/passwd", None):
            if bad is None:
                continue  # None intentionally preserves legacy callers.
            with self.assertRaises(ValueError):
                framing_filter("medium", width=1280, height=720,
                               fps=24, duration=bad)
        self.assertIn("sin(n/", framing_filter(
            "medium", width=1280, height=720, fps=24))
        with self.assertRaises(ValueError):
            framing_filter("wide;movie=/etc/passwd", width=1280,
                           height=720, fps=24, duration=2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg needed for visual camera verification")
    def test_encoded_smooth_camera_moves_at_real_scene_resolution(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/"camera.mp4"
            render_motion_clip(
                kind="fox", topic="Original sunny river story",
                narration="The fox walks by the quiet river.",
                scene_index=1, scene_count=3, style="cartoon",
                duration=2.4, width=1280, height=720, fps=24,
                destination=destination,
                direction={"weather": "day", "action": "idle",
                           "emotion": "happy", "shot": "medium"})
            self.assertGreater(destination.stat().st_size, 1000)
            early = image_at(destination, .2)
            late = image_at(destination, 2.0)
            self.assertEqual(early.size, (1280, 720))
            diff = ImageChops.difference(early.crop((690, 230, 1190, 530)),
                                         late.crop((690, 230, 1190, 530)))
            self.assertGreater(sum(ImageStat.Stat(diff).mean), .2)


if __name__ == "__main__":
    unittest.main()
