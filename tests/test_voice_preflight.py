"""PCM provenance and no-duplicate-TTS regression tests for the M0 video gate."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.episode import build_preview
from automate_ytb.production import load_plan
from automate_ytb.scene_plan import plan as make_plan
from automate_ytb.voice_preflight import prepare, consume, _sha


LINES = (
    "Solar wind streams away from the Sun.",
    "The magnetic field bends its paths.",
    "Particles collide high in the sky.",
    "Excited oxygen atoms release light.",
    "The aurora dances across the night.",
)


class _NaturalFiveSecondSpeech:
    calls = 0

    def __init__(self, *, engine, language, voice):
        if engine != "kokoro" or language != "en":
            raise AssertionError("Unexpected paid or fallback engine")
        self.voice = voice or "af_heart"
        self.speed = 1.0

    def audio(self, text):
        self.__class__.calls += 1
        if not text.strip():
            raise AssertionError("Empty Kokoro narration")
        # Real 16-bit, non-silent PCM bytes are written into a verifiable WAV.
        return b"\x00\x20" * (24000 * 5 + 24000 * 3 // 5), 24000


class _ShortSpeech(_NaturalFiveSecondSpeech):
    def audio(self, text):
        self.__class__.calls += 1
        return b"\x00\x20" * (24000 * 2), 24000


class VoiceBeforeBlenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="narration-m0-")
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.json"
        data = make_plan(
            topic="Why Do Northern Lights Dance?",
            script=" ".join(LINES), duration=30, shot_seconds=6,
            character="Original Earth and aurora science graphics",
        )
        self.plan.write_text(json.dumps(data), encoding="utf-8")
        self.source_sha = _sha(self.plan)
        self.bundle = self.root / "speech"

    def tearDown(self):
        self.temp.cleanup()

    def _prepare(self):
        _NaturalFiveSecondSpeech.calls = 0
        with patch("automate_ytb.episode.SpeechEngine", _NaturalFiveSecondSpeech):
            return prepare(plan=self.plan, output_dir=self.bundle,
                           language="en", voice_style="natural",
                           voice_name="af_heart")

    def test_preflight_preserves_original_and_reuses_exact_wav(self):
        info = self._prepare()
        self.assertEqual(_NaturalFiveSecondSpeech.calls, 5)
        self.assertEqual(info["status"], "passed")
        self.assertEqual(_sha(self.plan), self.source_sha)
        prepared_plan = self.bundle / "plan.json"
        voice, requested, wav = consume(
            manifest=self.bundle / "manifest.json",
            plan=prepared_plan, language="en", voice_style="natural",
            voice_name="af_heart")
        self.assertEqual(requested, 30000)
        self.assertEqual(voice["engine"], "kokoro-natural")
        self.assertEqual(_sha(wav), info["narrationSha256"])
        self.assertEqual(load_plan(prepared_plan)["scenes"][0]["narration"], LINES[0])

        output = self.root / "final"
        # Real build-preview routing must not call the synthesizer again.
        # FFmpeg is not needed for this unit routing test: the actual
        # encoder is exercised in separate workflow release gates.
        with (patch("automate_ytb.episode._narrate_scenes",
                    side_effect=AssertionError("Kokoro was generated twice")),
              patch("automate_ytb.episode.make_thumbnails", return_value=[]),
              patch("automate_ytb.episode.create_local_art",
                    return_value={"status": "reused"}),
              patch("automate_ytb.episode.production._run"),
              patch("automate_ytb.episode.production.render",
                    return_value={"video": str(output / "preview.mp4"),
                                  "scenesRendered": 5}),
              patch("automate_ytb.story_preflight.inspect",
                    return_value={"status": "sampled-clean",
                                  "exactRepeatCount": 0,
                                  "nearRepeatNeighborCount": 0,
                                  "speakingPaceWarningCount": 0})):
            result = build_preview(
                plan_path=prepared_plan, output=output, voice="kokoro",
                voice_name="af_heart", voice_style="natural",
                language="en", caption_timing="audio",
                voice_preflight=self.bundle / "manifest.json",
                style="science", resolution="shorts")
        self.assertEqual(result["voice"]["engine"], "kokoro-natural")
        self.assertEqual(_sha(output / "narration.wav"), info["narrationSha256"])
        self.assertEqual(_NaturalFiveSecondSpeech.calls, 5)
        report = json.loads((output / "narration-pacing.json").read_text())
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["requestedDurationMs"], 30000)

    def test_excessive_silence_fails_before_3d_without_success_marker(self):
        with patch("automate_ytb.episode.SpeechEngine", _ShortSpeech):
            with self.assertRaisesRegex(ValueError, "does not fit"):
                prepare(plan=self.plan, output_dir=self.bundle,
                        language="en", voice_style="natural")
        self.assertFalse((self.bundle / "manifest.json").exists())
        result = json.loads((self.bundle / "narration-pacing.json").read_text())
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["publicationApproved"])
        self.assertEqual(_sha(self.plan), self.source_sha)

    def test_tampered_voice_plan_and_wrong_config_fail_closed(self):
        self._prepare()
        manifest = self.bundle / "manifest.json"
        ready = self.bundle / "plan.json"
        with self.assertRaisesRegex(ValueError, "requested voice"):
            consume(manifest=manifest, plan=ready, language="fr",
                    voice_style="natural", voice_name="ff_siwis")
        initial = (self.bundle / "narration.wav").read_bytes()
        (self.bundle / "narration.wav").write_bytes(initial[:-4] + b"\x00\x00\x00\x00")
        with self.assertRaisesRegex(ValueError, "changed"):
            consume(manifest=manifest, plan=ready, language="en",
                    voice_style="natural", voice_name="af_heart")
        (self.bundle / "narration.wav").write_bytes(initial)
        ready.write_text(ready.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed"):
            consume(manifest=manifest, plan=ready, language="en",
                    voice_style="natural", voice_name="af_heart")

    def test_forbids_legacy_espeak_or_partial_episode_preflight(self):
        self._prepare()
        for voice,limit,caption in [
            ("espeak",None,"audio"), ("none",None,"audio"),
            ("kokoro",1,"audio"), ("kokoro",None,"estimated"),
        ]:
            with self.subTest(voice=voice, limit=limit, caption=caption):
                with self.assertRaisesRegex(ValueError, "Preflight WAV reuse"):
                    build_preview(
                        plan_path=self.bundle / "plan.json",
                        output=self.root / "fail",
                        voice=voice, limit=limit, caption_timing=caption,
                        voice_preflight=self.bundle / "manifest.json",
                        style="science", resolution="shorts")
if __name__ == "__main__":
    unittest.main()
