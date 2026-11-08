"""Captions are tied to measured Kokoro speech and safe on mobile."""
import unittest
from automate_ytb.forest_captions25d import caption_plate
from automate_ytb.forest_voice_timeline import ENGLISH_SCRIPT,measured_timeline


class CaptionTests(unittest.TestCase):
    def setUp(self):
        beats=[]
        for i,text in enumerate(ENGLISH_SCRIPT):
            start=170+i*3170
            beats.append(dict(index=i+1,text=text,startMs=start,endMs=start+3000))
        self.timeline=measured_timeline(dict(engine="kokoro-natural",
            language="en",durationSeconds=13.,beats=beats))

    def test_no_subtitles_before_or_after_measured_speech(self):
        beat=self.timeline.beats[0]
        self.assertIsNone(caption_plate(0.,self.timeline).getbbox())
        self.assertIsNone(caption_plate(beat.speech_end+.02,self.timeline).getbbox())

    def test_caption_visible_only_in_mobile_safe_region(self):
        beat=self.timeline.beats[0]
        plate=caption_plate((beat.speech_start+beat.speech_end)/2,self.timeline)
        self.assertEqual(plate.size,(1080,1920))
        bbox=plate.getbbox()
        self.assertIsNotNone(bbox)
        self.assertGreater(bbox[1],1100)
        self.assertLess(bbox[3],1600)
        self.assertEqual(plate.getpixel((0,0))[3],0)

    def test_rejects_missing_pcm_timeline(self):
        with self.assertRaises(ValueError):
            caption_plate(1.,None)


if __name__=="__main__":
    unittest.main()
