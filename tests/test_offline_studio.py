"""Offline end-to-end movie checks: no paid models, no network, no publication."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.offline_studio import build, draw_scene, make_narration
from automate_ytb.production import audit, load_plan
from automate_ytb.scene_plan import plan

SCRIPT = (
    "Une vidéo commence par une question originale. "
    "Le scénario organise des idées déjà vérifiées. "
    "Chaque scène doit être illustrée avec soin. "
    "Une voix relie les images à la narration. "
    "Un contrôle qualité termine le montage."
)
CHARACTER = "An original blue-eyed violet owl with an amber scarf"


class OfflineStudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_original_cards_deterministic_and_scene_specific(self):
        data = plan(topic="Comment raconter une histoire ?", script=SCRIPT,
                    character=CHARACTER, duration=30, shot_seconds=6)
        one = self.root / "first.png"
        same = self.root / "same.png"
        two = self.root / "second.png"
        draw_scene(topic=data["topic"], scene=data["scenes"][0], index=0,
                   count=5, character=CHARACTER, destination=one)
        draw_scene(topic=data["topic"], scene=data["scenes"][0], index=0,
                   count=5, character=CHARACTER, destination=same)
        draw_scene(topic=data["topic"], scene=data["scenes"][1], index=1,
                   count=5, character=CHARACTER, destination=two)
        with Image.open(one) as image:
            self.assertEqual(image.size, (1280, 720))
        def checksum(file):
            return hashlib.sha256(file.read_bytes()).hexdigest()
        self.assertEqual(checksum(one), checksum(same))
        self.assertNotEqual(checksum(one), checksum(two))

    def test_does_not_invent_missing_narration(self):
        with self.assertRaisesRegex(ValueError, "Need 5"):
            build(topic="Original question", script="Only one sentence.",
                  character=CHARACTER, duration=30, shot_seconds=6,
                  directory=self.root / "bad", silent=True)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Requires local FFmpeg to render real video")
    def test_full_free_preview_mp4_and_provenance(self):
        folder = self.root / "episode"
        result = build(topic="Comment raconter une histoire ?", script=SCRIPT,
                       character=CHARACTER, duration=30, shot_seconds=6,
                       directory=folder, silent=True)
        self.assertEqual(result["artEngine"], "procedural-vector")
        self.assertEqual(result["externalApiRequests"], 0)
        self.assertFalse(result["publicationApproved"])
        self.assertFalse(result["hasNarrationAudio"])
        self.assertEqual(result["assetAudit"]["ready"], 5)
        self.assertTrue((folder / "thumbnail-draft.png").exists())
        self.assertEqual(audit(folder / "scene-plan.json")["counts"]["changed"], 0)
        self.assertEqual(len(load_plan(folder / "scene-plan.json")["scenes"]), 5)
        self.assertGreater((folder / "render/preview.mp4").stat().st_size, 5000)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1",
                                str(folder / "render/preview.mp4")],
                               check=True, capture_output=True, text=True)
        self.assertAlmostEqual(float(probe.stdout.strip()), 30., delta=0.6)
        # A deliberate on-disk edit invalidates an earlier media approval.
        first = folder / "assets" / "scene-001.png"
        with Image.open(first) as image:
            changed = image.copy()
        changed.putpixel((0, 0), (255, 0, 0))
        changed.save(first)
        self.assertEqual(audit(folder / "scene-plan.json")["counts"]["changed"], 1)
        with self.assertRaisesRegex(ValueError, "modified"):
            build(topic="Comment raconter une histoire ?", script=SCRIPT,
                  character=CHARACTER, duration=30, shot_seconds=6,
                  directory=folder, silent=True)

    @unittest.skipUnless(shutil.which("espeak-ng") and shutil.which("ffmpeg")
                         and shutil.which("ffprobe"),
                         "Requires espeak-ng, ffmpeg and ffprobe")
    def test_voice_is_timeboxed_to_scenes(self):
        data = plan(topic="Voix originales", script=SCRIPT, duration=30,
                    shot_seconds=6, character=CHARACTER)
        wav = make_narration(data, self.root / "narration.wav", "fr")
        self.assertGreater(wav.stat().st_size, 10000)
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of",
                                "default=noprint_wrappers=1:nokey=1",
                                str(wav)], check=True, capture_output=True, text=True)
        self.assertAlmostEqual(float(probe.stdout.strip()), 30., delta=0.15)


if __name__ == "__main__":
    unittest.main()
