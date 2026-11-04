"""Ash changes the source geometry lighting and moves on its own timeline."""
import unittest

from PIL import Image, ImageChops

from automate_ytb.science_volcano_atmosphere import (
    VERSION, SIZE, LOW, ORIGIN, cast_plume_shadow, draw_windborne_ash,
)
from automate_ytb.science_volcano import _base, _explosion


class VolcanicAtmosphereTests(unittest.TestCase):
    def test_terrain_receives_ash_but_sky_and_ui_do_not(self):
        self.assertIn("rock-shadow", VERSION)
        self.assertEqual((SIZE, LOW, ORIGIN),
                         ((1080,1380), (270,345), (540,345)))
        baseline = _base(False).copy()
        early = baseline.copy()
        late = baseline.copy()
        cast_plume_shadow(early, 0., 6.8)
        cast_plume_shadow(late, 4.1, 6.8)
        self.assertEqual(early.tobytes(), baseline.tobytes())
        self.assertEqual(late.getpixel((40, 50)), baseline.getpixel((40, 50)))
        self.assertEqual(late.getpixel((60,1250)), baseline.getpixel((60,1250)))
        self.assertIsNotNone(ImageChops.difference(
            late.crop((480,450,830,1000)).convert("RGB"),
            baseline.crop((480,450,830,1000)).convert("RGB")).getbbox())
        repeated = baseline.copy()
        cast_plume_shadow(repeated, 4.1, 6.8)
        self.assertEqual(late.tobytes(), repeated.tobytes())

    def test_ash_veil_has_independent_motion_and_no_blank_frame(self):
        base = Image.new("RGBA", SIZE, (15,25,42,255))
        early = base.copy()
        after = base.copy()
        draw_windborne_ash(early, .8, 6.8)
        draw_windborne_ash(after, 2.2, 6.8)
        self.assertNotEqual(early.tobytes(), after.tobytes())
        self.assertEqual(after.getchannel("A").getextrema(), (255,255))
        self.assertEqual(after.getpixel((0,1300)), base.getpixel((0,1300)))

    def test_composited_eruption_preserves_full_frame(self):
        stage = _base(False).copy()
        _explosion(stage, 3.1, 6.8)
        self.assertEqual(stage.size, SIZE)
        self.assertEqual(stage.getchannel("A").getextrema(), (255,255))

    def test_invalid_stages_and_clocks_fail_explicitly(self):
        for t,duration in ((-1,6), (7,6), (1,0),
                           (float("nan"),6), (1,float("inf"))):
            with self.assertRaises(ValueError):
                cast_plume_shadow(Image.new("RGBA", SIZE), t, duration)
            with self.assertRaises(ValueError):
                draw_windborne_ash(Image.new("RGBA", SIZE), t, duration)
        with self.assertRaises(ValueError):
            cast_plume_shadow(Image.new("RGB",SIZE),1.,6.)
        with self.assertRaises(ValueError):
            draw_windborne_ash(Image.new("RGBA",(800,800)),1.,6.)
