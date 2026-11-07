"""Cinematic storm effects: stable depth, time, alpha, motion and H.264 safety."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.science_lightning_fx import (
    SIZE, cloud_volume, paint_environment, paint_terrain,
    bloom_electric_channel, paint_foreground_weather,
    paint_reactive_storm_light, _storm_flash_masks,
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

    def test_lightning_actually_relights_clouds_and_wet_ground_at_strike(self):
        baseline=Image.new("RGBA",SIZE,(8,20,36,255))
        start=baseline.copy()
        light=baseline.copy()
        repeat=baseline.copy()
        finish=baseline.copy()
        paint_reactive_storm_light(start,"return",0,7.0)
        paint_reactive_storm_light(light,"return",1.4,7.0)
        paint_reactive_storm_light(repeat,"return",1.4,7.0)
        paint_reactive_storm_light(finish,"return",7.0,7.0)
        self.assertEqual(start.tobytes(),baseline.tobytes())
        self.assertEqual(finish.tobytes(),baseline.tobytes())
        self.assertEqual(light.tobytes(),repeat.tobytes())
        # Light must be visible away from the stroke itself, in BOTH
        # upper cloud banks and actual wet surfaces near the radio mast.
        self.assertGreater(light.getpixel((600,240))[0],
                           baseline.getpixel((600,240))[0]+38)
        self.assertGreater(light.getpixel((730,835))[1],
                           baseline.getpixel((730,835))[1]+28)
        self.assertEqual(light.getchannel("A").getextrema(),(255,255))
        cloud,ground=_storm_flash_masks()
        self.assertIs(cloud,_storm_flash_masks()[0])
        self.assertIs(ground,_storm_flash_masks()[1])
        self.assertGreater(cloud.getpixel((600,240)),cloud.getpixel((600,830)))
        self.assertGreater(ground.getpixel((730,830)),ground.getpixel((730,240)))

    def test_faint_leader_and_connection_dont_create_false_white_screen(self):
        baseline=Image.new("RGBA",SIZE,(9,19,42,255))
        charge=baseline.copy()
        leader=baseline.copy()
        connection=baseline.copy()
        paint_reactive_storm_light(charge,"charge",3.5,7.)
        paint_reactive_storm_light(leader,"leader",5.46,7.)
        paint_reactive_storm_light(connection,"connection",6.16,7.)
        self.assertEqual(charge.tobytes(),baseline.tobytes())
        self.assertIsNotNone(ImageChops.difference(
            leader.convert("RGB"),baseline.convert("RGB")).getbbox())
        self.assertLess(leader.getpixel((600,240))[0],85)
        self.assertLess(connection.getpixel((600,240))[0],105)
        self.assertEqual(connection.getchannel("A").getextrema(),(255,255))

    def test_flash_rejects_invalid_size_mode_or_timing(self):
        for image,beat,t,duration in (
            (Image.new("RGB",SIZE),"return",1.,7.),
            (Image.new("RGBA",(800,600)),"return",1.,7.),
            (Image.new("RGBA",SIZE),"bad",1.,7.),
            (Image.new("RGBA",SIZE),"return",float("nan"),7.),
            (Image.new("RGBA",SIZE),"return",1.,0.),
            (Image.new("RGBA",SIZE),"return",9.,7.),
        ):
            with self.assertRaises(ValueError):
                paint_reactive_storm_light(image,beat,t,duration)

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
