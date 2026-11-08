"""Physics-backed regression tests for original 2.5D animal foot contacts."""
from __future__ import annotations

import math
import unittest

from PIL import ImageChops

from automate_ytb.rig25d import (
    solve_two_bone, walking_leg, GROUND, PERIOD, SUPPORT, UPPER, LOWER,
)
from automate_ytb.forest25d import (
    frame, character_plate, FPS, SIZE, SECONDS, ORIGIN_X, SPEED, TORSO_Y, KINDS,
)


class GroundedTwoBoneTests(unittest.TestCase):
    def test_solver_maintains_exact_unstretched_bone_lengths(self):
        hip=(120.,220.)
        target=(145.,334.)
        for sign in (-1,1):
            knee=solve_two_bone(hip,target,UPPER,LOWER,bend=sign)
            self.assertAlmostEqual(math.dist(hip,knee),UPPER,places=6)
            self.assertAlmostEqual(math.dist(knee,target),LOWER,places=6)
        knee_a=solve_two_bone(hip,target,UPPER,LOWER,bend=1)
        knee_b=solve_two_bone(hip,target,UPPER,LOWER,bend=-1)
        self.assertNotEqual(knee_a,knee_b)

    def test_refuses_inaccessible_target_instead_of_teleporting_paw(self):
        for target in ((0.,0.),(1.,300.),(float("nan"), 40.)):
            with self.subTest(target=target), self.assertRaises(ValueError):
                solve_two_bone((0.,0.),target,UPPER,LOWER,bend=1)
        with self.assertRaises(ValueError):
            solve_two_bone((0.,0.),(0.,120.),72,72,bend=0)
        with self.assertRaises(ValueError):
            walking_leg(-.01,side="left",origin_x=195,speed=44,torso_y=915)

    def test_paw_is_world_locked_through_stance_even_as_body_advances(self):
        contacts=[]
        hips=[]
        for i in range(25):
            t=i/FPS
            paw=walking_leg(t,side="left",origin_x=ORIGIN_X,
                            speed=SPEED,torso_y=TORSO_Y)
            if paw.planted:
                contacts.append(paw.foot)
                hips.append(paw.hip)
        self.assertGreater(len(contacts),20)
        self.assertEqual(len(set(contacts)),1)
        self.assertGreater(hips[-1][0]-hips[0][0],20)

    def test_alternating_legs_have_real_ik_through_whole_cycle(self):
        both_grounded=0
        for i in range(round(PERIOD*FPS*3)):
            t=i/FPS
            poses=[walking_leg(t,side=side,origin_x=ORIGIN_X,
                               speed=SPEED,torso_y=TORSO_Y)
                   for side in ("left","right")]
            if all(p.planted for p in poses):
                both_grounded+=1
            for p in poses:
                self.assertLess(abs(math.dist(p.hip,p.knee)-UPPER),1e-6)
                self.assertLess(abs(math.dist(p.knee,p.foot)-LOWER),1e-6)
                if p.planted:
                    self.assertEqual(p.foot[1],GROUND)
                else:
                    self.assertLessEqual(p.foot[1],GROUND)
        self.assertGreater(both_grounded,0)

    def test_swing_reconnects_to_next_world_anchor_without_jump(self):
        t0=PERIOD*SUPPORT
        t1=PERIOD
        def pose(t):
            return walking_leg(t,side="left",origin_x=ORIGIN_X,
                               speed=SPEED,torso_y=TORSO_Y)
        before=pose(t0)
        just_after=pose(t0+.00001)
        just_before_landing=pose(t1-.00001)
        landing=pose(t1)
        self.assertLess(math.dist(before.foot,just_after.foot),.001)
        self.assertLess(math.dist(just_before_landing.foot,landing.foot),.001)
        self.assertEqual(before.foot[1],GROUND)
        self.assertEqual(landing.foot[1],GROUND)
        self.assertAlmostEqual(landing.foot[0]-before.foot[0],
                               SPEED*PERIOD,places=6)

    def test_original_species_share_ik_without_artwork_identity_leakage(self):
        self.assertEqual(KINDS,("fox","rabbit","cat"))
        signatures={}
        for kind in KINDS:
            with self.subTest(kind=kind):
                image,meta=character_plate(.7,kind=kind)
                self.assertEqual(image.size,SIZE)
                self.assertEqual(meta["kind"],kind)
                self.assertEqual(image.mode,"RGBA")
                for side in ("left","right"):
                    pose=meta[side]
                    self.assertLess(abs(math.dist(pose.hip,pose.knee)-UPPER),1e-6)
                    self.assertLess(abs(math.dist(pose.knee,pose.foot)-LOWER),1e-6)
                # Same grounded motion, but truly different original species art.
                signatures[kind]=image.crop((350,920,550,1240)).tobytes()
        self.assertEqual(len(set(signatures.values())),3)
        for invalid in ("owl","human","",None):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                character_plate(.7,kind=invalid)

    def test_rabbit_tail_is_small_and_attached_not_floating_disk(self):
        image,meta=character_plate(.7,kind="rabbit")
        x=round(meta["bodyX"])
        y=round(meta["bodyY"])
        # Old full-size rabbit disc occupied space ~70 px left of the
        # torso; the new authored tail overlaps the torso edge instead.
        self.assertEqual(image.getpixel((x-70,y+320))[3],0)
        self.assertGreater(image.getpixel((x+35,y+320))[3],0)

    def test_species_are_composited_into_actual_foreground_and_camera(self):
        for kind in ("rabbit","cat"):
            with self.subTest(kind=kind):
                first=frame(.3,kind=kind)
                later=frame(1.3,kind=kind)
                self.assertEqual(first.size,SIZE)
                self.assertIsNotNone(ImageChops.difference(first,later).getbbox())

    def test_actual_foreground_and_actor_change_across_real_frames(self):
        first=frame(.3)
        second=frame(2.8)
        self.assertEqual(first.size,SIZE)
        self.assertEqual(first.mode,"RGB")
        self.assertIsNotNone(ImageChops.difference(first,second).getbbox())
        p,meta=character_plate(1.2)
        self.assertEqual(p.size,SIZE)
        self.assertGreater(meta["bodyX"],ORIGIN_X)
        self.assertIn("left",meta)
        with self.assertRaises(ValueError):
            frame(SECONDS+.1)


if __name__=="__main__":
    unittest.main()
