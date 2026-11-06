"""Integration tests: real encoded moving footage and actual FFmpeg camera filter."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.subject_reframe import crop_expression, track_crop


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Real FFmpeg/ffprobe required for optical tracking tests")
class PortraitTrackingIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="optical-shorts-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def make_moving_subject(self) -> Path:
        # A genuine moving encoded MP4, not mocked decoded frames.
        from PIL import Image, ImageDraw
        frames = 36
        path = self.root / "moving-original.mp4"
        p = subprocess.Popen([
            "ffmpeg", "-nostdin", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", "480x270", "-r", "12", "-i", "pipe:0",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", path.as_posix(),
        ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for frame in range(frames):
                img = Image.new("RGB", (480, 270), (3, 10, 19))
                pen = ImageDraw.Draw(img)
                x = round(82 + 290 * frame / (frames - 1))
                pen.ellipse((x - 27, 96, x + 27, 152),
                            fill=(205, 245, 245))
                assert p.stdin is not None
                p.stdin.write(img.tobytes())
            p.stdin.close()
            assert p.stderr is not None
            err = p.stderr.read().decode("utf8", "replace")
            if p.wait(timeout=30):
                raise RuntimeError(err[-450:])
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()
        return path

    def test_moving_subject_tracked_and_camera_renders(self):
        original = self.make_moving_subject()
        report = track_crop(source=original, start=0, seconds=3.0,
                            source_width=480, crop_width=152)
        frames = report["keyframes"]
        self.assertGreaterEqual(report["sampledFrames"], 5)
        self.assertGreater(frames[-1]["cropX"] - frames[0]["cropX"], 60)
        self.assertTrue(all(0 <= f["cropX"] <= 328
                            and f["cropX"] % 2 == 0 for f in frames))
        self.assertTrue(all(a["timeSeconds"] < b["timeSeconds"]
                            for a, b in zip(frames, frames[1:])))
        self.assertTrue(report["requiresVisualReview"])
        self.assertNotIn("object-detection", report["method"])

        dynamic = self.root / "vertical-camera.mp4"
        expr = crop_expression(report)
        proc = subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(original),
            "-vf", f"setpts=PTS-STARTPTS,crop=152:270:x='{expr}':y=0,"
                   "scale=180:320:flags=bicubic,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", str(dynamic),
        ], capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr[-1000:])
        data = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "stream=width,height", "-of", "json", str(dynamic),
        ])
        self.assertEqual(
            (json.loads(data)["streams"][0]["width"],
             json.loads(data)["streams"][0]["height"]), (180, 320))
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(dynamic),
                        "-f", "null", "-"],
                       check=True, timeout=60)

    def test_near_black_fallback_stays_centered(self):
        dark = self.root / "dark.mp4"
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-y",
            "-f", "lavfi", "-i",
            "color=c=black:s=480x270:r=12:d=2.1",
            "-c:v", "libx264", "-preset", "ultrafast", str(dark),
        ], check=True, timeout=30)
        report = track_crop(source=dark, start=0, seconds=2.0,
                            source_width=480, crop_width=152)
        self.assertEqual(report["lowInformationFrames"], report["sampledFrames"])
        self.assertEqual(len(set(x["cropX"] for x in report["keyframes"])), 1)

    def test_malformed_video_and_crop_rejected(self):
        with self.assertRaises((ValueError, RuntimeError)):
            track_crop(source=self.root / "missing.webm", start=0, seconds=3,
                       source_width=480, crop_width=152)
        with self.assertRaises(ValueError):
            track_crop(source=self.root / "missing.webm", start=-1, seconds=3,
                       source_width=480, crop_width=152)
        with self.assertRaises(ValueError):
            crop_expression({"sourceWidth": 480, "cropWidth": 152,
                             "keyframes": [{"cropX": 700, "timeSeconds": 0}]})


if __name__ == "__main__":
    unittest.main()
