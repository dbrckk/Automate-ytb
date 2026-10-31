"""Visual reviews are generated from real encoded MP4, with bounded sampling."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.review_board import _selection, _motion_metrics, _frame_at, generate
from automate_ytb.scene_plan import plan


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required for video contact sheet tests")
class ReviewBoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.plan_file = self.folder / "scene-plan.json"
        story = " ".join(
            f"A little owl visits a different original place {i}."
            for i in range(5))
        data = plan(topic="Original illustrated forest", script=story,
                    duration=30, shot_seconds=6,
                    character="A violet owl with a unique striped scarf")
        self.plan_file.write_text(json.dumps(data), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _video(self, *, color=None, duration=30, portrait=False):
        resolution = "360x640" if portrait else "640x360"
        filename = self.folder / (
            ("portrait-" if portrait else "landscape-") +
            ("black.mp4" if color else "colors.mp4"))
        source = (f"color=c={color}:s={resolution}:r=6:d={duration}"
                  if color else
                  f"testsrc2=size={resolution}:rate=6:duration={duration}")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y",
                        "-f", "lavfi", "-i", source,
                        "-c:v", "libx264", "-preset", "ultrafast",
                        "-pix_fmt", "yuv420p", str(filename)],
                       check=True, capture_output=True)
        return filename

    def test_real_mp4_produces_phone_friendly_contact_board(self):
        report = generate(plan=self.plan_file, video=self._video(),
                          destination=self.folder/"board", max_samples=5)
        self.assertEqual(report["sampledSceneCount"], 5)
        self.assertTrue(report["technicalVisualCheckPassed"])
        self.assertEqual(report["totalSceneCount"], 5)
        self.assertFalse(report["publicationApproved"])
        self.assertEqual(report["pages"], ["storyboard-01.jpg"])
        self.assertEqual(len(report["videoSha256"]), 64)
        with Image.open(self.folder/"board"/"storyboard-01.jpg") as image:
            self.assertEqual(image.size, (1120, 2030))
        persisted = json.loads((self.folder/"board"/"visual-review.json").read_text())
        self.assertEqual(persisted["schemaVersion"], 3)
        self.assertEqual(persisted["videoOrientation"], "landscape")
        self.assertEqual(persisted["decodedReviewFrameSize"], [640, 360])
        self.assertEqual(persisted["contactSheetScenesPerPage"], 8)
        self.assertEqual(persisted["motionPairsCompared"], 5)
        self.assertEqual(persisted["frozenAnimatedSceneCount"], 0)
        self.assertEqual(len(persisted["frames"]), 5)
        self.assertIn("meanAbsoluteLumaChange", persisted["frames"][0]["motion"])
        self.assertGreater(
            persisted["frames"][0]["laterTimeSeconds"],
            persisted["frames"][0]["timeSeconds"])
        self.assertNotIn("frame", persisted["frames"][0])
        self.assertFalse(persisted["publicationApproved"])

    def test_native_9_16_contact_sheets_preserve_all_tall_frames(self):
        video = self._video(portrait=True)
        decoded = _frame_at(video, 1.5, portrait=True)
        self.assertEqual(decoded.size, (360, 640))
        reviewed = generate(
            plan=self.plan_file, video=video,
            destination=self.folder/"portrait-board", max_samples=5)
        self.assertTrue(reviewed["technicalVisualCheckPassed"], reviewed["errors"])
        self.assertEqual(reviewed["videoOrientation"], "portrait")
        self.assertEqual(reviewed["decodedReviewFrameSize"], [360, 640])
        self.assertTrue(reviewed["contactSheetPreservesFrame"])
        self.assertEqual(reviewed["contactSheetScenesPerPage"], 4)
        self.assertEqual(reviewed["pages"],
                         ["storyboard-01.jpg", "storyboard-02.jpg"])
        self.assertEqual(reviewed["sampledSceneCount"], 5)
        self.assertEqual(reviewed["motionPairsCompared"], 5)
        self.assertTrue(all(
            item["motion"]["changedPixelFraction"] > 0.01
            for item in reviewed["frames"]))
        for filename in reviewed["pages"]:
            with Image.open(self.folder/"portrait-board"/filename) as image:
                self.assertEqual(image.size, (1120, 2030))

    def test_native_science_rig_freezing_is_blocked_without_blocking_stills(self):
        original = json.loads(self.plan_file.read_text(encoding="utf8"))
        for scene in original["scenes"]:
            scene["motionRig"] = "original-science-v1"
            scene["renderStyle"] = "science"
        self.plan_file.write_text(json.dumps(original), encoding="utf8")
        frozen = generate(
            plan=self.plan_file,
            video=self._video(color="gray", portrait=True),
            destination=self.folder/"frozen-science", max_samples=5)
        self.assertFalse(frozen["technicalVisualCheckPassed"])
        self.assertEqual(frozen["frozenAnimatedSceneCount"], 5)
        self.assertTrue(all(x["animatedRigExpected"]
                            for x in frozen["frames"]))
        moving = generate(
            plan=self.plan_file, video=self._video(portrait=True),
            destination=self.folder/"moving-science", max_samples=5)
        self.assertTrue(moving["technicalVisualCheckPassed"], moving["errors"])
        self.assertEqual(moving["frozenAnimatedSceneCount"], 0)
        self.assertTrue(all(x["animatedRigExpected"]
                            for x in moving["frames"]))

    def test_black_mp4_is_flagged_as_bad_preview(self):
        report = generate(plan=self.plan_file, video=self._video(color="black"),
                          destination=self.folder/"black-review", max_samples=5)
        self.assertFalse(report["technicalVisualCheckPassed"])
        self.assertEqual(report["nearBlackSceneCount"], 5)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["pages"])

    def test_static_animated_rig_is_blocked_but_static_documentary_is_allowed(self):
        source = json.loads(self.plan_file.read_text())
        for scene in source["scenes"]:
            scene["motionRig"] = "original-owl-v1"
            scene["renderStyle"] = "cartoon"
        self.plan_file.write_text(json.dumps(source), encoding="utf8")
        frozen_video = self._video(color="gray")
        detected = generate(plan=self.plan_file, video=frozen_video,
                            destination=self.folder/"static-cartoon",
                            max_samples=5)
        self.assertFalse(detected["technicalVisualCheckPassed"])
        self.assertEqual(detected["frozenAnimatedSceneCount"], 5)
        self.assertEqual(detected["motionPairsCompared"], 5)
        self.assertTrue(any("frozen" in err for err in detected["errors"]))
        # An intentionally static documentary frame is not a broken animated
        # rig. Report its motion measurements but don't falsely fail it.
        for scene in source["scenes"]:
            scene["motionRig"] = None
            scene["renderStyle"] = "documentary"
        self.plan_file.write_text(json.dumps(source), encoding="utf8")
        still = generate(plan=self.plan_file, video=frozen_video,
                         destination=self.folder/"static-documentary",
                         max_samples=5)
        self.assertTrue(still["technicalVisualCheckPassed"])
        self.assertEqual(still["frozenAnimatedSceneCount"], 0)
        self.assertEqual(still["motionPairsCompared"], 5)

    def test_actual_moving_encoded_video_is_not_falsely_classified_frozen(self):
        source = json.loads(self.plan_file.read_text())
        for scene in source["scenes"]:
            scene["motionRig"] = "original-owl-v1"
            scene["renderStyle"] = "cartoon"
        self.plan_file.write_text(json.dumps(source), encoding="utf8")
        detected = generate(plan=self.plan_file, video=self._video(),
                            destination=self.folder/"animated-cartoon",
                            max_samples=5)
        self.assertEqual(detected["frozenAnimatedSceneCount"], 0)
        self.assertTrue(detected["technicalVisualCheckPassed"])
        self.assertTrue(all(item["motion"]["changedPixelFraction"] > 0.01
                            for item in detected["frames"]))

    def test_motion_metrics_are_deterministic_without_audio_or_network(self):
        a = Image.new("RGB", (96, 54), "gray")
        b = Image.new("RGB", (96, 54), "gray")
        still = _motion_metrics(a, b)
        self.assertEqual(still["meanAbsoluteLumaChange"], 0)
        self.assertEqual(still["changedPixelFraction"], 0)
        c = Image.new("RGB", (96, 54), "white")
        moving = _motion_metrics(a, c)
        self.assertGreater(moving["meanAbsoluteLumaChange"], 30)
        self.assertEqual(moving["changedPixelFraction"], 1.0)

    def test_rejects_mismatched_duration_and_bad_sample_limit(self):
        with self.assertRaisesRegex(ValueError, "Sample count"):
            _selection(5, 1)
        with self.assertRaisesRegex(ValueError, "duration"):
            generate(plan=self.plan_file, video=self._video(duration=10),
                     destination=self.folder/"bad-length", max_samples=4)

    def test_even_sampling_spreads_over_all_scenes(self):
        self.assertEqual(_selection(5, 5), [0, 1, 2, 3, 4])
        self.assertEqual(len(_selection(150, 12)), 12)
        self.assertEqual(len(set(_selection(150, 12))), 12)
        self.assertTrue(max(_selection(150, 12)) > 130)


if __name__ == "__main__":
    unittest.main()
