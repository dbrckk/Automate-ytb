"""Rounded procedural EVA model contract and pixel-level regressions."""
from __future__ import annotations

import math
import unittest
from PIL import Image, ImageChops, ImageDraw

from automate_ytb.science_astronaut3d import (
    draw_astronaut3d, camera_pose, astronaut_pose,
)
from automate_ytb.science_eva_shapes import (
    torso_rings, rounded_boot_vertices, render_torso, render_boot,
)


class RoundedEVAQualityTests(unittest.TestCase):
    def setUp(self):
        self.blank=Image.new("RGBA",(1080,1920),(8,22,44,255))

    def test_torso_cross_sections_are_continuous_and_tapered(self):
        center=(.2,1.95,3.8)
        rings=torso_rings(center)
        self.assertEqual(len(rings),8)
        self.assertTrue(all(len(r)==21 for r in rings))
        for ring in rings:
            self.assertAlmostEqual(ring[0][0],ring[-1][0],places=6)
            self.assertAlmostEqual(ring[0][2],ring[-1][2],places=6)
            self.assertTrue(all(math.isfinite(c) for vertex in ring for c in vertex))
        width=lambda ring:max(p[0] for p in ring)-min(p[0] for p in ring)
        self.assertLess(width(rings[0]),width(rings[4]))
        self.assertLess(width(rings[-1]),width(rings[4]))
        self.assertGreater(width(rings[4]),.95)

    def test_boot_has_rounded_three_dimensional_toe_and_sole(self):
        rings=rounded_boot_vertices((.5,.1,3.6),(.27,.19,.39))
        self.assertEqual(len(rings),10)
        self.assertTrue(all(len(r)==17 for r in rings))
        samples={tuple(round(v,5) for v in p) for row in rings for p in row}
        self.assertGreater(len(samples),90)
        self.assertTrue(any(z<3.28 for _,_,z in samples))
        self.assertTrue(any(z>3.90 for _,_,z in samples))
        self.assertGreater(len({round(y,4) for x,y,z in samples}),6)

    def test_soft_armor_is_projected_and_animated_without_title_damage(self):
        cam=camera_pose(1.3,6)
        pose=astronaut_pose(1.3,6)
        layer=Image.new("RGBA",(1080,885))
        draw=ImageDraw.Draw(layer,"RGBA")
        render_torso(draw,cam,pose["torso"])
        render_boot(draw,cam,pose["foot_l"])
        self.assertIsNotNone(layer.getbbox())
        self.assertGreater(len(layer.getcolors(1080*885) or []),18)
        a,b,c=self.blank.copy(),self.blank.copy(),self.blank.copy()
        draw_astronaut3d(a,.25,6)
        draw_astronaut3d(b,4.8,6)
        draw_astronaut3d(c,.25,6)
        self.assertEqual(a.tobytes(),c.tobytes())
        self.assertEqual(a.getchannel("A").getextrema(),(255,255))
        for box in ((0,0,1080,570),(0,1455,1080,1920)):
            self.assertEqual(a.crop(box).tobytes(),self.blank.crop(box).tobytes())
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB"),b.convert("RGB")).getbbox())

    def test_invalid_geometry_is_rejected(self):
        for center in ((0.,float("nan"),3.),(0.,1.),(0.,0.,float("inf"))):
            with self.subTest(center=center),self.assertRaises(ValueError):
                torso_rings(center)
        for extent in ((0.,.2,.2),(.2,-.1,.2),(.2,.2,float("nan"))):
            with self.subTest(extent=extent),self.assertRaises(ValueError):
                rounded_boot_vertices((0.,.1,3.),extent)
        with self.assertRaises(ValueError):
            rounded_boot_vertices((0.,.1,3.),(.3,.2,.3),lat=2)
        with self.assertRaises(ValueError):
            rounded_boot_vertices((0.,.1,3.),(.3,.2,.3),lon=5)


if __name__=="__main__":
    unittest.main()
