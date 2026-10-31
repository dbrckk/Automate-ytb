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

from automate_ytb.narration import SpeechEngine, SAMPLE_RATE_KOKORO, DEFAULT_VOICES, VOICE_CHOICES, _segment_pause_ms
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

    def test_every_one_click_speaker_is_usable_with_the_proper_language(self):
        import numpy as np

        class LocalKokoroPipeline:
            def __init__(self, *, lang_code, repo_id=None):
                self.lang_code = lang_code
            def __call__(self, text, *, voice, speed):
                calls.append((self.lang_code, voice, speed))
                yield types.SimpleNamespace(
                    graphemes=text,
                    audio=np.array([0.1, -0.1, 0.2, -0.2], dtype="float32"))

        choices = {
            "fr": ("ff_siwis",),
            "en": ("af_heart", "af_bella", "am_michael"),
        }
        self.assertEqual({k: tuple(sorted(v)) for k,v in VOICE_CHOICES.items()},
                         {k: tuple(sorted(v)) for k,v in choices.items()})
        self.assertEqual(DEFAULT_VOICES, {"fr": "ff_siwis", "en": "af_heart"})
        calls = []
        module = types.ModuleType("kokoro")
        module.KPipeline = LocalKokoroPipeline
        with patch.dict(sys.modules, {"kokoro": module}):
            for language, supported in choices.items():
                for speaker in supported:
                    with self.subTest(language=language, speaker=speaker):
                        engine = SpeechEngine(
                            engine="kokoro", language=language, voice=speaker)
                        audio, rate = engine.audio("Original narration.")
                        self.assertTrue(audio)
                        self.assertEqual(rate, SAMPLE_RATE_KOKORO)
                        self.assertEqual(calls[-1][:2],
                                         ("f" if language == "fr" else "a", speaker))
                incompatible = "af_bella" if language == "fr" else "ff_siwis"
                with self.assertRaisesRegex(ValueError, "combination"):
                    SpeechEngine(engine="kokoro", language=language,
                                 voice=incompatible)

    def test_android_workflow_exposes_only_supported_voices_and_rejects_invalid_ones(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/one-click-preview.yml").read_text(
                        encoding="utf-8")
        self.assertIn("voice_name:", workflow)
        self.assertIn("options: [auto, af_heart, af_bella, am_michael, ff_siwis]",
                      workflow)
        self.assertIn("default: auto", workflow)
        self.assertIn("YT_VOICE_NAME: ${{ inputs.voice_name }}", workflow)
        self.assertIn("case \"$YT_LANGUAGE:$YT_VOICE_NAME\" in", workflow)
        self.assertIn("en:af_heart|en:af_bella|en:am_michael|fr:ff_siwis)", workflow)
        self.assertIn('VOICE_ARGS=(--voice-name "$YT_VOICE_NAME")', workflow)
        self.assertIn('"${VOICE_ARGS[@]}"', workflow)

    def test_kokoro_punctuation_pauses_do_not_stop_mid_sentence(self):
        from automate_ytb.voice_pacing import natural_pause_ms, VERSION
        self.assertIn("no-artificial-mid-sentence-pauses", VERSION)
        for part in ("The ocean current flows", "without a final period",
                     "une phrase continue", "warm water"):
            self.assertEqual(natural_pause_ms(part, neural=True), 0)
            self.assertEqual(natural_pause_ms(part, neural=False), 80)
        self.assertEqual(natural_pause_ms("Ready.", neural=True), 190)
        self.assertEqual(natural_pause_ms("Really?", neural=True), 190)
        self.assertEqual(natural_pause_ms("And then...", neural=True), 290)
        self.assertEqual(natural_pause_ms("Perhaps,", neural=True), 105)
        self.assertEqual(natural_pause_ms("Therefore:", neural=True), 160)
        with self.assertRaises(ValueError):
            natural_pause_ms(" ", neural=True)

    def test_real_caption_phrase_break_does_not_create_digital_silence(self):
        from automate_ytb.captions import caption_phrases
        original = (
            "The ocean gently carries warm water across a wide basin "
            "and gradually turns northward before reaching colder regions.")
        phrases = caption_phrases(original)
        self.assertGreaterEqual(len(phrases), 2)
        self.assertFalse(phrases[0].endswith((".", "!", "?", ":", ";", ",")))
        data = json.loads(self.plan.read_text(encoding="utf8"))
        data["scenes"][0]["narration"] = original
        self.plan.write_text(json.dumps(data), encoding="utf8")
        pcm = b"\x00\x20" * 4800
        calls = []
        class FixedSpeech:
            def __init__(self, *, engine, language, voice):
                self.engine, self.language = engine, language
                self.voice = voice or "af_heart"
                self.speed = 1.0
            def audio(self, text):
                calls.append(text)
                return pcm, 24000
        with patch("automate_ytb.episode.SpeechEngine", FixedSpeech):
            result = _narrate_scenes(
                self.plan, self.root / "continuous.wav", "en", 1,
                engine="kokoro", caption_timing="audio")
        self.assertEqual(calls, phrases)
        self.assertEqual(result["delivery"]["insertedBetweenPhraseSilenceMs"], 0)
        self.assertEqual(result["captionTiming"], "audio-derived-synthesized-phrases")
        self.assertFalse(result["wordAlignment"])
        updated = load_plan(self.plan)
        boundaries = updated["scenes"][0]["captionSegments"]
        self.assertEqual(len(boundaries), len(phrases))
        self.assertEqual(boundaries[0]["endMs"] -
                         boundaries[0]["startMs"], 200)
        with wave.open(str(self.root / "continuous.wav"), "rb") as audio:
            sound = audio.readframes(audio.getnframes())
        # Both adjacent fragments contain their actual PCM, with neither
        # the former 95ms digital silence nor an invented word alignment.
        import struct
        offset = boundaries[0]["endMs"] * 48
        around = sound[offset - 200:offset + 200]
        self.assertTrue(any(value for value in struct.unpack(
            "<" + "h"*(len(around)//2), around)))

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
        self.assertLess(np.count_nonzero(samples == 0), 3)
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
