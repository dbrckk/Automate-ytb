"""Evidence-based visual defects in compressed MP4s, without editorial overclaim."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automate_ytb.visual_preflight import (
    SAMPLE_FPS, SAMPLE_SIZE, VISUAL_QA_VERSION,
    analyze_samples, inspect_video,
)


class VisualPreflightTests(unittest.TestCase):
    def test_black_white_and_flash_are_diagnostic_not_approval(self):
        w,h=96,54
        pixels=w*h
        black=bytes([0])*pixels
        white=bytes([255])*pixels
        report=analyze_samples(black+white+black, width=w, height=h, fps=2)
        self.assertIn("v1", VISUAL_QA_VERSION)
        self.assertEqual(report["nearBlackFrames"],2)
        self.assertEqual(report["nearWhiteFrames"],1)
        self.assertEqual(report["largeLumaSteps"],2)
        self.assertEqual(report["status"],"review")
        self.assertGreater(len(report["warnings"]),1)

    def test_still_frames_and_missing_frames_require_review(self):
        frame=bytes((i%170)+40 for i in range(96*54))
        report=analyze_samples(frame*8)
        self.assertGreaterEqual(report["consecutiveNearStillFrames"],4)
        self.assertEqual(report["status"],"review")
        empty=analyze_samples(b"")
        self.assertEqual(empty["sampledFrames"],0)
        self.assertEqual(empty["status"],"review")

    def test_actual_moving_frames_are_not_mislabelled_still(self):
        frames=b"".join(bytes(((j*3+i*9)%170)+30 for j in range(96*54))
                       for i in range(8))
        report=analyze_samples(frames)
        self.assertEqual(report["status"],"no-obvious-sampled-defects")
        self.assertEqual(report["consecutiveNearStillFrames"],0)
        self.assertEqual(report["sampledDurationSeconds"],4)

    def test_reject_bad_raw_sample_shapes_and_files(self):
        with self.assertRaises(ValueError):
            analyze_samples(b"a", width=96,height=54)
        with self.assertRaises(ValueError):
            analyze_samples(bytes(96*54),fps=0)
        with self.assertRaises(ValueError):
            analyze_samples(bytes(96*54),width=100000)
        with self.assertRaises(ValueError):
            inspect_video(Path("/tmp/no-such-visual-preflight-video.mp4"))

    @unittest.skipUnless(shutil.which("ffmpeg"), "Actual local FFmpeg required")
    def test_actual_h264_mp4_uses_decoded_sampled_video_not_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/"animation.mp4"
            subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-y",
                 "-f","lavfi","-i","testsrc2=size=96x54:rate=24",
                 "-t","1.4","-c:v","libx264","-threads","1",
                 "-pix_fmt","yuv420p",str(dest)],
                capture_output=True,check=True,timeout=40)
            report=inspect_video(dest)
            self.assertGreaterEqual(report["sampledFrames"],2)
            self.assertEqual(report["sampleRateFps"],SAMPLE_FPS)
            self.assertEqual(report["version"],VISUAL_QA_VERSION)
            self.assertNotEqual(report["status"],"inspection-failed")


if __name__=="__main__":
    unittest.main()
