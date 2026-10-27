"""Follow-through after original 2D jump impacts.

A short, bounded angular spring is a deliberate cartoon motion cue, not a
physical simulation. Regression tests include actual FFmpeg evaluation.
"""
from __future__ import annotations

import shutil
import subprocess
import unittest

from automate_ytb.joint_motion import (
    JOINT_VERSION, IMPACT_AMPLITUDES, landing_recoil, joint_angle)


class ImpactFollowthroughTests(unittest.TestCase):
    def test_recoil_only_activates_for_validated_jumps(self):
        self.assertIn("v3", JOINT_VERSION)
        self.assertEqual(set(IMPACT_AMPLITUDES), {"ear", "wing", "leg", "tail"})
        self.assertTrue(all(0 < amplitude < .12
                            for amplitude in IMPACT_AMPLITUDES.values()))
        for part in IMPACT_AMPLITUDES:
            for side in (("tail",) if part == "tail" else ("left", "right")):
                expr = landing_recoil("jump", part=part, side=side)
                self.assertEqual(expr, landing_recoil("jump", part=part, side=side))
                self.assertIn("mod(t,1.75)", expr)
                self.assertIn("1.39", expr)
                self.assertIn("exp(-9*", expr)
                self.assertIn("sin(26*", expr)
                self.assertNotIn(";", expr)
                self.assertEqual(landing_recoil("rest", part=part, side=side), "0")
                self.assertIn(expr, joint_angle("jump", part=part, side=side))
        self.assertNotEqual(landing_recoil("jump", part="ear", side="left"),
                            landing_recoil("jump", part="ear", side="right"))
        for invalid in (
                dict(action="unknown", part="wing", side="left"),
                dict(action="jump", part="wrong", side="left"),
                dict(action="jump", part="tail", side="left"),
                dict(action="jump", part="leg", side="tail")):
            with self.subTest(**invalid), self.assertRaises(ValueError):
                landing_recoil(**invalid)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required to validate real filter")
    def test_actual_ffmpeg_rotate_evaluates_spring_after_contact(self):
        # This evaluates every frame through the same FFmpeg rotate filter as
        # the rig, across the 1.39s contact cue. No external source media.
        expr = joint_angle("jump", part="ear", side="left")
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "color=c=yellow:s=64x64:r=24:d=1.85",
             "-vf", f"format=rgba,rotate=a='{expr}':ow=90:oh=90:c=none,format=yuv420p",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])


if __name__ == "__main__":
    unittest.main()
