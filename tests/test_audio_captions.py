"""Audio-derived caption boundaries must describe the exact synthesized WAV."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import wave

from automate_ytb.captions import caption_phrases, subtitles_for_scenes
from automate_ytb.episode import _narrate_scenes, build_preview
from automate_ytb.production import load_plan
from automate_ytb.quality import check
from automate_ytb.scene_plan import plan


class FakeSpeechEngine:
    def __init__(self, **kwargs):
        self.voice = None
        self.calls = 0

    def audio(self, text):
        # Different deterministic real PCM lengths make proportional
        # word-count timing observably wrong in this fixture.
        self.calls += 1
        seconds = (0.7, 1.9, 0.9)[(self.calls - 1) % 3]
        return b"\x00\x30" * int(24000 * seconds), 24000


class AudioCaptionTimingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan_file = self.root / "scene-plan.json"
        script = " ".join(f"Une histoire originale progresse au chapitre {i}."
                          for i in range(5))
        data = plan(topic="Histoire originale", script=script, duration=30,
                    shot_seconds=6, character="Une chouette violette originale")
        data["scenes"][0]["narration"] = (
            "Une chouette violette traverse lentement la forêt lumineuse "
            "et rencontre un minuscule papillon bleu qui lui raconte une "
            "histoire étonnante sur la grande rivière mystérieuse."
        )
        self.plan_file.write_text(json.dumps(data), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_pcm_phrase_timings_match_exported_srt(self):
        with patch("automate_ytb.episode.SpeechEngine", FakeSpeechEngine):
            report = _narrate_scenes(
                self.plan_file, self.root / "narration.wav",
                "fr", limit=1, caption_timing="audio")
        scenes = load_plan(self.plan_file)["scenes"][:1]
        scene = scenes[0]
        phrases = caption_phrases(scene["narration"])
        self.assertGreater(len(phrases), 1)
        self.assertEqual(report["captionPhraseCount"], len(phrases))
        self.assertFalse(report["wordAlignment"])
        self.assertEqual(report["providerApiCalls"], 0)
        intervals = scene["captionSegments"]
        self.assertEqual([p["text"] for p in intervals], phrases)
        self.assertEqual(intervals[0]["startMs"], 0)
        self.assertEqual(intervals[-1]["endMs"], scene["endMs"])
        # The first 0.7-second audio fragment plus an 80-ms pause.
        self.assertAlmostEqual(intervals[0]["endMs"], 780, delta=1)
        srt, meta = subtitles_for_scenes(scenes, use_audio_boundaries=True)
        self.assertEqual(meta["method"], "audio-derived-synthesized-phrases")
        self.assertIn("00:00:00,780", srt)
        self.assertEqual(srt.count(" --> "), len(phrases))
        with wave.open(str(self.root / "narration.wav")) as audio:
            self.assertEqual(audio.getframerate(), 24000)
            self.assertEqual(round(audio.getnframes() * 1000 / 24000),
                             scene["endMs"])

    def test_refuses_altered_or_missing_audio_boundaries(self):
        with patch("automate_ytb.episode.SpeechEngine", FakeSpeechEngine):
            _narrate_scenes(self.plan_file, self.root / "voice.wav",
                            "fr", limit=1, caption_timing="audio")
        scenes = load_plan(self.plan_file)["scenes"][:1]
        scenes[0]["captionSegments"][0]["text"] = "Wrong words!"
        with self.assertRaisesRegex(ValueError, "text differs"):
            subtitles_for_scenes(scenes, use_audio_boundaries=True)
        scenes[0].pop("captionSegments")
        with self.assertRaisesRegex(ValueError, "Missing"):
            subtitles_for_scenes(scenes, use_audio_boundaries=True)

    def test_legacy_speech_keeps_estimated_captions(self):
        with patch("automate_ytb.episode.SpeechEngine", FakeSpeechEngine):
            report = _narrate_scenes(
                self.plan_file, self.root / "voice.wav",
                "fr", limit=1, caption_timing="estimated")
        self.assertEqual(report["captionTiming"], "estimated")
        scenes = load_plan(self.plan_file)["scenes"][:1]
        self.assertNotIn("captionSegments", scenes[0])
        _, meta = subtitles_for_scenes(scenes)
        self.assertEqual(meta["method"], "estimated-proportional-phrases")

    def test_failure_preserves_scene_plan(self):
        original = self.plan_file.read_bytes()

        class BadRate(FakeSpeechEngine):
            def audio(self, text):
                pcm, _ = super().audio(text)
                return pcm, 24000 if self.calls == 1 else 22050

        with patch("automate_ytb.episode.SpeechEngine", BadRate):
            with self.assertRaisesRegex(RuntimeError, "mismatched"):
                _narrate_scenes(self.plan_file, self.root / "bad.wav",
                                "fr", limit=1, caption_timing="audio")
        self.assertEqual(self.plan_file.read_bytes(), original)
        self.assertFalse((self.root / "bad.wav").exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/FFprobe required for real MP4 integration")
    def test_real_video_and_quality_gate_accept_audio_cues(self):
        with patch("automate_ytb.episode.SpeechEngine", FakeSpeechEngine):
            result = build_preview(
                plan_path=self.plan_file, output=self.root / "output",
                style="documentary", voice="espeak", limit=1,
                caption_timing="audio")
        self.assertEqual(result["render"]["captionGeneration"]["method"],
                         "audio-derived-synthesized-phrases")
        qa = check(plan=self.plan_file, output=self.root / "output",
                   expected_voice="espeak", expected_soundtrack="none")
        self.assertEqual(qa["status"], "passed", qa["errors"])
        self.assertTrue(qa["checks"]["captionTextMatchesPlan"])


if __name__ == "__main__":
    unittest.main()
