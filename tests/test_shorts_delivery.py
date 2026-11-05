"""Platform export tests use actually encoded FFmpeg videos."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automate_ytb.shorts_delivery import validate_short


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Actual FFmpeg binaries are required")
class ShortsDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="shorts-delivery-")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _render(self, filename, shape, fps, with_audio):
        file = self.root / filename
        command = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
            "-y", "-f", "lavfi", "-i",
            f"color=c=darkblue:s={shape}:r={fps}:d=1.2",
        ]
        if with_audio:
            command += ["-f", "lavfi", "-i",
                        "sine=frequency=390:duration=1.2"]
        command += [
            "-c:v", "libx264", "-preset", "ultrafast",
            "-crf", "30", "-pix_fmt", "yuv420p",
        ]
        if with_audio:
            command += ["-c:a", "aac", "-ar", "48000", "-b:a", "96k"]
        else:
            command += ["-an"]
        command += ["-t", "1.2", str(file)]
        subprocess.run(command, capture_output=True, check=True, timeout=60)
        return file

    def test_real_vertical_h264_aac_is_upload_compatible(self):
        report = validate_short(
            self._render("vertical.mp4", "720x1280", 30, True),
            require_audio=True)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["uploadTechnicallyReady"])
        self.assertFalse(report["publicationApproved"])
        self.assertTrue(report["humanReviewRequired"])
        self.assertEqual(report["targetPlatforms"],
                         ["TikTok", "YouTube Shorts"])
        self.assertEqual(report["media"]["audioCodec"], "aac")

    def test_horizontal_and_missing_audio_fail_closed(self):
        report = validate_short(
            self._render("horizontal.mp4", "1280x720", 24, False),
            require_audio=True)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("9:16" in e for e in report["errors"]))
        self.assertTrue(any("audio" in e for e in report["errors"]))

    def test_missing_source_and_untrusted_flag_fail_closed(self):
        with self.assertRaises(ValueError):
            validate_short(self.root / "missing.mp4")
        with self.assertRaises(ValueError):
            validate_short(self.root / "missing.mp4", require_audio="true")


if __name__ == "__main__":
    unittest.main()
