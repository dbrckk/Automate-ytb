"""Reusable source material must improve actual volcano art, not fake scores."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw, ImageStat

from automate_ytb.rock_surface25d import (
    VERSION,weathered_rock,
)
from automate_ytb.science_volcano import _base,draw_volcano,SIZE
from automate_ytb.science_volcano_mesh import shaded_terrain
from automate_ytb.science_portrait import PortraitScienceScene


class OriginalRockSurface25DTests(unittest.TestCase):
    def test_rock_source_preserves_original_opacity_and_spatial_illumination(self):
        plate=Image.new("RGBA",(400,300))
        d=ImageDraw.Draw(plate)
        d.polygon([(200,20),(75,250),(330,250)],fill=(116,98,94,255))
        raw=plate.tobytes()
        rock=weathered_rock(plate,seed=45)
        self.assertIsNot(rock,plate)
        self.assertEqual(plate.tobytes(),raw)
        self.assertEqual(rock.getchannel("A").tobytes(),
                         plate.getchannel("A").tobytes())
        self.assertEqual(rock.getpixel((0,0))[3],0)
        self.assertNotEqual(rock.tobytes(),raw)
        self.assertEqual(rock.tobytes(),weathered_rock(plate,seed=45).tobytes())
        self.assertNotEqual(rock.tobytes(),weathered_rock(plate,seed=46).tobytes())
        self.assertTrue(VERSION.endswith("p515-v1"))

    def test_volcanic_production_mesh_keeps_real_alpha_and_new_rock_detail(self):
        material=shaded_terrain()
        self.assertIs(shaded_terrain(),material)
        self.assertEqual(material.size,SIZE)
        self.assertEqual(material.getpixel((2,200))[3],0)
        self.assertEqual(material.getpixel((540,1180))[3],0)
        self.assertGreater(material.getpixel((540,620))[3],100)
        self.assertGreater(len({
            material.getpixel((x,y))[:3] for x in range(380,701,17)
            for y in range(580,850,19)
            if material.getpixel((x,y))[3] > 0}),70)

    def test_volcano_source_sky_no_longer_has_spaced_star_like_dots(self):
        base=_base(True)
        self.assertEqual(base.mode,"RGBA")
        self.assertEqual(base.size,SIZE)
        for x,y in ((20,80),(251,100),(762,90),(1000,170)):
            red,green,blue,alpha=base.getpixel((x,y))
            self.assertLess(red,100)
            self.assertLess(green,140)
            self.assertLess(blue,160)
            self.assertEqual(alpha,255)
        self.assertEqual(base.tobytes(),_base(True).tobytes())

    def test_actual_native_volcano_scenes_preserve_9_16_motion(self):
        scene=PortraitScienceScene(
            topic="How do volcanoes erupt?",
            narration="Gas pressure grows inside the magma chamber beneath the summit.",
            scene_index=2)
        a=scene.frame(.45,6.8)
        b=scene.frame(2.9,6.8)
        self.assertEqual(a.size,(1080,1920))
        self.assertEqual(a.mode,"RGB")
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.tobytes(),scene.frame(.45,6.8).tobytes())

    def test_invalid_shapes_seeds_fail_closed(self):
        for sample in (Image.new("RGB",(400,300)),
                       Image.new("RGBA",(40,90))):
            with self.assertRaises(ValueError):
                weathered_rock(sample)
        for seed in (-1,False,1_000_001,math.nan):
            with self.assertRaises(ValueError):
                weathered_rock(Image.new("RGBA",(400,300)),seed=seed)
        empty=Image.new("RGBA",(250,180))
        out=weathered_rock(empty)
        self.assertEqual(out.tobytes(),empty.tobytes())


if __name__=="__main__":
    unittest.main()
