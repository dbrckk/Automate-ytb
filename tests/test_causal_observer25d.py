"""P5.27: real object-level causal motion, not just changing a background."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.causal_action25d import (
    VERSION, action_phase, contributing_sources, ease,
)
from automate_ytb.science_causal_vfx import event_phase
from automate_ytb.science_rainbow import (
    RAIN_SOURCES_X, BEATS, observer_light_paths, draw_rainbow,
)
from automate_ytb.science_audio_cues import audio_event_fraction
from automate_ytb.science_portrait import PortraitScienceScene


TOPIC="Why Can't You Reach the End of a Rainbow?"
FINAL="Millions of droplets create the rainbow each observer sees; when you move, its apparent end moves too."


class CausalObserverTests(unittest.TestCase):
    def test_genuine_shared_audio_action_clock_retains_ocean_semantics(self):
        self.assertIn("p527",VERSION)
        for time in (0.,.1,.6,1.2,2.8,4.8,5.7,6.6):
            for cue in (None,.18,.45,.81):
                with self.subTest(t=time,cue=cue):
                    self.assertAlmostEqual(
                        event_phase(time,6.6,cue),
                        action_phase(time,6.6,event_progress=cue))
        self.assertEqual(action_phase(0,6.6),0)
        self.assertEqual(action_phase(6.6,6.6),1)
        self.assertEqual(ease(0),0)
        self.assertEqual(ease(1),1)

    def test_world_raindrops_never_move_and_contributions_crossfade(self):
        nodes=(100.,180.,260.,340.)
        for target in (100.,101.,148.,179.9,180.,180.1,201.,260.,339.,340.):
            weighted=contributing_sources(nodes,target)
            self.assertAlmostEqual(sum(w for _,w in weighted),1)
            self.assertTrue(all(0<=w<=1 for _,w in weighted))
            self.assertTrue(all(0<=i<len(nodes) for i,_ in weighted))
        before=contributing_sources(nodes,180-.000001)
        after=contributing_sources(nodes,180+.000001)
        brightness=lambda x:sum(nodes[i]*w for i,w in x)
        self.assertLess(abs(brightness(before)-brightness(after)),.00001)
        self.assertEqual(contributing_sources(nodes,-999),((0,1.),))
        self.assertEqual(contributing_sources(nodes,999),((3,1.),))
        self.assertEqual(tuple(RAIN_SOURCES_X),tuple(range(125,1010,59)))

    def test_mobile_observer_moves_while_fixed_droplet_sources_switch(self):
        samples=[observer_light_paths(t,6.6) for t in (0,1.5,3.3,5.1,6.6)]
        x=[s["observer_x"] for s in samples]
        self.assertTrue(all(a<=b for a,b in zip(x,x[1:])))
        self.assertGreater(x[-1]-x[0],220)
        self.assertAlmostEqual(samples[0]["phase"],0)
        self.assertAlmostEqual(samples[-1]["phase"],1)
        reds=[{i for i,w in s["red"] if w>.01} for s in samples]
        violets=[{i for i,w in s["violet"] if w>.01} for s in samples]
        self.assertNotEqual(reds[0],reds[-1])
        self.assertNotEqual(violets[0],violets[-1])
        self.assertTrue(all(max(nodes)<len(RAIN_SOURCES_X)
                            for nodes in reds+violets))
        # Optical arc is view-relative; droplets never change positions.
        self.assertAlmostEqual(
            samples[-1]["arc_center_x"]-samples[0]["arc_center_x"],
            x[-1]-x[0])

    def test_real_narration_anchors_walking_to_spoken_move_phrase(self):
        segments=[
            {"text":"Millions of droplets create the rainbow each observer sees;",
             "startMs":0,"endMs":3100},
            {"text":"when you move, its apparent end moves too.",
             "startMs":3100,"endMs":6600},
        ]
        cue=audio_event_fraction("rainbow","arc",segments,0)
        self.assertAlmostEqual(cue,4850/6600)
        start=PortraitScienceScene(
            topic=TOPIC,narration=FINAL,scene_index=5,
            caption_segments=segments,scene_start_ms=0)
        self.assertEqual(start.rainbow_beat,"arc")
        self.assertEqual(start._narrated_event_fraction,cue)
        self.assertEqual(
            observer_light_paths(.5,6.6,event_progress=cue)["phase"],0)
        self.assertGreater(
            observer_light_paths(4.9,6.6,event_progress=cue)["phase"],0)
        self.assertIsNone(audio_event_fraction("rainbow","arc",None,0))

    def test_all_real_source_shots_have_new_causal_geometry(self):
        for beat in BEATS:
            with self.subTest(beat=beat):
                a=Image.new("RGBA",(1080,1920))
                b=Image.new("RGBA",(1080,1920))
                draw_rainbow(ImageDraw.Draw(a,"RGBA"),beat,1.4,6.6,True,canvas=a)
                draw_rainbow(ImageDraw.Draw(b,"RGBA"),beat,5.3,6.6,True,canvas=b)
                self.assertEqual(a.size,(1080,1920))
                self.assertIsNotNone(
                    ImageChops.difference(a.convert("RGB"),b.convert("RGB")).getbbox(),
                    f"{beat} must animate native optical objects")
                self.assertEqual(
                    a.crop((0,1522,1080,1920)).tobytes(),
                    b.crop((0,1522,1080,1920)).tobytes())

    def test_end_of_rainbow_final_scene_has_genuinely_moving_walker(self):
        shot=PortraitScienceScene(
            topic=TOPIC,narration=FINAL,scene_index=5)
        first=shot.frame(.5,6.6)
        last=shot.frame(6.2,6.6)
        self.assertEqual(first.size,(1080,1920))
        self.assertEqual(first.mode,"RGB")
        world=(80,1000,1000,1494)
        diff=ImageChops.difference(first.crop(world),last.crop(world))
        self.assertIsNotNone(diff.getbbox())
        # The header is stationary. The *spoken active caption* naturally
        # advances between these two times: comparing caption bytes would
        # incorrectly forbid synchronized subtitles from changing.
        # The animated high-altitude cloud layer enters at y=435. Only
        # the overlaid static editorial title itself must remain unchanged.
        head=(0,0,1080,400)
        self.assertEqual(first.crop(head).tobytes(),
                         last.crop(head).tobytes())
        for frame in (first,last):
            self.assertGreater(
                sum(frame.crop((65,1522,1015,1722)).convert("L").getdata()),
                100000)

    def test_strict_malformed_actions_are_rejected(self):
        for t,duration,cue in ((-1,6,None),(7,6,None),
                               (0,0,None),(1,6,True),
                               (1,6,float("nan"))):
            with self.assertRaises(ValueError):
                action_phase(t,duration,event_progress=cue)
        for invalid in (
            ((120.,119.),100),
            ((200.,),100),
            ((100.,float("nan")),100),
            ((100.,200.),float("inf")),
            ((100.,200.),True),
        ):
            with self.assertRaises(ValueError):
                contributing_sources(*invalid)
        with self.assertRaises(ValueError):
            draw_rainbow(ImageDraw.Draw(Image.new("RGBA",(1080,1920))),
                         "arc",1,6,True,event_progress=1.2)


if __name__=="__main__":
    unittest.main()
