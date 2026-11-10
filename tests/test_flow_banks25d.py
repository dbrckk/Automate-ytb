"""Original source-grounded 2.5D flow banks: lava and ocean currents."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageDraw,ImageChops

from automate_ytb.flow_banks25d import (
    VERSION,MATERIALS,advancing_path,flow_banks,draw_organic_flow,
)
from automate_ytb.science_volcano import _lava,_lava_track,_base
from automate_ytb.science_portrait import PortraitScienceScene


class OriginalFlowBankTests(unittest.TestCase):
    sample=((45.,180.),(99.,146.),(168.,157.),(210.,112.),(281.,91.))

    def test_one_true_source_trajectory_drives_widths_and_moving_material(self):
        self.assertTrue(VERSION.endswith("p522-v1"))
        self.assertEqual(set(MATERIALS),{"water","magma"})
        for material in MATERIALS:
            left,right=flow_banks(self.sample,material=material,
                                  width=42,seed=513)
            self.assertEqual(len(left),len(self.sample))
            self.assertEqual(len(right),len(self.sample))
            self.assertNotEqual(left,right)
            self.assertEqual((left,right),
                             flow_banks(self.sample,material=material,
                                        width=42,seed=513))
            # Real geological source asymmetric banks instead of 2
            # parallel and constant-width cylinders or rounded caps.
            widths=[math.dist(a,b) for a,b in zip(left,right)]
            self.assertGreater(max(widths)-min(widths),4.)
            frame=Image.new("RGBA",(340,270))
            other=frame.copy()
            later=frame.copy()
            draw_organic_flow(ImageDraw.Draw(frame,"RGBA"),self.sample,
                              material=material,width=42,t=1.2,
                              duration=6.8,seed=513)
            draw_organic_flow(ImageDraw.Draw(other,"RGBA"),self.sample,
                              material=material,width=42,t=1.2,
                              duration=6.8,seed=513)
            draw_organic_flow(ImageDraw.Draw(later,"RGBA"),self.sample,
                              material=material,width=42,t=3.8,
                              duration=6.8,seed=513)
            self.assertEqual(frame.tobytes(),other.tobytes())
            self.assertNotEqual(frame.tobytes(),later.tobytes())
            self.assertGreater(frame.getchannel("A").getextrema()[1],100)
            self.assertEqual(frame.getpixel((0,0))[3],0)
            self.assertEqual(frame.getpixel((339,269))[3],0)

    def test_arc_length_advance_is_monotone_and_attached_to_same_origin(self):
        full=advancing_path(self.sample,1.0)
        self.assertEqual(full,tuple(self.sample))
        self.assertEqual(advancing_path(self.sample,0.),())
        fronts=[advancing_path(self.sample,f)
                for f in (.15,.34,.56,.78,1.)]
        self.assertTrue(all(f[0]==self.sample[0] for f in fronts))
        self.assertTrue(all(f[-1][0]<g[-1][0] for f,g in zip(fronts,fronts[1:])))
        self.assertTrue(all(len(f)<=len(g) for f,g in zip(fronts,fronts[1:])))
        self.assertEqual(fronts[0],advancing_path(self.sample,.15))

    def test_original_volcano_drainage_is_cached_and_dual_slope(self):
        left=_lava_track(0)
        right=_lava_track(1)
        self.assertIs(left,_lava_track(0))
        self.assertIs(right,_lava_track(1))
        self.assertEqual(left[0],(540,356))
        self.assertEqual(right[0],(530,355))
        self.assertGreater(len(left),45)
        self.assertGreater(len(right),45)
        self.assertLess(right[-1][0],100.)
        self.assertGreater(left[-1][0],1000.)
        for value in (-1,2,True,"0"):
            with self.assertRaises(ValueError):
                _lava_track(value)

    def test_original_lava_appears_after_event_begins_and_stays_reproducible(self):
        original=_base(False).copy()
        beginning=original.copy()
        early=original.copy()
        late=original.copy()
        _lava(beginning,0.,6.8)
        _lava(early,1.8,6.8)
        _lava(late,5.2,6.8)
        self.assertEqual(original.tobytes(),beginning.tobytes())
        self.assertNotEqual(early.tobytes(),late.tobytes())
        self.assertNotEqual(original.tobytes(),early.tobytes())
        replay=original.copy()
        _lava(replay,1.8,6.8)
        self.assertEqual(early.tobytes(),replay.tobytes())

    def test_invalid_river_and_time_constraints_fail_closed(self):
        valid=self.sample
        for path in (((0,0),),((0,0),(0,0)),
                     ((0,0),(math.nan,1)),
                     ((0,0),(4001,1)),
                     ((True,2),(5,8))):
            with self.subTest(path=path),self.assertRaises(ValueError):
                flow_banks(path,material="magma",width=12)
        for material,width,seed in (("snow",12,7),("magma",True,7),
                                    ("water",121,7),("water",12,True)):
            with self.assertRaises(ValueError):
                flow_banks(valid,material=material,width=width,seed=seed)
        for progress in (-.01,1.01,math.nan,True):
            with self.assertRaises(ValueError):
                advancing_path(valid,progress)
        for t,duration in ((-1.,6.),(7.,6.),(math.nan,6.),
                           (1.,0.),(1.,math.inf),(True,6.)):
            with self.assertRaises(ValueError):
                draw_organic_flow(ImageDraw.Draw(Image.new("RGBA",(340,270))),
                                  valid,material="magma",width=40,
                                  t=t,duration=duration)

    def test_real_native_lava_and_ocean_flow_videos_with_narration(self):
        examples=(
            ("How do volcanoes erupt?",
             "Escaping lava flows down the slopes while ash settles.",
             "volcano_beat","lava"),
            ("Why do ocean currents move?",
             "Global winds push surface waters, driving powerful currents.",
             "beat","wind"),
        )
        for topic,text,field,expected in examples:
            with self.subTest(topic=topic):
                scene=PortraitScienceScene(topic=topic,
                                           narration=text,scene_index=3)
                self.assertEqual(getattr(scene,field),expected)
                a=scene.frame(.8,6.8)
                b=scene.frame(3.5,6.8)
                self.assertEqual(a.size,(1080,1920))
                self.assertEqual(a.mode,"RGB")
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),scene.frame(.8,6.8).tobytes())


if __name__=="__main__":
    unittest.main()
