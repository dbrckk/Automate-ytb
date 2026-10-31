"""Kokoro engine contract and true scene-audio timing without external model calls."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import wave

from automate_ytb.narration import SpeechEngine, SAMPLE_RATE_KOKORO, _segment_pause_ms
from automate_ytb.episode import _narrate_scenes
from automate_ytb.production import load_plan
from automate_ytb.scene_plan import plan


class SpeechTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / "scene-plan.json"
        script = " ".join(f"Original sentence {i} explains the scene." for i in range(5))
        self.plan.write_text(json.dumps(plan(topic="Une histoire originale", script=script,
                                             duration=30, shot_seconds=6,
                                             character="A brand-new original purple owl"),
                                       ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_supported_kokoro_voice_and_model_loaded_once(self):
        import numpy as np
        instances = []
        class FakePipeline:
            def __init__(self, *, lang_code, repo_id=None):
                self.lang_code = lang_code
                instances.append(self)

            def __call__(self, text, *, voice, speed):
                self.last_text = text
                self.last_voice = voice
                self.last_speed = speed
                yield text, "phonemes", np.array([0., 0.7, -0.7], dtype="float32")
                yield types.SimpleNamespace(
                    graphemes=text, phonemes="phonemes",
                    audio=np.array([0.3, -0.3], dtype="float32"))

        module = types.ModuleType("kokoro")
        module.KPipeline = FakePipeline
        with patch.dict(sys.modules, {"kokoro": module}):
            voice = SpeechEngine(engine="kokoro", language="fr")
            pcm, rate = voice.audio("Une chouette parle.")
            self.assertEqual(rate, SAMPLE_RATE_KOKORO)
            self.assertEqual(instances[0].lang_code, "f")
            self.assertEqual(instances[0].last_voice, "ff_siwis")
            # Sentence punctuation receives 70ms, not a fixed 100ms for
            # every arbitrary model chunk.
            self.assertEqual(len(pcm) // 2, 3 + 1680 + 2)
            self.assertEqual(len(instances), 1)
            voice.audio("Une seconde phrase.")
            self.assertEqual(len(instances), 1)

    def test_segment_pause_is_driven_by_punctuation_not_chunk_boundaries(self):
        self.assertEqual(_segment_pause_ms("Une phrase continue"), 0)
        self.assertEqual(_segment_pause_ms("Un mot, "), 30)
        self.assertEqual(_segment_pause_ms("La fin. "), 70)
        self.assertEqual(_segment_pause_ms("Pourquoi ?"), 70)
        self.assertEqual(_segment_pause_ms(None), 0)

    def test_unpunctuated_kokoro_chunks_crossfade_without_audible_silence(self):
        import numpy as np
        class FakePipeline:
            def __init__(self, **kwargs):
                pass
            def __call__(self, text, **kwargs):
                yield types.SimpleNamespace(
                    graphemes="La voix ne s'arrête pas",
                    audio=np.full(900, 0.25, dtype="float32"))
                yield types.SimpleNamespace(
                    graphemes="au milieu de la phrase.",
                    audio=np.full(900, -0.25, dtype="float32"))
        kokoro = types.ModuleType("kokoro")
        kokoro.KPipeline = FakePipeline
        with patch.dict(sys.modules, {"kokoro": kokoro}):
            pcm, rate = SpeechEngine(engine="kokoro", language="fr").audio(
                "La voix ne s'arrête pas au milieu de la phrase.")
        self.assertEqual(rate, SAMPLE_RATE_KOKORO)
        samples = np.frombuffer(pcm, dtype="<i2")
        self.assertEqual(samples.size, 900 + 900 - 192)
        self.assertFalse(np.any(samples == 0).all())
        self.assertLess(np.max(np.abs(np.diff(samples.astype(np.int32)))), 200)
        self.assertLess(samples[-1], -8000)
        self.assertGreater(samples[0], 8000)

    def test_comma_keeps_short_pause_for_prosody(self):
        import numpy as np
        class FakePipeline:
            def __init__(self, **kwargs):
                pass
            def __call__(self, text, **kwargs):
                yield ("Bonjour,", "phonemes", np.full(500, 0.25, dtype="float32"))
                yield ("comment allez-vous?", "phonemes",
                       np.full(600, 0.3, dtype="float32"))
        kokoro = types.ModuleType("kokoro")
        kokoro.KPipeline = FakePipeline
        with patch.dict(sys.modules, {"kokoro": kokoro}):
            pcm, rate = SpeechEngine(engine="kokoro", language="fr").audio(
                "Bonjour, comment allez-vous?")
        signal = np.frombuffer(pcm, dtype="<i2")
        self.assertEqual(rate, SAMPLE_RATE_KOKORO)
        self.assertEqual(signal.size, 500 + 720 + 600)
        self.assertTrue(np.all(signal[500:1220] == 0))

    def test_kokoro_refuses_invalid_or_empty_audio(self):
        import numpy as np
        module = types.ModuleType("kokoro")
        class FakePipeline:
            def __init__(self, **kwargs):
                pass
            def __call__(self, text, **kwargs):
                yield text, "", np.array([math.nan], dtype="float32")
        module.KPipeline = FakePipeline
        with patch.dict(sys.modules, {"kokoro": module}):
            voice = SpeechEngine(engine="kokoro", language="en")
            with self.assertRaisesRegex(RuntimeError, "non-finite"):
                voice.audio("Hello.")
            with self.assertRaisesRegex(ValueError, "combination"):
                SpeechEngine(engine="kokoro", language="fr", voice="af_heart")
        with self.assertRaisesRegex(ValueError, "Custom"):
            SpeechEngine(engine="espeak", language="fr", voice="ff_siwis")

    def test_scene_audio_expands_duration_without_word_clipping(self):
        pcm8s = b"\x01\x00" * (24000 * 8)
        class FakeSpeechEngine:
            def __init__(self, *, engine, language, voice):
                self.engine, self.language, self.voice = engine, language, "ff_siwis"
            def audio(self, text):
                return pcm8s, 24000

        with patch("automate_ytb.episode.SpeechEngine", FakeSpeechEngine):
            result = _narrate_scenes(self.plan, self.root/"narration.wav",
                                     "fr", limit=1, engine="kokoro")
        self.assertEqual(result["engine"], "kokoro-natural")
        self.assertEqual(result["providerApiCalls"], 0)
        self.assertFalse(result["wordAlignment"])
        updated = load_plan(self.plan)
        self.assertGreaterEqual(updated["scenes"][0]["endMs"], 8350)
        self.assertEqual(updated["scenes"][1]["startMs"], updated["scenes"][0]["endMs"])
        self.assertFalse(updated["publicationApproved"])
        with wave.open(str(self.root/"narration.wav")) as audio:
            self.assertEqual(audio.getframerate(), 24000)
            self.assertGreaterEqual(audio.getnframes(), 24000 * 8)

    def test_wrong_sample_rates_fail_without_plan_mutation(self):
        initial = load_plan(self.plan)
        class BadSpeechEngine:
            voice = None
            def __init__(self, **kwargs):
                pass
            def audio(self, text):
                self.calls = getattr(self, "calls", 0) + 1
                return b"\x01\x00" * 100, 24000 if self.calls == 1 else 22050
        with patch("automate_ytb.episode.SpeechEngine", BadSpeechEngine):
            with self.assertRaisesRegex(RuntimeError, "mismatched"):
                _narrate_scenes(self.plan, self.root/"failed.wav",
                                 "fr", limit=2, engine="kokoro")
        self.assertFalse((self.root/"failed.wav").exists())
        self.assertEqual(load_plan(self.plan), initial)


if __name__ == "__main__":
    unittest.main()
