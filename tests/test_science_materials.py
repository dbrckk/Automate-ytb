"""World-space EVA material and curved-visor render contract."""
from __future__ import annotations

import unittest
from PIL import Image, ImageChops

from automate_ytb.science_materials import (
    MATERIALS, Material, shade_surface,
)
from automate_ytb.science_astronaut3d import (
    astronaut_pose, camera_pose, draw_astronaut3d,
)


class ScienceMaterialTests(unittest.TestCase):
    def test_material_properties_are_distinct_and_grounded(self):
        self.assertEqual(set(MATERIALS),
                         {"fabric","ceramic","alloy","glass","solar","gold"})
        self.assertGreater(MATERIALS["fabric"].roughness,
                           MATERIALS["glass"].roughness)
        self.assertGreater(MATERIALS["gold"].metallic,
                           MATERIALS["fabric"].metallic)
        self.assertGreater(MATERIALS["glass"].coating,
                           MATERIALS["solar"].coating)
        for mat in MATERIALS.values():
            self.assertIsInstance(mat,Material)

    def test_roughness_metallic_fresnel_and_real_view_matter(self):
        base=(118,158,191)
        normal=(0.,.18,-.98)
        surface=(0.,0.,0.)
        eye=(0.,.3,-5.)
        a=shade_surface(base,normal,surface,eye,"fabric")
        b=shade_surface(base,normal,surface,eye,"glass")
        c=shade_surface(base,normal,surface,eye,"alloy")
        d=shade_surface(base,normal,surface,(4.,.3,-5.),"glass")
        self.assertNotEqual(a,b)
        self.assertNotEqual(a,c)
        self.assertNotEqual(b,d)
        for rgb in (a,b,c,d):
            self.assertEqual(len(rgb),4)
            self.assertEqual(rgb[-1],255)
            self.assertTrue(all(type(k) is int and 0<=k<=255 for k in rgb))
            self.assertEqual(
                rgb,shade_surface(base,normal,surface,eye,
                                  "fabric" if rgb==a else
                                  "alloy" if rgb==c else "glass")
                if rgb in (a,b,c) else d)

    def test_invalid_inputs_fail_closed(self):
        for v in (0.0, 1.01,float("nan")):
            with self.assertRaises(ValueError):
                Material(v,.2,.3,.1)
        for args in (
            ((20,30,40),(0.,0.,0.),(0.,0.,0.),(0.,0.,-4.),"fabric"),
            ((20,30,40),(0.,0.,-1.),(0.,0.,0.),(0.,0.,0.),"glass"),
            ((20,30,400),(0.,0.,-1.),(0.,0.,0.),(0.,0.,-4.),"glass"),
            ((20,30,40),(0.,0.,-1.),(0.,0.,0.),(0.,0.,-4.),"unknown"),
        ):
            with self.subTest(args=args),self.assertRaises(ValueError):
                shade_surface(*args)

    def test_shaded_astronaut_keeps_mobile_safe_areas_and_moves(self):
        blank=Image.new("RGBA",(1080,1920),(6,18,36,255))
        a,b,c=blank.copy(),blank.copy(),blank.copy()
        draw_astronaut3d(a,.2,6.)
        draw_astronaut3d(b,4.7,6.)
        draw_astronaut3d(c,.2,6.)
        self.assertEqual(a.tobytes(),c.tobytes())
        self.assertEqual(a.getchannel("A").getextrema(),(255,255))
        self.assertEqual(b.getchannel("A").getextrema(),(255,255))
        for region in ((0,0,1080,570),(0,1455,1080,1920)):
            self.assertEqual(a.crop(region).tobytes(),
                             blank.crop(region).tobytes())
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB"),b.convert("RGB")).getbbox())
        eye=camera_pose(1.,6.).eye
        self.assertNotEqual(eye,camera_pose(5.,6.).eye)
        self.assertIsNotNone(camera_pose(1.,6.).project(
            astronaut_pose(1.,6.)["head"]))


if __name__=="__main__":
    unittest.main()
