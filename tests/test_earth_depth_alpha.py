"""Regression for Pillow RGBA-draw overwrites in science volumetric FX."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops

from automate_ytb.earth_cinematic_depth import (
    draw_depth_behind, draw_depth_above,
)


class DepthAlphaCompositingTests(unittest.TestCase):
    def test_opaque_video_frame_remains_opaque_after_every_pass(self):
        # If a translucent brush is mistakenly applied directly to an RGBA
        # source, Pillow replaces its alpha rather than blending. At export
        # the low alpha is discarded: huge opaque cyan bars appear.
        for beat in ("inertia","wind","ocean","stop","poles","day","astronaut"):
            with self.subTest(beat=beat):
                image=Image.new("RGBA",(1080,1920),(10,28,47,255))
                draw_depth_behind(image,beat,1.2,6)
                draw_depth_above(image,beat,1.2,6)
                self.assertEqual(
                    image.getchannel("A").getextrema(),(255,255),
                    "All atmospheric light and fog must alpha-composite")

    def test_fog_blends_instead_of_hiding_underlying_architecture(self):
        image=Image.new("RGBA",(1080,1920),(11,24,46,255))
        original=image.copy()
        draw_depth_behind(image,"inertia",2,6)
        pixel=image.getpixel((10,1035))
        # The old unblended rectangle overwrote the pixel with
        # (89,175,194,24); correct mixing retains most of the dark sky.
        self.assertLess(pixel[1],135)
        self.assertEqual(pixel[3],255)
        self.assertIsNotNone(ImageChops.difference(
            original.convert("RGB"),image.convert("RGB")).getbbox())

    def test_lighting_motion_kept_and_reproducible(self):
        a=Image.new("RGBA",(1080,1920),(10,24,47,255))
        b=a.copy()
        c=a.copy()
        for painter in (draw_depth_behind,draw_depth_above):
            painter(a,"wind",.2,6)
            painter(b,"wind",4.8,6)
            painter(c,"wind",.2,6)
        self.assertEqual(a.tobytes(),c.tobytes())
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB"),b.convert("RGB")).getbbox())


if __name__=="__main__":
    unittest.main()
