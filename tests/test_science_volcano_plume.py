"""Real geometric smoke/ejecta checks, source position and safety."""
import unittest
from PIL import Image,ImageChops
from automate_ytb.science_volcano_plume import (
    VERSION,ORIGIN,SIZE,LOW,EMITTER_COUNT,_billow,draw_ash,draw_ejecta
)
from automate_ytb.science_volcano import _explosion

class VolcanicAshTests(unittest.TestCase):
    def test_palette_cached_and_original_ash_depth(self):
        self.assertIn("ballistic",VERSION)
        self.assertEqual(SIZE,(1080,1380))
        self.assertEqual(LOW,(270,345))
        self.assertEqual(ORIGIN,(540,345))
        self.assertGreaterEqual(EMITTER_COUNT,100)
        self.assertIs(_billow(13,2,4),_billow(13,2,4))
        self.assertEqual(_billow(13,2,4).mode,"RGBA")

    def test_volcano_plume_grows_and_does_not_tint_lower_sky(self):
        a=Image.new("RGBA",SIZE,(5,17,33,255))
        zero=a.copy()
        draw_ash(a,0,6.8)
        self.assertEqual(a.tobytes(),zero.tobytes())
        b=zero.copy()
        draw_ash(b,1.3,6.8)
        c=zero.copy()
        draw_ash(c,4.0,6.8)
        self.assertNotEqual(b.tobytes(),zero.tobytes())
        self.assertNotEqual(c.tobytes(),b.tobytes())
        self.assertEqual(b.getpixel((0,1250)),zero.getpixel((0,1250)))
        self.assertEqual(c.getpixel((1030,1350)),zero.getpixel((1030,1350)))
        same=zero.copy()
        draw_ash(same,4.0,6.8)
        self.assertEqual(c.tobytes(),same.tobytes())

    def test_particles_are_animated_in_crater_domain(self):
        first=Image.new("RGBA",SIZE,(3,10,17,255))
        later=first.copy()
        draw_ejecta(first,1.4,6.8)
        draw_ejecta(later,2.6,6.8)
        self.assertNotEqual(first.tobytes(),later.tobytes())
        self.assertEqual(first.getpixel((20,1300)),(3,10,17,255))
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"),later.convert("RGB")).getbbox())

    def test_real_erupting_summit_composites_plume_and_ejecta(self):
        from automate_ytb.science_volcano import _base
        frame=_base(False).copy()
        a=frame.copy()
        _explosion(a,1.8,6.8)
        self.assertNotEqual(a.crop((300,40,800,570)).tobytes(),
                            frame.crop((300,40,800,570)).tobytes())

    def test_invalid_clocks_and_stages_are_rejected(self):
        for bad in (-.1,7.0,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                draw_ash(Image.new("RGBA",SIZE),bad,6.8)
        for bad in (0.,-2.,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                draw_ejecta(Image.new("RGBA",SIZE),1,bad)
        with self.assertRaises(ValueError):
            draw_ash(Image.new("RGB",SIZE),1,6.8)
        with self.assertRaises(ValueError):
            draw_ejecta(Image.new("RGBA",(320,200)),1,6.8)
        for args in ((0,0,3),(30,0,3),(12,6,3),(12,1,6)):
            with self.assertRaises(ValueError):
                _billow(*args)
