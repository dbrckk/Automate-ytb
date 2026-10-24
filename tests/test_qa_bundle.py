"""Preserving both independent QA reports and preventing false publication approval."""
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.qa_bundle import consolidate


class QualityBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.structural = self.root / "quality-report.json"
        self.media = self.root / "media-report.json"
        self.video = self.root / "preview.mp4"
        self.srt = self.root / "draft-captions.srt"
        self.vtt = self.root / "draft-captions.vtt"
        self.output = self.root / "qa-summary.json"
        self.video.write_bytes(b"mock-video-body" * 250)
        self.srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello.\n", encoding="utf8")
        self.vtt.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello.\n", encoding="utf8")
        self.structural.write_text(json.dumps({
            "status": "passed", "publicationApproved": False,
            "checks": {"actualDurationSeconds": 2.0},
            "errors": [], "warnings": ["Original narration needs review"],
        }), encoding="utf8")
        self.media.write_text(json.dumps({
            "status": "pass", "publicationApproved": False,
            "media": {"fileBytes": self.video.stat().st_size, "durationSeconds": 2.0,
                      "width": 1280, "height": 720},
            "subtitleCues": 1, "errors": [], "warnings": [],
        }), encoding="utf8")

    def tearDown(self):
        self.temp.cleanup()

    def run_check(self):
        return consolidate(structural_report=self.structural, media_report=self.media,
                           video=self.video, srt=self.srt, vtt=self.vtt,
                           output=self.output)

    def test_separate_reports_and_combined_manifest(self):
        original_a, original_b = self.structural.read_bytes(), self.media.read_bytes()
        result = self.run_check()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["technicalPreviewReady"])
        self.assertFalse(result["publicationApproved"])
        self.assertEqual(result["checks"]["subtitleCues"], 1)
        self.assertEqual(self.structural.read_bytes(), original_a)
        self.assertEqual(self.media.read_bytes(), original_b)
        self.assertEqual(json.loads(self.output.read_text())["status"], "passed")

    def test_independent_failure_blocks_completion(self):
        data = json.loads(self.media.read_text())
        data["status"] = "fail"
        data["errors"] = ["Corrupted subtitles"]
        self.media.write_text(json.dumps(data))
        result = self.run_check()
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["technicalPreviewReady"])
        self.assertFalse(result["publicationApproved"])

    def test_mismatched_video_and_reports_are_blocking(self):
        data = json.loads(self.media.read_text())
        data["media"]["fileBytes"] = 10
        self.media.write_text(json.dumps(data))
        self.assertFalse(self.run_check()["technicalPreviewReady"])
        data["media"]["fileBytes"] = self.video.stat().st_size
        data["media"]["durationSeconds"] = 5.0
        self.media.write_text(json.dumps(data))
        self.assertFalse(self.run_check()["technicalPreviewReady"])

    def test_missing_vtt_or_bad_signature_rejected(self):
        self.vtt.unlink()
        with self.assertRaisesRegex(ValueError, "required"):
            self.run_check()
        self.vtt.write_text("Malformed", encoding="utf8")
        self.assertEqual(self.run_check()["status"], "failed")


if __name__ == "__main__":
    unittest.main()
