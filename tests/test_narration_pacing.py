"""Auditable PCM padding checks for original science Shorts narration."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

from automate_ytb.episode import _narrate_scenes
from automate_ytb.narration_pacing import inspect
from automate_ytb.scene_plan import plan
from automate_ytb.production import load_plan


class ScienceNarrationPacingTests(unittest.TestCase):
    def test_overlong_scene_tails_block_science_release(self):
        rows = [
            {"sceneId": f"scene-{i:03d}", "spokenAudioMs": 3000,
             "sceneDurationMs": 6000, "tailPaddingMs": 3000}
            for i in range(1, 6)
        ]
        report = inspect(rows, strict=True)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["totalTailPaddingMs"], 15000)
        self.assertEqual(report["maxSceneTailPaddingMs"], 3000)
        self.assertEqual(report["tailPaddingFraction"], 0.5)
        self.assertTrue(report["errors"])
        self.assertFalse(report["publicationApproved"])
        self.assertEqual(inspect(rows, strict=False)["status"],
                         "review-recommended")

    def test_well_paced_scenes_pass_without_fabricating_speech(self):
        rows = [
            {"sceneId": f"scene-{i:03d}", "spokenAudioMs": 5550,
             "sceneDurationMs": 6000, "tailPaddingMs": 450}
            for i in range(1, 6)
        ]
        report = inspect(rows, strict=True)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["totalTailPaddingMs"], 2250)
        self.assertEqual(report["tailPaddingFraction"], 0.075)
        self.assertFalse(report["errors"])
        self.assertFalse(report["publicationApproved"])

    def test_real_pcm_duration_overshoot_blocks_strict_30s_export(self):
        # 31.555s was a real, otherwise clean reference export. A media
        # quality gate used to accept it as a requested 30-second Short.
        rows = [
            {"sceneId": f"scene-{i+1:03d}",
             "spokenAudioMs": spoken,
             "sceneDurationMs": length,
             "tailPaddingMs": 350}
            for i, (spoken, length) in enumerate(
                ((5870, 6220), (6270, 6620), (5870, 6220),
                 (5910, 6260), (5885, 6235)))
        ]
        report = inspect(rows, strict=True, requested_duration_ms=30000)
        self.assertEqual(report["durationDriftMs"], 1555)
        self.assertEqual(report["requestedDurationMs"], 30000)
        self.assertEqual(report["maxAllowedDurationDriftMs"], 600)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any("requested duration" in e
                            for e in report["errors"]))
        self.assertEqual(
            inspect(rows, strict=False, requested_duration_ms=30000)["status"],
            "review-recommended")
        self.assertFalse(report["publicationApproved"])

    def test_nominal_30s_native_shorts_duration_tolerance(self):
        rows = [
            {"sceneId": f"scene-{i+1:03d}", "spokenAudioMs": 5660,
             "sceneDurationMs": 6010, "tailPaddingMs": 350}
            for i in range(5)
        ]
        passing = inspect(rows, strict=True, requested_duration_ms=30000)
        self.assertEqual(passing["status"], "passed")
        self.assertEqual(passing["durationDriftMs"], 50)
        self.assertFalse(passing["errors"])
        for requested in (0, -1, True, 30.0, float("nan"), "30000",
                          3600001):
            with self.subTest(requested=requested), self.assertRaises(ValueError):
                inspect(rows, strict=True, requested_duration_ms=requested)
        self.assertIsNone(inspect(rows, strict=True)["durationDriftMs"])

    def test_malformed_claims_of_pcm_padding_are_rejected(self):
        bad = {"sceneId": "scene-001", "spokenAudioMs": 4000,
               "sceneDurationMs": 6000, "tailPaddingMs": 1500}
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            inspect([bad], strict=True)
        for malformed in ([], [dict(bad, spokenAudioMs=True)],
                          [dict(bad, tailPaddingMs=-1)]):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    inspect(malformed, strict=True)

    def test_measured_pcm_padding_matches_real_wav_and_plan(self):
        text = " ".join((
            "The Sun heats tropical oceans.",
            "Wind drives the upper ocean waters.",
            "Earth rotation bends moving currents.",
            "Cold saline waters sink near the poles.",
            "Ocean circulation redistributes heat worldwide.",
        ))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "plan.json"
            source.write_text(json.dumps(plan(
                topic="Ocean currents around Earth",
                script=text,
                character="Original Earth and ocean science graphics",
                duration=30, shot_seconds=6,
            )), encoding="utf-8")

            class DeterministicSpeech:
                def __init__(self, *, engine, language, voice):
                    self.voice = voice or "af_heart"
                    self.speed = 1.0

                def audio(self, phrase):
                    # Actual signed 16-bit, non-silent PCM, no cloud model.
                    return b"\x00\x20" * 4800, 24000

            wav = root / "narration.wav"
            with patch("automate_ytb.episode.SpeechEngine", DeterministicSpeech):
                details = _narrate_scenes(
                    source, wav, "en", None,
                    engine="kokoro", caption_timing="audio")
            measured = details["measuredScenePacing"]
            self.assertEqual(len(measured), 5)
            with wave.open(str(wav), "rb") as audio:
                duration_ms = round(audio.getnframes() * 1000 /
                                    audio.getframerate())
            self.assertEqual(sum(x["sceneDurationMs"] for x in measured),
                             duration_ms)
            scenes = load_plan(source)["scenes"]
            self.assertEqual(scenes[-1]["endMs"], duration_ms)
            self.assertTrue(all(
                scene["tailPaddingMs"] ==
                scene["sceneDurationMs"] - scene["spokenAudioMs"]
                for scene in measured))
            result = inspect(measured, strict=True)
            self.assertEqual(result["status"], "failed")
            self.assertGreater(result["totalTailPaddingMs"], 10000)
            self.assertFalse(result["publicationApproved"])


if __name__ == "__main__":
    unittest.main()
