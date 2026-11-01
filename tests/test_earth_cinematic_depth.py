"""Cinematic 2.5D depth pass must be reproducible and preserve readable UI."""
from __future__ import annotations

import unittest
from PIL import Image, ImageChops

from automate_ytb.earth_cinematic_depth import (
    draw_depth_behind, draw_depth_above, _soft_light, SCENES,
)


class EarthCinematicDepthTests(unittest.TestCase):
    def test_every_shot_has_actual_timed_depth_cues(self):
        for beat in sorted(SCENES):
            with self.subTest(beat=beat):
                a=Image.new("RGBA",(1080,1920),(7,23,43,255))
                b=a.copy()
                again=a.copy()
                for painter in (draw_depth_behind,draw_depth_above):
                    painter(a,beat,.2,4.)
                    painter(b,beat,2.6,4.)
                    painter(again,beat,.2,4.)
                self.assertEqual(a.tobytes(),again.tobytes())
                diff=ImageChops.difference(
                    a.convert("RGB"),b.convert("RGB"))
                self.assertIsNotNone(
                    diff.crop((0,600,1080,1455)).getbbox(),
                    "cinematic depth must react to actual scene time")
                self.assertIsNone(
                    ImageChops.difference(
                        a.convert("RGB").crop((0,0,1080,535)),
                        Image.new("RGB",(1080,535),(7,23,43))
                    ).getbbox(),
                    "title and upper narration label must stay unobscured")

    def test_light_sprite_is_transparent_and_cached(self):
        sprite=_soft_light(512,(41,163,230))
        self.assertIs(sprite,_soft_light(512,(41,163,230)))
        self.assertEqual(sprite.mode,"RGBA")
        self.assertEqual(sprite.getpixel((0,0))[3],0)
        self.assertGreater(sprite.getpixel((256,256))[3],0)

    def test_bad_inputs_fail_before_painting(self):
        pic=Image.new("RGBA",(1080,1920))
        for painter in (draw_depth_behind,draw_depth_above):
            for beat,t,duration in (("wrong",.5,4),
                                    ("ocean",float("nan"),4),
                                    ("wind",-1,4),
                                    ("day",4.01,4),
                                    ("poles",1,0)):
                with self.subTest(painter=painter.__name__,beat=beat,t=t):
                    with self.assertRaises(ValueError):
                        painter(pic,beat,t,duration)
            with self.assertRaises(ValueError):
                painter(Image.new("RGBA",(720,1280)),"wind",1,3)


if __name__=="__main__":
    unittest.main()
