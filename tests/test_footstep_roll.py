"""Ground-contact paw travel uses smoothstep and remains safe."""
import unittest
from automate_ytb.choreography import CHOREOGRAPHY_VERSION,leg_position


class FootstepRollTests(unittest.TestCase):
    def test_ground_contact_and_eased_swing(self):
        self.assertIn("v8",CHOREOGRAPHY_VERSION)
        for action in ("walk","run"):
            left=leg_position(action,side="left")
            right=leg_position(action,side="right")
            for x,y in (left,right):
                self.assertIn("max(0,-sin(",x)
                self.assertIn("3-2*",x)
                self.assertNotIn(";",x+y)
                self.assertNotIn("t*0.37",x+y)
            self.assertNotEqual(left,right)

    def test_jump_not_modified(self):
        x,y=leg_position("jump",side="left")
        self.assertIn("mod(t,1.75)",y)
