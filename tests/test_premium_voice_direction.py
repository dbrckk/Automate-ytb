"""Preview voice policies: neural by default for human quality review.

The PCM test double verifies timeline, style/rate and source WAV; this does
not pretend to score the naturalness of real speaker audio. CI separately
renders a real Kokoro episode and keeps the final source WAV for listening.
"""
from __future__ import annotations

import wave
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.universal_kinetic import synthesize
from automate_ytb.voice_pacing import speaking_speed,phrase_speed,natural_pause_ms


class FakePCM:
    calls=[]
    def __init__(self,*,engine,language,voice):
        self.engine=engine
        self.language=language
        self.voice=voice
        self.speed=1.
    def audio(self,text):
        self.calls.append((self.engine,text,self.speed))
        return (b"\0\x30"*24000*2),24000


class PremiumVoiceDirectionTests(unittest.TestCase):
    def setUp(self):
        FakePCM.calls=[]

    def test_live_neural_phrasing_is_selected_for_real_premium_episode(self):
        story={"language":"en","beats":[
            {"narration":"But the train still glides along the rails."},
            {"narration":"Suddenly the motor pushes it forward!"}
        ]}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"narration.wav"
            cues=[]
            with patch("automate_ytb.universal_kinetic.SpeechEngine",FakePCM):
                boundaries=synthesize(story,"kokoro",path,voice_name="af_heart",
                                      caption_cues=cues,voice_style="expressive")
            self.assertEqual(len(boundaries),3)
            self.assertGreater(boundaries[-1],boundaries[1])
            with wave.open(str(path)) as audio:
                self.assertEqual(audio.getframerate(),24000)
                self.assertEqual(audio.getsampwidth(),2)
                self.assertEqual(audio.getnchannels(),1)
            self.assertTrue(all(c[0]=="kokoro" for c in FakePCM.calls))
            used={round(c[2],2) for c in FakePCM.calls}
            self.assertIn(.93,used)
            self.assertIn(1.00,used)
            self.assertEqual(len(cues),len(FakePCM.calls))
            self.assertTrue(all(c["endMs"]>c["startMs"] for c in cues))
            self.assertAlmostEqual(speaking_speed(style="natural"),.94)

    def test_technical_espeak_path_remains_byte_timing_compatible(self):
        story={"language":"en","beats":[
            {"narration":"The rain falls on the street."},
            {"narration":"The tree bends towards the sun."}
        ]}
        with tempfile.TemporaryDirectory() as folder:
            with patch("automate_ytb.universal_kinetic.SpeechEngine",FakePCM):
                synthesize(story,"espeak",Path(folder)/"test.wav",
                           voice_style="expressive")
            self.assertTrue(all(rate==1.0 for _,_,rate in FakePCM.calls))
            self.assertGreater(natural_pause_ms("A sentence.",neural=True),0)
            self.assertEqual(natural_pause_ms("An unfinished phrase",neural=True),0)

    def test_invalid_style_fails_closed_before_synthesis(self):
        story={"language":"en","beats":[{"narration":"Hello world."},
                                         {"narration":"Good morning."}]}
        with tempfile.TemporaryDirectory() as folder:
            with patch("automate_ytb.universal_kinetic.SpeechEngine",FakePCM):
                with self.assertRaises(ValueError):
                    synthesize(story,"kokoro",Path(folder)/"bad.wav",
                               voice_style="ultra human")
        self.assertEqual(FakePCM.calls,[])


if __name__=="__main__":
    unittest.main()
