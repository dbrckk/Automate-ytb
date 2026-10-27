"""The repeating jump must have no discontinuity at its cycle seam."""
import unittest
from automate_ytb.choreography import CHOREOGRAPHY_VERSION, body_position


class SeamlessJumpTests(unittest.TestCase):
    def test_jump_crouch_and_landing_cancel_at_cycle_boundary(self):
        self.assertIn("v6", CHOREOGRAPHY_VERSION)
        x,y=body_position("jump",x=180,y=184)
        self.assertIn("mod(t,1.75)",y)
        self.assertIn("0.18",y)
        self.assertIn("1.39",y)
        self.assertIn("12*(",y)
        self.assertIn(")-(",y)
        self.assertNotIn(";",x+y)
        self.assertEqual((x,y),body_position("jump",x=180,y=184))
