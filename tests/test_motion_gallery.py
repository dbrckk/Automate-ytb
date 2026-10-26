"""Offline motion-review gallery must show genuine decoded production video."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from PIL import Image

from scripts.render_motion_gallery import (
    EXAMPLES, SAMPLE_FRAMES, render_motion_gallery,
)


class MotionReviewTests(unittest.TestCase):
    def test_curated_actions_and_frame_samples(self):
        self.assertEqual(set(EXAMPLES), {"fox", "rabbit", "cat", "owl"})
        self.assertEqual(len(SAMPLE_FRAMES), 4)
        self.assertEqual(tuple(sorted(SAMPLE_FRAMES)), SAMPLE_FRAMES)
        self.assertLess(SAMPLE_FRAMES[-1], round(1.45 * 24))
        with self.assertRaises(ValueError):
            render_motion_gallery(Path("/tmp/never.png"), actors=("unsafe",))
        with self.assertRaises(ValueError):
            render_motion_gallery(Path("/tmp/never.png"), actors=("fox", "fox"))
        with self.assertRaises(ValueError):
            render_motion_gallery(Path("/tmp/never.png"), actors=())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required for visual motion review")
    def test_review_uses_decoded_real_fox_animation_frames(self):
        with tempfile.TemporaryDirectory() as dirname:
            gallery = Path(dirname) / "motion-gallery.png"
            result = render_motion_gallery(gallery, actors=("fox",))
            self.assertTrue(gallery.is_file())
            self.assertEqual(result["characters"][0]["actor"], "fox")
            self.assertGreater(result["characters"][0]["meanDeltaScore"], 0.4)
            self.assertEqual(result["characters"][0]["frames"], 35)
            self.assertTrue((gallery.parent/"motion-clips"/"fox-jump.mp4").is_file())
            with Image.open(gallery) as image:
                self.assertEqual(image.size, (1920, 354))
            self.assertEqual(json.loads(gallery.with_suffix(".json").read_text())[
                "characters"][0]["codec"], "h264")


if __name__ == "__main__":
    unittest.main()
