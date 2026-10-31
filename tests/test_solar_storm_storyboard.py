"""Protect the actual six-scene Solar Storm release against wrong NASA imagery.

The script's production shot map is checked directly, with the actual NASA SVS
asset catalog. This is a semantic guard, not a fake rendering success.
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from production.solar_storm import render_short as solar


class ScientificShotMappingTests(unittest.TestCase):
    def test_actual_storyboard_uses_correct_science_video_sources(self):
        solar.validate_storyboard()
        self.assertEqual(len(solar.SHOT_PLAN), 6)
        self.assertEqual(sum(len(s) for s in solar.SHOT_PLAN), 13)
        self.assertTrue(any(key == "cme_launch" for key, _, _ in solar.SHOT_PLAN[2]))
        self.assertFalse(any(key == "magnetosphere" for key, _, _ in solar.SHOT_PLAN[2]))
        self.assertTrue(all(key == "magnetosphere" for key, _, _ in solar.SHOT_PLAN[3]))
        self.assertTrue(any(key == "aurora" for key, _, _ in solar.SHOT_PLAN[4]))
        self.assertIn("/a013003/CME.webm", solar.MEDIA["cme_launch"])
        self.assertIn("Earth_Only.mp4", solar.MEDIA["magnetosphere"])

    def test_previous_visual_mismatch_is_rejected(self):
        old_plan = [list(shot) for shot in solar.SHOT_PLAN]
        old_plan[2][1] = ("magnetosphere", 3.0, .51)
        with patch.object(solar, "SHOT_PLAN", old_plan):
            with self.assertRaisesRegex(ValueError, "Scientifically mismatched"):
                solar.validate_storyboard()

    def test_launch_visual_cannot_be_removed_or_replaced_by_another_sun_clip(self):
        altered = [list(s) for s in solar.SHOT_PLAN]
        altered[2][1] = ("sun171", 7.0, .51)
        with patch.object(solar, "SHOT_PLAN", altered):
            with self.assertRaisesRegex(ValueError, "Sun-origin CME"):
                solar.validate_storyboard()

    def test_satellite_impact_footage_must_match_spoken_effects(self):
        altered = [list(s) for s in solar.SHOT_PLAN]
        altered[4] = [("aurora", 9.0, .5), ("aurora", 21.0, .5)]
        with patch.object(solar, "SHOT_PLAN", altered):
            with self.assertRaisesRegex(ValueError, "both aurora and satellite"):
                solar.validate_storyboard()

    def test_nasa_catalog_and_roles_cannot_diverge(self):
        with patch.dict(solar.MEDIA, {"unreviewed": "https://example.invalid/foo.mp4"}):
            with self.assertRaisesRegex(ValueError, "role catalog"):
                solar.validate_storyboard()


if __name__ == "__main__":
    unittest.main()
