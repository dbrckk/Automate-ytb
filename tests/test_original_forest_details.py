"""Original woodland detail: reproducible visual cues without hiding actors."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.scenic_world import draw_landscape_details, WORLD_VERSION


def forest_plate(*, seed: int, night: bool) -> Image.Image:
    picture = Image.new("RGB", (1280, 720), (8, 10, 15))
    draw_landscape_details(ImageDraw.Draw(picture),
                           kind="forest", night=night, seed=seed)
    return picture


class OriginalForestDetailsTests(unittest.TestCase):
    def test_deterministic_visual_layers_have_mobile_legible_footprint(self):
        self.assertIn("v2", WORLD_VERSION)
        first = forest_plate(seed=1137, night=False)
        second = forest_plate(seed=1137, night=False)
        self.assertEqual(first.tobytes(), second.tobytes())
        before = Image.new("RGB", first.size, (8, 10, 15))
        diff = ImageChops.difference(first, before)
        self.assertIsNotNone(diff.getbbox())
        # The central animal/shadow zone stays identical to the input plate.
        self.assertIsNone(diff.crop((0, 0, 600, 720)).getbbox())
        self.assertIsNotNone(diff.crop((700, 450, 1250, 710)).getbbox())
        # Ground details cover far more than a few scattered pixels.
        changed = sum(1 for value in diff.convert("L").crop(
            (700, 450, 1250, 710)).getdata() if value > 5)
        self.assertGreater(changed, 10000)

    def test_night_palette_and_seed_variation_are_distinct(self):
        day = forest_plate(seed=37, night=False)
        night = forest_plate(seed=37, night=True)
        another = forest_plate(seed=38, night=False)
        self.assertIsNotNone(ImageChops.difference(day, night).getbbox())
        self.assertIsNotNone(ImageChops.difference(day, another).getbbox())
        self.assertEqual(day.size, (1280, 720))
        self.assertEqual(day.mode, "RGB")

    def test_unknown_terrain_is_rejected(self):
        img = Image.new("RGB", (1280, 720))
        with self.assertRaises(ValueError):
            draw_landscape_details(ImageDraw.Draw(img), kind="castle",
                                   night=False, seed=1)


if __name__ == "__main__":
    unittest.main()
