"""Physical event-directed story timings and backward-compatibility."""
import math
import unittest
from PIL import ImageChops

from automate_ytb.forest_story25d import STORY, story_shot, story_overlay
from automate_ytb.forest_contact25d import IMPACT_TIME
from automate_ytb.forest25d import frame


class Story25DTests(unittest.TestCase):
    def test_four_contiguous_physical_beats(self):
        self.assertEqual(len(STORY),4)
        self.assertEqual(STORY[0][1],0.)
        self.assertEqual(STORY[1][1],IMPACT_TIME)
        self.assertEqual(STORY[-1][2],7.2)
        for previous,next_ in zip(STORY,STORY[1:]):
            self.assertEqual(previous[2],next_[1])
        for t,name in ((0.,"discovery"),(IMPACT_TIME,"contact"),
                       (IMPACT_TIME+.7,"arrival"),(7.2,"departure")):
            self.assertEqual(story_shot(t).beat,name)

    def test_shot_camera_is_bounded_and_stationary_at_cuts(self):
        for name,start,end,*_ in STORY:
            with self.subTest(beat=name):
                for t in (start,end):
                    p=story_shot(t if t<7.2 else 7.2)
                    self.assertAlmostEqual(p.camera_x,0.,places=5)
                    self.assertAlmostEqual(p.camera_y,0.,places=5)
                mid=story_shot((start+end)/2)
                self.assertLessEqual(abs(mid.camera_x),34.)
                self.assertLessEqual(abs(mid.camera_y),12.)

    def test_title_overlay_is_real_transparent_rgba(self):
        t=(STORY[0][1]+STORY[0][2])/2
        overlay=story_overlay(t)
        self.assertEqual(overlay.mode,"RGBA")
        self.assertEqual(overlay.size,(1080,1920))
        self.assertIsNotNone(overlay.getbbox())
        self.assertEqual(overlay.getpixel((0,0))[3],0)

    def test_real_story_frames_change_and_require_interaction(self):
        a=frame(IMPACT_TIME+.4,kind="fox",interaction=True,story=True)
        b=frame(IMPACT_TIME+.7,kind="fox",interaction=True,story=True)
        self.assertEqual(a.size,(1080,1920))
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
        with self.assertRaises(ValueError):
            frame(1.,story=True)

    def test_invalid_clocks(self):
        for t in (-.1,7.21,math.nan,math.inf,True):
            with self.subTest(t=t),self.assertRaises(ValueError):
                story_shot(t)


if __name__=="__main__":
    unittest.main()
