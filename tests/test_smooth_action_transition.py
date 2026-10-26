"""Interpolated gesture changes keep zero end velocity at each boundary."""
import unittest
from automate_ytb.action_timeline import _weight, choreograph, TIMELINE_VERSION


class SmoothActionTransitionTests(unittest.TestCase):
    def test_smoothstep_weight_is_bounded_and_reproducible(self):
        value=_weight(1.5)
        self.assertIn("v3",TIMELINE_VERSION)
        self.assertIn("min(1,max(0",value)
        self.assertIn("3-2*",value)
        self.assertEqual(value,_weight(1.5))
        self.assertNotIn(";",value)

    def test_multiple_action_interpolation_preserves_trusted_paths(self):
        result=choreograph("The fox walks, then jumps.",duration=4.0,
             fallback_action="walk",
             pose=lambda action: (("100" if action=="walk" else "300"),))
        self.assertEqual(len(result),1)
        self.assertIn("3-2*",result[0])
        self.assertIn("100",result[0])
        self.assertIn("300",result[0])
