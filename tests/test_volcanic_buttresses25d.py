"""Actual 2.5D volcanic mountains need rock geometry, not rigid pyramids."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageChops

from automate_ytb.science_volcano_mesh import (
    SIZE,TERRAIN_VERSION,CONE_OUTLINE,RINGS,SEGMENTS,
    height_at,shaded_terrain,eroded_silhouette,
)
from automate_ytb.science_volcano import _base
from automate_ytb.science_portrait import PortraitScienceScene


class OriginalErodedVolcanicReliefTests(unittest.TestCase):
    def test_evolving_hillside_has_micro_shoulder_geometry_not_triangle(self):
        self.assertTrue(TERRAIN_VERSION.endswith("terraced-flanks"))
        self.assertEqual(CONE_OUTLINE[-2:],((1080,1380),(0,1380)))
        outline=eroded_silhouette()
        self.assertEqual(CONE_OUTLINE[:-2],outline)
        self.assertGreater(len(outline),130)
        self.assertEqual(outline[0],(0,1032))
        self.assertEqual(outline[-1],(1080,1008))
        self.assertIn((529,343),outline)
        self.assertIn((549,336),outline)
        self.assertEqual(tuple(sorted(x for x,y in outline)),
                         tuple(x for x,y in outline))
        self.assertGreaterEqual(SEGMENTS,96)

    def test_radial_buttresses_create_distinct_rock_strata_and_actual_relief(self):
        radii=(140,260,370,460)
        for radius in radii:
            heights=[height_at(radius,k*.28) for k in range(18)]
            with self.subTest(radius=radius):
                self.assertGreater(max(heights)-min(heights),18)
        self.assertGreater(height_at(65,0),height_at(0,0)+70)
        self.assertEqual(height_at(520,0),0.)
        self.assertGreater(height_at(140,0),height_at(350,0))

    def test_original_terrain_reuses_same_mask_cutaway_and_exterior(self):
        material=shaded_terrain()
        self.assertIs(material,shaded_terrain())
        self.assertEqual(material.size,SIZE)
        self.assertEqual(material.mode,"RGBA")
        self.assertEqual(material.getpixel((0,120))[3],0)
        self.assertGreater(material.getpixel((540,620))[3],100)
        self.assertEqual(material.getpixel((540,1180))[3],0)
        outside=_base(False)
        section=_base(True)
        self.assertEqual(outside.size,SIZE)
        self.assertEqual(section.size,SIZE)
        self.assertNotEqual(outside.tobytes(),section.tobytes())

    def test_real_1080x1920_mountain_eruption_and_lava_remain_animated(self):
        topics=(
            "Ash and glowing fragments erupt from the volcanic crater.",
            "Molten lava flows down the volcanic slopes and slowly cools.",
        )
        for phrase in topics:
            with self.subTest(phrase=phrase):
                scene=PortraitScienceScene(
                    topic="How do volcanoes erupt?",
                    narration=phrase,scene_index=3)
                a=scene.frame(1.1,6.8)
                b=scene.frame(2.9,6.8)
                self.assertEqual(a.mode,"RGB")
                self.assertEqual(a.size,(1080,1920))
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),scene.frame(1.1,6.8).tobytes())


if __name__=="__main__":
    unittest.main()
