"""Real cold-water storyboard has motion without an opaque diagram card."""
from __future__ import annotations
import math
import unittest
from PIL import Image, ImageDraw
from automate_ytb.density_plume25d import VERSION,sinking_plume_frame
from automate_ytb.science_storyboards import draw_storyboard
from automate_ytb.science_portrait import PortraitScienceScene


class ColdWaterPlumeSourceTests(unittest.TestCase):
    def test_connected_original_source_is_animated_and_alpha_safe(self):
        a=sinking_plume_frame((820,622),.7)
        b=sinking_plume_frame((820,622),3.2)
        self.assertEqual(a.size,(820,622))
        self.assertEqual(a.mode,"RGBA")
        self.assertEqual(a.getpixel((0,0))[3],0)
        self.assertEqual(a.getpixel((819,621))[3],0)
        self.assertGreater(a.getchannel("A").getextrema()[1],20)
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.tobytes(),
                         sinking_plume_frame((820,622),.7).tobytes())
        self.assertTrue(VERSION.endswith("p519-v2"))

    def test_source_refuses_unsafe_shapes_clocks_and_booleans(self):
        for size,t,seed in (
            ((True,622),1.,1),((820,False),1.,1),
            ((820,901),1.,1),([820,622],1.,1),
            ((820,622),True,1),((820,622),-1,1),
            ((820,622),math.nan,1),((820,622),181,1),
            ((820,622),1.,False),
        ):
            with self.subTest(parameters=(size,t,seed)):
                with self.assertRaises(ValueError):
                    sinking_plume_frame(size,t,seed=seed)

    def test_direct_draw_is_compatible_but_real_scene_has_no_rectangular_card(self):
        native=Image.new("RGBA",(1080,1920))
        legacy=native.copy()
        draw_storyboard(ImageDraw.Draw(native,"RGBA"),
                        "sinking",.8,True,duration=6.8,canvas=native)
        draw_storyboard(ImageDraw.Draw(legacy,"RGBA"),
                        "sinking",.8,True,duration=6.8)
        self.assertNotEqual(native.tobytes(),legacy.tobytes())
        self.assertEqual(native.getpixel((150,770))[3],0)
        self.assertGreater(legacy.getpixel((150,770))[3],0)
        self.assertEqual(native.crop((0,0,1080,520)).tobytes(),
                         legacy.crop((0,0,1080,520)).tobytes())

    def test_real_native_storyboard_has_original_moving_polar_water(self):
        scene=PortraitScienceScene(
            topic="Why do ocean currents move?",
            narration="Cold salty polar water sinks into deep circulation.",
            scene_index=4)
        self.assertEqual(scene.beat,"sinking")
        a=scene.frame(.9,6.8)
        b=scene.frame(3.5,6.8)
        self.assertEqual(a.size,(1080,1920))
        self.assertEqual(a.mode,"RGB")
        self.assertNotEqual(a.crop((200,790,910,1370)).tobytes(),
                            b.crop((200,790,910,1370)).tobytes())


if __name__=="__main__":
    unittest.main()
