"""Evidence-based visual defects in compressed MP4s, without editorial overclaim."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automate_ytb.visual_preflight import (
    SAMPLE_FPS, SAMPLE_SIZE, VISUAL_QA_VERSION,
    analyze_samples, inspect_video, sampling_windows,
)


class VisualPreflightTests(unittest.TestCase):
    def test_black_white_and_flash_are_diagnostic_not_approval(self):
        w,h=96,54
        pixels=w*h
        black=bytes([0])*pixels
        white=bytes([255])*pixels
        report=analyze_samples(black+white+black, width=w, height=h, fps=2)
        self.assertIn("v2", VISUAL_QA_VERSION)
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

    def test_full_episode_sampling_is_bounded_and_time_distributed(self):
        self.assertEqual(sampling_windows(1.4), [(0.0, 1.4)])
        self.assertEqual(sampling_windows(18), [(0.0, 18.0)])
        self.assertEqual(sampling_windows(120),
                         [(0.0, 6.0), (57.0, 6.0), (114.0, 6.0)])
        for duration in (18.01, 19, 100, 900, 3600):
            windows = sampling_windows(duration)
            self.assertEqual(len(windows), 3)
            self.assertEqual(windows[0][0], 0)
            self.assertLessEqual(sum(length for _, length in windows), 18)
            self.assertTrue(all(start >= 0 and start + length <= duration + .001
                                for start, length in windows))
        for invalid in (0, -1, float("nan"), float("inf"), True, 100000000):
            with self.assertRaises(ValueError):
                sampling_windows(invalid)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg with ffprobe required")
    def test_late_black_tail_is_found_without_scanning_full_video(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/"late-black.mp4"
            subprocess.run(
                ["ffmpeg","-nostdin","-hide_banner","-v","error","-y",
                 "-f","lavfi","-i","testsrc2=size=96x54:rate=12",
                 "-t","22","-vf","fade=t=out:st=18:d=0.2",
                 "-threads","1","-c:v","libx264","-preset","ultrafast",
                 "-pix_fmt","yuv420p",str(dest)],
                capture_output=True,check=True,timeout=60)
            report=inspect_video(dest)
            self.assertEqual(report["samplingStrategy"],"opening-middle-ending")
            self.assertEqual(len(report["sampledWindows"]),3)
            self.assertLessEqual(report["sampledFrames"],36)
            self.assertGreaterEqual(report["videoDurationSeconds"],21)
            self.assertEqual(report["sampledWindows"][0]["nearBlackFrames"],0)
            self.assertGreater(report["sampledWindows"][-1]["nearBlackFrames"],0)
            self.assertEqual(report["status"],"review")
            self.assertTrue(any("16.00s" in text for text in report["warnings"]))

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
