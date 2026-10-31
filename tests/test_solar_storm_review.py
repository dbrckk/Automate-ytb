"""Focused QA for actual Solar Storm scene review and contact-sheet export."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from production.solar_storm import review_frames


class SolarStormReviewTests(unittest.TestCase):
    def test_actual_images_are_exported_outside_the_final_mp4(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            video = folder / "solar.mp4"
            video.write_bytes(b"placeholder; image extraction is patched")
            first = Image.new("RGB", (1080, 1920), (12, 34, 66))
            second = Image.new("RGB", (1080, 1920), (55, 90, 132))
            ImageDraw.Draw(first).ellipse((230, 460, 800, 1160), fill="yellow")
            ImageDraw.Draw(second).rectangle((270, 510, 820, 1350), fill="orange")
            with patch.object(review_frames, "_frame", side_effect=[first, second]) as decode:
                result = review_frames.create_contact_sheet(
                    video, [{"start": .1, "end": .9}, {"start": 1.1, "end": 1.9}],
                    folder / "contact_sheet.jpg")
            self.assertEqual(decode.call_count, 2)
            self.assertEqual(result["sampled_scenes"], 2)
            self.assertFalse(result["editorial_approved"])
            self.assertEqual(len(result["frames"]), 2)
            with Image.open(folder / "contact_sheet.jpg") as sheet:
                self.assertEqual(sheet.size, (720, 686))
                self.assertEqual(sheet.format, "JPEG")

    def test_black_frames_cannot_pass_technical_visual_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "video.mp4"
            video.write_bytes(b"placeholder")
            with patch.object(review_frames, "_frame",
                              return_value=Image.new("RGB", (1080, 1920))):
                with self.assertRaisesRegex(RuntimeError, "Blank decoded"):
                    review_frames.create_contact_sheet(
                        video, [{"start": 0., "end": 1.}], Path(tmp)/"sheet.jpg")

    def test_nonmonotonic_narration_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "video.mp4"
            video.write_bytes(b"placeholder")
            frame = Image.new("RGB", (1080, 1920), "blue")
            ImageDraw.Draw(frame).rectangle((100, 100, 900, 900), fill="white")
            with patch.object(review_frames, "_frame", return_value=frame):
                with self.assertRaisesRegex(ValueError, "timeline"):
                    review_frames.create_contact_sheet(
                        video, [{"start": 1, "end": 2},
                                {"start": .5, "end": 1.5}], Path(tmp)/"sheet.jpg")

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg not installed")
    def test_real_h264_encode_and_frame_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "video.mp4"
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=5:duration=1",
                 "-c:v", "libx264", "-preset", "ultrafast",
                 "-pix_fmt", "yuv420p", str(video)],
                timeout=60, check=True)
            result = review_frames.create_contact_sheet(
                video, [{"start": .1, "end": .8}], Path(tmp)/"sheet.jpg")
            self.assertEqual(result["sampled_scenes"], 1)
            self.assertGreater(result["frames"][0]["channel_contrast"], 5)


if __name__ == "__main__":
    unittest.main()
