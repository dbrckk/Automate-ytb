"""Action-driven foreground must move at real per-frame timestamps."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops

from automate_ytb.earth_kinetic_fx import draw_foreground


class KineticForegroundTests(unittest.TestCase):
    def test_every_action_is_deterministic_and_moves_in_the_actual_scene(self):
        for action in ("stop","inertia","wind","ocean","poles","day","astronaut"):
            with self.subTest(action=action):
                a=Image.new("RGBA",(1080,1920),(13,28,47,255))
                b=a.copy()
                repeat=a.copy()
                draw_foreground(a,action,.17,4.)
                draw_foreground(b,action,2.3,4.)
                draw_foreground(repeat,action,.17,4.)
                self.assertEqual(a.tobytes(),repeat.tobytes())
                changed=ImageChops.difference(a.convert("RGB"),b.convert("RGB"))
                self.assertIsNotNone(
                    changed.crop((20,600,1060,1490)).getbbox(),
                    f"Action {action} did not produce visible 30 fps geometry")

    def test_invalid_frames_fail_without_leaving_a_partial_render(self):
        frame=Image.new("RGBA",(1080,1920))
        for a,t,dur in (("fake",0,4),("ocean",-1,4),
                        ("wind",float("nan"),4),("stop",4.5,4),
                        ("astronaut",0,0)):
            with self.subTest(a=a,t=t,dur=dur),self.assertRaises(ValueError):
                draw_foreground(frame,a,t,dur)
        with self.assertRaises(ValueError):
            draw_foreground(Image.new("RGB",(1080,1920)),"wind",1,3)
        with self.assertRaises(ValueError):
            draw_foreground(Image.new("RGBA",(720,1280)),"wind",1,3)


if __name__=="__main__":
    unittest.main()
