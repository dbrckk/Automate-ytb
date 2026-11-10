"""New moving material sources must genuinely integrate across science topics."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageChops

from automate_ytb.fluid_emitter25d import (
    VERSION,MATERIALS,emitter_anchor,emitter_frame,
)
from automate_ytb.science_volcano import _base,_explosion
from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.science_storyboards import _wind


class OriginalFluidEmitter25DTests(unittest.TestCase):
    def test_two_fluid_materials_have_connected_unique_source_anchor(self):
        self.assertEqual(set(MATERIALS),{"magma","spray"})
        self.assertTrue(VERSION.endswith("p520-v1"))
        self.assertEqual(emitter_anchor((300,280),"magma"),(150,263))
        self.assertEqual(emitter_anchor((690,190),"spray"),(21,95))
        for material,size in (("magma",(300,280)),
                              ("spray",(690,190))):
            with self.subTest(material=material):
                a=emitter_frame(size,1.4,6.8,material=material)
                b=emitter_frame(size,3.9,6.8,material=material)
                self.assertEqual(a.size,size)
                self.assertEqual(a.mode,"RGBA")
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),
                                 emitter_frame(size,1.4,6.8,
                                               material=material).tobytes())
                self.assertEqual(a.getpixel((0,0))[3],0)
                self.assertGreater(a.getchannel("A").getextrema()[1],90)

    def test_rising_magma_begins_emitting_only_after_vent_opens(self):
        blank=emitter_frame((300,280),0,6.8,material="magma")
        self.assertIsNone(blank.getchannel("A").getbbox())
        start=emitter_frame((300,280),.9,6.8,material="magma")
        active=emitter_frame((300,280),4.8,6.8,material="magma")
        self.assertIsNotNone(start.getchannel("A").getbbox())
        self.assertNotEqual(start.tobytes(),active.tobytes())
        self.assertEqual(start.getpixel((0,279))[3],0)

    def test_invalid_clock_and_source_dimensions_are_rejected(self):
        for size,t,duration,material,seed in (
            ((True,280),1.,6.8,"magma",1),
            ((300,False),1.,6.8,"magma",1),
            ((127,280),1.,6.8,"magma",1),
            ((300,901),1.,6.8,"magma",1),
            ([300,280],1.,6.8,"magma",1),
            ((300,280),True,6.8,"magma",1),
            ((300,280),-1,6.8,"magma",1),
            ((300,280),math.nan,6.8,"magma",1),
            ((300,280),1.,False,"magma",1),
            ((300,280),7.,6.8,"magma",1),
            ((300,280),1.,6.8,"smoke",1),
            ((300,280),1.,6.8,"magma",False),
            ((300,280),1.,6.8,"magma",1_000_001),
        ):
            with self.subTest(params=(size,t,duration,material,seed)):
                with self.assertRaises(ValueError):
                    emitter_frame(size,t,duration,material=material,seed=seed)

    def test_actual_erupting_volcano_uses_moving_original_fountain(self):
        original=_base(False).copy()
        early=original.copy()
        late=original.copy()
        _explosion(early,1.3,6.8)
        _explosion(late,4.2,6.8)
        self.assertNotEqual(early.crop((385,80,690,350)).tobytes(),
                            late.crop((385,80,690,350)).tobytes())
        self.assertNotEqual(early.tobytes(),original.tobytes())
        repeat=original.copy()
        _explosion(repeat,1.3,6.8)
        self.assertEqual(early.tobytes(),repeat.tobytes())

    def test_actual_ocean_wind_source_animates_without_modifying_header(self):
        import PIL.ImageDraw
        native=Image.new("RGBA",(1080,1920))
        previous=native.copy()
        _wind(PIL.ImageDraw.Draw(native,"RGBA"),1.2,True,canvas=native)
        _wind(PIL.ImageDraw.Draw(previous,"RGBA"),1.2,True)
        self.assertNotEqual(native.tobytes(),previous.tobytes())
        self.assertEqual(native.crop((0,0,1080,690)).tobytes(),
                         previous.crop((0,0,1080,690)).tobytes())

    def test_real_wind_source_supports_long_narrated_segments(self):
        from PIL import ImageDraw
        from automate_ytb.science_storyboards import draw_storyboard
        # This used to fail at 6.8s because an unrelated default duration
        # was hardcoded inside the water spray source emitter.
        first=Image.new("RGBA",(1080,1920))
        another=Image.new("RGBA",(1080,1920))
        draw_storyboard(ImageDraw.Draw(first,"RGBA"),"wind",9.4,True,
                        duration=12.0,canvas=first)
        draw_storyboard(ImageDraw.Draw(another,"RGBA"),"wind",11.2,True,
                        duration=12.0,canvas=another)
        self.assertNotEqual(first.tobytes(),another.tobytes())
        self.assertEqual(first.size,(1080,1920))

    def test_real_two_subject_native_video_frames_follow_narration(self):
        examples=(
            ("How do volcanoes erupt?",
             "When magma reaches the surface, expanding gases blast ash and glowing fragments high into the sky.",
             "volcano_beat","eruption"),
            ("Why do ocean currents move?",
             "Global winds push surface waters, driving powerful currents.",
             "beat","wind"),
        )
        for topic,narration,field,expected in examples:
            with self.subTest(subject=topic):
                shot=PortraitScienceScene(topic=topic,narration=narration,
                                           scene_index=3)
                self.assertEqual(getattr(shot,field),expected)
                a=shot.frame(1.0,6.8)
                b=shot.frame(2.8,6.8)
                self.assertEqual(a.mode,"RGB")
                self.assertEqual(a.size,(1080,1920))
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),shot.frame(1.0,6.8).tobytes())


if __name__=="__main__":
    unittest.main()
