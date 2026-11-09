"""Cinematic storm effects: stable depth, time, alpha, motion and H.264 safety."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.science_lightning_fx import (
    SIZE, cloud_volume, paint_environment, paint_terrain,
    bloom_electric_channel, paint_foreground_weather,
    paint_reactive_storm_light, _reactive_light_masks,
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

    def test_original_flash_relights_both_clouds_and_ground(self):
        dark=Image.new("RGBA",SIZE,(8,20,38,255))
        flash=dark.copy()
        paint_reactive_storm_light(flash,"return",1.4,7.)
        self.assertGreater(flash.getpixel((600,240))[0],
                           dark.getpixel((600,240))[0]+25)
        self.assertGreater(flash.getpixel((700,845))[1],
                           dark.getpixel((700,845))[1]+25)
        self.assertEqual(flash.getchannel("A").getextrema(),(255,255))

    def test_flash_reuses_exact_existing_bolt_pulses_and_is_deterministic(self):
        dark=Image.new("RGBA",SIZE,(8,20,38,255))
        before=dark.copy()
        at_strike=dark.copy()
        repeated=dark.copy()
        after=dark.copy()
        paint_reactive_storm_light(before,"return",0.,7.)
        paint_reactive_storm_light(at_strike,"return",1.4,7.)
        paint_reactive_storm_light(repeated,"return",1.4,7.)
        paint_reactive_storm_light(after,"return",7.,7.)
        self.assertEqual(before.tobytes(),dark.tobytes())
        self.assertEqual(after.tobytes(),dark.tobytes())
        self.assertEqual(at_strike.tobytes(),repeated.tobytes())

    def test_non_bolt_beats_never_create_extra_flashes(self):
        baseline=Image.new("RGBA",SIZE)
        for beat in ("charge","thunder"):
            frame=baseline.copy()
            paint_reactive_storm_light(frame,beat,3.5,7.)
            self.assertEqual(frame.tobytes(),baseline.tobytes())
        # Our layer can be composited directly into the transparent 2.5D
        # stage before the electric action without making it opaque.
        layer=baseline.copy()
        paint_reactive_storm_light(layer,"return",1.4,7.)
        self.assertEqual(layer.getpixel((0,0))[3],0)
        self.assertGreater(layer.getpixel((700,845))[3],0)

    def test_spatial_flash_fields_are_cached_and_separated_by_depth(self):
        clouds,wet=_reactive_light_masks()
        self.assertIs(clouds,_reactive_light_masks()[0])
        self.assertIs(wet,_reactive_light_masks()[1])
        self.assertEqual(clouds.size,SIZE)
        self.assertGreater(clouds.getpixel((600,240)),
                           clouds.getpixel((600,845)))
        self.assertGreater(wet.getpixel((700,845)),
                           wet.getpixel((700,240)))

    def test_flash_rejects_invalid_dimensions_and_clock(self):
        cases=(
            (Image.new("RGB",SIZE),"return",1.,7.),
            (Image.new("RGBA",(720,1280)),"return",1.,7.),
            (Image.new("RGBA",SIZE),"unknown",1.,7.),
            (Image.new("RGBA",SIZE),"return",float("nan"),7.),
            (Image.new("RGBA",SIZE),"return",1.,0.),
            (Image.new("RGBA",SIZE),"return",8.,7.),
        )
        for frame,beat,t,duration in cases:
            with self.subTest(beat=beat,t=t,duration=duration):
                with self.assertRaises(ValueError):
                    paint_reactive_storm_light(frame,beat,t,duration)

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
