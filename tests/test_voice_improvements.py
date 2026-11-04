"""Speech-style and export verification without installing/download Kokoro in unit CI."""
from __future__ import annotations

import math
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.narration import VOICE_CHOICES
from automate_ytb.voice_audition import CANDIDATES, generate, listening_excerpt
from automate_ytb.voice_pacing import phrase_speed, speaking_speed


class VoiceImprovementTests(unittest.TestCase):
    def test_validated_speaker_ids(self):
        self.assertTrue(set(CANDIDATES).issubset(VOICE_CHOICES["en"]))
        self.assertNotIn("af_nicole", VOICE_CHOICES["fr"])

    def test_excerpt_preserves_first_complete_sentence(self):
        self.assertEqual(
            listening_excerpt("A storm forms. Another storm dissipates."),
            "A storm forms.")
        value = listening_excerpt("The " + "interesting " * 42 + "ocean.", max_characters=90)
        self.assertLessEqual(len(value), 90)
        self.assertFalse(value.endswith(" ocean."))

    def test_expressive_direction_is_bounded_and_opt_in(self):
        self.assertEqual(speaking_speed(style="expressive"), .95)
        self.assertGreater(phrase_speed("A volcano erupts!", style="expressive"),
                           phrase_speed("But the ice holds.", style="expressive"))
        self.assertEqual(phrase_speed("An eruption!", style="natural"), .94)
        self.assertEqual(phrase_speed("Still?", style="natural"), .94)
        for phrase in ("A volcano erupts!", "What happens next?", "But why?", "Light moves."):
            self.assertTrue(.88 <= phrase_speed(phrase, style="expressive") <= 1.04)

    @unittest.skipUnless(shutil.which("ffmpeg"), "Real MP3 encode requires FFmpeg")
    def test_artifacts_encode_to_real_mp3_with_mocked_pcm(self):
        # Mock the TTS ONLY; this verifies the actual MP3 encoder, filenames
        # and manifest logic, not real Kokoro voice tone or naturalness.
        samples = [round(5000*math.sin(i*.08)) for i in range(24000)]
        pcm = struct.pack("<" + "h"*len(samples), *samples)

        class SyntheticSpeech:
            def __init__(self, **kwargs):
                self.voice = kwargs["voice"]
                self.speed = 1

            def audio(self, text):
                return pcm, 24000

        with tempfile.TemporaryDirectory() as directory:
            with patch("automate_ytb.voice_audition.SpeechEngine", SyntheticSpeech):
                report = generate(script="Sunlight heats the ocean. Winds follow.",
                                  output=Path(directory), style="expressive")
            self.assertEqual(len(report["samples"]), len(CANDIDATES))
            self.assertEqual(report["excerpt"], "Sunlight heats the ocean.")
            self.assertFalse(report["bestVoiceAutomaticallySelected"])
            for sample in report["samples"]:
                data = (Path(directory) / sample["file"]).read_bytes()
                self.assertGreater(len(data), 1000)
                self.assertFalse((Path(directory) /
                                  (sample["voiceId"] + ".wav")).exists())
            self.assertTrue((Path(directory) / "audition-report.json").is_file())


if __name__ == "__main__":
    unittest.main()
