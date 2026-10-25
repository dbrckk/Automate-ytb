"""Script-grounded varied landscapes remain consistent across scenes and MP4."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.scenic_world import (
    LANDSCAPES, WORLD_VERSION, detect_landscape, landscapes_for_scenes)
from automate_ytb.animated_forest import (
    render_character_poster, render_motion_clip, art_brief_sha256)
from automate_ytb.animated_owl import render_character_poster as owl_poster
from automate_ytb.episode import create_local_art, build_preview
from automate_ytb.scene_plan import plan
from automate_ytb.production import load_plan, render, _write_json


def sample(mp4: Path, t: float) -> Image.Image:
    result = subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-ss", str(t),
        "-i", str(mp4), "-frames:v", "1", "-f",
        "image2pipe", "-vcodec", "png", "-"], check=True,
        capture_output=True, timeout=90)
    with Image.open(io.BytesIO(result.stdout)) as img:
        return img.convert("RGB")


def distance(a: Image.Image, b: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(
        a.convert("RGB").crop((700, 430, 1210, 690)),
        b.convert("RGB").crop((700, 430, 1210, 690)))).mean)


class LandscapeTests(unittest.TestCase):
    def test_authored_location_detected_without_guessing_random_setting(self):
        self.assertEqual(set(LANDSCAPES),
                         {"river", "forest", "meadow", "village"})
        examples = {
            "Le renard traverse une rivière.": "river",
            "The rabbit follows a stream.": "river",
            "La chouette revient au village.": "village",
            "The cat goes home to a cottage.": "village",
            "Le lapin bondit dans la prairie.": "meadow",
            "The fox jumps through a meadow.": "meadow",
            "Le renard retourne en forêt.": "forest",
            "The owl sits in the forest.": "forest",
        }
        for phrase, expected in examples.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(detect_landscape(phrase), expected)
        self.assertIsNone(detect_landscape("The fox eats a bright red apple."))
        self.assertIsNone(detect_landscape("Le renard prépare une jolie surprise."))
        with self.assertRaises(ValueError):
            detect_landscape(None)

    def test_location_persists_until_script_explicitly_changes_place(self):
        scenes = [
            {"narration": "The fox follows a river."},
            {"narration": "He pauses to listen to the birds."},
            {"narration": "He enters a small village."},
            {"narration": "A rabbit gives him a map."},
            {"narration": "They return to the forest."},
            {"narration": "They finally sleep peacefully."},
        ]
        self.assertEqual(landscapes_for_scenes(scenes),
                         ["river", "river", "village", "village",
                          "forest", "forest"])
        self.assertEqual(landscapes_for_scenes([{"narration": "A fox sleeps."}]),
                         ["forest"])
        self.assertIn("v1", WORLD_VERSION)
        with self.assertRaises(ValueError):
            landscapes_for_scenes([{"wrong": "narration"}])

    def test_posters_show_distinct_original_landmarks_and_determinism(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pictures = {}
            args = dict(kind="fox", topic="A unique little journey",
                        narration="The fox walks carefully.",
                        scene_index=1, scene_count=4, style="cartoon")
            for place in LANDSCAPES:
                dest = root / (place + ".png")
                duplicate = root / (place + "-copy.png")
                render_character_poster(destination=dest, landscape=place, **args)
                render_character_poster(destination=duplicate, landscape=place, **args)
                self.assertEqual(dest.read_bytes(), duplicate.read_bytes())
                with Image.open(dest) as src:
                    self.assertEqual(src.size, (1280, 720))
                    pictures[place] = src.copy().convert("RGB")
            for place in ("river", "village", "meadow"):
                self.assertGreater(distance(pictures["forest"],
                                            pictures[place]), 15, place)
            self.assertGreater(distance(pictures["river"],
                                        pictures["village"]), 15)
            dest = root / "owl-village.png"
            owl_poster(topic="Original owl", narration="The owl sees a cabin.",
                       scene_index=2, scene_count=5, style="cartoon",
                       destination=dest, landscape="village")
            self.assertTrue(dest.stat().st_size > 1000)

    def test_approved_character_art_hash_is_bound_to_inherited_location(self):
        args = dict(kind="fox", topic="An original river story",
                    narration="The fox looks for friends.",
                    character="Original red fox with golden scarf",
                    style="cartoon", scene_id="scene-002")
        forest = art_brief_sha256(**args, landscape="forest")
        river = art_brief_sha256(**args, landscape="river")
        self.assertNotEqual(forest, river)
        self.assertEqual(river, art_brief_sha256(**args, landscape="river"))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / "plan.json"
            data = plan(
                topic="Original river journey",
                script=" ".join([
                    "The fox follows a quiet river.",
                    "It looks around for a lost book.",
                    "A wise owl sings an ancient tune.",
                    "The wind pushes some leaves along.",
                    "At last a friend greets the fox.",
                ]),
                character="An original orange fox with a golden scarf",
                duration=30, shot_seconds=6)
            p.write_text(json.dumps(data), encoding="utf8")
            create_local_art(p, style="cartoon", limit=2)
            approved = load_plan(p)
            self.assertEqual(landscapes_for_scenes(approved["scenes"])[1], "river")
            approved["scenes"][0]["narration"] = "The fox crosses a forest."
            _write_json(p, approved)
            with self.assertRaisesRegex(ValueError, "Artwork brief changed"):
                render(plan_path=p, output=root/"tampered", limit=2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required to compare encoded world designs")
    def test_encoded_village_and_river_change_actual_video_frames(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = dict(kind="rabbit", topic="An original forest story",
                          narration="The rabbit is looking for a friend.",
                          scene_index=2, scene_count=4, style="cartoon",
                          duration=1.1, width=1280, height=720, fps=24,
                          direction={"weather": "day", "action": "idle",
                                     "emotion": "curious", "shot": "wide"})
            result = {}
            for place in ("village", "river"):
                dest = root / (place + ".mp4")
                render_motion_clip(destination=dest, landscape=place, **common)
                self.assertGreater(dest.stat().st_size, 1000)
                result[place] = sample(dest, .6)
            self.assertGreater(distance(result["river"], result["village"]), 10)


if __name__ == "__main__":
    unittest.main()
