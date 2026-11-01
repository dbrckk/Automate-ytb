"""Cinematic storm effects: stable depth, time, alpha, motion and H.264 safety."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.science_lightning_fx import (
    SIZE, cloud_volume, paint_environment, paint_terrain,
    bloom_electric_channel, paint_foreground_weather,
)
from automate_ytb.science_lightning import PATH


class LightningCinematicFXTests(unittest.TestCase):
    def test_translucent_cloud_volumes_are_cached_and_depth_variant(self):
        sky=cloud_volume(0,0)
        self.assertIs(sky,cloud_volume(0,0))
        self.assertEqual(sky.mode,"RGBA")
        self.assertGreater(sky.getchannel("A").getextrema()[1],0)
        self.assertLess(sky.getchannel("A").getextrema()[0],200)
        self.assertNotEqual(sky.size,cloud_volume(2,0).size)
        for depth,variant in ((-1,0),(3,0),(0,-1),(1,3)):
            with self.assertRaises(ValueError):
                cloud_volume(depth,variant)

    def test_parallax_storm_frames_move_reproducibly_and_stay_opaque(self):
        first=Image.new("RGBA",SIZE)
        later=Image.new("RGBA",SIZE)
        same=Image.new("RGBA",SIZE)
        paint_environment(first,.2,"leader",7)
        paint_environment(later,4.3,"leader",7)
        paint_environment(same,.2,"leader",7)
        self.assertEqual(first.tobytes(),same.tobytes())
        self.assertEqual(first.getchannel("A").getextrema(),(255,255))
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"),later.convert("RGB")).getbbox())
        terrain=Image.new("RGBA",SIZE)
        paint_terrain(ImageDraw.Draw(terrain),1.)
        self.assertIsNotNone(terrain.getbbox())

    def test_physical_stroke_bloom_and_rain_change_across_time(self):
        a=Image.new("RGBA",SIZE,(8,20,38,255))
        b=a.copy()
        bloom_electric_channel(a,"return",1.4,7,PATH)
        bloom_electric_channel(b,"return",5.1,7,PATH)
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB"),b.convert("RGB")).getbbox())
        first=a.copy()
        paint_foreground_weather(a,.2,"return")
        paint_foreground_weather(b,4.3,"return")
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB"),first.convert("RGB")).getbbox())
        self.assertEqual(a.getchannel("A").getextrema(),(255,255))
        self.assertEqual(b.getchannel("A").getextrema(),(255,255))

    def test_invalid_scene_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            paint_environment(Image.new("RGB",SIZE),.2,"leader",7)
        with self.assertRaises(ValueError):
            paint_environment(Image.new("RGBA",SIZE),math.inf,"leader",7)
        with self.assertRaises(ValueError):
            bloom_electric_channel(Image.new("RGBA",(720,930)),
                                   "return",1,7,PATH)


if __name__=="__main__":
    unittest.main()
