"""A second narrated forest animal has its own grounded contact shadow."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest
from PIL import Image

from automate_ytb.animated_forest import render_layers

DUO = "Le renard marche avec le lapin dans la forêt."
SOLO = "Le renard marche dans la forêt."
DIRECTION = {"weather": "day", "action": "walk", "emotion": "curious", "shot": "wide"}


def layers(path: Path, narration: str) -> dict[str, Path]:
    return render_layers(
        path,kind="fox",topic="Original paired walk",narration=narration,
        scene_index=1,scene_count=2,style="cartoon",
        direction=DIRECTION,landscape="forest")


class CompanionGroundTests(unittest.TestCase):
    def test_guest_shadow_only_when_second_actor_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pair=layers(root/"pair",DUO)
            alone=layers(root/"alone",SOLO)
            self.assertNotIn("companion_shadow",alone)
            self.assertIn("companion_shadow",pair)
            with Image.open(pair["companion_shadow"]) as shade:
                self.assertEqual(shade.mode,"RGBA")
                self.assertEqual(shade.size,(212,70))
                self.assertEqual(shade.getpixel((0,0))[3],0)
                self.assertGreater(shade.getpixel((106,35))[3],10)
                self.assertLess(shade.getpixel((106,35))[3],130)
            repeated=layers(root/"repeat",DUO)
            self.assertEqual(pair["companion_shadow"].read_bytes(),
                             repeated["companion_shadow"].read_bytes())

    def test_shadow_palette_respects_scene_weather(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            day=layers(root/"day",DUO)
            with Image.open(day["companion_shadow"]) as image:
                day_alpha=image.getpixel((106,35))[3]
            from automate_ytb.animated_forest import render_layers as render
            night=render(
                root/"night",kind="fox",topic="Original paired walk",
                narration=DUO,scene_index=1,scene_count=2,style="cartoon",
                direction={**DIRECTION,"weather":"night"},landscape="forest")
            with Image.open(night["companion_shadow"]) as image:
                night_alpha=image.getpixel((106,35))[3]
            self.assertGreater(day_alpha,night_alpha)


if __name__ == "__main__":
    unittest.main()
