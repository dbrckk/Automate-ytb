"""P4.7 continuous animated editorial cuts and sharp mobile typography."""
import math
import unittest

from PIL import Image, ImageDraw

from automate_ytb.forest_voice_timeline import (
    TimedBeat, ENGLISH_SCRIPT, measured_timeline,
)
from automate_ytb.forest_editorial_lens25d import (
    VERSION, DURATION, focus_radius, editorial_focus,
)


def story_timeline():
    beats=[dict(index=i+1,text=text,startMs=170+i*3170,
                endMs=3170+i*3170) for i,text in enumerate(ENGLISH_SCRIPT)]
    return measured_timeline(dict(engine="kokoro-natural",language="en",
                                  durationSeconds=13,beats=beats))


class EditorialLensTests(unittest.TestCase):
    def test_measured_cuts_get_short_focus_pull_not_static_dissolve(self):
        seq=story_timeline()
        self.assertIn("p47",VERSION)
        self.assertEqual(focus_radius(seq.beats[0].start,seq.beats[0]),0.)
        for beat in seq.beats[1:]:
            self.assertGreater(focus_radius(beat.start,beat),1.)
            self.assertGreater(focus_radius(beat.start+.04,beat),0.)
            self.assertEqual(focus_radius(beat.start+DURATION,beat),0.)
            self.assertEqual(focus_radius(beat.end,beat),0.)

    def test_full_hd_image_blurs_briefly_then_restores_unmodified_art(self):
        beat=story_timeline().beats[1]
        original=Image.new("RGB",(1080,1920),(15,35,55))
        ImageDraw.Draw(original).rectangle((240,300,360,420),
                                            fill=(250,250,210))
        entry=editorial_focus(original,t=beat.start,beat=beat)
        recovered=editorial_focus(original,t=beat.start+DURATION,beat=beat)
        self.assertEqual(entry.size,original.size)
        self.assertNotEqual(entry.tobytes(),original.tobytes())
        self.assertEqual(recovered.tobytes(),original.tobytes())
        self.assertEqual(original.getpixel((240,300)),(250,250,210))

    def test_final_035s_voice_paced_tail_stays_sharp(self):
        seq=story_timeline()
        last=seq.beats[-1]
        self.assertAlmostEqual(seq.duration-last.end,.35,places=5)
        for t in (last.end,last.end+.02,seq.duration):
            self.assertEqual(focus_radius(t,last),0.)
        picture=Image.new("RGB",(1080,1920),(30,60,90))
        self.assertEqual(editorial_focus(picture,t=seq.duration,beat=last).tobytes(),
                         picture.tobytes())

    def test_bad_timestamps_and_non_rbg_frames_rejected(self):
        beat=story_timeline().beats[1]
        image=Image.new("RGB",(1080,1920))
        for bad in (math.nan,math.inf,-1.,beat.end+1,True):
            with self.assertRaises(ValueError):
                focus_radius(bad,beat)
        for img in (Image.new("RGBA",(1080,1920)),Image.new("RGB",(540,960))):
            with self.assertRaises(ValueError):
                editorial_focus(img,t=beat.start,beat=beat)
        with self.assertRaises(ValueError):
            focus_radius(beat.start,None)


if __name__=="__main__":
    unittest.main()
