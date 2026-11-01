"""Causal rather than backdrop-only motion in original Earth-stop stories."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops

from automate_ytb.earth_story_actions import (
    ACTOR_BEATS, ALL_BEATS, action_state, draw_story_actions,
)


class EarthActingStoriesTests(unittest.TestCase):
    def setUp(self):
        self.blank = Image.new("RGBA", (1080, 1920), (8, 23, 42, 255))

    def test_each_story_actually_acts_not_just_pans(self):
        for beat in ACTOR_BEATS:
            with self.subTest(beat=beat):
                a, b = self.blank.copy(), self.blank.copy()
                draw_story_actions(a, beat, .2, 6)
                draw_story_actions(b, beat, 5.4, 6)
                diff = ImageChops.difference(
                    a.convert("RGB").crop((0, 650, 1080, 1460)),
                    b.convert("RGB").crop((0, 650, 1080, 1460)))
                self.assertIsNotNone(diff.getbbox())
                self.assertEqual(
                    a.crop((0, 0, 1080, 600)).tobytes(),
                    self.blank.crop((0, 0, 1080, 600)).tobytes(),
                    "Characters must leave fixed 9:16 title and labels intact")
                repeat = self.blank.copy()
                draw_story_actions(repeat, beat, .2, 6)
                self.assertEqual(a.tobytes(), repeat.tobytes(),
                                 "Scene motion must be deterministic")

    def test_car_really_reaches_cone_before_impact(self):
        first = action_state("inertia", 0, 6)
        middle = action_state("inertia", 3, 6)
        last = action_state("inertia", 6, 6)
        self.assertEqual(first["cone_flight"], 0)
        self.assertEqual(first["cone_x"], 529)
        self.assertGreater(last["cone_flight"], middle["cone_flight"])
        self.assertGreater(last["cone_x"], first["cone_x"])
        self.assertEqual(last["cone_flight"], 1)
        self.assertGreater(last["car_x"], first["car_x"])

    def test_people_brace_in_same_gust_and_float_follows_tide(self):
        wind_start = action_state("wind", 0, 6)
        wind_end = action_state("wind", 6, 6)
        self.assertGreater(wind_end["lean"], wind_start["lean"])
        self.assertGreater(wind_end["umbrella_bend"], wind_start["umbrella_bend"])
        ocean_start = action_state("ocean", 0, 6)
        ocean_end = action_state("ocean", 6, 6)
        self.assertGreater(ocean_start["sea_y"] - ocean_end["sea_y"], 250)
        for t in (0, .3, 1.5, 3.6, 6):
            state = action_state("ocean", t, 6)
            self.assertLess(abs(state["buoy_y"]-state["sea_y"]), 41)

    def test_non_actor_beats_unchanged_and_invalid_clock_rejected(self):
        for beat in ALL_BEATS - ACTOR_BEATS:
            with self.subTest(beat=beat):
                pic = self.blank.copy()
                draw_story_actions(pic, beat, .5, 4)
                self.assertEqual(pic.tobytes(), self.blank.tobytes())
        for args in [
            ("wind", float("nan"), 4), ("ocean", 2.1, 2),
            ("inertia", -1, 4), ("bad", 1, 4), ("wind", 1, 0),
            ("wind", 1, float("inf")),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                draw_story_actions(self.blank, *args)
        with self.assertRaises(ValueError):
            draw_story_actions(Image.new("RGB", (1080, 1920)),
                               "wind", .2, 4)


if __name__ == "__main__":
    unittest.main()
