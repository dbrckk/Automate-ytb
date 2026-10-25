"""Organic secondary animation stays deterministic and reviewable."""
import unittest
from automate_ytb.choreography import body_position, secondary_position, CHOREOGRAPHY_VERSION
from automate_ytb.director import ACTIONS


class OrganicAnimationTests(unittest.TestCase):
    def test_all_actions_have_repeatable_secondary_sway(self):
        self.assertIn("v3", CHOREOGRAPHY_VERSION)
        for action in ACTIONS:
            a=secondary_position(action,base=357,side="tail")
            self.assertEqual(a,secondary_position(action,base=357,side="tail"))
            self.assertEqual(a.count("sin("),2)
            self.assertNotIn(";",a)
            self.assertIn("0.35",a)
        self.assertNotEqual(secondary_position("run",base=357,side="tail"),
                            secondary_position("rest",base=357,side="tail"))

    def test_breathing_is_quasiperiodic_and_bounded_by_constants(self):
        for action in ("idle","rest","talk"):
            x,y=body_position(action,x=180,y=184)
            self.assertIn("1.2*sin(t*0.37)",x)
            self.assertIn("1.3*sin(t*0.41)",y)
            self.assertNotIn("movie=",x+y)
        with self.assertRaises(ValueError):
            secondary_position("untrusted",base=357,side="tail")
