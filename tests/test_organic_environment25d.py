"""Prove reusable organic 2.5D assets and real cross-topic integrations.

Validate source-alpha safety, caching, deterministic art, physical contours,
visible shading, and compatibility with three production subject families.
"""
from __future__ import annotations

import hashlib
import unittest

from PIL import Image, ImageDraw, ImageStat

from automate_ytb.organic_environment25d import (
    VERSION,cloud_bank,drifting_cloud_bank,ridge_points,terrain_strata,water_caustics
)


class SharedOrganicEnvironmentTests(unittest.TestCase):
    def test_contour_is_multiscale_natural_and_deterministic(self):
        points=ridge_points(920,seed=109,horizon=.4,relief=.17)
        self.assertEqual(points,ridge_points(920,seed=109,horizon=.4,relief=.17))
        self.assertEqual(points[0][0],0)
        self.assertEqual(points[-1][0],919)
        self.assertGreater(len(points),100)
        slopes=[b[1]-a[1] for a,b in zip(points,points[1:])]
        # The returned ridge uses units of 1/10000 of stage height.
        # Quantizing the *increment* to 250 units hid actual smooth
        # variation: inspect many distinct gradients at native precision.
        self.assertGreater(len(set(slopes)),20)
        self.assertGreater(max(p[1] for p in points)-min(p[1] for p in points),200)
        self.assertTrue(any(v>0 for v in slopes))
        self.assertTrue(any(v<0 for v in slopes))

    def test_cloud_is_connected_coherent_and_not_a_flat_ellipse(self):
        cloud=cloud_bank((540,290),seed=97)
        self.assertEqual(cloud.mode,"RGBA")
        self.assertEqual(cloud.size,(540,290))
        self.assertIs(cloud,cloud_bank((540,290),seed=97))
        self.assertEqual(cloud.getpixel((100,0))[3],0)
        self.assertGreater(cloud.getchannel("A").getextrema()[1],35)
        self.assertGreater(ImageStat.Stat(cloud.convert("RGB")).stddev[0],5)
        contour=[]
        a=cloud.getchannel("A")
        for x in range(30,510,8):
            visible=next((y for y in range(20,275)
                          if a.getpixel((x,y))>20),275)
            contour.append(visible)
        self.assertGreater(max(contour)-min(contour),28)
        self.assertGreater(len(set(contour)),10)

    def test_erosion_and_water_are_distinct_mask_safe_materials(self):
        floor=terrain_strata((540,300),seed=100,color=(81,75,67))
        waves=water_caustics((540,300),seed=100)
        self.assertEqual(floor.getpixel((0,0))[3],0)
        self.assertGreater(floor.getpixel((270,285))[3],50)
        self.assertNotEqual(floor.tobytes(),waves.tobytes())
        self.assertGreater(waves.getchannel("A").getextrema()[1],6)
        self.assertEqual(
            hashlib.sha256(waves.tobytes()).hexdigest(),
            hashlib.sha256(water_caustics((540,300),seed=100).tobytes()).hexdigest())

    def test_input_validation_is_fail_closed(self):
        for size in ((0,320),(80,200),(1080,4000),(320.0,320)):
            with self.assertRaises(ValueError):
                cloud_bank(size,42)
        with self.assertRaises(ValueError):
            cloud_bank((540,290),-1)
        with self.assertRaises(ValueError):
            water_caustics((540,290),10,opacity=255)
        with self.assertRaises(ValueError):
            terrain_strata((540,290),10,color=(300,0,0))
        with self.assertRaises(ValueError):
            ridge_points(540,seed=5,horizon=float("nan"),relief=.1)

    def test_same_authored_bank_is_reused_across_three_real_domains(self):
        from automate_ytb.science_rainbow import daylight_background,draw_rainbow
        from automate_ytb.science_volcano import _base
        from automate_ytb.science_ocean_depth import lighting_plate
        self.assertTrue(VERSION.endswith("p59-v1"))
        rainbow=daylight_background(101)
        self.assertEqual(rainbow.size,(1080,1920))
        self.assertEqual(rainbow.mode,"RGBA")
        self.assertEqual(rainbow.tobytes(),daylight_background(101).tobytes())
        volcano=_base(False)
        self.assertEqual(volcano.size,(1080,1380))
        self.assertIs(volcano,_base(False))
        sea=lighting_plate("wind")
        self.assertEqual(sea.size,(920,890))
        self.assertIs(sea,lighting_plate("wind"))
        self.assertEqual(sea.getpixel((0,0))[3],0)
        self.assertEqual(sea.getpixel((460,440))[3],255)
        # Full-screen opaque slideshow boxes have been removed from the
        # rainbow generator. The authored optical rays still draw normally.
        canvas=Image.new("RGBA",(1080,1920))
        draw_rainbow(ImageDraw.Draw(canvas,"RGBA"),"sunlight",.3,6.,True)
        self.assertEqual(canvas.getpixel((80,600))[3],0)
        self.assertGreater(canvas.getchannel("A").getextrema()[1],230)


    def test_subpixel_cloud_parallax_is_deterministic_and_alpha_safe(self):
        first=drifting_cloud_bank((540,290),seed=97,t=0.,speed=.85)
        middle=drifting_cloud_bank((540,290),seed=97,t=2.75,speed=.85)
        self.assertEqual(first.size,(540,290))
        self.assertEqual(first.mode,"RGBA")
        self.assertEqual(first.getpixel((90,0))[3],0)
        self.assertNotEqual(first.tobytes(),middle.tobytes())
        self.assertEqual(middle.tobytes(),drifting_cloud_bank(
            (540,290),seed=97,t=2.75,speed=.85).tobytes())
        # Never mutate the cached original multi-scale RGBA source.
        unchanged=cloud_bank((540,290),seed=97)
        original=unchanged.tobytes()
        drifting_cloud_bank((540,290),seed=97,t=12.)
        self.assertEqual(unchanged.tobytes(),original)

    def test_atmospheric_motion_rejects_unsafe_inputs(self):
        for t in (-1,181,float("nan"),float("inf"),True):
            with self.assertRaises(ValueError):
                drifting_cloud_bank((540,290),seed=5,t=t)
        for speed in (0.,4.,float("nan")):
            with self.assertRaises(ValueError):
                drifting_cloud_bank((540,290),seed=5,t=3.,speed=speed)
        with self.assertRaises(ValueError):
            drifting_cloud_bank((540,290),seed=5,t=1.,phase=99)
        with self.assertRaises(ValueError):
            drifting_cloud_bank((540,290),seed=5,t=1.,opacity=-1)

    def test_real_rainbow_atmosphere_moves_but_leaves_header_untouched(self):
        from automate_ytb.science_rainbow import (
            daylight_background, animate_daylight_clouds,
        )
        base=daylight_background(101)
        start=base.copy()
        future=base.copy()
        animate_daylight_clouds(start,101,0.)
        animate_daylight_clouds(future,101,4.)
        self.assertNotEqual(
            start.crop((40,540,1030,870)).tobytes(),
            future.crop((40,540,1030,870)).tobytes())
        self.assertEqual(
            start.crop((0,0,1080,260)).tobytes(),
            base.crop((0,0,1080,260)).tobytes())
        self.assertEqual(
            start.crop((0,1550,1080,1920)).tobytes(),
            base.crop((0,1550,1080,1920)).tobytes())
        with self.assertRaises(ValueError):
            animate_daylight_clouds(Image.new("RGB",(1080,1920)),101,2.)

    def test_real_volcano_upper_atmosphere_changes_with_clock(self):
        from automate_ytb.science_volcano import draw_volcano
        a=Image.new("RGBA",(1080,1920))
        b=Image.new("RGBA",(1080,1920))
        draw_volcano(a,"magma",0.,6.,True)
        draw_volcano(b,"magma",4.,6.,True)
        self.assertNotEqual(
            a.crop((100,390,950,540)).tobytes(),
            b.crop((100,390,950,540)).tobytes())


if __name__=="__main__":
    unittest.main()
