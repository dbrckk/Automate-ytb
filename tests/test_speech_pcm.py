"""Regression coverage for real signed-PCM cleanup and subtitle timekeeping."""
from array import array
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from automate_ytb.episode import _narrate_scenes
from automate_ytb.captions import caption_phrases, subtitles_for_scenes
from automate_ytb.production import load_plan
from automate_ytb.scene_plan import plan
from automate_ytb.speech_pcm import compact_speech_pcm


RATE = 24000


def pcm(*sections):
    signal = array("h")
    for ms, sample in sections:
        signal.extend([sample] * round(RATE * ms / 1000))
    return signal.tobytes()


class SpeechPcmTests(unittest.TestCase):
    def test_trim_only_long_leading_and_trailing_silence(self):
        raw = pcm((650, 0), (700, 9000), (720, 0))
        clean, metrics = compact_speech_pcm(raw, RATE)
        duration = len(clean) / (2 * RATE)
        self.assertGreater(metrics["leadingTrimMs"], 500)
        self.assertGreater(metrics["trailingTrimMs"], 550)
        self.assertAlmostEqual(duration, .82, delta=.05)
        self.assertEqual(metrics["method"], "edge-silence-window-v1")

    def test_interior_pause_is_retained(self):
        original = pcm((550, 0), (350, 7000), (480, 0),
                       (360, -7000), (610, 0))
        cleaned, _ = compact_speech_pcm(original, RATE)
        samples = array("h")
        samples.frombytes(cleaned)
        self.assertGreaterEqual(samples.count(0), int(.40 * RATE))
        self.assertLess(len(cleaned), len(original))

    def test_tight_audio_is_not_shortened(self):
        original = pcm((900, 12000))
        cleaned, stats = compact_speech_pcm(original, RATE)
        self.assertEqual(len(cleaned), len(original))
        self.assertEqual(stats["leadingTrimMs"], 0)
        self.assertEqual(stats["trailingTrimMs"], 0)
        self.assertLess(abs(int.from_bytes(cleaned[:2], "little", signed=True)), 300)

    def test_short_edge_pauses_are_left_intact(self):
        original = pcm((70, 0), (500, 14000), (100, 0))
        cleaned, stats = compact_speech_pcm(original, RATE)
        self.assertEqual(len(cleaned), len(original))
        self.assertEqual(stats["trailingTrimMs"], 0)

    def test_rejects_empty_silent_or_misaligned_pcm(self):
        with self.assertRaisesRegex(RuntimeError, "silent"):
            compact_speech_pcm(pcm((1500, 0)), RATE)
        with self.assertRaises(ValueError):
            compact_speech_pcm(b"\x12", RATE)
        with self.assertRaises(ValueError):
            compact_speech_pcm(b"\0\0", 0)


class NarrationSilenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.json"
        data = plan(
            topic="Une histoire originale",
            script=" ".join(f"Un sujet pédagogique détaille la partie {i}."
                            for i in range(5)),
            duration=30, shot_seconds=6,
            character="Original purple owl with gold scarf")
        data["scenes"][0]["narration"] = (
            "La chouette raconte une première aventure. "
            "Elle traverse une belle forêt et découvre une nouvelle histoire.")
        self.plan.write_text(json.dumps(data), encoding="utf8")

    def tearDown(self):
        self.temp.cleanup()

    def test_subtitles_use_cleaned_pcm_duration(self):
        class Speech:
            voice = "ff_siwis"
            def __init__(self, **kwargs):
                pass
            def audio(self, text):
                return pcm((600, 0), (700, 9000), (650, 0)), RATE

        with patch("automate_ytb.episode.SpeechEngine", Speech):
            result = _narrate_scenes(self.plan, self.root / "narration.wav",
                                     "fr", limit=1, caption_timing="audio")
        scene = load_plan(self.plan)["scenes"][0]
        phrases = caption_phrases(scene["narration"])
        self.assertGreater(len(phrases), 1)
        self.assertEqual(result["captionPhraseCount"], len(phrases))
        self.assertEqual(result["phraseSilenceCleanup"]["trimmedPhrases"],
                         len(phrases))
        self.assertGreater(result["phraseSilenceCleanup"]["removedSilenceMs"], 2000)
        # Each measured fragment is ~0.82 s and there is an 80ms join.
        self.assertAlmostEqual(scene["captionSegments"][0]["endMs"], 900, delta=55)
        srt, _ = subtitles_for_scenes([scene], use_audio_boundaries=True)
        self.assertEqual(srt.count(" --> "), len(phrases))
        with wave.open(str(self.root / "narration.wav")) as sound:
            self.assertEqual(round(sound.getnframes() * 1000 / sound.getframerate()),
                             scene["endMs"])

    def test_silent_fragment_causes_clean_failure(self):
        original = self.plan.read_bytes()
        class SilentSecondPhrase:
            voice = None
            def __init__(self, **kwargs):
                self.calls = 0
            def audio(self, text):
                self.calls += 1
                return (pcm((800, 0)) if self.calls == 2
                        else pcm((800, 5000))), RATE

        with patch("automate_ytb.episode.SpeechEngine", SilentSecondPhrase):
            with self.assertRaisesRegex(RuntimeError, "silent"):
                _narrate_scenes(self.plan, self.root / "broken.wav", "fr",
                                limit=1, caption_timing="audio")
        self.assertEqual(self.plan.read_bytes(), original)
        self.assertFalse((self.root / "broken.wav").exists())


if __name__ == "__main__":
    unittest.main()
