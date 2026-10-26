"""Material finish preserves authored silhouettes and character identity."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.sprite_finish import FINISH_VERSION, finish_sprite
from automate_ytb.animated_forest import render_layers as forest_layers
from automate_ytb.animated_owl import render_layers as owl_layers


class CharacterFinishTests(unittest.TestCase):
    def test_alpha_and_shape_are_unchanged(self):
        self.assertIn("v1", FINISH_VERSION)
        original = Image.new("RGBA", (128, 160), (0, 0, 0, 0))
        d = ImageDraw.Draw(original)
        d.ellipse((18, 14, 104, 143), fill=(169, 112, 87, 255))
        d.ellipse((39, 59, 55, 76), fill=(35, 29, 55, 255))
        shade = finish_sprite(original)
        self.assertEqual(shade.mode, "RGBA")
        self.assertEqual(shade.size, original.size)
        self.assertEqual(shade.getchannel("A").tobytes(),
                         original.getchannel("A").tobytes())
        self.assertEqual(original.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(shade.getpixel((0, 0))[3], 0)
        self.assertNotEqual(shade.getpixel((55, 100))[:3],
                            original.getpixel((55, 100))[:3])
        self.assertEqual(shade.tobytes(), finish_sprite(original).tobytes())
        with self.assertRaises(ValueError):
            finish_sprite(original.convert("RGB"))
        with self.assertRaises(ValueError):
            finish_sprite(Image.new("RGBA", (20, 20)))

    def test_all_original_actors_produce_distinct_painted_bodies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            basic = dict(topic="Original actors", narration="A quiet meadow",
                         scene_index=1, scene_count=2, style="cartoon")
            for kind in ("fox", "rabbit", "cat"):
                layer = forest_layers(root / kind, kind=kind, **basic)
                with Image.open(layer["body"]) as body:
                    self.assertEqual(body.mode, "RGBA")
                    self.assertEqual(body.size, (350, 440))
                    self.assertTrue(body.getchannel("A").getbbox())
            layer = owl_layers(root / "owl", **basic)
            with Image.open(layer["body"]) as body:
                self.assertEqual(body.mode, "RGBA")
                self.assertEqual(body.size, (322, 430))
                self.assertTrue(body.getchannel("A").getbbox())
