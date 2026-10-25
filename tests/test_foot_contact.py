"""Grounded walk/run gait: stance phase and alternating lifted swing."""
import unittest
from automate_ytb.choreography import leg_position, CHOREOGRAPHY_VERSION


class FootContactTests(unittest.TestCase):
    def test_walk_and_run_ground_contact_and_counterphase(self):
        self.assertIn("v3", CHOREOGRAPHY_VERSION)
        for action in ("walk","run"):
            left=leg_position(action,side="left")
            right=leg_position(action,side="right")
            for x,y in (left,right):
                self.assertIn("cos(",x)
                self.assertIn("max(0,-sin(",y)
                self.assertNotIn(";",x+y)
                self.assertIn("+335-",y)
            self.assertNotEqual(left,right)
            self.assertIn("3.141593",right[1])

    def test_existing_jump_and_idle_remain_valid(self):
        for action in ("jump","rest","idle","talk","fly","surprise"):
            x,y=leg_position(action,side="left")
            self.assertIn("sin(",x+y)
            self.assertNotIn("max(0,-sin(",y)
        with self.assertRaises(ValueError):
            leg_position("unknown",side="left")
