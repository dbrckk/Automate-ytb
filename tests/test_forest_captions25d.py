"""Captions are tied to measured Kokoro speech and safe on mobile."""
import unittest
from automate_ytb.forest_captions25d import caption_plate,caption_chunks,VERSION
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

    def test_compact_phrases_without_full_width_black_background(self):
        beat=self.timeline.beats[0]
        chunks=caption_chunks(beat.narration)
        self.assertGreaterEqual(len(chunks),2)
        self.assertIn("p40",VERSION)
        first=caption_plate(beat.speech_start+
                            .30*(beat.speech_end-beat.speech_start),self.timeline)
        # Old subtitles filled a 940px-wide opaque rectangle at this row.
        # New lettering cannot fill the empty side margins or entire width.
        self.assertEqual(first.getpixel((80,1438))[3],0)
        self.assertEqual(first.getpixel((1000,1438))[3],0)
        self.assertEqual(first.getpixel((540,1550))[3],0)

    def test_measured_caption_chunks_change_within_a_beat(self):
        beat=self.timeline.beats[0]
        duration=beat.speech_end-beat.speech_start
        a=caption_plate(beat.speech_start+.2*duration,self.timeline)
        b=caption_plate(beat.speech_start+.8*duration,self.timeline)
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_rejects_missing_pcm_timeline(self):
        with self.assertRaises(ValueError):
            caption_plate(1.,None)


if __name__=="__main__":
    unittest.main()
