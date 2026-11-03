"""Dynamic magma reservoir, pressure and rising conduit visuals."""
import unittest
from PIL import Image,ImageChops

from automate_ytb.science_volcano_magma import (
    VERSION,SIZE,LOW,BEATS,_chamber_mask,_conduit_mask,draw_magma
)
from automate_ytb.science_volcano import _base

class DynamicMagmaTests(unittest.TestCase):
    def test_mask_cache_and_geometry(self):
        self.assertIn("convective",VERSION)
        self.assertEqual(SIZE,(1080,1380))
        self.assertEqual(LOW,(270,345))
        self.assertEqual(BEATS,("magma","pressure","ascent"))
        self.assertIs(_chamber_mask(),_chamber_mask())
        self.assertIs(_conduit_mask(),_conduit_mask())
        self.assertEqual(_chamber_mask().getpixel((542,1120)),255)
        self.assertEqual(_chamber_mask().getpixel((50,400)),0)
        self.assertEqual(_conduit_mask().getpixel((542,690)),255)
        self.assertEqual(_conduit_mask().getpixel((400,690)),0)

    def test_each_beat_changes_continuously_and_is_repeatable(self):
        for beat in BEATS:
            with self.subTest(beat=beat):
                first=_base(True).copy()
                second=_base(True).copy()
                repeat=_base(True).copy()
                draw_magma(first,beat,.5,6.8)
                draw_magma(second,beat,3.1,6.8)
                draw_magma(repeat,beat,.5,6.8)
                self.assertEqual(first.tobytes(),repeat.tobytes())
                self.assertIsNotNone(ImageChops.difference(
                    first.convert("RGB"),second.convert("RGB")).getbbox())
                self.assertEqual(first.getpixel((50,350)),
                                 second.getpixel((50,350)))

    def test_rising_conduit_front_progresses_up_and_no_rock_leak(self):
        a=_base(True).copy()
        b=_base(True).copy()
        draw_magma(a,"ascent",1.1,6.8)
        draw_magma(b,"ascent",5.4,6.8)
        self.assertNotEqual(a.getpixel((540,660)),b.getpixel((540,660)))
        self.assertEqual(a.getpixel((30,60)),b.getpixel((30,60)))

    def test_rejects_invalid_clock_and_stage(self):
        for beat,t,dur in (
            ("missing",1,6),(BEATS[0],-1,6),
            (BEATS[0],7,6),(BEATS[0],1,0),
            (BEATS[0],float("nan"),6),
            (BEATS[0],1,float("inf"))
        ):
            with self.assertRaises(ValueError):
                draw_magma(Image.new("RGBA",SIZE),beat,t,dur)
        for im in (Image.new("RGB",SIZE),
                   Image.new("RGBA",(270,345))):
            with self.assertRaises(ValueError):
                draw_magma(im,"magma",1,6)
