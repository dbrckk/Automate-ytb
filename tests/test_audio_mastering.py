"""End-to-end audio mastering measured from the final encoded MP4, not inputs."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.media_qa import assess, _audio_measurements
from automate_ytb.production import ingest, render
from automate_ytb.scene_plan import plan


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and FFprobe required for EBU R128")
class AudioMasteringTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.root = Path(self.workspace.name)
        script = " ".join(f"Un personnage raconte une histoire originale {i}."
                          for i in range(5))
        data = plan(topic="Le récit original de la chouette", script=script,
                    duration=30, shot_seconds=6,
                    character="Une chouette violette originale")
        self.plan = self.root / "scene-plan.json"
        self.plan.write_text(json.dumps(data), encoding="utf-8")
        scene = self.root / "illustration.png"
        Image.new("RGB", (320, 256), (51, 81, 131)).save(scene)
        ingest(plan_path=self.plan, scene_id="scene-001", image_path=scene,
               provider="local-drawing",
               rights_note="A fully original illustrated image, made by the test suite.",
               cost_usd="0", rights_confirmed=True)
        self.narration = self.root / "speech.wav"
        self.music = self.root / "original-music.wav"
        for file, freq in ((self.narration, 440), (self.music, 220)):
            subprocess.run(
                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=6",
                 "-ar", "48000", str(file)],
                check=True, timeout=30)

    def tearDown(self):
        self.workspace.cleanup()

    def _encode(self, name, *, audio=None, music=None):
        output = self.root / name
        result = render(plan_path=self.plan, output=output, limit=1,
                        resolution="720p", fps=24, audio=audio, music=music)
        self.assertEqual(result["audioMastering"],
                         "ffmpeg-loudnorm-ebu-r128-single-pass")
        self.assertEqual(result["targetTruePeakDbtp"], -1.5)
        self.assertFalse(result["publicationApproved"])
        return Path(result["video"]), result

    def test_narration_mastered_to_expected_loudness(self):
        path, manifest = self._encode("narration", audio=self.narration)
        qa = assess(video=path, expected_duration=6, require_audio=True,
                    target_lufs=-16)
        self.assertFalse(qa["errors"], qa)
        self.assertIsNotNone(qa["integratedLufs"])
        self.assertAlmostEqual(qa["integratedLufs"], -16, delta=3)
        self.assertLessEqual(qa["truePeakDbtp"], -1.0)
        self.assertAlmostEqual(manifest["targetIntegratedLufs"], -16)
        self.assertIn("ebur128", qa["audioMeasurement"])

    def test_original_music_only_mastered_more_quietly(self):
        path, manifest = self._encode("music-only", music=self.music)
        qa = assess(video=path, target_lufs=-24)
        self.assertFalse(qa["errors"], qa)
        self.assertAlmostEqual(qa["integratedLufs"], -24, delta=3)
        self.assertLessEqual(qa["truePeakDbtp"], -1.0)
        self.assertEqual(manifest["targetIntegratedLufs"], -24)

    def test_narration_and_music_ducked_then_mastered(self):
        path, manifest = self._encode("mixed", audio=self.narration,
                                      music=self.music)
        qa = assess(video=path, target_lufs=-16, require_audio=True)
        self.assertFalse(qa["errors"], qa)
        self.assertAlmostEqual(qa["integratedLufs"], -16, delta=3)
        self.assertLessEqual(qa["truePeakDbtp"], -1.0)
        self.assertEqual(manifest["audioMixMode"],
                         "ducked-narration-plus-original-bed")

    def test_invalid_target_rejected_and_meters_on_silent_stream(self):
        path, _ = self._encode("narration-validation", audio=self.narration)
        for invalid in (float("nan"), float("inf"), -40.0, 0.0):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                assess(video=path, target_lufs=invalid)
        stats = _audio_measurements(path)
        self.assertIsNotNone(stats["samplePeakDbfs"])
        self.assertIsNotNone(stats["truePeakDbtp"])

if __name__ == "__main__":
    unittest.main()
