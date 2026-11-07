"""Verify spatial storm illumination follows real channel geometry."""
from __future__ import annotations

import unittest
from PIL import Image, ImageChops

from automate_ytb.science_lightning_fx import (
    SIZE, bloom_electric_channel,
)


class LightningSpatialLightTests(unittest.TestCase):
    def test_cloud_illumination_tracks_channel_not_fixed_oval(self):
        def render(x):
            stage=Image.new("RGBA",SIZE,(10,18,30,255))
            channel=((x,180),(x+15,390),(x,670))
            bloom_electric_channel(stage,"return",1.44,7.2,channel)
            return stage

        left=render(190)
        right=render(880)
        self.assertIsNotNone(ImageChops.difference(left.convert("RGB"),right.convert("RGB")).getbbox())
        # A true spatially localized light should move with the strike.
        left_near=sum(left.getpixel((190,y))[:3][i]
                      for y in (240,360,490) for i in range(3))
        left_far=sum(left.getpixel((880,y))[:3][i]
                     for y in (240,360,490) for i in range(3))
        right_near=sum(right.getpixel((880,y))[:3][i]
                       for y in (240,360,490) for i in range(3))
        right_far=sum(right.getpixel((190,y))[:3][i]
                      for y in (240,360,490) for i in range(3))
        self.assertGreater(left_near,left_far)
        self.assertGreater(right_near,right_far)

    def test_reflections_appear_at_actual_grounded_return_stroke(self):
        stage=Image.new("RGBA",SIZE,(10,18,30,255))
        channel=((700,695),(665,480),(485,270))
        bloom_electric_channel(stage,"return",1.44,7.2,channel)
        # The grounded tower is at x=700, not at the sky endpoint x=485.
        wet=stage.crop((560,810,840,930))
        self.assertIsNotNone(ImageChops.difference(
            wet.convert("RGB"),Image.new("RGB",wet.size,(10,18,30))).getbbox())

    def test_other_storm_actions_have_no_false_return_stroke_reflections(self):
        for beat in ("charge","thunder"):
            with self.subTest(beat=beat):
                stage=Image.new("RGBA",SIZE,(10,18,30,255))
                bloom_electric_channel(stage,beat,1.44,7.2,
                                       ((700,695),(600,450),(485,270)))
                self.assertEqual(stage.getpixel((700,875)),(10,18,30,255))


if __name__=="__main__":
    unittest.main()
