"""Periodic secondary acting must follow the *same* original jump beats.

Expressions are generated only by trusted fixed choreography; this test never
evaluates user-supplied text or arbitrary filter graphs.
"""
from __future__ import annotations

import math
import unittest

from automate_ytb.choreography import (
    CHOREOGRAPHY_VERSION, body_position, secondary_position,
)


def evaluate_trusted(expression: str, time_seconds: float) -> float:
    return float(eval(expression, {"__builtins__": {}}, {
        "t": time_seconds,
        "mod": lambda x, y: x % y,
        "sin": math.sin,
        "min": min,
        "max": max,
    }))


class JumpSecondaryFollowThroughTests(unittest.TestCase):
    def test_secondary_parts_track_original_body_flight_cycle(self):
        self.assertIn("v10", CHOREOGRAPHY_VERSION)
        _, body_y = body_position("jump", x=180, y=184)
        self.assertIn("mod(t,1.75)", body_y)
        for side in ("left", "right", "tail"):
            expression = secondary_position("jump", base=350, side=side)
            self.assertIn("mod(t,1.75)", expression)
            self.assertIn("1.39", expression)
            self.assertNotIn(";", expression)
            self.assertEqual(
                expression, secondary_position("jump", base=350, side=side))
            for boundary in (0.0, 1.75, 3.50):
                at = evaluate_trusted(expression, boundary)
                before = evaluate_trusted(expression, boundary - .001)
                after = evaluate_trusted(expression, boundary + .001)
                self.assertAlmostEqual(at, 350.0, places=6)
                self.assertLess(abs(before - after), 0.2)

    def test_left_right_reactions_are_opposed_and_follow_airborne_arc(self):
        left = secondary_position("jump", base=350, side="left")
        right = secondary_position("jump", base=350, side="right")
        tail = secondary_position("jump", base=350, side="tail")
        for t in (.18, .45, .75, 1.02, 1.39, 1.58):
            a = evaluate_trusted(left, t) - 350
            b = evaluate_trusted(right, t) - 350
            c = evaluate_trusted(tail, t) - 350
            self.assertAlmostEqual(a, -b, places=5)
            self.assertAlmostEqual(a, c, places=5)
            self.assertTrue(all(math.isfinite(v) for v in (a, b, c)))
            self.assertLessEqual(abs(a), 70)
        self.assertGreater(evaluate_trusted(left, .65), 355)
        self.assertLess(evaluate_trusted(right, .65), 345)
        # The character returns to its original pose before the next jump.
        self.assertAlmostEqual(evaluate_trusted(left, 1.75), 350, places=6)

    def test_no_change_to_existing_non_jump_secondary_actions(self):
        for action in ("idle", "walk", "run", "fly", "talk", "surprise", "rest"):
            for side in ("left", "right", "tail"):
                expression = secondary_position(action, base=350, side=side)
                self.assertNotIn("mod(t,1.75)", expression)
                self.assertIn("0.35", expression)
                self.assertEqual(expression.count("sin("), 2)


if __name__ == "__main__":
    unittest.main()
