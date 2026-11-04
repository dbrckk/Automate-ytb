"""Deterministic ocean depth, compositing and mobile-safe graphics regression."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops

from automate_ytb.science_ocean_depth import (
    PALETTES, SIZE, ORIGIN, draw_depth, lighting_plate,
)


class OceanDepthTests(unittest.TestCase):
    def test_five_distinct_cached_illustrated_lighting_schemes(self):
        self.assertEqual(len(PALETTES), 5)
        samples = []
        for beat in PALETTES:
            panel = lighting_plate(beat)
            self.assertEqual(panel.mode, "RGBA")
            self.assertEqual(panel.size, SIZE)
            self.assertIs(lighting_plate(beat), panel)
            self.assertEqual(panel.getpixel((0, 0))[3], 0)
            self.assertEqual(panel.getpixel((460, 440))[3], 255)
            samples.append(panel.getpixel((460, 440))[:3])
        self.assertEqual(len(set(samples)), 5)

    def test_animated_depth_does_not_touch_caption_or_header(self):
        a = Image.new("RGBA", (1080, 1920), (3, 12, 25, 255))
        b = a.copy()
        draw_depth(a, "sinking", t=1.5, duration=6.0)
        draw_depth(b, "sinking", t=4.5, duration=6.0)
        # A dim textured picture should cover the full stage but not any UI.
        self.assertNotEqual(a.getpixel((500, 1050)), (3, 12, 25, 255))
        self.assertEqual(a.getpixel((500, 400)), (3, 12, 25, 255))
        self.assertEqual(a.getpixel((500, 1650)), (3, 12, 25, 255))
        self.assertEqual(a.getpixel((50, 1000)), (3, 12, 25, 255))
        self.assertIsNotNone(ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox())

    def test_seek_is_deterministic_and_nonfinite_times_are_rejected(self):
        one = Image.new("RGBA", (1080, 1920), (2, 12, 18, 255))
        two = one.copy()
        draw_depth(one, "wind", t=2.0, duration=6.0)
        draw_depth(two, "wind", t=2.0, duration=6.0)
        self.assertEqual(one.tobytes(), two.tobytes())
        for kwargs in ({"t": float("nan"), "duration": 6.0},
                       {"t": -1, "duration": 6.0},
                       {"t": 7.0, "duration": 6.0},
                       {"t": 1, "duration": 0}):
            with self.assertRaises(ValueError):
                draw_depth(two, "wind", **kwargs)


if __name__ == "__main__":
    unittest.main()
