"""Character rendering stays original, repeatable, and distinct across scenes."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from automate_ytb.character_art import render_character_scene


class CharacterArtTests(unittest.TestCase):
    def test_consistent_output_for_same_scene_and_varied_between_scenes(self):
        with tempfile.TemporaryDirectory() as root:
            a, b, c = [Path(root) / f"{n}.png" for n in "abc"]
            args = dict(topic="La forêt mystérieuse",
                        narration="Une chouette traverse une forêt enchantée.",
                        scene_count=5, style="cartoon",
                        character="Original purple owl with round glasses")
            render_character_scene(**args, scene_index=1, destination=a)
            render_character_scene(**args, scene_index=1, destination=b)
            render_character_scene(**args, scene_index=2, destination=c)
            self.assertEqual(hashlib.sha256(a.read_bytes()).digest(),
                             hashlib.sha256(b.read_bytes()).digest())
            self.assertNotEqual(hashlib.sha256(a.read_bytes()).digest(),
                                hashlib.sha256(c.read_bytes()).digest())
            with Image.open(a) as image:
                self.assertEqual(image.size, (1280, 720))

    def test_rejects_invalid_style_or_missing_character(self):
        with tempfile.TemporaryDirectory() as root:
            kwargs = dict(topic="Test", narration="Une histoire originale.",
                          scene_index=1, scene_count=2,
                          character="Original owl", style="cartoon",
                          destination=Path(root) / "test.png")
            with self.assertRaises(ValueError):
                render_character_scene(**{**kwargs, "style": "unknown"})
            with self.assertRaises(ValueError):
                render_character_scene(**{**kwargs, "character": ""})


if __name__ == "__main__":
    unittest.main()
