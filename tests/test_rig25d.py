"""Physics-backed regression tests for original 2.5D animal foot contacts."""
from __future__ import annotations

import math
import unittest

from PIL import ImageChops

from automate_ytb.rig25d import (
    solve_two_bone, walking_leg, GROUND, PERIOD, SUPPORT, UPPER, LOWER,
)
from automate_ytb.forest25d import (
    frame, character_plate, FPS, SIZE, SECONDS, ORIGIN_X, SPEED, TORSO_Y,
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
