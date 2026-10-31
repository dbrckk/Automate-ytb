"""Real 30fps NASA-source camera motion and non-stretched 9:16 FFmpeg QA."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw, ImageStat
from production.solar_storm.camera_motion import (
    ENGINE, PANS, SOURCE_TYPES, build_portrait_camera, camera_metadata,
)


class SolarCinematicCameraTests(unittest.TestCase):
    def test_every_authored_shot_has_safe_native_vertical_camera(self):
        self.assertEqual(len(PANS), 13)
        for index in range(13):
            for key in ("sun131", "magnetosphere", "aurora", "cme_launch"):
                graph = build_portrait_camera(key, index)
                self.assertTrue(graph.startswith("fps=30,scale=1080:1920:"))
                self.assertIn("crop=1080:1920:", graph)
                self.assertIn("zoompan=z=", graph)
                self.assertIn("d=1:s=1080x1920:fps=30", graph)
                self.assertIn("force_original_aspect_ratio=increase", graph)
                self.assertIn("format=yuv420p", graph)
                self.assertNotIn("setpts=", graph)
        meta = camera_metadata("cme_launch", 5)
        self.assertEqual(meta["engine"], ENGINE)
        self.assertEqual(meta["focal_subject"], "sunward CME launch")
        self.assertIs(meta["time_stretched"], False)

    def test_rejects_unreviewed_media_keys_and_unsafe_indices(self):
        for bad_key in ("cme", "../../secret", "", "new_source"):
            with self.assertRaises(ValueError):
                build_portrait_camera(bad_key, 0)
        for bad_index in (-1, 13, 10.5, True):
            with self.assertRaises(ValueError):
                build_portrait_camera("sun131", bad_index)

    def test_real_ffmpeg_output_has_motion_and_correct_timing(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            still = Image.new("RGB", (640, 360), (18, 33, 57))
            draw = ImageDraw.Draw(still)
            for x in range(0, 640, 35):
                draw.rectangle((x, 0, x + 11, 359),
                               fill=(50 + x // 12, 75 + x // 20, 125))
            draw.ellipse((220, 35, 420, 280), fill=(255, 150, 40))
            frame = folder / "fixed.png"
            still.save(frame)
            dest = folder / "moving.mp4"
            duration = 1.1
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30",
                "-i", str(frame), "-t", str(duration),
                "-vf", build_portrait_camera("sun131", 0),
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "27",
                "-pix_fmt", "yuv420p", str(dest)
            ], check=True, timeout=55)
            result = subprocess.run([
                "ffprobe", "-v", "error", "-of", "json",
                "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                str(dest)
            ], check=True, capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)
            self.assertEqual(info["streams"][0]["width"], 1080)
            self.assertEqual(info["streams"][0]["height"], 1920)
            self.assertEqual(info["streams"][0]["r_frame_rate"], "30/1")
            self.assertAlmostEqual(float(info["format"]["duration"]),
                                   duration, delta=0.12)
            sampled = []
            for second in (0.1, 0.9):
                shot = folder / f"{second:.1f}.png"
                subprocess.run([
                    "ffmpeg", "-y", "-v", "error", "-ss", str(second),
                    "-i", str(dest), "-frames:v", "1", "-update", "1", str(shot)
                ], check=True, timeout=25)
                with Image.open(shot) as raw:
                    sampled.append(raw.convert("RGB").resize((90, 160)))
            delta = ImageStat.Stat(ImageChops.difference(*sampled)).mean
            self.assertGreater(max(delta), 0.4, "Encoded crop is still frozen")


if __name__ == "__main__":
    unittest.main()
