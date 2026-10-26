"""Independent head-attention motion primitive regression."""
import unittest
from automate_ytb.choreography import attention_offset
from automate_ytb.director import ACTIONS


class AttentionOffsetTests(unittest.TestCase):
    def test_all_actions_are_bounded_and_repeatable(self):
        for action in ACTIONS:
            x,y=attention_offset(action,scene_index=1)
            self.assertEqual((x,y),attention_offset(action,scene_index=1))
            self.assertIn("sin(t*0.53)",x)
            self.assertIn("sin(t*0.39)",y)
            self.assertNotIn(";",x+y)
            self.assertNotIn("movie",x+y)
        self.assertNotEqual(attention_offset("surprise",scene_index=1),
                            attention_offset("rest",scene_index=1))
        self.assertNotEqual(attention_offset("idle",scene_index=1),
                            attention_offset("idle",scene_index=2))

    def test_rejects_untrusted_action_or_index(self):
        for bad in (0,-1,1201,True,1.1):
            with self.assertRaises(ValueError):
                attention_offset("idle",scene_index=bad)
        with self.assertRaises(ValueError):
            attention_offset("run;movie=/etc/passwd",scene_index=1)
