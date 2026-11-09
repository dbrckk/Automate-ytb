"""P4.6 original mesh-deformed canopy and understory regression checks."""
import math
import unittest

from PIL import ImageChops

from automate_ytb.forest_canopy_wind25d import (
    VERSION, SIZE, WINDOWS, ROOT_Y, wind_offset, living_canopy,
)
from automate_ytb.forest_cinematic_world25d import plates
from automate_ytb.forest25d import frame


class LivingCanopyTests(unittest.TestCase):
    def test_both_original_plates_move_at_real_frame_rate(self):
        self.assertIn("p46",VERSION)
        for layer in WINDOWS:
            with self.subTest(layer=layer):
                before=living_canopy(.7,layer=layer)
                after=living_canopy(.7+1/30,layer=layer)
                self.assertEqual(before.size,SIZE)
                self.assertEqual(before.mode,"RGBA")
                self.assertIsNotNone(before.getbbox())
                self.assertIsNotNone(ImageChops.difference(
                    before.convert("RGB"),after.convert("RGB")).getbbox())
                self.assertEqual(before.tobytes(),
                                 living_canopy(.7,layer=layer).tobytes())

    def test_wind_root_is_anchored_but_upper_crown_flexes(self):
        for layer in WINDOWS:
            with self.subTest(layer=layer):
                root=ROOT_Y[layer]
                for t in (0.,.4,2.7,7.2):
                    self.assertEqual(wind_offset(t,470.,root,layer=layer),0.)
                    self.assertEqual(wind_offset(t,470.,root+12,layer=layer),0.)
                top=WINDOWS[layer][0]+70
                self.assertGreater(abs(wind_offset(.7,470.,top,layer=layer)),1.0)
                self.assertNotEqual(wind_offset(.7,100.,top,layer=layer),
                                    wind_offset(.7,850.,top,layer=layer))
                self.assertLessEqual(abs(wind_offset(.7,470.,top,layer=layer)),26.)

    def test_heavy_authoring_plates_are_cached_and_not_edited(self):
        authored=plates()
        tree_pixels=authored["trees"].tobytes()
        understory_pixels=authored["understory"].tobytes()
        for layer in WINDOWS:
            _=living_canopy(1.,layer=layer)
            _=living_canopy(4.5,layer=layer)
            top,bottom=WINDOWS[layer]
            image=living_canopy(4.5,layer=layer)
            self.assertIsNone(image.crop((0,0,1080,top)).getbbox())
            self.assertIsNone(image.crop((0,bottom,1080,1920)).getbbox())
        self.assertIs(plates(),authored)
        self.assertEqual(tree_pixels,authored["trees"].tobytes())
        self.assertEqual(understory_pixels,authored["understory"].tobytes())

    def test_existing_story_rig_and_optical_framing_remain_valid(self):
        image=frame(2.42,kind="fox",interaction=True,
                    story=True,show_story_titles=False)
        self.assertEqual(image.mode,"RGB")
        self.assertEqual(image.size,SIZE)
        self.assertNotEqual(image.getpixel((50,50)),
                            image.getpixel((900,1410)))

    def test_rejects_invalid_clocks_positions_and_layer_names(self):
        for bad in (math.nan,math.inf,-1.,7.3,True):
            with self.assertRaises(ValueError):
                living_canopy(bad,layer="trees")
        for bad in (math.nan,math.inf,-5.,1081.,True):
            with self.assertRaises(ValueError):
                wind_offset(2.,bad,900.,layer="trees")
        for bad in (math.nan,-5.,1921.,True):
            with self.assertRaises(ValueError):
                wind_offset(2.,500.,bad,layer="trees")
        with self.assertRaises(ValueError):
            living_canopy(2.,layer="untrusted")
        with self.assertRaises(ValueError):
            wind_offset(1.,500.,900.,layer="untrusted")


if __name__=="__main__":
    unittest.main()
