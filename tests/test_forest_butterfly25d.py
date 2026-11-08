"""Real causal butterfly interaction regression tests."""
import math
import unittest

from PIL import ImageChops

from automate_ytb.forest25d import frame, ORIGIN_X, SPEED, TORSO_Y
from automate_ytb.forest_contact25d import IMPACT_TIME, contact_at
from automate_ytb.forest_butterfly25d import butterfly_pose, butterfly_plate


def pose(t):
    return butterfly_pose(t,origin_x=ORIGIN_X,speed=SPEED,torso_y=TORSO_Y)


class Butterfly25DTests(unittest.TestCase):
    def test_strictly_no_response_before_real_paw_contact(self):
        for t in (0.,IMPACT_TIME-.01,IMPACT_TIME,IMPACT_TIME+.10):
            with self.subTest(t=t):
                p=pose(t)
                self.assertFalse(p.visible)
                self.assertEqual(p.phase,"waiting")
                self.assertIsNone(butterfly_plate(
                    t,origin_x=ORIGIN_X,speed=SPEED,
                    torso_y=TORSO_Y).getbbox())

    def test_causal_world_space_target_and_three_real_flight_phases(self):
        hit=contact_at(IMPACT_TIME+.5,origin_x=ORIGIN_X,
                       speed=SPEED,torso_y=TORSO_Y)
        self.assertTrue(hit.planted)
        approach=pose(IMPACT_TIME+.5)
        hover=pose(IMPACT_TIME+2.)
        retreat=pose(IMPACT_TIME+3.1)
        self.assertEqual((approach.phase,hover.phase,retreat.phase),
                         ("approach","hover","retreat"))
        self.assertTrue(all(p.visible for p in (approach,hover,retreat)))
        self.assertGreater(approach.x,hit.x+30)
        self.assertGreater(hover.x,hit.x+130)
        self.assertLess(hover.y,hit.y-195)
        self.assertGreater(retreat.x,hover.x+30)

    def test_flight_phases_have_no_positional_teleport(self):
        for t in (IMPACT_TIME+1.55,IMPACT_TIME+2.55):
            a,b=pose(t-.0001),pose(t+.0001)
            self.assertLess(math.hypot(a.x-b.x,a.y-b.y),2.)
        # The hover must clear the fox's face, not paint over its eyes.
        p=pose(IMPACT_TIME+2.15)
        self.assertGreater(p.x,contact_at(IMPACT_TIME+2.15,
            origin_x=ORIGIN_X,speed=SPEED,torso_y=TORSO_Y).x+175)

    def test_wings_move_in_real_independent_rgba_frames(self):
        a=butterfly_plate(IMPACT_TIME+.8,origin_x=ORIGIN_X,
                          speed=SPEED,torso_y=TORSO_Y)
        b=butterfly_plate(IMPACT_TIME+.8+1/30,origin_x=ORIGIN_X,
                          speed=SPEED,torso_y=TORSO_Y)
        self.assertEqual(a.mode,"RGBA")
        self.assertEqual(a.size,(1080,1920))
        self.assertIsNotNone(a.getbbox())
        self.assertGreater(a.getbbox()[2]-a.getbbox()[0],75)
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_interaction_switch_preserves_legacy_default(self):
        t=IMPACT_TIME+2.
        original=frame(t,kind="rabbit")
        enriched=frame(t,kind="rabbit",interaction=True)
        self.assertIsNotNone(ImageChops.difference(original,enriched).getbbox())
        self.assertEqual(original.size,enriched.size)

    def test_rejects_unbounded_or_nonfinite_clocks(self):
        for t in (math.nan,math.inf,-1.,7.21,True):
            with self.subTest(t=t),self.assertRaises(ValueError):
                pose(t)


if __name__=="__main__":
    unittest.main()
