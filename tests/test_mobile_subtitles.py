"""Short mobile captions: timing integrity, readability and fail-closed behavior."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from automate_ytb.mobile_subtitles import (
    MAX_CHARS, MIN_SEGMENT_MS, create_mobile_srt, parse_srt, segment_cues,
)


class MobileCaptionsTests(unittest.TestCase):
    SOURCE = (
        "1\n00:00:00,000 --> 00:00:04,590\n"
        "These luminous waves are real auroras, seen in time-lapse photographs from the\n\n"
        "2\n00:00:04,590 --> 00:00:07,000\n"
        "International Space Station.\n\n"
        "3\n00:00:07,000 --> 00:00:11,300\n"
        "Charged particles from the Sun are guided toward Earth's polar regions by\n\n"
        "4\n00:00:11,300 --> 00:00:14,000\nits magnetic field.\n\n"
    )

    def test_short_word_groups_preserve_real_phrase_times_and_every_word(self):
        original = parse_srt(self.SOURCE)
        mobile = segment_cues(original)
        self.assertGreater(len(mobile), len(original))
        self.assertEqual(mobile[0][0], 0)
        self.assertEqual(mobile[-1][1], 14000)
        self.assertEqual(
            " ".join(row[2] for row in mobile),
            " ".join(row[2] for row in original),
        )
        self.assertTrue(all(len(text) <= MAX_CHARS for _, _, text in mobile))
        self.assertTrue(all(end - start >= MIN_SEGMENT_MS for start, end, _ in mobile))
        self.assertTrue(all(left[1] == right[0] for left, right in zip(mobile, mobile[1:])))

    def test_mobile_file_has_valid_srt_and_binding_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "original.srt"
            dst = Path(temp) / "mobile.srt"
            src.write_text(self.SOURCE, encoding="utf-8")
            report = create_mobile_srt(src, dst)
            self.assertGreater(report["mobileCues"], report["sourceCues"])
            self.assertEqual(parse_srt(dst.read_text()), segment_cues(parse_srt(self.SOURCE)))
            self.assertIn("proportional", report["timingMethod"])
            self.assertFalse(report["publicationApproved"])

    def test_rejects_duplicate_or_overlapping_cues(self):
        bad = self.SOURCE.replace(
            "00:00:04,590 --> 00:00:07,000",
            "00:00:03,500 --> 00:00:07,000",
        )
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            parse_srt(bad)

    def test_rejects_invalid_timing_and_bad_index(self):
        for content in (
            self.SOURCE.replace("1\n", "2\n", 1),
            self.SOURCE.replace("00:00:04,590", "00:00:74,590", 1),
            self.SOURCE.replace("00:00:04,590", "00:00:00,000", 1),
        ):
            with self.subTest(content=content[:35]):
                with self.assertRaises(ValueError):
                    parse_srt(content)

    def test_refuses_caption_that_cannot_fit_in_measured_audio_time(self):
        with self.assertRaisesRegex(ValueError, "cannot fit"):
            segment_cues([(0, 350, "This sentence contains far more than eight words for a fraction of a second")])

    def test_refuses_unbreakable_long_word(self):
        with self.assertRaisesRegex(ValueError, "Unbreakable"):
            segment_cues([(0, 1000, "a" * (MAX_CHARS + 1))])

    def test_rejects_missing_file_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "input.srt"
            alias = Path(temp) / "alias.srt"
            with self.assertRaises(ValueError):
                create_mobile_srt(src, Path(temp) / "out.srt")
            src.write_text(self.SOURCE)
            alias.symlink_to(src)
            with self.assertRaises(ValueError):
                create_mobile_srt(alias, Path(temp) / "out.srt")


if __name__ == "__main__":
    unittest.main()
