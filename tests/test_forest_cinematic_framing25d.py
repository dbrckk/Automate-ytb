"""Physical cinematic crops are real resamplings, not fake zoom metadata."""
import math
import unittest
from PIL import Image,ImageChops

from automate_ytb.forest_cinematic_framing25d import (
    SHOTS,SIZE,shot_crop,cinematic_reframe,
)


class PhysicalCinematicFramingTests(unittest.TestCase):
    def test_every_shot_is_bounded_and_changes_optical_scale(self):
        sizes={}
        for name in SHOTS:
            x0,y0,x1,y1=shot_crop(2.5,beat=name,body_x=310.)
            self.assertGreaterEqual(x0,0)
            self.assertGreaterEqual(y0,0)
            self.assertLessEqual(x1,SIZE[0])
            self.assertLessEqual(y1,SIZE[1])
            self.assertLess(x1-x0,SIZE[0])
            sizes[name]=(x1-x0,y1-y0)
        self.assertGreater(sizes["discovery"][0],sizes["contact"][0])
        self.assertGreater(sizes["departure"][0],sizes["arrival"][0])

    def test_crops_track_real_actor_world_position(self):
        a=shot_crop(1.,beat="arrival",body_x=200.)
        b=shot_crop(5.,beat="arrival",body_x=500.)
        self.assertGreater(b[0],a[0])

    def test_optical_reframing_produces_real_pixels(self):
        im=Image.new("RGBA",SIZE,(25,75,110,255))
        for y in range(560,1360):
            for x in range(300,600):
                im.putpixel((x,y),(245,174,92,255))
        wide=cinematic_reframe(im,t=2.,beat="discovery",body_x=300.)
        close=cinematic_reframe(im,t=2.,beat="contact",body_x=300.)
        self.assertEqual(wide.size,SIZE)
        self.assertIsNotNone(ImageChops.difference(wide.convert("RGB"),close.convert("RGB")).getbbox())

    def test_rejects_unbounded_clocks_subjects_and_fake_stages(self):
        for t in (math.nan,-1,8,True):
            with self.subTest(t=t),self.assertRaises(ValueError):
                shot_crop(t,beat="contact",body_x=300.)
        for x in (0,700,math.inf):
            with self.assertRaises(ValueError):
                shot_crop(2.,beat="contact",body_x=x)
        with self.assertRaises(ValueError):
            cinematic_reframe(Image.new("RGB",SIZE),t=2.,
                              beat="contact",body_x=300.)


if __name__=="__main__":
    unittest.main()
