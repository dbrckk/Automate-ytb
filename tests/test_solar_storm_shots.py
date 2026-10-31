"""Real NASA shot coverage and color-aware reviewer regressions."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from production.solar_storm import review_frames, review_shots


def _shots():
    # The actual authored production has 2+2+2+2+3+2 = 13 shots.
    distribution = (2, 2, 2, 2, 3, 2)
    return [
        {"scene": scene, "source": "sun131" if idx % 2 else "aurora",
         "start": 1.2, "duration": 1.1}
        for scene, count in enumerate(distribution) for idx in range(count)
    ]


def _frame(color: tuple[int, int, int]) -> Image.Image:
    frame = Image.new("RGB", (1080, 1920), color)
    ImageDraw.Draw(frame).ellipse((220, 500, 880, 1260), fill="white")
    return frame


class AllShotReviewTests(unittest.TestCase):
    def test_all_thirteen_actual_shots_are_sampled_and_labeled(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "final.mp4"
            source.write_bytes(b"ffmpeg extraction is patched")
            frames = [_frame(((idx*19)%170+20, (idx*13)%140+40, 100))
                      for idx in range(13)]
            output = Path(tmp) / "shot_contact_sheet.jpg"
            with patch.object(review_frames, "_frame", side_effect=frames) as extract:
                report = review_shots.review_encoded_shots(
                    source, _shots(), 14.3, output)
            self.assertEqual(extract.call_count, 13)
            self.assertEqual(report["sampled_shots"], 13)
            self.assertFalse(report["editorial_approved"])
            self.assertEqual(report["frames"][0]["narration_scene"], 1)
            self.assertEqual(report["frames"][-1]["narration_scene"], 6)
            self.assertEqual(report["frames"][-1]["shot"], 13)
            self.assertEqual(report["frames"][-1]["source"], "aurora")
            with Image.open(output) as rendered:
                self.assertEqual(rendered.format, "JPEG")
                self.assertEqual(rendered.size, (1080, 3430))

    def test_incorrect_timeline_and_invalid_sources_are_rejected(self):
        good = _shots()
        with self.assertRaisesRegex(ValueError, "duration mismatch"):
            review_shots.timeline(good, 20)
        with self.assertRaisesRegex(ValueError, "shot 2"):
            altered = [dict(x) for x in good]
            altered[1]["source"] = "bad\nlabel"
            review_shots.timeline(altered, 14.3)
        with self.assertRaisesRegex(ValueError, "six narrated"):
            review_shots.timeline(good[:-2], 12.1)
        with self.assertRaisesRegex(ValueError, "shot 1"):
            altered = [dict(x) for x in good]
            altered[0]["scene"] = 2
            review_shots.timeline(altered, 14.3)

    def test_same_grayscale_different_colors_do_not_trigger_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"final.mp4"
            src.write_bytes(b"mocked frame extraction")
            a = _frame((190, 20, 20))
            b = _frame((20, 140, 20))
            # Both show the same silhouette; simple luminance hash can collide.
            with patch.object(review_frames, "_frame", side_effect=[a, b]):
                report = review_frames.create_contact_sheet(
                    src,[{"start": 0, "end": 1}, {"start": 1, "end": 2}],
                    Path(tmp)/"sheet.jpg")
            self.assertFalse(report["frames"][1]["possible_duplicate_of"])

    def test_identical_frames_still_generate_review_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"final.mp4"
            src.write_bytes(b"mocked frame extraction")
            a = _frame((50, 90, 140))
            with patch.object(review_frames, "_frame", side_effect=[a, a.copy()]):
                report = review_frames.create_contact_sheet(
                    src,[{"start": 0, "end": 1}, {"start": 1, "end": 2}],
                    Path(tmp)/"sheet.jpg")
            self.assertEqual(report["frames"][1]["possible_duplicate_of"], [1])
            self.assertTrue(report["warnings"])

    def test_untrusted_contact_sheet_labels_cannot_inject_newlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)/"final.mp4"
            src.write_bytes(b"mocked video")
            with self.assertRaisesRegex(ValueError, "labels"):
                review_frames.create_contact_sheet(
                    src,[{"start": 0, "end": 1}],Path(tmp)/"sheet.jpg",
                    labels=["SHOT\nWARNING"])


if __name__ == "__main__":
    unittest.main()
