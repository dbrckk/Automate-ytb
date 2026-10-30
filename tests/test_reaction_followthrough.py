"""Cinematic damping for a scripted surprise, never arbitrary FFmpeg syntax."""
import unittest

from automate_ytb.choreography import CHOREOGRAPHY_VERSION, body_position


class ReactionFollowThroughTests(unittest.TestCase):
    def test_surprise_has_two_damped_motion_frequencies(self):
        self.assertIn("v9", CHOREOGRAPHY_VERSION)
        x, y = body_position("surprise", x=180, y=184)
        for term in ("exp(-1.3*t)", "exp(-0.8*t)", "sin(t*3.1)"):
            self.assertIn(term, x)
        for term in ("exp(-1.1*t)", "exp(-1.8*t)", "sin(t*12)"):
            self.assertIn(term, y)
        self.assertNotIn(";", x + y)
        self.assertEqual((x, y), body_position("surprise", x=180, y=184))

    def test_other_actions_do_not_have_surprise_aftershocks(self):
        for action in ("idle", "walk", "run", "jump", "fly", "talk", "rest"):
            x, y = body_position(action, x=180, y=184)
            self.assertNotIn("exp(-0.8*t)", x + y)
            self.assertNotIn("exp(-1.8*t)", x + y)

if __name__ == "__main__":
    unittest.main()
