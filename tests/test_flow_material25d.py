"""Live source-material regression for original 2.5D circular currents."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageDraw,ImageStat

from automate_ytb.flow_material25d import (
    VERSION,PALETTES,vortex_source,vortex_frame,
)
from automate_ytb.science_storyboards import draw_storyboard
from automate_ytb.science_portrait import PortraitScienceScene


class FlowMaterial25DTests(unittest.TestCase):
    def test_cached_source_preserves_original_texture_and_transparent_edges(self):
        ocean=vortex_source(670,palette="ocean",seed=377)
        self.assertIs(ocean,vortex_source(670,palette="ocean",seed=377))
        self.assertEqual(ocean.mode,"RGBA")
        self.assertEqual(ocean.size,(670,670))
        self.assertEqual(ocean.getpixel((0,0))[3],0)
        self.assertGreater(ocean.getpixel((335,335))[3],100)
        self.assertGreater(max(ImageStat.Stat(ocean.convert("RGB")).stddev),20)
        self.assertNotEqual(ocean.tobytes(),
                            vortex_source(670,palette="storm",seed=377).tobytes())
        self.assertEqual(set(PALETTES),{"ocean","lagoon","storm"})
        self.assertTrue(VERSION.endswith("p514-v1"))

    def test_original_swirling_filaments_move_without_mutating_cached_source(self):
        base=vortex_source(410)
        signature=base.tobytes()
        a=vortex_frame(410,1.2)
        b=vortex_frame(410,2.8)
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.tobytes(),vortex_frame(410,1.2).tobytes())
        self.assertEqual(vortex_source(410).tobytes(),signature)
        for image in (a,b):
            self.assertEqual(image.getpixel((0,0))[3],0)
            self.assertEqual(image.getpixel((409,409))[3],0)
            self.assertGreater(image.getpixel((205,205))[3],100)
        self.assertNotEqual(
            vortex_frame(410,2.8,clockwise=True).tobytes(),
            vortex_frame(410,2.8,clockwise=False).tobytes())

    def test_invalid_dimensions_palette_clock_and_booleans_fail_closed(self):
        for diameter in (False,12,127,901,400.0):
            with self.assertRaises(ValueError):
                vortex_source(diameter)
        for palette in ("other",None,True):
            with self.assertRaises(ValueError):
                vortex_source(410,palette=palette)
        for t in (True,-1,181,float("nan"),math.inf):
            with self.assertRaises(ValueError):
                vortex_frame(410,t)
        with self.assertRaises(ValueError):
            vortex_frame(410,.5,clockwise=1)

    def test_actual_coriolis_storyboard_uses_new_moving_source(self):
        original=Image.new("RGBA",(1080,1920))
        schematic=Image.new("RGBA",(1080,1920))
        draw_storyboard(ImageDraw.Draw(original,"RGBA"),
                        "coriolis",.7,True,duration=6.,canvas=original)
        draw_storyboard(ImageDraw.Draw(schematic,"RGBA"),
                        "coriolis",.7,True,duration=6.)
        self.assertNotEqual(original.tobytes(),schematic.tobytes())
        self.assertEqual(original.crop((0,0,1080,520)).tobytes(),
                         schematic.crop((0,0,1080,520)).tobytes())
        self.assertEqual(original.crop((0,1522,1080,1920)).tobytes(),
                         schematic.crop((0,1522,1080,1920)).tobytes())

    def test_real_1080x1920_renderer_preserves_text_and_animates_source(self):
        shot=PortraitScienceScene(
            topic="Why do ocean currents move?",
            narration="Earth rotation bends currents through the Coriolis effect.",
            scene_index=3)
        self.assertEqual(shot.beat,"coriolis")
        early=shot.frame(.45,6.)
        late=shot.frame(2.1,6.)
        self.assertEqual(early.mode,"RGB")
        self.assertEqual(early.size,(1080,1920))
        self.assertNotEqual(early.crop((205,755,875,1425)).tobytes(),
                            late.crop((205,755,875,1425)).tobytes())
        self.assertEqual(early.tobytes(),shot.frame(.45,6.).tobytes())


if __name__=="__main__":
    unittest.main()
