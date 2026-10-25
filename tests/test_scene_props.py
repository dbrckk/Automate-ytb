"""Script-grounded original prop art and real FFmpeg pickup/obstacle tests."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_forest import (
    render_motion_clip as forest_video,
    render_character_poster as forest_poster)
from automate_ytb.animated_owl import (
    render_motion_clip as owl_video,
    render_character_poster as owl_poster)
from automate_ytb.scene_props import (
    PROP_VERSION, select_interaction, draw_prop, draw_reach,
    create_layers, append_overlays)


def _frame(file: Path, time: float) -> Image.Image:
    res = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(time),
         "-i", str(file), "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        check=True, capture_output=True, timeout=90)
    with Image.open(io.BytesIO(res.stdout)) as src:
        return src.convert("RGB")


def _change(a: Image.Image, b: Image.Image, box: tuple) -> float:
    delta = ImageChops.difference(a.crop(box), b.crop(box))
    return sum(ImageStat.Stat(delta).mean)


class ScriptedScenePropTests(unittest.TestCase):
    def test_grounded_detection_supports_two_languages_without_inventing_objects(self):
        cases = {
            "Le renard ramasse une pomme rouge.": ("apple", "pickup"),
            "The rabbit picks up an old book.": ("book", "pickup"),
            "La chouette regarde une fleur.": ("flower", "inspect"),
            "The cat watches a flower in the meadow.": ("flower", "inspect"),
            "Le lapin saute par-dessus la pierre.": ("stone", "obstacle"),
            "The fox jumps over a rock.": ("stone", "obstacle"),
            "La chouette cueille une fleur.": ("flower", "pickup"),
            "The owl finds a book.": ("book", "inspect"),
        }
        for phrase, (prop, action) in cases.items():
            with self.subTest(phrase=phrase):
                cue = select_interaction(phrase)
                self.assertIsNotNone(cue)
                self.assertEqual((cue["prop"], cue["action"]), (prop, action))
                self.assertEqual(cue["version"], PROP_VERSION)
        for sentence in (
            "Le renard court dans la forêt sans objet.",
            "A book lies on the floor.",
            "An apple appears in the background.",
            "The owl observes the moon.",
            "La saison des pommes commence.",
        ):
            with self.subTest(sentence=sentence):
                self.assertIsNone(select_interaction(sentence))
        with self.assertRaises(ValueError):
            select_interaction(None)

    def test_original_prop_sprites_are_transparent_and_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for name in ("apple", "flower", "book", "stone"):
                first, second = folder / f"{name}1.png", folder / f"{name}2.png"
                draw_prop(first, kind=name)
                draw_prop(second, kind=name)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                with Image.open(first) as src:
                    self.assertEqual(src.mode, "RGBA")
                    self.assertEqual(src.size, (138, 138))
                    self.assertIsNotNone(src.getchannel("A").getbbox())
                    self.assertEqual(src.getpixel((0, 0))[3], 0)
            with self.assertRaises(ValueError):
                draw_prop(folder / "bad.png", kind="unknown")
            for actor in ("fox", "rabbit", "cat", "owl"):
                hand = folder / f"reach-{actor}.png"
                draw_reach(hand, actor=actor)
                with Image.open(hand) as image:
                    self.assertEqual(image.size, (120, 96))
                    self.assertGreater(image.getpixel((95, 40))[3], 0)
            with self.assertRaises(ValueError):
                draw_reach(folder / "illegal.png", actor="real-person")

    def test_scene_generates_only_props_explicitly_used(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertIsNone(create_layers(
                root, narration="A cat explores the garden.", actor="cat"))
            self.assertEqual(list(root.iterdir()), [])
            inspect = create_layers(
                root, narration="The cat observes a flower.", actor="cat")
            self.assertEqual(inspect["action"], "inspect")
            self.assertTrue((root / "prop.png").is_file())
            self.assertFalse((root / "reach.png").exists())
            pickup = create_layers(
                root, narration="The cat picks up a flower.", actor="cat")
            self.assertEqual(pickup["action"], "pickup")
            self.assertTrue((root / "reach.png").is_file())

    def test_overlay_graph_preserves_no_prop_paths_and_input_integrity(self):
        graph, label, names = append_overlays(
            graph="base", label="f",
            names=["background", "tail"], narration="A fox sleeps.",
            duration=3, body_x="180", body_y="184")
        self.assertEqual((graph, label, names), ("base", "f", ["background", "tail"]))
        graph, label, names = append_overlays(
            graph="base", label="f", names=["background", "tail"],
            narration="The fox picks up an apple.",
            duration=3, body_x="180", body_y="184")
        self.assertEqual(label, "h")
        self.assertEqual(names[-2:], ["reach", "prop"])
        self.assertIn("[2:v]overlay", graph)
        self.assertIn("[3:v]overlay", graph)
        self.assertNotIn("movie=", graph)
        with self.assertRaises(ValueError):
            append_overlays(graph="", label="unsafe",
                            names=["base"], narration="Fox picks up an apple.",
                            duration=3, body_x="180", body_y="184")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required for rendered interaction checks")
    def test_fox_pickup_apple_transports_actual_prop_between_frames(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            video = root / "pickup-apple.mp4"
            text = "Le renard ramasse une pomme rouge."
            forest_video(
                kind="fox", topic="Une pomme originale",
                narration=text, scene_index=1, scene_count=3,
                style="cartoon", duration=2.9, width=1280,
                height=720, fps=24, destination=video,
                direction={"weather": "day", "action": "walk",
                           "emotion": "happy", "shot": "wide"})
            early = _frame(video, .1)
            late = _frame(video, 2.4)
            self.assertEqual(early.size, (1280, 720))
            self.assertGreater(_change(early, late, (645, 465, 800, 625)), 8)
            self.assertGreater(_change(early, late, (465, 420, 610, 565)), 8)
            poster = root / "approved.png"
            forest_poster(
                kind="fox", topic="Une pomme originale",
                narration=text, scene_index=1, scene_count=3,
                style="cartoon", destination=poster)
            self.assertTrue(poster.stat().st_size > 1000)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required for rendered interaction checks")
    def test_owl_observes_flower_and_rabbit_jumps_over_stone(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            owl = root / "owl-flower.mp4"
            owl_video(topic="La fleur", narration="La chouette observe une fleur.",
                      scene_index=1, scene_count=3,
                      style="cartoon", duration=1.6, width=1280,
                      height=720, fps=24, destination=owl,
                      direction={"weather": "night", "action": "idle",
                                 "emotion": "curious", "shot": "wide"})
            self.assertEqual(_frame(owl, .7).size, (1280, 720))
            png = root / "owl-poster.png"
            owl_poster(topic="La fleur", narration="La chouette observe une fleur.",
                       scene_index=1, scene_count=3,
                       style="cartoon", destination=png)
            self.assertGreater(png.stat().st_size, 1000)
            rabbit = root / "rabbit-stone.mp4"
            forest_video(
                kind="rabbit", topic="Un saut original",
                narration="Le lapin saute par-dessus une pierre.",
                scene_index=1, scene_count=3,
                style="cartoon", duration=1.6, width=1280,
                height=720, fps=24, destination=rabbit,
                direction={"weather": "rain", "action": "jump",
                           "emotion": "surprised", "shot": "wide"})
            self.assertEqual(_frame(rabbit, .7).size, (1280, 720))
            self.assertGreater(rabbit.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
