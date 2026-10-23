"""Original soundtrack, scene-aware bed and readable subtitle regression checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

from automate_ytb.captions import _chunks, subtitles_for_scenes
from automate_ytb.episode import build_preview
from automate_ytb.production import _write_json, load_plan
from automate_ytb.scene_plan import plan
from automate_ytb.soundtrack import SAMPLERATE, _theme, create_bed


class SoundtrackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan_path = self.root / "scene-plan.json"
        script = ("La chouette regarde la lune. "
                  "La pluie tombe doucement sur les arbres. "
                  "Elle découvre une lumière étrange. "
                  "Le matin arrive dans la forêt. "
                  "Enfin, elle sourit et s'envole.")
        content = plan(topic="Une chouette sous la pluie", script=script,
                       duration=30, shot_seconds=6,
                       character="Une chouette violette originale")
        _write_json(self.plan_path, content)

    def tearDown(self):
        self.temp.cleanup()

    def test_original_audio_is_deterministic_with_proper_length(self):
        first, second = self.root / "bed1.wav", self.root / "bed2.wav"
        a = create_bed(plan_path=self.plan_path, output=first)
        b = create_bed(plan_path=self.plan_path, output=second)
        self.assertEqual(a["engine"], "ambient-original-v1")
        self.assertEqual(a["sceneThemes"], b["sceneThemes"])
        self.assertIn("rain", a["sceneThemes"])
        self.assertIn("night", a["sceneThemes"])
        self.assertEqual(a["externalApiCalls"], 0)
        self.assertFalse(a["containsThirdPartyMusic"])
        self.assertEqual(hashlib.sha256(first.read_bytes()).digest(),
                         hashlib.sha256(second.read_bytes()).digest())
        with wave.open(str(first), "rb") as audio:
            self.assertEqual(audio.getnchannels(), 1)
            self.assertEqual(audio.getframerate(), SAMPLERATE)
            self.assertEqual(audio.getnframes(), 30 * SAMPLERATE)

    def test_limited_soundtrack_does_not_exceed_selected_scenes(self):
        file = self.root / "short.wav"
        r = create_bed(plan_path=self.plan_path, output=file, limit=1)
        with wave.open(str(file), "rb") as data:
            self.assertEqual(data.getnframes(), 6 * SAMPLERATE)
        self.assertEqual(len(r["sceneThemes"]), 1)
        with self.assertRaisesRegex(ValueError, "positive"):
            create_bed(plan_path=self.plan_path, output=file, limit=0)

    def test_caption_reflow_preserves_text_and_uses_scene_boundaries(self):
        data = load_plan(self.plan_path)
        # Add text long enough for multiple subtitle cues in each scene.
        for scene in data["scenes"]:
            scene["narration"] = (
                "La chouette explore doucement la forêt immense pendant une "
                "soirée pleine de belles découvertes et de questions nouvelles."
            )
        output, report = subtitles_for_scenes(data["scenes"])
        self.assertGreater(report["cueCount"], len(data["scenes"]))
        self.assertFalse(report["wordLevelAligned"])
        self.assertEqual(output.count("-->"), report["cueCount"])
        self.assertTrue(output.endswith("\n"))
        for scene in data["scenes"]:
            self.assertEqual(
                " ".join(" ".join(_chunks(scene["narration"])).split()),
                scene["narration"])
        self.assertIn("00:00:00,000 -->", output)
        self.assertIn("00:00:30,000", output)

    def test_direction_theme_mapping_uses_actual_storyboard_values(self):
        self.assertEqual(_theme({"weather":"night","emotion":"neutral"}), "night")
        self.assertEqual(_theme({"weather":"rain","emotion":"happy"}), "rain")
        self.assertEqual(_theme({"weather":"day","emotion":"curious"}), "wonder")
        self.assertEqual(_theme({"weather":"day","emotion":"happy"}), "warm")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe required for an actual MP4")
    def test_actual_mp4_with_ambient_only(self):
        report = build_preview(plan_path=self.plan_path,
                               output=self.root / "ambience",
                               soundtrack="ambient", voice="none", limit=1)
        self.assertTrue(report["render"]["hasBackgroundMusic"])
        self.assertEqual(report["render"]["audioMixMode"], "original-bed-only")
        self.assertFalse(report["render"]["hasNarrationAudio"])
        self.assertFalse(report["publicationApproved"])
        self.assertTrue(Path(report["soundtrack"]["file"]).is_file())
        self.assertTrue(Path(report["render"]["video"]).is_file())
        probe = subprocess.run(
            ["ffprobe","-v","error","-show_entries",
             "stream=codec_type:format=duration","-of","json",
             report["render"]["video"]],
            capture_output=True,text=True,check=True)
        info=json.loads(probe.stdout)
        self.assertEqual({x["codec_type"] for x in info["streams"]},
                         {"audio","video"})
        self.assertAlmostEqual(float(info["format"]["duration"]), 6.,delta=0.4)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "eSpeak and FFmpeg required for voiced audio mix")
    def test_real_narration_automatically_ducks_background_music(self):
        report=build_preview(plan_path=self.plan_path,
                             output=self.root / "mixed",
                             soundtrack="ambient", voice="espeak", limit=1)
        video = Path(report["render"]["video"])
        self.assertTrue(video.is_file())
        self.assertEqual(report["render"]["audioMixMode"],
                         "ducked-narration-plus-original-bed")
        self.assertTrue(report["render"]["hasNarrationAudio"])
        self.assertTrue(report["render"]["hasBackgroundMusic"])
        self.assertEqual(report["soundtrack"]["externalApiCalls"], 0)
        self.assertFalse(report["render"]["captionsPreciselyAligned"])
        self.assertGreater(report["render"]["captionGeneration"]["cueCount"], 0)


if __name__=="__main__":
    unittest.main()
