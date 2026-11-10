"""No-scene-card geometry, moving water occlusion, and real video framing."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageChops

from automate_ytb.world_volume25d import (
    VERSION,KINDS,world_volume_alpha,
)
from automate_ytb.science_ocean_depth import (
    PALETTES,ORIGIN,SIZE,draw_depth,lighting_plate,
)
from automate_ytb.science_portrait import PortraitScienceScene


class OriginalOpenVolumeTests(unittest.TestCase):
    def test_cached_source_volume_is_feathered_not_box_shaped(self):
        for kind in KINDS:
            alpha=world_volume_alpha(SIZE,kind=kind,seed=171)
            self.assertIs(alpha,world_volume_alpha(SIZE,kind=kind,seed=171))
            self.assertEqual(alpha.mode,"L")
            self.assertEqual(alpha.size,SIZE)
            self.assertEqual(alpha.getpixel((0,0)),0)
            self.assertEqual(alpha.getpixel((919,889)),0)
            self.assertEqual(alpha.getpixel((460,440)),255)
            self.assertEqual(alpha.getpixel((0,440)),0)
            self.assertLess(alpha.getpixel((30,440)),140)
            self.assertLess(alpha.getpixel((460,26)),140)
            self.assertGreater(alpha.getpixel((160,440)),150)
            self.assertTrue(VERSION.endswith("p519-v1"))
        self.assertNotEqual(
            world_volume_alpha(SIZE,seed=171).tobytes(),
            world_volume_alpha(SIZE,seed=172).tobytes())

    def test_validation_rejects_bool_aliases_and_unsafe_source_dimensions(self):
        for size,kind,seed in (
            ((True,890),"water",1),((920,False),"water",1),
            ((100,890),"water",1),((2000,890),"water",1),
            ([920,890],"water",1),((920,890),"cards",1),
            ((920,890),"water",True),((920,890),"water",-1),
            ((920,890),"haze",1_000_001),
        ):
            with self.assertRaises(ValueError):
                world_volume_alpha(size,kind=kind,seed=seed)

    def test_all_five_actual_scenes_share_dissolving_atmosphere(self):
        for beat in PALETTES:
            with self.subTest(beat=beat):
                plate=lighting_plate(beat)
                self.assertEqual(plate.size,SIZE)
                self.assertIs(plate,lighting_plate(beat))
                self.assertEqual(plate.getpixel((460,440))[3],255)
                self.assertEqual(plate.getpixel((0,440))[3],0)
                self.assertLess(plate.getpixel((30,440))[3],140)
                self.assertLess(plate.getpixel((460,26))[3],140)

    def test_motion_is_clipped_to_original_atmosphere_not_painted_outside(self):
        original=(6,21,39,255)
        frame=Image.new("RGBA",(1080,1920),original)
        another=frame.copy()
        draw_depth(frame,"coriolis",t=.75,duration=6.8)
        draw_depth(another,"coriolis",t=2.8,duration=6.8)
        self.assertEqual(frame.getpixel((80,1040)),original)
        self.assertEqual(frame.getpixel((999,1040)),original)
        self.assertEqual(frame.getpixel((540,600)),original)
        self.assertEqual(frame.getpixel((540,1490)),original)
        self.assertEqual(frame.getpixel((540,420)),original)
        self.assertEqual(frame.getpixel((540,1660)),original)
        self.assertNotEqual(frame.getpixel((540,1080)),original)
        self.assertNotEqual(frame.crop((240,700,820,1370)).tobytes(),
                            another.crop((240,700,820,1370)).tobytes())

    def test_real_science_scene_preserves_9_16_and_narration_overlay(self):
        shot=PortraitScienceScene(
            topic="Why do ocean currents move?",
            narration="Earth rotation bends currents through the Coriolis effect.",
            scene_index=3)
        early=shot.frame(.6,6.8)
        late=shot.frame(2.4,6.8)
        self.assertEqual(early.mode,"RGB")
        self.assertEqual(early.size,(1080,1920))
        self.assertNotEqual(early.tobytes(),late.tobytes())
        self.assertEqual(early.tobytes(),shot.frame(.6,6.8).tobytes())


if __name__=="__main__":
    unittest.main()
