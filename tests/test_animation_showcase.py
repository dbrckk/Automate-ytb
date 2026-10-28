"""Fast contract tests for the genuine four-actor Android video showcase."""
from pathlib import Path
import tempfile
import unittest
import wave

from automate_ytb.soundtrack import SAMPLERATE

from scripts.render_animation_showcase import (
    SCENES, SCENE_SECONDS, FPS, _stamp, write_captions, write_original_score)


class AnimationShowcaseTests(unittest.TestCase):
    def test_original_four_character_story(self):
        self.assertEqual(len(SCENES),4)
        self.assertEqual({s[0] for s in SCENES},{"fox","rabbit","cat","owl"})
        self.assertEqual(FPS,24)
        self.assertGreaterEqual(SCENE_SECONDS,3)
        self.assertEqual(_stamp(4.25),"00:00:04,250")

    def test_french_subtitles_are_contiguous_and_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"subtitles.srt"
            write_captions(path)
            text=path.read_text(encoding="utf-8")
            self.assertEqual(text.count(" --> "),4)
            self.assertIn("00:00:00,000 --> 00:00:04,170",text)
            self.assertIn("00:00:12,750 --> 00:00:16,920",text)
            self.assertIn("renard",text)
            self.assertIn("chouette",text)

    def test_free_original_music_duration(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"original-score.wav"
            write_original_score(path)
            with wave.open(str(path),"rb") as wav:
                self.assertEqual(wav.getnchannels(),1)
                self.assertEqual(wav.getframerate(),SAMPLERATE)
                self.assertAlmostEqual(wav.getnframes()/SAMPLERATE,17.0,places=2)
            self.assertGreater(path.stat().st_size,400000)


if __name__=="__main__":
    unittest.main()
