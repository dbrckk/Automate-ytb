"""Terrain is actual lit projected geometry, safe and deterministic."""
import math
import unittest

from PIL import Image

from automate_ytb.science_volcano_mesh import (
    SIZE, CONE_OUTLINE, TERRAIN_VERSION, RINGS, SEGMENTS,
    height_at, project, shaded_terrain,
)


class ShadedVolcanoTests(unittest.TestCase):
    def test_depressed_crater_and_eroded_irregular_slopes(self):
        self.assertIn("heightfield", TERRAIN_VERSION)
        self.assertGreaterEqual(len(RINGS), 18)
        self.assertGreaterEqual(SEGMENTS, 48)
        self.assertGreater(height_at(65, 0), height_at(0, 0) + 70)
        self.assertGreater(height_at(140, 0), height_at(350, 0))
        self.assertNotEqual(height_at(350, .1), height_at(350, 1.3))
        for value in (-1, 521, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                height_at(value, 0)
        with self.assertRaises(ValueError):
            project(0, float("nan"), 0)

    def test_camera_projection_summit_and_base(self):
        self.assertEqual(SIZE, (1080, 1380))
        _, high = project(0, 0, height_at(65, 0))
        _, base = project(0, 0, height_at(520, 0))
        self.assertLess(high, 365)
        self.assertGreater(base, 1040)
        self.assertGreater(len(CONE_OUTLINE), 10)

    def test_cached_mesh_clipping_materials(self):
        stage = shaded_terrain()
        self.assertIs(stage, shaded_terrain())
        self.assertEqual(stage.mode, "RGBA")
        self.assertEqual(stage.size, SIZE)
        self.assertEqual(stage.getpixel((2, 200))[3], 0)
        self.assertEqual(stage.getpixel((540, 1180))[3], 0)
        self.assertGreater(stage.getpixel((540, 620))[3], 100)
        shades = {stage.getpixel((x, y))[:3] for x in range(380, 701, 35)
                  for y in range(580, 850, 38)
                  if stage.getpixel((x, y))[3] > 0}
        self.assertGreater(len(shades), 16)
        rgba = stage.getchannel("A").getextrema()
        self.assertEqual(rgba, (0, 255))
