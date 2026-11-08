"""P3.8 physical soft-body, no fake camera-only animation, grounded IK QA."""
import math
import unittest

from PIL import Image,ImageDraw,ImageChops

from automate_ytb.forest_organic_mesh25d import (
    VERSION, BODY_SIZE, TAIL_SIZE, organic_pose, deform_body, deform_tail,
)
from automate_ytb.forest25d import character_plate
from automate_ytb.forest_contact25d import IMPACT_TIME
from automate_ytb.rig25d import GROUND, walking_leg


def test_sprite(size):
    sprite=Image.new("RGBA",size)
    d=ImageDraw.Draw(sprite)
    d.ellipse((round(size[0]*.15),round(size[1]*.14),
               round(size[0]*.87),round(size[1]*.89)),
              fill=(238,145,79,255))
    d.ellipse((round(size[0]*.44),round(size[1]*.34),
               round(size[0]*.56),round(size[1]*.45)),
              fill=(13,38,61,255))
    return sprite


class OrganicBodyMeshTests(unittest.TestCase):
    def test_damped_recoil_only_follows_real_foot_impact(self):
        for t in (0.,IMPACT_TIME-.01,IMPACT_TIME):
            self.assertEqual(organic_pose(t,interaction=True).recoil,0.)
        response=organic_pose(IMPACT_TIME+.17,interaction=True)
        self.assertGreater(response.recoil,.1)
        self.assertGreater(response.shoulder_drop,organic_pose(IMPACT_TIME+.17,
                          interaction=False).shoulder_drop)
        self.assertLess(organic_pose(IMPACT_TIME+3.,interaction=True).recoil,
                        response.recoil)
        self.assertEqual(organic_pose(IMPACT_TIME+.17,interaction=False).recoil,0.)
        self.assertIn("p38",VERSION)

    def test_actual_nonrigid_mesh_changes_body_pixels_and_is_deterministic(self):
        source=test_sprite(BODY_SIZE)
        at_rest=deform_body(source,organic_pose(.5,interaction=False))
        during_step=deform_body(source,organic_pose(1.0,interaction=False))
        self.assertEqual(at_rest.size,BODY_SIZE)
        self.assertEqual(at_rest.mode,"RGBA")
        self.assertIsNotNone(at_rest.getbbox())
        self.assertIsNotNone(ImageChops.difference(
            at_rest.convert("RGB"),during_step.convert("RGB")).getbbox())
        self.assertEqual(at_rest.tobytes(),
            deform_body(source,organic_pose(.5,interaction=False)).tobytes())
        # Source artwork stays immutable: deformation is a new physical image.
        self.assertEqual(source.getpixel((130,245)),(238,145,79,255))

    def test_inertial_tail_has_anchor_near_rump(self):
        original=test_sprite(TAIL_SIZE)
        before=deform_tail(original,organic_pose(.4))
        after=deform_tail(original,organic_pose(1.0))
        self.assertEqual(before.size,TAIL_SIZE)
        self.assertIsNotNone(
            ImageChops.difference(before.convert("RGB"),after.convert("RGB")).getbbox())
        anchor=(155,182)
        self.assertEqual(before.getpixel(anchor)[3],after.getpixel(anchor)[3])

    def test_actual_rig_has_same_world_foot_targets_during_recoil(self):
        t=IMPACT_TIME+.21
        expected={side:walking_leg(t,side=side,origin_x=195.,
                                  speed=44.,torso_y=915.,ground_y=GROUND)
                  for side in ("left","right")}
        self.assertTrue(expected["right"].planted)
        for kind in ("fox","rabbit","cat"):
            plate,meta=character_plate(t,kind=kind,interaction=True)
            self.assertEqual(plate.size,(1080,1920))
            self.assertEqual(meta["organicMesh"],VERSION)
            self.assertGreater(meta["physicalRecoil"],0)
            self.assertEqual(meta["expression"],"surprise")
            for side in ("left","right"):
                self.assertEqual(meta[side].foot,expected[side].foot)
                self.assertAlmostEqual(
                    math.dist(meta[side].hip,meta[side].knee),72.,places=6)
                self.assertAlmostEqual(
                    math.dist(meta[side].knee,meta[side].foot),72.,places=6)

    def test_invalid_clocks_and_sprite_inputs_fail_closed(self):
        for t in (math.inf,math.nan,-.1,7.21,True):
            with self.subTest(t=t),self.assertRaises(ValueError):
                organic_pose(t,interaction=True)
        with self.assertRaises(ValueError):
            organic_pose(.2,interaction="yes")
        with self.assertRaises(ValueError):
            deform_body(Image.new("RGB",BODY_SIZE),organic_pose(.3))
        with self.assertRaises(ValueError):
            deform_tail(Image.new("RGBA",BODY_SIZE),organic_pose(.3))
        with self.assertRaises(ValueError):
            deform_body(Image.new("RGBA",TAIL_SIZE),organic_pose(.3))


if __name__=="__main__":
    unittest.main()
