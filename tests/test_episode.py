"""Offline end-to-end YouTube draft smoke checks, including actual FFmpeg output."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.episode import build_preview, create_local_art
from automate_ytb.production import audit, load_plan
from automate_ytb.scene_plan import plan


class OfflineEpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plan = self.root / "scene-plan.json"
        script = ("La chouette découvre une lumière. "
                  "Elle traverse un jardin. "
                  "Un papillon apparaît au loin. "
                  "Ils explorent ensemble la forêt. "
                  "Au matin, la chouette rentre chez elle.")
        data = plan(topic="Voyage original d'une chouette", script=script,
                    duration=30, shot_seconds=6,
                    character="Petite chouette violette et originale")
        self.plan.write_text(json.dumps(data), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_original_local_images_have_verifiable_rights_and_reuse(self):
        first = create_local_art(self.plan, limit=1)
        self.assertEqual(first["created"], 1)
        self.assertEqual(first["apiCalls"], 0)
        second = create_local_art(self.plan, limit=1)
        self.assertEqual(second["reused"], 1)
        self.assertEqual(audit(self.plan)["counts"]["ready"], 1)
        self.assertFalse(load_plan(self.plan)["publicationApproved"])

    def test_changed_asset_refuses_auto_replace(self):
        create_local_art(self.plan, limit=1)
        file = self.root / "assets" / "scene-001.png"
        file.write_bytes(b"tampered-image")
        with self.assertRaisesRegex(ValueError, "modified or unreviewed"):
            create_local_art(self.plan, limit=1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg required for integration render")
    def test_real_video_and_thumbnails(self):
        result = build_preview(plan_path=self.plan,
                               output=self.root / "renders", voice="none", limit=1)
        self.assertTrue(Path(result["render"]["video"]).is_file())
        self.assertEqual(len(result["thumbnails"]), 3)
        self.assertFalse(result["publicationApproved"])
        self.assertEqual(result["art"]["apiCalls"], 0)
        probe = subprocess.run(["ffprobe", "-v", "error",
                                "-show_entries", "format=duration",
                                "-of", "default=nw=1:nk=1",
                                result["render"]["video"]], capture_output=True,
                               text=True, check=True)
        self.assertAlmostEqual(float(probe.stdout), 6, delta=.6)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "FFmpeg and eSpeak required for voiced render")
    def test_espeak_audio_expands_timeline_without_clipping(self):
        result = build_preview(plan_path=self.plan,
                               output=self.root / "speech", voice="espeak", limit=1)
        self.assertTrue(result["render"]["hasNarrationAudio"])
        self.assertFalse(result["voice"]["wordAlignment"])
        self.assertEqual(load_plan(self.plan)["scenes"][0]["startMs"], 0)
        check = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
             "-of", "json", result["render"]["video"]],
            capture_output=True, text=True, check=True)
        kinds = {s["codec_type"] for s in json.loads(check.stdout)["streams"]}
        self.assertEqual(kinds, {"video", "audio"})


if __name__ == "__main__":
    unittest.main()
