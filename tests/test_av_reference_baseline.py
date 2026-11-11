"""Real technical AV benchmarking; no unapproved video or voice data in Git."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_audiovisual.py"
SPEC = importlib.util.spec_from_file_location("benchmark_audiovisual", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)


class BaselineUnitTests(unittest.TestCase):
    def test_changed_pixels_statistics_and_no_motion(self):
        size = BENCH.FRAME_BYTES
        dark = b"\x00" * size
        white = b"\xff" * size
        m = BENCH._motion_metrics(dark + dark + white)
        self.assertEqual(m["sampleCount"], 3)
        self.assertEqual(m["motionPairs"], 2)
        self.assertEqual(m["medianChangedPixelsPercent"], 50.0)
        self.assertEqual(m["meanChangedPixelsPercent"], 50.0)
        self.assertEqual(m["p90ChangedPixelsPercent"], 100.0)
        self.assertEqual(m["nearBlackSamples"], 2)
        self.assertEqual(m["maxConsecutiveNearFrozenPairs"], 1)

    def test_reject_partial_or_insufficient_decoded_frames(self):
        with self.assertRaises(ValueError):
            BENCH._motion_metrics(b"\x00" * (BENCH.FRAME_BYTES + 2))
        with self.assertRaises(ValueError):
            BENCH._motion_metrics(b"\x00" * BENCH.FRAME_BYTES)

    def test_safe_labels_required_before_opening_private_paths(self):
        for label in ("PRIVATE/secret", "../home", "", "A", "image.png", "has space"):
            with self.subTest(label=label), self.assertRaises(ValueError):
                BENCH.measure(Path("/no-such-file"), label)

    def test_reference_metrics_document_is_metadata_only(self):
        benchmark = json.loads((ROOT / "docs" / "av-reference-baseline-2026-11-11.json").read_text(encoding="utf-8"))
        self.assertEqual(benchmark["schemaVersion"], 1)
        self.assertFalse(benchmark["automatedArtisticJudgment"])
        self.assertFalse(benchmark["humanAudioReviewCompleted"])
        self.assertEqual([v["label"] for v in benchmark["videos"]],
                         ["reference-private", "ocean-baseline"])
        for item in benchmark["videos"]:
            self.assertNotIn("sourcePath", item)
            self.assertNotIn("frames", item)
            self.assertNotIn("PCM", item)
            self.assertEqual(len(item["sha256"]), 64)
            self.assertGreater(item["motion"]["sampleCount"], 50)
            self.assertEqual(item["media"]["videoCodec"], "h264")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe are required for full AV smoke testing")
class BaselineRealMediaTests(unittest.TestCase):
    def test_encoded_synthetic_mp4_and_privacy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "local-secret-name.mp4"
            target = root / "baseline.json"
            # This video is generated here: no third-party assets or downloads.
            subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "testsrc2=size=160x288:rate=30:duration=2.5",
                            "-f", "lavfi", "-i", "sine=frequency=440:duration=2.5",
                            "-shortest", "-c:v", "libx264", "-preset", "ultrafast",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", str(source)],
                           check=True, timeout=45)
            self.assertEqual(BENCH.main(["--video", str(source), "--label", "synthetic", "--output", str(target)]), 0)
            report = json.loads(target.read_text(encoding="utf-8"))
            v = report["videos"][0]
            self.assertEqual(v["media"]["width"], 160)
            self.assertEqual(v["media"]["height"], 288)
            self.assertEqual(v["media"]["videoCodec"], "h264")
            self.assertEqual(v["audio"]["measurement"], "ffmpeg-ebur128-peak-true")
            self.assertGreater(v["motion"]["medianChangedPixelsPercent"], 0)
            self.assertNotIn("local-secret-name", target.read_text(encoding="utf-8"))
            self.assertNotIn(str(root), target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
