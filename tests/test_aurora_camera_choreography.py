"""Prove continuous, stage-specific 3D camera motion without Blender imports."""
from __future__ import annotations

import math
import unittest

from automate_ytb.aurora_camera_choreography import (
    BEAT_CAMERA_KEYS, SAMPLE_COUNT, VERSION, evidence, pose,
)


class StoryDrivenCameraTests(unittest.TestCase):
    def test_all_five_original_action_scenes_have_distinct_real_camera_paths(self):
        self.assertEqual(
            set(BEAT_CAMERA_KEYS),
            {"solar_wind", "magnetic_field", "collisions", "emission", "curtains"},
        )
        self.assertIn("story-camera", VERSION)
        signature = set()
        for beat, keys in BEAT_CAMERA_KEYS.items():
            with self.subTest(beat=beat):
                self.assertEqual([k[0] for k in keys], [0., .44, 1.])
                start = pose(beat, 0.)
                middle = pose(beat, .44)
                end = pose(beat, 1.)
                self.assertEqual(start, (keys[0][1], keys[0][2]))
                self.assertEqual(middle, (keys[1][1], keys[1][2]))
                self.assertEqual(end, (keys[-1][1], keys[-1][2]))
                self.assertGreater(math.dist(start[0], end[0]), .6)
                self.assertGreater(math.dist(start[1], end[1]), .25)
                signature.add((start, middle, end))
                proof = evidence(beat)
                self.assertEqual(proof["cameraKeyframeCount"], 3)
                self.assertEqual(proof["cameraPathSampleCount"], SAMPLE_COUNT)
                self.assertGreaterEqual(proof["cameraTravelMilliunits"], 650)
                self.assertGreaterEqual(proof["cameraFocusTravelMilliunits"], 280)
        self.assertEqual(len(signature), len(BEAT_CAMERA_KEYS))

    def test_smooth_movement_has_no_midbeat_velocity_jump_or_whip(self):
        for beat in BEAT_CAMERA_KEYS:
            with self.subTest(beat=beat):
                path = [pose(beat, i/100) for i in range(101)]
                increments = [math.dist(a[0], b[0]) for a,b in zip(path, path[1:])]
                self.assertLess(max(increments), .15)
                # Real C1 continuity at the exact editorial action beat.
                left = pose(beat, .44 - .0001)
                mid = pose(beat, .44)
                right = pose(beat, .44 + .0001)
                for component in (0, 1):  # camera and focus
                    backwards = tuple(
                        (mid[component][i] - left[component][i])/.0001
                        for i in range(3))
                    forwards = tuple(
                        (right[component][i] - mid[component][i])/.0001
                        for i in range(3))
                    self.assertLess(math.dist(backwards, forwards), .025)
                self.assertEqual(pose(beat, .44), mid)

    def test_no_nonfinite_or_unbounded_unsafe_camera_values(self):
        for beat in BEAT_CAMERA_KEYS:
            for sample in range(101):
                camera, focus = pose(beat, sample/100)
                self.assertTrue(all(math.isfinite(n) for n in (*camera, *focus)))
                self.assertLess(camera[1], -7.5)
                self.assertGreater(camera[2], 2.5)
                self.assertLess(abs(camera[0]), 2)
                self.assertTrue(1 <= focus[2] <= 3.5)
                self.assertGreater(math.dist(camera, focus), 7)

    def test_invalid_action_clocks_fail_closed(self):
        for beat,q in (
            ("nonexistent", .5),
            ("curtains", -0.001),
            ("curtains", 1.1),
            ("curtains", float("nan")),
            ("curtains", float("inf")),
            ("curtains", True),
        ):
            with self.subTest(beat=beat,q=q), self.assertRaises(ValueError):
                pose(beat, q)
        with self.assertRaises(ValueError):
            evidence("incorrect")


if __name__ == "__main__":
    unittest.main()
