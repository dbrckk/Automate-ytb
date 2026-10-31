"""Regression for world-locked original animal paws during walk and run."""
from __future__ import annotations
import unittest

from automate_ytb.choreography import leg_position, CHOREOGRAPHY_VERSION, LEG_MOTION
from automate_ytb.joint_motion import joint_angle, JOINT_VERSION


class FootContactGaitTests(unittest.TestCase):
    def test_paws_are_world_locked_during_contact_and_alternate(self):
        self.assertIn("v9", CHOREOGRAPHY_VERSION)
        self.assertIn("v4", JOINT_VERSION)
        for action in ("walk", "run"):
            reach, lift, frequency = LEG_MOTION[action]
            for side, phase in (("left", "0"), ("right", "3.141593")):
                with self.subTest(action=action, side=side):
                    x, y = leg_position(action, side=side)
                    swing = f"max(0,-sin(t*{frequency}+{phase}))"
                    eased = f"({swing})*({swing})*(3-2*({swing}))"
                    self.assertIn(eased, x)
                    self.assertIn(eased, y)
                    self.assertIn(str(reach), x)
                    self.assertIn(str(lift), y)
                    # The planted contact cannot inherit periodic body bob
                    # or the independently oscillating torso translation.
                    self.assertNotIn("1.2*sin(t*0.37)", x)
                    self.assertNotIn("abs(sin(", y)
                    self.assertNotIn("1.3*sin(t*0.41)", y)
                    self.assertEqual((x, y), leg_position(action, side=side))
                    angle = joint_angle(action, part="leg", side=side)
                    self.assertIn("pow(max(0,-sin(", angle)
                    self.assertIn(f"+{float(phase):.6f}", angle)
                    self.assertNotIn(";", x+y+angle)

    def test_other_actions_retain_their_original_rigs(self):
        for action in ("idle", "talk", "rest", "jump", "fly", "surprise"):
            x, y = leg_position(action, side="left")
            self.assertNotIn("pow(max(0,-sin(", x+y)
            self.assertNotIn("pow(max(0,-sin(", joint_angle(action, part="leg", side="left"))

    def test_input_validation_is_unchanged(self):
        for invalid_action in ("walk;movie=/etc/passwd", "slide"):
            with self.assertRaises(ValueError):
                leg_position(invalid_action, side="left")
            with self.assertRaises(ValueError):
                joint_angle(invalid_action, part="leg", side="left")
        with self.assertRaises(ValueError):
            leg_position("walk", side="tail")


if __name__ == "__main__":
    unittest.main()
