"""Regression and safety contracts for provider-neutral YouTube image production."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.production import audit, ingest, load_plan, prepare, render
from automate_ytb.scene_plan import plan


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plan_path = self.root / "scene-plan.json"
        script = " ".join(f"Original narration point {i} explains a distinct idea."
                          for i in range(5))
        data = plan(topic="Why do birds sing?", script=script, duration=30,
                    character="An original purple bird with a teal scarf",
                    shot_seconds=6)
        self.plan_path.write_text(json.dumps(data), encoding="utf-8")
        self.image = self.root / "owned-art.png"
        Image.new("RGB", (640, 360), (60, 130, 170)).save(self.image)

    def tearDown(self):
        self.tmp.cleanup()

    def approved_image(self, scene_id="scene-001", *, replace=False):
        return ingest(plan_path=self.plan_path, scene_id=scene_id,
                      image_path=self.image, provider="human-illustrator",
                      rights_note="I made the original illustration and own the artwork.",
                      cost_usd="0.35", rights_confirmed=True, replace=replace)

    def test_export_production_kit_has_prompts_but_no_provider_actions(self):
        dest = self.root / "provider" / "prompts.jsonl"
        result = prepare(self.plan_path, dest, "0.125")
        rows = [json.loads(s) for s in dest.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 5)
        self.assertEqual(result["quotedEstimateUsd"], "0.6250")
        self.assertEqual(result["providerRequestsSent"], 0)
        self.assertFalse(result["publicationApproved"])
        self.assertEqual(rows[0]["outputAsset"], "assets/scene-001.png")
        self.assertTrue(all(x["requiresRightsReview"] for x in rows))

    def test_requires_explicit_rights_and_records_actual_asset_digest(self):
        with self.assertRaisesRegex(ValueError, "confirm-rights"):
            ingest(plan_path=self.plan_path, scene_id="scene-001",
                   image_path=self.image, provider="generator",
                   rights_note="I own all necessary commercial rights to this image.",
                   cost_usd="0.1")
        self.assertEqual(audit(self.plan_path)["counts"]["missing"], 5)
        entry = self.approved_image()
        self.assertEqual(len(entry["sha256"]), 64)
        self.assertEqual(audit(self.plan_path)["counts"], {
            "ready": 1, "missing": 4, "unreviewed": 0, "changed": 0})
        saved = load_plan(self.plan_path)
        self.assertTrue(saved["scenes"][0]["assetApproved"])
        self.assertFalse(saved["publicationApproved"])
        self.assertEqual(saved["scenes"][0]["assetProvider"], "human-illustrator")

    def test_modified_image_invalidates_approval(self):
        self.approved_image()
        Image.new("RGB", (640, 360), (230, 80, 30)).save(
            self.root / "assets" / "scene-001.png")
        self.assertEqual(audit(self.plan_path)["counts"]["changed"], 1)
        with self.assertRaisesRegex(ValueError, "not ready"):
            render(plan_path=self.plan_path, output=self.root / "preview",
                   limit=1)

    def test_no_overwrite_without_explicit_replace(self):
        self.approved_image()
        with self.assertRaisesRegex(ValueError, "exists"):
            self.approved_image()
        self.approved_image(replace=True)

    def test_rejects_traversal_or_tampered_timings(self):
        original = load_plan(self.plan_path)
        original["scenes"][0]["imageAsset"] = "../../wrong.png"
        self.plan_path.write_text(json.dumps(original), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsafe image path"):
            prepare(self.plan_path, self.root / "export.jsonl")
        original["scenes"][0]["imageAsset"] = "assets/scene-001.png"
        original["scenes"][1]["startMs"] = 500
        self.plan_path.write_text(json.dumps(original), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Non-contiguous"):
            load_plan(self.plan_path)

    def test_rejects_fake_or_negative_cost(self):
        for invalid in ("NaN", "Infinity", "-1", "999999"):
            with self.subTest(value=invalid):
                with self.assertRaisesRegex(ValueError, "amount"):
                    prepare(self.plan_path, self.root / "out.jsonl", invalid)

    def test_stale_or_unapproved_assets_never_render(self):
        with self.assertRaisesRegex(ValueError, "not ready"):
            render(plan_path=self.plan_path, output=self.root / "preview", limit=1)
        self.assertFalse(audit(self.plan_path)["readyForPreview"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe required for actual video render")
    def test_audio_preview_and_timeline_consistency(self):
        self.approved_image("scene-001")
        self.approved_image("scene-002")
        sound = self.root / "self-authored-tone.wav"
        subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=10",
            "-ar", "44100", str(sound)
        ], check=True)
        output = self.root / "audio-preview"
        report = render(plan_path=self.plan_path, output=output, limit=2,
                        audio=sound, fps=24)
        self.assertTrue(report["hasNarrationAudio"])
        self.assertFalse(report["captionsPreciselyAligned"])
        self.assertFalse(report["publicationApproved"])
        probe = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type:format=duration",
            "-of", "json", str(output / "preview.mp4")
        ], text=True, capture_output=True, check=True)
        streams = json.loads(probe.stdout)
        self.assertEqual({x["codec_type"] for x in streams["streams"]},
                         {"video", "audio"})
        self.assertAlmostEqual(float(streams["format"]["duration"]), 12.0,
                               delta=0.7)
        self.assertEqual((output / "draft-captions.srt").read_text(
            encoding="utf-8").count("-->"), 2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe required for actual video render")
    def test_actual_render_outputs_playable_silent_preview(self):
        self.approved_image()
        output = self.root / "rendered"
        report = render(plan_path=self.plan_path, output=output, limit=1,
                        resolution="720p", fps=24)
        self.assertTrue((output / "preview.mp4").is_file())
        self.assertTrue((output / "draft-captions.srt").is_file())
        self.assertFalse(report["publicationApproved"])
        self.assertFalse(report["hasNarrationAudio"])
        self.assertEqual(report["scenesRendered"], 1)
        first = report["videoSha256"]
        rerun = render(plan_path=self.plan_path, output=output, limit=1,
                       resolution="720p", fps=24)
        self.assertEqual(first, rerun["videoSha256"])
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output / "preview.mp4")], text=True, capture_output=True, check=True)
        self.assertAlmostEqual(float(probe.stdout), 6.0, delta=0.6)


if __name__ == "__main__":
    unittest.main()
