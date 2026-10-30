"""Regression of periodic original-character jump motion.

Evaluate only expressions emitted by the trusted choreography module.
No user-provided expressions are accepted.
"""
from __future__ import annotations

import math
import unittest

from automate_ytb.choreography import CHOREOGRAPHY_VERSION, body_position


def evaluate_trusted_expression(expr: str, time_s: float) -> float:
    safe = {
        "t": time_s,
        "mod": lambda a, b: a % b,
        "sin": math.sin,
        "abs": abs,
        "min": min,
        "max": max,
        "exp": math.exp,
    }
    return float(eval(expr, {"__builtins__": {}}, safe))


class ContinuousJumpTests(unittest.TestCase):
    def test_jump_returns_to_ground_without_boundary_teleport(self):
        self.assertIn("v9", CHOREOGRAPHY_VERSION)
        x, y = body_position("jump", x=180, y=184)
        self.assertIn("mod(t,1.75)", y)
        self.assertNotIn(";", x + y)
        for edge in (0.0, 1.75, 3.5, 5.25):
            self.assertAlmostEqual(evaluate_trusted_expression(y, edge), 184, places=6)
            left = evaluate_trusted_expression(y, edge - 0.001)
            right = evaluate_trusted_expression(y, edge + 0.001)
            self.assertLess(abs(left - right), 0.05)
        self.assertGreater(evaluate_trusted_expression(y, 0.18), 190)
        self.assertLess(evaluate_trusted_expression(y, 0.60), 140)
        self.assertGreater(evaluate_trusted_expression(y, 1.40), 184)

    def test_jump_stays_finite_and_bounded_across_repetitions(self):
        _, expression = body_position("jump", x=180, y=184)
        values = [evaluate_trusted_expression(expression, i / 60) for i in range(420)]
        self.assertTrue(all(math.isfinite(v) for v in values))
        self.assertGreater(min(values), 90)
        self.assertLess(max(values), 200)

    def test_other_actions_do_not_inherit_jump_cycle(self):
        for action in ("idle", "walk", "run", "fly", "talk", "surprise", "rest"):
            self.assertNotIn("mod(t,1.75)", body_position(action, x=180, y=184)[1])


if __name__ == "__main__":
    unittest.main()
