"""Storm haze compositing must preserve scene depth and native framing."""
from __future__ import annotations

import unittest
from PIL import Image, ImageChops

from automate_ytb.science_earth_stop import (
    _storm_cloud_sprite, _storm_clouds,
)


class ScienceCloudSceneTests(unittest.TestCase):
    def test_cloud_sprites_are_translucent_cached_originals(self):
        for kind in range(4):
            sprite=_storm_cloud_sprite(kind)
            self.assertIs(sprite,_storm_cloud_sprite(kind))
            self.assertEqual(sprite.size,(298,128))
            self.assertEqual(sprite.mode,"RGBA")
            self.assertLess(sprite.getchannel("A").getextrema()[1],120)
            self.assertGreater(sprite.getchannel("A").getextrema()[1],0)

    def test_clouds_blend_with_city_and_move_in_time(self):
        base=Image.new("RGBA",(1080,1920),(12,29,46,255))
        first,second,again=base.copy(),base.copy(),base.copy()
        _storm_clouds(first,.2)
        _storm_clouds(second,4)
        _storm_clouds(again,.2)
        self.assertEqual(first.tobytes(),again.tobytes())
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"),second.convert("RGB")).getbbox())
        self.assertEqual(first.getchannel("A").getextrema(),(255,255))
        self.assertLess(first.getpixel((111,742))[1],100)
        for bounds in ((0,0,1080,560),(0,1050,1080,1920)):
            self.assertEqual(first.crop(bounds).tobytes(),
                             base.crop(bounds).tobytes())

    def test_invalid_style_rejected(self):
        for invalid in (-1,4,99,True):
            with self.assertRaises(ValueError):
                _storm_cloud_sprite(invalid)


if __name__ == "__main__":
    unittest.main()
