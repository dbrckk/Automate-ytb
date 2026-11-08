"""P3.7 original character material, grounded sculpted paw and acting QA."""
import math
import unittest

from PIL import Image, ImageDraw, ImageChops

from automate_ytb.forest_character_art25d import (
    VERSION, finish_sprite, facial_pose, draw_plush_leg, scarf_tip,
)
from automate_ytb.forest_contact25d import IMPACT_TIME
from automate_ytb.forest25d import character_plate, frame
from automate_ytb.rig25d import walking_leg, GROUND


class CharacterArt25DTests(unittest.TestCase):
    def test_material_preserves_original_silhouette_for_all_species_and_parts(self):
        for kind in ("fox","rabbit","cat"):
            for part,size in (("body",(350,440)),("ear",(150,240)),
                              ("tail",(230,240))):
                with self.subTest(kind=kind,part=part):
                    raw=Image.new("RGBA",size)
                    brush=ImageDraw.Draw(raw)
                    brush.ellipse((size[0]//7,size[1]//7,
                                   size[0]*6//7,size[1]*6//7),
                                  fill=(126,128,139,255))
                    alpha_before=raw.getchannel("A").tobytes()
                    painted=finish_sprite(raw,kind=kind,part=part)
                    again=finish_sprite(raw,kind=kind,part=part)
                    self.assertEqual(alpha_before,painted.getchannel("A").tobytes())
                    self.assertEqual(raw.getchannel("A").tobytes(),alpha_before)
                    self.assertEqual(painted.tobytes(),again.tobytes())
                    self.assertIsNotNone(
                        ImageChops.difference(painted.convert("RGB"),
                                              raw.convert("RGB")).getbbox())
                    self.assertIn("p37",VERSION)

    def test_real_impact_drives_expression_without_premature_surprise(self):
        self.assertEqual(facial_pose(0.7,interaction=True),"body")
        self.assertEqual(facial_pose(IMPACT_TIME-.12,interaction=True),"look-down")
        self.assertEqual(facial_pose(IMPACT_TIME+.21,interaction=True),"surprise")
        self.assertEqual(facial_pose(IMPACT_TIME+.75,interaction=True),"follow")
        self.assertNotEqual(facial_pose(IMPACT_TIME+.21,interaction=False),"surprise")
        self.assertEqual(facial_pose(0,interaction=False),"blink")

    def test_plush_leg_paints_without_changing_paw_world_contact(self):
        t=IMPACT_TIME+.025
        pose=walking_leg(t,side="right",origin_x=195,
                         speed=44,torso_y=915,ground_y=GROUND)
        self.assertTrue(pose.planted)
        self.assertEqual(pose.foot[1],GROUND)
        for kind in ("fox","rabbit","cat"):
            canvas=Image.new("RGBA",(1080,1920))
            draw_plush_leg(ImageDraw.Draw(canvas),pose=pose,
                           kind=kind,side="right")
            self.assertIsNotNone(canvas.getbbox())
            x=round(pose.foot[0])
            self.assertGreater(canvas.getpixel((x,round(GROUND)))[3],0)

    def test_articulated_scarf_tip_moves_deterministically(self):
        a=scarf_tip(.5,x=195,y=915,kind="fox",contact=False)
        b=scarf_tip(1.1,x=195,y=915,kind="fox",contact=False)
        self.assertEqual(a.size,(350,440))
        self.assertIsNotNone(
            ImageChops.difference(a.convert("RGB"),b.convert("RGB")).getbbox())
        self.assertEqual(a.tobytes(),
                         scarf_tip(.5,x=195,y=915,kind="fox",contact=False).tobytes())

    def test_true_character_plate_uses_contact_acting_and_keeps_original_ik(self):
        t=IMPACT_TIME+.21
        for kind in ("fox","rabbit","cat"):
            actor,meta=character_plate(t,kind=kind,interaction=True)
            self.assertEqual(actor.size,(1080,1920))
            self.assertEqual(meta["expression"],"surprise")
            self.assertEqual(meta["art"],VERSION)
            self.assertTrue(meta["right"].planted)
            self.assertEqual(meta["right"].foot[1],GROUND)

    def test_framed_cinematic_story_keeps_all_character_detail(self):
        a=frame(IMPACT_TIME+.2,kind="fox",interaction=True,story=True,
                show_story_titles=False)
        self.assertEqual(a.mode,"RGB")
        self.assertEqual(a.size,(1080,1920))

    def test_invalid_art_and_clocks_fail_closed(self):
        raw=Image.new("RGBA",(350,440))
        with self.assertRaises(ValueError):
            finish_sprite(raw,kind="owl",part="body")
        with self.assertRaises(ValueError):
            finish_sprite(raw,kind="fox",part="ear")
        for t in (math.inf,math.nan,-1,8,True):
            with self.subTest(t=t),self.assertRaises(ValueError):
                facial_pose(t,interaction=True)


if __name__=="__main__":
    unittest.main()
