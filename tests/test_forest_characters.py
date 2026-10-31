"""Original forest character selection, rendered frames and immutable approvals."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_forest import (
    character_kind, render_character_poster, render_motion_clip,
    art_brief_sha256, FOREST_RIG_VERSION)
from automate_ytb.episode import build_preview, create_local_art
from automate_ytb.production import audit, load_plan, render
from automate_ytb.scene_plan import plan


def frame(path: Path, second: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(second),
         "-i", str(path), "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, timeout=60, check=True)
    with Image.open(io.BytesIO(result.stdout)) as image:
        return image.convert("RGB")


def diff(a: Image.Image, b: Image.Image) -> float:
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean)


class ForestCharacterTests(unittest.TestCase):
    def test_explicit_french_and_english_character_names(self):
        examples = {
            "fox": ("Un renard roux", "An original fox", "Renarde"),
            "rabbit": ("Un lapin", "A small rabbit", "A happy bunny", "Lièvre"),
            "cat": ("Un chat original", "A turquoise cat", "Petit chaton"),
        }
        for kind, labels in examples.items():
            for label in labels:
                with self.subTest(label=label):
                    self.assertEqual(character_kind(label), kind)
        for label in ("Une chouette originale", "An owl", "A human actor",
                      "An astronaut", "Une forme géométrique", "wildlife"):
            self.assertIsNone(character_kind(label))
        with self.assertRaises(ValueError):
            character_kind(None)

    def test_poster_is_deterministic_and_animals_are_visually_different(self):
        images = {}
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for kind in ("fox", "rabbit", "cat"):
                args = dict(
                    kind=kind, topic="Voyage original",
                    narration="Un animal traverse le jardin en souriant.",
                    scene_index=1, scene_count=5,
                    style="cartoon")
                first, second = folder / f"{kind}-1.png", folder / f"{kind}-2.png"
                render_character_poster(destination=first, **args)
                render_character_poster(destination=second, **args)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                with Image.open(first) as im:
                    self.assertEqual(im.size, (1280, 720))
                    images[kind] = im.convert("RGB").crop((190, 200, 540, 610))
            self.assertGreater(diff(images["fox"], images["rabbit"]), 24)
            self.assertGreater(diff(images["rabbit"], images["cat"]), 16)

    def test_hash_tracks_exact_character_and_visual_direction(self):
        self.assertIn("v40", FOREST_RIG_VERSION)
        common = dict(
            kind="fox", topic="Forêt", narration="Le renard observe la pluie.",
            character="Original red fox", style="cartoon",
            scene_id="scene-001")
        plain = art_brief_sha256(**common)
        self.assertEqual(plain, art_brief_sha256(**common))
        self.assertNotEqual(plain, art_brief_sha256(**(common | {"kind": "cat"})))
        self.assertNotEqual(plain, art_brief_sha256(
            **(common | {"narration": "Autre texte."})))
        with self.assertRaises(ValueError):
            art_brief_sha256(**(common | {"kind": "dragon"}))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg required for actual video frame evidence")
    def test_fox_and_rabbit_animate_in_real_encoded_video(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            frames = {}
            for kind in ("fox", "rabbit"):
                out = root / f"{kind}.mp4"
                render_motion_clip(
                    kind=kind, topic="Original fantasy forest",
                    narration="The character explores the woods.",
                    scene_index=1, scene_count=5,
                    style="cartoon", duration=2,
                    width=1280, height=720, fps=24,
                    destination=out,
                    direction={"weather": "wind", "action": "walk",
                               "emotion": "happy", "shot": "medium"})
                self.assertTrue(out.is_file())
                frames[kind] = (frame(out, 0.2), frame(out, 1.5))
                self.assertGreater(
                    diff(frames[kind][0].crop((150, 240, 570, 615)),
                         frames[kind][1].crop((150, 240, 570, 615))), 0.5)
            self.assertGreater(diff(frames["fox"][0], frames["rabbit"][0]), 4)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg required for end-to-end forest video preview")
    def test_one_click_preview_animates_fox_and_reuses_verified_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "scene-plan.json"
            script = " ".join([
                "Le petit renard marche en forêt.",
                "Il découvre une petite rivière.",
                "Le renard sourit aux oiseaux.",
                "Il explore une grande prairie.",
                "Au matin, il rentre chez lui."])
            data = plan(
                topic="L'aventure originale du renard",
                script=script, duration=30, shot_seconds=6,
                character="An original small red fox wearing a golden scarf")
            source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
            out = root / "out"
            first = build_preview(
                plan_path=source, output=out,
                style="cartoon", voice="none", limit=1)
            self.assertEqual(first["art"]["characterRig"],
                             "original-forest-fox-v1")
            self.assertEqual(first["render"]["animatedForestScenes"], 1)
            self.assertEqual(first["render"]["animatedOwlScenes"], 0)
            self.assertEqual(audit(source, limit=1)["counts"]["ready"], 1)
            self.assertEqual(load_plan(source)["scenes"][0]["motionRig"],
                             "original-forest-fox-v1")
            previous_sha = first["render"]["videoSha256"]
            second = build_preview(
                plan_path=source, output=out,
                style="cartoon", voice="none", limit=1)
            self.assertEqual(second["art"]["reused"], 1)
            self.assertEqual(second["render"]["videoSha256"], previous_sha)
            edited = load_plan(source)
            edited["scenes"][0]["motionRig"] = "original-forest-cat-v1"
            source.write_text(json.dumps(edited, ensure_ascii=False), encoding="utf8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                render(plan_path=source, output=root / "modified", limit=1)

    def test_non_animal_character_keeps_original_card_renderer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "plan.json"
            data = plan(topic="Original video",
                        script="Un. Deux. Trois. Quatre. Cinq.",
                        duration=30, shot_seconds=6,
                        character="An original humanoid explorer")
            source.write_text(json.dumps(data), encoding="utf-8")
            res = create_local_art(source, style="cartoon", limit=1)
            self.assertEqual(res["characterRig"], "none")
            self.assertNotIn("motionRig", load_plan(source)["scenes"][0])


if __name__ == "__main__":
    unittest.main()
