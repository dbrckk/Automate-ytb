"""Actual antialiased animal sprites, deterministic RGBA output and safe dimensions."""
from __future__ import annotations
import tempfile
from pathlib import Path
import unittest
from PIL import Image

from automate_ytb.sprite_supersampling import (
    RENDER_SCALE, SPRITE_RENDER_VERSION, sprite_canvas, resolve_sprite)
from automate_ytb.animated_forest import (
    _sprite_body, _sprite_tail, _sprite_leg, _sprite_ear, _sprite_mouth)
from automate_ytb.animated_owl import (
    _body as owl_body, _wing as owl_wing, _mouth as owl_mouth)


class SupersampledAnimalTests(unittest.TestCase):
    def test_subpixel_edges_and_deterministic_reconstruction(self):
        self.assertEqual(RENDER_SCALE, 2)
        self.assertIn("lanczos", SPRITE_RENDER_VERSION)
        canvas, paint = sprite_canvas((96, 96))
        self.assertEqual(canvas.size, (192, 192))
        paint.ellipse((11, 11, 85, 85), fill=(249, 170, 75, 255),
                      outline=(28, 39, 70, 255), width=3)
        image = resolve_sprite(canvas, (96, 96))
        self.assertEqual(image.getpixel((0, 0))[3], 0)
        alphas = image.getchannel("A").histogram()
        self.assertGreater(sum(alphas[1:255]), 80)
        self.assertEqual(image.size, (96, 96))
        self.assertEqual(image.mode, "RGBA")
        with self.assertRaises(ValueError):
            resolve_sprite(canvas, (350, 440))
        with self.assertRaises(ValueError):
            sprite_canvas((25000, 12000))

    def test_sprite_geometry_and_colors_survive_resolution_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for kind in ("fox", "rabbit", "cat"):
                assets = [
                    ("body", (350, 440), lambda f: _sprite_body(
                        f, kind=kind, blink=False, emotion="happy")),
                    ("tail", (230, 240), lambda f: _sprite_tail(f, kind=kind)),
                    ("leg", (100, 125), lambda f: _sprite_leg(
                        f, kind=kind, side="left")),
                    ("ear", (150, 240), lambda f: _sprite_ear(
                        f, kind=kind, side="right")),
                    ("mouth", (350, 440), lambda f: _sprite_mouth(f, kind=kind)),
                ]
                for name, size, render in assets:
                    with self.subTest(kind=kind, sprite=name):
                        a = root / f"{kind}-{name}-a.png"
                        b = root / f"{kind}-{name}-b.png"
                        render(a)
                        render(b)
                        self.assertEqual(a.read_bytes(), b.read_bytes())
                        with Image.open(a) as sprite:
                            self.assertEqual(sprite.size, size)
                            self.assertEqual(sprite.mode, "RGBA")
                            self.assertIsNotNone(sprite.getchannel("A").getbbox())

    def test_owl_pose_and_speech_are_antialiased(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parts = (
                (owl_body, {"blink": False, "emotion": "curious"}, (322, 430)),
                (owl_wing, {"right": True}, (164, 212)),
                (owl_mouth, {}, (322, 430)),
            )
            for i, (render, kwargs, size) in enumerate(parts):
                path = root / f"owl-{i}.png"
                render(path, **kwargs)
                with Image.open(path) as im:
                    self.assertEqual(im.size, size)
                    self.assertEqual(im.mode, "RGBA")
                    self.assertIsNotNone(im.getchannel("A").getbbox())


if __name__ == "__main__":
    unittest.main()
