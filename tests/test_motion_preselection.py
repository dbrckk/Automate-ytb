"""Real FFmpeg and deterministic regression checks for M2 source motion selection."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.auto_edit import _sample_quality, select_excerpts
from automate_ytb.shot_diversity import NEAR_STATIC_PIXEL_DELTA


class MotionSelectionTests(unittest.TestCase):
    def test_prefers_genuine_moving_candidate_when_source_has_slack(self):
        candidates = []
        def measured(_source, start, _seconds):
            candidates.append(start)
            dynamic = start > 7.
            return {
                "sampledFrames": 3, "spatialSignature": [90]*48,
                "technicalSelectionScore": .67 if dynamic else .32,
                "temporalNearStaticSource": not dynamic,
                "temporalSourcePixelDeltas": [9., 12.] if dynamic else [0., 0.],
                "requiresVisualReview": False,
            }
        with patch("automate_ytb.auto_edit._sample_quality", side_effect=measured):
            shots = select_excerpts([Path("owned.mp4")], [4000], [14000], (1,))
        self.assertEqual(len(shots), 1)
        self.assertGreater(shots[0]["candidateCount"], 1)
        self.assertGreater(shots[0]["startSeconds"], 7)
        self.assertFalse(shots[0]["technicalReview"]["temporalNearStaticSource"])
        self.assertTrue(all(0 <= start <= 10 for start in candidates))

    def test_still_only_sources_preserve_nonoverlap_and_review_flag(self):
        def measured(_source, _start, _seconds):
            return {
                "sampledFrames": 3, "spatialSignature": [70]*48,
                "technicalSelectionScore": .1,
                "temporalNearStaticSource": True,
                "temporalSourcePixelDeltas": [0., 0.],
                "requiresVisualReview": False,
            }
        with patch("automate_ytb.auto_edit._sample_quality", side_effect=measured):
            shots = select_excerpts([Path("owned.mp4")], [4000, 4000], [8000], (2,))
        self.assertEqual(len(shots), 2)
        self.assertTrue(all(s["technicalReview"]["temporalNearStaticSource"] for s in shots))
        self.assertEqual([s["startSeconds"] for s in shots], [0., 4.])


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
class RealTemporalSamplesTests(unittest.TestCase):
    def test_decoded_static_vs_moving_original_video(self):
        with tempfile.TemporaryDirectory() as folder:
            for name, source, static in (
                ("still", "color=c=gray:size=160x120:rate=12", True),
                ("moving", "testsrc2=size=160x120:rate=12", False),
            ):
                with self.subTest(name=name):
                    movie = Path(folder) / f"{name}.mp4"
                    subprocess.run([
                        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                        "-y", "-f", "lavfi", "-i", source,
                        "-t", "7", "-c:v", "mpeg4", "-q:v", "5",
                        "-threads", "1", str(movie),
                    ], capture_output=True, check=True, timeout=35)
                    report = _sample_quality(movie, 0, 6)
                    self.assertEqual(report["sampledFrames"], 3)
                    self.assertEqual(len(report["temporalSourcePixelDeltas"]), 2)
                    self.assertEqual(report["temporalNearStaticSource"], static)
                    self.assertEqual(report["temporalSelectionPenalty"],
                                     .35 if static else 0.)
                    if not static:
                        self.assertGreater(max(report["temporalSourcePixelDeltas"]),
                                           NEAR_STATIC_PIXEL_DELTA)

    def test_invalid_window_fails_before_source_decode(self):
        with self.assertRaisesRegex(ValueError, "Invalid bounded"):
            _sample_quality(Path("missing.mp4"), float("nan"), 5)
        with self.assertRaisesRegex(ValueError, "Invalid bounded"):
            _sample_quality(Path("missing.mp4"), 0, 0)


if __name__ == "__main__":
    unittest.main()
