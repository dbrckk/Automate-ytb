"""Regression for the authored surprise reaction's damped follow-through."""
import unittest
from automate_ytb.choreography import CHOREOGRAPHY_VERSION, body_position

class ReactionFollowThroughTests(unittest.TestCase):
    def test_surprise_has_two_damped_motion_frequencies(self):
        self.assertIn("v6",CHOREOGRAPHY_VERSION)
        x,y=body_position("surprise",x=180,y=184)
        self.assertIn("exp(-1.3*t)",x)
        self.assertIn("exp(-0.8*t)",x)
        self.assertIn("exp(-1.1*t)",y)
        self.assertIn("exp(-1.8*t)",y)
        self.assertNotIn(";",x+y)
        self.assertEqual((x,y),body_position("surprise",x=180,y=184))
    def test_other_actions_unaffected(self):
        for action in ("idle","walk","run","jump","fly","talk","rest"):
            x,y=body_position(action,x=180,y=184)
            self.assertNotIn("exp(-0.8*t)",x+y)
