"""Preserving both independent QA reports and preventing false publication approval."""
import json
from pathlib import Path
import tempfile

from PIL import Image
from automate_ytb.production import _sha
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

    def test_visual_report_required_when_explicit_and_checked_against_video(self):
        from automate_ytb.production import _sha
        visual_path = self.root / "visual-review.json"
        data = {
            "status": "sampled",
            "technicalVisualCheckPassed": True,
            "publicationApproved": False,
            "sampledSceneCount": 4,
            "nearBlackSceneCount": 0,
            "videoSha256": _sha(self.video),
            "errors": [],
            "warnings": ["Manual visual review required"],
        }
        visual_path.write_text(json.dumps(data), encoding="utf8")
        checked = consolidate(structural_report=self.structural,
                              media_report=self.media, video=self.video,
                              srt=self.srt, vtt=self.vtt, output=self.output,
                              visual_report=visual_path)
        self.assertTrue(checked["technicalPreviewReady"])
        self.assertEqual(checked["checks"]["visualScenesSampled"], 4)
        self.assertIn("Manual visual review required", checked["warnings"])
        data["videoSha256"] = "0"*64
        visual_path.write_text(json.dumps(data), encoding="utf8")
        checked = consolidate(structural_report=self.structural,
                              media_report=self.media, video=self.video,
                              srt=self.srt, vtt=self.vtt, output=self.output,
                              visual_report=visual_path)
        self.assertFalse(checked["technicalPreviewReady"])
        data["videoSha256"] = _sha(self.video)
        data["technicalVisualCheckPassed"] = False
        data["status"] = "failed"
        visual_path.write_text(json.dumps(data), encoding="utf8")
        checked = consolidate(structural_report=self.structural,
                              media_report=self.media, video=self.video,
                              srt=self.srt, vtt=self.vtt, output=self.output,
                              visual_report=visual_path)
        self.assertFalse(checked["technicalPreviewReady"])

    def test_visual_motion_gate_rejects_missing_pairs_or_frozen_animation(self):
        from automate_ytb.production import _sha
        path = self.root / "visual-review-v2.json"
        visual = {
            "schemaVersion": 2, "status": "sampled",
            "technicalVisualCheckPassed": True, "publicationApproved": False,
            "sampledSceneCount": 4, "motionPairsCompared": 4,
            "frozenAnimatedSceneCount": 0, "nearBlackSceneCount": 0,
            "videoSha256": _sha(self.video), "errors": [], "warnings": [],
        }

        def reviewed():
            path.write_text(json.dumps(visual), encoding="utf8")
            return consolidate(
                structural_report=self.structural, media_report=self.media,
                video=self.video, srt=self.srt, vtt=self.vtt,
                output=self.output, visual_report=path)

        self.assertTrue(reviewed()["technicalPreviewReady"])
        self.assertEqual(reviewed()["checks"]["visualMotionPairs"], 4)
        visual["motionPairsCompared"] = 3
        self.assertFalse(reviewed()["technicalPreviewReady"])
        visual["motionPairsCompared"] = 4
        visual["frozenAnimatedSceneCount"] = 1
        self.assertFalse(reviewed()["technicalPreviewReady"])
        visual["frozenAnimatedSceneCount"] = 0
        self.assertTrue(reviewed()["technicalPreviewReady"])

    def test_schema3_requires_existing_verified_contact_sheet_and_correct_orientation(self):
        report_path = self.root / "visual-review.json"
        original = json.loads(self.media.read_text(encoding="utf8"))
        original["media"]["width"], original["media"]["height"] = 1080, 1920
        self.media.write_text(json.dumps(original), encoding="utf8")
        jpeg = self.root / "storyboard-01.jpg"
        Image.new("RGB", (1120, 2030), (12, 34, 59)).save(
            jpeg, "JPEG", quality=85)
        visual = {
            "schemaVersion": 3, "status": "sampled",
            "technicalVisualCheckPassed": True,
            "publicationApproved": False,
            "sampledSceneCount": 3, "motionPairsCompared": 3,
            "frozenAnimatedSceneCount": 0, "nearBlackSceneCount": 0,
            "videoSha256": _sha(self.video),
            "videoOrientation": "portrait",
            "decodedReviewFrameSize": [360, 640],
            "contactSheetPreservesFrame": True,
            "contactSheetScenesPerPage": 4,
            "pages": ["storyboard-01.jpg"],
            "pageSha256": {"storyboard-01.jpg": _sha(jpeg)},
            "errors": [], "warnings": [],
        }
        def check():
            report_path.write_text(json.dumps(visual), encoding="utf8")
            return consolidate(
                structural_report=self.structural, media_report=self.media,
                video=self.video, srt=self.srt, vtt=self.vtt,
                output=self.output, visual_report=report_path)
        good = check()
        self.assertTrue(good["technicalPreviewReady"], good["errors"])
        self.assertTrue(good["checks"]["contactSheetsVerified"])
        self.assertEqual(good["checks"]["reviewOrientation"], "portrait")

        visual["videoOrientation"] = "landscape"
        self.assertFalse(check()["technicalPreviewReady"])
        visual["videoOrientation"] = "portrait"
        visual["decodedReviewFrameSize"] = [640, 360]
        self.assertFalse(check()["technicalPreviewReady"])
        visual["decodedReviewFrameSize"] = [360, 640]
        visual["contactSheetScenesPerPage"] = 8
        self.assertFalse(check()["technicalPreviewReady"])
        visual["contactSheetScenesPerPage"] = 4
        visual["pages"] = ["../../elsewhere.jpg"]
        self.assertFalse(check()["technicalPreviewReady"])
        visual["pages"] = ["storyboard-01.jpg"]
        jpeg.unlink()
        self.assertFalse(check()["technicalPreviewReady"])

    def test_schema3_rejects_forged_or_unreadable_contact_sheet_jpeg(self):
        report_path = self.root / "visual-review.json"
        jpeg = self.root / "storyboard-01.jpg"
        Image.new("RGB", (1120, 2030), (8, 25, 42)).save(
            jpeg, "JPEG", quality=84)
        data = {
            "schemaVersion": 3, "status": "sampled",
            "technicalVisualCheckPassed": True, "publicationApproved": False,
            "sampledSceneCount": 4, "motionPairsCompared": 4,
            "frozenAnimatedSceneCount": 0, "nearBlackSceneCount": 0,
            "videoSha256": _sha(self.video), "videoOrientation": "landscape",
            "decodedReviewFrameSize": [640, 360],
            "contactSheetPreservesFrame": False,
            "contactSheetScenesPerPage": 8, "pages": ["storyboard-01.jpg"],
            "pageSha256": {"storyboard-01.jpg": _sha(jpeg)},
            "errors": [], "warnings": [],
        }
        def verify():
            report_path.write_text(json.dumps(data), encoding="utf8")
            return consolidate(
                structural_report=self.structural, media_report=self.media,
                video=self.video, srt=self.srt, vtt=self.vtt,
                output=self.output, visual_report=report_path)
        self.assertTrue(verify()["technicalPreviewReady"])
        jpeg.write_bytes(jpeg.read_bytes() + b"tampered")
        self.assertFalse(verify()["technicalPreviewReady"])
        data["pageSha256"]["storyboard-01.jpg"] = _sha(jpeg)
        self.assertTrue(verify()["technicalPreviewReady"])
        # An internally consistent checksum is not enough if the file
        # is not the expected JPEG dimensions or cannot be decoded.
        Image.new("RGB", (900, 1400), "black").save(jpeg, "JPEG")
        data["pageSha256"]["storyboard-01.jpg"] = _sha(jpeg)
        self.assertFalse(verify()["technicalPreviewReady"])
        jpeg.write_bytes(b"x" * 2048)
        data["pageSha256"]["storyboard-01.jpg"] = _sha(jpeg)
        self.assertFalse(verify()["technicalPreviewReady"])

    def test_story_preflight_warnings_propagate_without_false_auto_approval(self):
        from automate_ytb.production import _sha
        story = self.root / "story-preflight.json"
        plan = self.root / "scene-plan.json"
        plan.write_text('{"original":"authored narration"}', encoding="utf8")
        evidence = {
            "schemaVersion": 1, "version": "story-preflight-v1",
            "sourcePlanSha256": _sha(plan),
            "status": "needs-editorial-revision",
            "exactRepeatCount": 3,
            "nearRepeatNeighborCount": 1,
            "speakingPaceWarningCount": 2,
            "publicationApproved": False,
            "factChecked": False,
            "warnings": ["Systematic repetition; human review necessary"],
        }

        def verify():
            story.write_text(json.dumps(evidence), encoding="utf8")
            return consolidate(
                structural_report=self.structural, media_report=self.media,
                video=self.video, srt=self.srt, vtt=self.vtt,
                output=self.output, story_report=story, plan=plan)

        valid = verify()
        self.assertTrue(valid["technicalPreviewReady"])
        self.assertTrue(valid["editorialRevisionRecommended"])
        self.assertFalse(valid["publicationApproved"])
        self.assertEqual(valid["checks"]["narrationExactRepeatCount"], 3)
        self.assertIn("Systematic repetition", " ".join(valid["warnings"]))

        plan.write_text('{"changed":"authored narration"}', encoding="utf8")
        self.assertFalse(verify()["technicalPreviewReady"])
        plan.write_text('{"original":"authored narration"}', encoding="utf8")
        evidence["publicationApproved"] = True
        self.assertFalse(verify()["technicalPreviewReady"])
        evidence["publicationApproved"] = False
        evidence["factChecked"] = True
        self.assertFalse(verify()["technicalPreviewReady"])
        evidence["factChecked"] = False
        self.assertTrue(verify()["technicalPreviewReady"])

    def test_missing_vtt_or_bad_signature_rejected(self):
        self.vtt.unlink()
        with self.assertRaisesRegex(ValueError, "required"):
            self.run_check()
        self.vtt.write_text("Malformed", encoding="utf8")
        self.assertEqual(self.run_check()["status"], "failed")


if __name__ == "__main__":
    unittest.main()
