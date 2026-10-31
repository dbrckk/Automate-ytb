"""Natural offline speech delivery contract, samples and caption timing."""
from __future__ import annotations

from array import array
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave

from automate_ytb.voice_pacing import (
    STYLES, VERSION, natural_pause_ms, speaking_speed)
from automate_ytb.episode import _narrate_scenes, build_preview
from automate_ytb.production import load_plan
from automate_ytb.scene_plan import plan
from automate_ytb.captions import caption_phrases, subtitles_for_scenes


class NaturalNarrationTests(unittest.TestCase):
    def test_profiles_bounded_and_not_fake_voice_replacements(self):
        self.assertEqual(set(STYLES), {"natural", "gentle", "lively"})
        self.assertEqual(speaking_speed(style="natural"), .94)
        self.assertLess(speaking_speed(style="gentle"), .94)
        self.assertGreater(speaking_speed(style="lively"), 1)
        self.assertRegex(VERSION, r"^kokoro-phrasing-v[1-9][0-9]*(?:-|$)")
        for payload in ("high;amovie=/secret", "fastest", "", None):
            with self.subTest(value=payload):
                with self.assertRaises(ValueError):
                    speaking_speed(style=payload)

    def test_sentence_boundaries_have_deliberate_nonuniform_pauses(self):
        self.assertEqual(natural_pause_ms("Then she turns.", neural=False), 80)
        self.assertGreater(natural_pause_ms("Then she turns.", neural=True),
                           natural_pause_ms("Then she", neural=True))
        self.assertGreater(natural_pause_ms("Wait...", neural=True),
                           natural_pause_ms("The story ends.", neural=True))
        self.assertEqual(natural_pause_ms("A note,", neural=True), 105)
        with self.assertRaises(ValueError):
            natural_pause_ms("", neural=True)

    def test_synthesized_french_voice_style_and_pauses_remain_pcm_aligned(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = plan(topic="Original french storytelling",
                        script=" ".join([
                            "Une chouette découvre un lac très mystérieux.",
                            "Elle réfléchit longtemps avant de partir.",
                            "Son ami lui montre une petite lumière.",
                            "Elle suit tranquillement le sentier.",
                            "Enfin, elle raconte sa belle aventure.",
                        ]), character="Une petite chouette violette",
                        duration=30, shot_seconds=6)
            data["scenes"][0]["narration"] = (
                "La petite chouette violette découvre un chemin absolument merveilleux. "
                "Elle y rencontre un gentil lapin près du ruisseau tranquille.")
            file = root/"plan.json"
            file.write_text(json.dumps(data), encoding="utf8")
            seen = []

            class FakeNaturalTTS:
                voice = "ff_siwis"
                def __init__(self, *, engine, language, voice):
                    self.engine = engine
                def audio(self, value):
                    seen.append((self.speed, value))
                    signal = array("h", [9100] * (24000//3))
                    return signal.tobytes(), 24000

            with patch("automate_ytb.episode.SpeechEngine", FakeNaturalTTS):
                result = _narrate_scenes(
                    file, root/"narration.wav", "fr", limit=1,
                    engine="kokoro", caption_timing="audio",
                    narration_style="gentle")
            self.assertEqual(result["delivery"]["style"], "gentle")
            self.assertEqual(result["delivery"]["nativeSpeakingRate"], .88)
            self.assertTrue(result["delivery"]["punctuationAwarePauses"])
            self.assertEqual(result["delivery"]["insertedBetweenPhraseSilenceMs"],
                             190)
            self.assertTrue(all(speed == .88 for speed, text in seen))
            updated = load_plan(file)
            phrases = caption_phrases(updated["scenes"][0]["narration"])
            self.assertEqual(len(phrases), 2)
            cues = updated["scenes"][0]["captionSegments"]
            self.assertEqual(len(cues), 2)
            self.assertEqual(cues[1]["startMs"], 333 + 190)
            subtitles, info = subtitles_for_scenes(
                updated["scenes"][:1], use_audio_boundaries=True)
            self.assertEqual(subtitles.count(" --> "), 2)
            with wave.open(str(root/"narration.wav")) as wav:
                self.assertEqual(wav.getframerate(), 24000)
                self.assertEqual(round(wav.getnframes()*1000/24000),
                                 updated["scenes"][0]["endMs"])
            self.assertFalse(updated["publicationApproved"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak-ng") or shutil.which("espeak")),
                         "Real FFmpeg and offline eSpeak needed")
    def test_android_voice_listening_sample_is_mp3_and_full_wav_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = plan(topic="Une histoire de forêt originale",
                        script=" ".join([
                            "La chouette marche doucement vers son village.",
                            "Elle voit une lumière douce dans une maison.",
                            "Le petit renard l'accueille avec le sourire.",
                            "Une pluie fine commence à tomber dehors.",
                            "Enfin, la chouette s'endort en paix.",
                        ]),
                        character="Une chouette violette originale",
                        duration=30, shot_seconds=6)
            file = root/"plan.json"
            file.write_text(json.dumps(data), encoding="utf8")
            output = root/"video"
            result = build_preview(plan_path=file, output=output,
                                   limit=1, voice="espeak", voice_style="lively",
                                   caption_timing="audio", soundtrack="none")
            sample = output/"voice-sample.mp3"
            self.assertEqual(result["voicePreview"], str(sample))
            self.assertTrue(sample.stat().st_size > 800)
            self.assertTrue((output/"narration.wav").is_file())
            with wave.open(str(output/"narration.wav")) as wav:
                self.assertGreater(wav.getnframes(), 16000)
            info = subprocess.run(
                ["ffprobe", "-v", "error", "-of", "json",
                 "-show_entries", "format=duration:stream=codec_name",
                 str(sample)], capture_output=True, text=True, check=True)
            parsed = json.loads(info.stdout)
            self.assertTrue(any(s.get("codec_name") == "mp3"
                                for s in parsed["streams"]))
            self.assertLessEqual(float(parsed["format"]["duration"]), 12.2)
            self.assertTrue((output/"preview.mp4").is_file())
            self.assertFalse(result["publicationApproved"])


if __name__ == "__main__":
    unittest.main()
