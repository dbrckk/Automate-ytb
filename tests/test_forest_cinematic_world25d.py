"""Genuine P3.6 cinematic forest plate, motion and integration regression tests."""
import math
import unittest

from PIL import ImageChops

from automate_ytb.forest_cinematic_world25d import (
    VERSION, SIZE, plates, drifting_clouds, living_light,
)
from automate_ytb.forest25d import frame


class CinematicForestTests(unittest.TestCase):
    def test_original_cinematic_depth_plates_cached_and_visible(self):
        layers=plates()
        self.assertEqual(tuple(layers),(
            "sky","clouds","ridges","sunbeams","trees",
            "understory","meadow","foreground","grade"))
        self.assertIs(layers,plates())
        self.assertEqual(len(layers),9)
        self.assertEqual(layers["sky"].getpixel((0,0))[3],255)
        for name,layer in layers.items():
            with self.subTest(layer=name):
                self.assertEqual(layer.size,SIZE)
                self.assertEqual(layer.mode,"RGBA")
                self.assertIsNotNone(layer.getbbox())
        self.assertNotEqual(layers["sky"].getpixel((70,100)),
                            layers["sky"].getpixel((70,1050)))
        self.assertIn("p36",VERSION)

    def test_real_drifts_and_light_particles_change_between_frames(self):
        a=drifting_clouds(0.0)
        b=drifting_clouds(4.0)
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
        a=living_light(.2)
        b=living_light(1.2)
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
        self.assertIsNone(living_light(.2).getpixel((0,0))[3] or None)

    def test_new_painted_world_preserves_causal_contact_frame(self):
        shot=frame(2.43,kind="fox",interaction=True,story=True)
        self.assertEqual(shot.mode,"RGB")
        self.assertEqual(shot.size,SIZE)
        # sky and foliage are deliberately contrasting, not an opaque blank.
        self.assertNotEqual(shot.getpixel((50,50)),
                            shot.getpixel((1050,1490)))

    def test_lighting_rejects_nonfinite_and_out_of_bounds_clocks(self):
        for t in (math.nan,math.inf,-1.,7.3,True):
            with self.subTest(t=t):
                with self.assertRaises(ValueError):
                    drifting_clouds(t)
                with self.assertRaises(ValueError):
                    living_light(t)


if __name__=="__main__":
    unittest.main()
