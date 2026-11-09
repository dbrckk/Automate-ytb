"""P4.7 actual physical foley and measured Kokoro PCM preservation tests."""
from array import array
import math
from pathlib import Path
import tempfile
import unittest
import wave

from automate_ytb.forest_contact25d import IMPACT_TIME
from automate_ytb.forest_voice_timeline import ENGLISH_SCRIPT, measured_timeline
from automate_ytb.forest_soundscape25d import (
    RATE, VERSION, _ducker, _flower_chime, _footstep,
    mix_soundscape, render_soundscape, sound_events, source_to_video,
)


def timeline():
    # This is timing geometry only, not fabricated voice PCM or a Kokoro report
    # for the production exporter; its test PCM is synthesized separately.
    spans=[]
    for i,text in enumerate(ENGLISH_SCRIPT):
        start=170+i*3170
        spans.append(dict(index=i+1,text=text,
                          startMs=start,endMs=start+3000))
    return measured_timeline(dict(engine="kokoro-natural",language="en",
                                  durationSeconds=13.,beats=spans))


class OriginalCausalSoundscapeTests(unittest.TestCase):
    def test_foley_schedule_uses_actual_rig_impact_and_voice_paced_edit(self):
        seq=timeline()
        events=sound_events(seq)
        self.assertIn("p47",VERSION)
        self.assertGreaterEqual(len(events["footsteps"]),8)
        self.assertEqual(events["footsteps"][0][0],"right")
        self.assertAlmostEqual(events["footsteps"][0][2],.725,places=6)
        self.assertAlmostEqual(events["flower"],
                               source_to_video(IMPACT_TIME,seq),places=8)
        self.assertAlmostEqual(events["butterfly"],
                               source_to_video(IMPACT_TIME+.12,seq),places=8)
        self.assertLess(events["flower"],events["butterfly"])
        for side,video_t,source_t in events["footsteps"]:
            self.assertIn(side,("left","right"))
            self.assertAlmostEqual(source_to_video(source_t,seq),video_t,places=5)
            self.assertTrue(0<=video_t<=seq.duration)

    def test_impulses_never_begin_before_grounded_foot_or_flower(self):
        self.assertEqual(_flower_chime(-1/RATE),0.)
        self.assertEqual(_flower_chime(0.),0.)
        self.assertEqual(_footstep(-1/RATE),0.)
        self.assertGreater(abs(_flower_chime(.001)),.005)
        self.assertGreater(abs(_footstep(.005)),.005)
        self.assertEqual(_footstep(.2),0.)
        self.assertEqual(_flower_chime(.7),0.)

    def test_speech_attenuates_background_without_muting_voice(self):
        seq=timeline()
        beat=seq.beats[0]
        in_speech=(beat.speech_start+beat.speech_end)/2
        in_gap=(beat.speech_end+beat.end)/2
        self.assertLess(_ducker(in_speech,seq),_ducker(in_gap,seq))
        self.assertLessEqual(_ducker(in_gap,seq),1.)
        self.assertGreater(_ducker(in_speech,seq),0.)

    def test_real_24khz_pcm_is_mixed_length_correct_and_deterministic(self):
        seq=timeline()
        zero=b"\0\0"*round(seq.duration*RATE)
        first,report=mix_soundscape(zero,seq)
        self.assertEqual(len(first),len(zero))
        self.assertNotEqual(first,zero)
        self.assertEqual(report["channels"],1)
        self.assertEqual(report["sampleRate"],RATE)
        self.assertEqual(report["clippedSamples"],0)
        self.assertEqual(report["voiceGain"],1.)
        self.assertEqual(report["contactSourceSeconds"],round(IMPACT_TIME,5))
        self.assertTrue(report["speechDucking"])
        self.assertTrue(report["originalLocallySynthesized"])
        self.assertEqual(first,mix_soundscape(zero,seq)[0])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"original.wav"
            written=render_soundscape(path,zero,seq)
            self.assertEqual(written,report)
            with wave.open(str(path),"rb") as file:
                self.assertEqual(file.getnchannels(),1)
                self.assertEqual(file.getframerate(),RATE)
                self.assertEqual(file.getsampwidth(),2)
                self.assertEqual(file.readframes(file.getnframes()),first)

    def test_actual_voice_samples_remain_audible_above_score(self):
        seq=timeline()
        count=round(seq.duration*RATE)
        samples=array("h",[5000])*count
        combined,meta=mix_soundscape(samples.tobytes(),seq)
        decoded=array("h")
        decoded.frombytes(combined)
        self.assertEqual(meta["voiceGain"],1.)
        # At the start of speech, an original 5000-count voice survives the
        # ambience. No TTS voice is replaced with synthetic oscillators.
        offset=round((seq.beats[0].speech_start+.5)*RATE)
        self.assertGreater(decoded[offset],3200)
        self.assertLess(decoded[offset],7200)

    def test_validation_rejects_unsafe_pcm_or_event_timestamps(self):
        seq=timeline()
        with self.assertRaises(ValueError):
            mix_soundscape(b"\x00",seq)
        with self.assertRaises(ValueError):
            mix_soundscape(b"\x00\x00",seq)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                render_soundscape(Path(temp)/"not-wav.mp3",b"",seq)
        for bad in (math.nan,math.inf,-1.,7.3,True):
            with self.subTest(t=bad),self.assertRaises(ValueError):
                source_to_video(bad,seq)


if __name__=="__main__":
    unittest.main()
