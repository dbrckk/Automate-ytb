"""P5.2 visual contracts for original, textured 2.5D thunderstorm assets."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw, ImageStat

from automate_ytb.science_lightning_art import (
    ART_VERSION, detailed_cloud_volume, paint_industrial_detail,
)
from automate_ytb.science_lightning_fx import (
    SIZE, cloud_volume, environment_plates, paint_terrain,
)


class StormMaterialTests(unittest.TestCase):
    def test_clouds_have_lit_internal_material_not_flat_blurred_ellipses(self):
        self.assertIn("p52", ART_VERSION)
        for depth in range(3):
            for variant in range(3):
                with self.subTest(depth=depth, variant=variant):
                    cloud = detailed_cloud_volume(depth, variant)
                    self.assertIs(cloud, detailed_cloud_volume(depth, variant))
                    self.assertIs(cloud, cloud_volume(depth, variant))
                    self.assertEqual(cloud.mode, "RGBA")
                    alpha = cloud.getchannel("A")
                    self.assertGreater(alpha.getextrema()[1], 80)
                    # No rectangular sprite seams at any exterior edge.
                    w,h = cloud.size
                    self.assertEqual(alpha.getpixel((0,h//2)),0)
                    self.assertEqual(alpha.getpixel((w-1,h//2)),0)
                    self.assertEqual(alpha.getpixel((w//2,0)),0)
                    self.assertEqual(alpha.getpixel((w//2,h-1)),0)
                    interior = cloud.crop((w//4,h//4,w*3//4,h*3//4))
                    # Colors, structure and alpha vary within a single
                    # billow: not a monochromatic flat polygon.
                    self.assertGreater(ImageStat.Stat(
                        interior.getchannel("R")).stddev[0], 12)
                    self.assertGreater(ImageStat.Stat(
                        interior.getchannel("A")).stddev[0], 12)

    def test_cloud_depth_is_visually_separable_and_deterministic(self):
        clouds = [detailed_cloud_volume(d,0) for d in range(3)]
        self.assertEqual(len({c.size for c in clouds}), 3)
        for cloud in clouds:
            self.assertIsNotNone(cloud.getbbox())
        a = environment_plates(1.2,"leader",6.)
        b = environment_plates(1.2,"leader",6.)
        self.assertEqual(tuple(x[0] for x in a),tuple(x[0] for x in b))
        for (_,image),(_,repeat) in zip(a,b):
            self.assertEqual(image.tobytes(),repeat.tobytes())

    def test_mast_beacon_and_lattice_replace_plain_wireframe(self):
        plate = Image.new("RGBA",SIZE)
        draw = ImageDraw.Draw(plate,"RGBA")
        paint_industrial_detail(draw,1.0)
        r,g,b,a = plate.getpixel((700,694))
        self.assertGreater(r,g)
        self.assertGreater(a,0)
        # Thousands of shaded samples, lit windows and steel cross-braces.
        tower = plate.crop((650,685,755,815))
        self.assertGreater(ImageStat.Stat(tower.getchannel("R")).stddev[0],25)
        self.assertGreater(len(tower.getcolors(maxcolors=10000) or []),50)
        again=Image.new("RGBA",SIZE)
        paint_industrial_detail(ImageDraw.Draw(again,"RGBA"),1.0)
        self.assertEqual(again.tobytes(),plate.tobytes())
        later=Image.new("RGBA",SIZE)
        paint_industrial_detail(ImageDraw.Draw(later,"RGBA"),2.3)
        self.assertIsNotNone(ImageChops.difference(
            plate,later).getbbox())

    def test_existing_terrain_camera_and_lightning_contact_preserved(self):
        from automate_ytb.science_lightning import TOWER_TOP
        self.assertEqual(TOWER_TOP,(700,695))
        plate=Image.new("RGBA",SIZE)
        paint_terrain(ImageDraw.Draw(plate,"RGBA"),1.)
        self.assertGreater(plate.getpixel((700,694))[0],
                           plate.getpixel((700,694))[1])
        self.assertGreater(plate.getpixel((700,790))[3],0)
        for invalid in (float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                paint_industrial_detail(ImageDraw.Draw(plate),invalid)
        with self.assertRaises(ValueError):
            detailed_cloud_volume(9,0)


if __name__ == "__main__":
    unittest.main()
