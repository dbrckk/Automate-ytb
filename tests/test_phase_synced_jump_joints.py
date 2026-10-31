"""Flight-synchronized original joint rotations: numeric evidence, no outside assets.

The restricted evaluator below receives only deterministic strings emitted by
the trusted fixed joint_motion module, never user-authored expressions.
"""
from __future__ import annotations

import math
import unittest

from automate_ytb.joint_motion import (
    JOINT_VERSION, joint_angle, landing_recoil, AMPLITUDES,
)


def evaluate_trusted(expression: str, t: float) -> float:
    return float(eval(expression, {"__builtins__": {}}, {
        "t": t, "mod": lambda a, b: a % b,
        "sin": math.sin, "exp": math.exp, "pow": pow,
        "min": min, "max": max,
    }))


class PhaseSynchronizedJumpJointsTests(unittest.TestCase):
    def test_all_joints_reset_without_cycle_boundary_snap(self):
        self.assertIn("v5", JOINT_VERSION)
        for part in ("wing", "leg", "tail", "ear"):
            for side in (("tail",) if part == "tail" else ("left", "right")):
                with self.subTest(part=part, side=side):
                    expression = joint_angle("jump", part=part, side=side)
                    self.assertIn("mod(t,1.75)", expression)
                    self.assertNotIn(";", expression)
                    for edge in (0, 1.75, 3.50):
                        self.assertAlmostEqual(
                            evaluate_trusted(expression, edge), 0, places=6)
                        before = evaluate_trusted(expression, edge - .001)
                        after = evaluate_trusted(expression, edge + .001)
                        self.assertLess(abs(before-after), .005)
                    angles = [
                        evaluate_trusted(expression, j / 60)
                        for j in range(0, 420)
                    ]
                    self.assertTrue(all(math.isfinite(v) for v in angles))
                    self.assertLess(max(abs(v) for v in angles), 0.30)

    def test_antipodal_side_and_attached_flight_rotation(self):
        left = joint_angle("jump", part="wing", side="left")
        right = joint_angle("jump", part="wing", side="right")
        for t in (.07, .41, .72, 1.10, 1.49):
            self.assertAlmostEqual(
                evaluate_trusted(left, t),
                -evaluate_trusted(right, t), places=5)
        self.assertLess(evaluate_trusted(left, .10), 0)
        self.assertGreater(evaluate_trusted(left, .60), 0)
        self.assertAlmostEqual(evaluate_trusted(left, 1.75), 0, places=6)

    def test_landing_pulse_is_compact_and_non_jump_unchanged(self):
        for part in ("wing", "leg", "tail", "ear"):
            for side in (("tail",) if part == "tail" else ("left", "right")):
                impact = landing_recoil("jump", part=part, side=side)
                self.assertIn("mod(t,1.75)", impact)
                self.assertAlmostEqual(evaluate_trusted(impact, 1.39), 0)
                self.assertAlmostEqual(evaluate_trusted(impact, 1.75), 0)
                self.assertGreater(
                    abs(evaluate_trusted(impact, 1.48)), .00001)
                self.assertEqual(
                    landing_recoil("walk", part=part, side=side), "0")
                for action in ("idle", "walk", "run", "fly", "talk", "rest"):
                    non_jump = joint_angle(action, part=part, side=side)
                    self.assertNotIn("mod(t,1.75)", non_jump)
                self.assertLessEqual(AMPLITUDES[part]["jump"], .25)


if __name__ == "__main__":
    unittest.main()
