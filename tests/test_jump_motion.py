"""Physical beats for authored 2D jumps, without external rig dependencies."""
import unittest
from automate_ytb.choreography import CHOREOGRAPHY_VERSION,body_position,leg_position


class JumpMotionTests(unittest.TestCase):
    def test_jump_is_phased_and_reproducible(self):
        self.assertIn("v6",CHOREOGRAPHY_VERSION)
        x,y=body_position("jump",x=180,y=184)
        self.assertIn("mod(t,1.75)",y)
        self.assertIn("0.18",y)
        self.assertIn("0.75",y)
        self.assertIn("1.39",y)
        self.assertEqual((x,y),body_position("jump",x=180,y=184))
        self.assertNotIn(";",x+y)
        for side in ("left","right"):
            fx,fy=leg_position("jump",side=side)
            self.assertIn("mod(t,1.75)",fy)
            self.assertIn("335",fy)
            self.assertNotIn(";",fx+fy)

    def test_other_actions_do_not_inherit_jump_sequence(self):
        for action in ("walk","rest","run","fly"):
            _,y=body_position(action,x=180,y=184)
            self.assertNotIn("mod(t,1.75)",y)
