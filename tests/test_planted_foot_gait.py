"""Original walking and running feet alternate planted and airborne phases."""
import unittest
from automate_ytb.choreography import CHOREOGRAPHY_VERSION,leg_position


class PlantedFootGaitTests(unittest.TestCase):
    def test_walk_and_run_have_distinct_foot_phase_and_planted_stance(self):
        self.assertIn("v7",CHOREOGRAPHY_VERSION)
        for action in ("walk","run"):
            left=leg_position(action,side="left")
            right=leg_position(action,side="right")
            self.assertIn("max(0,-sin(",left[1])
            self.assertIn("max(0,-sin(",right[1])
            self.assertIn("3.141593",right[1])
            self.assertNotIn("3.141593",left[1])
            self.assertIn("335",left[1])
            self.assertEqual(left,leg_position(action,side="left"))
            self.assertNotIn(";",left[0]+left[1]+right[0]+right[1])

    def test_jumps_keep_existing_airborne_tuck(self):
        _,y=leg_position("jump",side="right")
        self.assertIn("mod(t,1.75)",y)
        self.assertNotIn("max(0,-sin(",y)
