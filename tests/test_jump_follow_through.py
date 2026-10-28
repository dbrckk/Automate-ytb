"""Secondary character parts track the same authored flight phase as the body."""
import unittest
from automate_ytb.choreography import secondary_position,body_position,CHOREOGRAPHY_VERSION


class JumpFollowThroughTests(unittest.TestCase):
    def test_jump_tail_and_wings_follow_body_flight(self):
        self.assertIn("v6",CHOREOGRAPHY_VERSION)
        _,body_y=body_position("jump",x=180,y=184)
        self.assertIn("mod(t,1.75)",body_y)
        for side in ("left","right","tail"):
            expression=secondary_position("jump",base=350,side=side)
            self.assertIn("mod(t,1.75)",expression)
            self.assertIn("1.39",expression)
            self.assertIn("exp(-9",expression)
            self.assertNotIn(";",expression)
            self.assertEqual(expression,secondary_position("jump",base=350,side=side))
        self.assertNotEqual(secondary_position("jump",base=350,side="left"),
                            secondary_position("jump",base=350,side="right"))

    def test_nonjump_follow_through_remains_unchanged(self):
        for action in ("walk","run","idle","rest","talk","fly"):
            expression=secondary_position(action,base=350,side="tail")
            self.assertEqual(expression.count("sin("),2)
            self.assertNotIn("mod(t,1.75)",expression)
