"""Story continuity: prior pickup carries forward until an explicit release."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.scene_props import (
    PROP_VERSION, carried_props_for_scenes, cue_for_scene, create_layers,
    append_overlays)
from automate_ytb.animated_forest import (
    art_brief_sha256, render_motion_clip)
from automate_ytb.episode import build_preview
from automate_ytb.production import load_plan, render, _write_json
from automate_ytb.scene_plan import plan


def _frame(file: Path, second: float) -> Image.Image:
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(second),
         "-i", str(file), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"], capture_output=True,
        check=True, timeout=90)
    with Image.open(io.BytesIO(proc.stdout)) as image:
        return image.convert("RGB")


def _diff(first: Image.Image, second: Image.Image, rect: tuple) -> float:
    delta = ImageChops.difference(first.crop(rect), second.crop(rect))
    return sum(ImageStat.Stat(delta).mean)


class SceneContinuityTests(unittest.TestCase):
    def test_pickup_carries_until_explicit_noun_release(self):
        texts = [
            "Le renard ramasse une pomme rouge.",
            "Il marche vers la maison.",
            "Il admire une fleur au bord du chemin.",
            "Il regarde la pomme dans ses pattes.",
            "Il pose la pomme sur la table.",
            "Il parcourt ensuite la forêt.",
        ]
        scenes = [{"narration": t} for t in texts]
        self.assertEqual(carried_props_for_scenes(scenes),
                         [None, "apple", None, "apple", None, None])
        self.assertEqual(cue_for_scene(texts[1], held_prop="apple")["action"], "carry")
        self.assertEqual(cue_for_scene(texts[3], held_prop="apple")["action"], "carry")
        self.assertEqual(cue_for_scene(texts[2], held_prop="apple")["prop"], "flower")
        self.assertIn("v2", PROP_VERSION)

    def test_inventory_replaced_and_consumed_without_hallucination(self):
        scenes = [{"narration": n} for n in [
            "The rabbit picks up an apple.",
            "It goes home.",
            "It picks up a flower.",
            "The rabbit keeps walking.",
            "It eats the flower.",
            "It continues its journey.",
        ]]
        self.assertEqual(carried_props_for_scenes(scenes),
                         [None, "apple", None, "flower", None, None])
        self.assertEqual(carried_props_for_scenes([
            {"narration": "An apple is on the table."},
            {"narration": "The fox walks into the garden."},
        ]), [None, None])
        with self.assertRaises(ValueError):
            carried_props_for_scenes([{"no_narration": "wrong"}])
        with self.assertRaises(ValueError):
            cue_for_scene("The fox walks.", held_prop="stone")

    def test_carried_sprite_preserves_stage_and_approved_hash(self):
        args = dict(kind="fox", topic="Original forest", narration="Then it walks.",
                    character="An original red fox", style="cartoon",
                    scene_id="scene-002")
        self.assertNotEqual(art_brief_sha256(**args),
                            art_brief_sha256(**args, held_prop="apple"))
        self.assertNotEqual(art_brief_sha256(**args, held_prop="apple"),
                            art_brief_sha256(**args, held_prop="book"))
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            cue = create_layers(p, narration="Then it walks.",
                                actor="fox", held_prop="apple")
            self.assertEqual(cue["action"], "carry")
            self.assertEqual(cue["prop"], "apple")
            self.assertTrue((p / "prop.png").is_file())
            self.assertFalse((p / "reach.png").exists())
        graph, label, inputs = append_overlays(
            graph="base", label="f", names=["background"],
            narration="Then it walks.", duration=2.0,
            body_x="180+4*sin(t)", body_y="184",
            held_prop="apple")
        self.assertEqual(inputs, ["background", "prop"])
        self.assertEqual(label, "g")
        self.assertIn("+301", graph)
        self.assertNotIn("652", graph)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_carried_prop_is_visible_in_actual_mp4_without_narration_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "carry.mp4"
            render_motion_clip(
                kind="fox", topic="Original woodland",
                narration="The fox walks into the forest.",
                scene_index=2, scene_count=3,
                style="cartoon", duration=1.6,
                width=1280, height=720, fps=24,
                destination=output,
                direction={"weather": "night", "action": "walk",
                           "emotion": "happy", "shot": "wide"},
                held_prop="apple")
            self.assertGreater(output.stat().st_size, 1000)
            # Compare to an identical scene without an inherited prop.
            baseline = Path(tmp) / "without.mp4"
            render_motion_clip(
                kind="fox", topic="Original woodland",
                narration="The fox walks into the forest.",
                scene_index=2, scene_count=3,
                style="cartoon", duration=1.6,
                width=1280, height=720, fps=24,
                destination=baseline,
                direction={"weather": "night", "action": "walk",
                           "emotion": "happy", "shot": "wide"})
            self.assertGreater(_diff(_frame(output, .7), _frame(baseline, .7),
                                     (470, 410, 630, 585)), 3.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/ffprobe required")
    def test_two_scene_preview_preserves_carried_prop_and_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_file = root / "scene-plan.json"
            script = " ".join([
                "Le renard ramasse une pomme rouge.",
                "Puis il marche en direction de la maison.",
                "Il traverse une prairie verdoyante.",
                "Il pose la pomme près de son panier.",
                "Il termine son voyage tranquillement.",
            ])
            data = plan(topic="Une pomme originale", script=script,
                        duration=30, shot_seconds=6,
                        character="An original red fox wearing a golden scarf")
            plan_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
            out = root / "preview"
            preview = build_preview(
                plan_path=plan_file, output=out, style="cartoon",
                voice="none", soundtrack="none",
                transition="dissolve", limit=2)
            continuity = preview["render"]["propContinuity"]
            self.assertEqual(continuity["carriedScenes"], 1)
            self.assertEqual(continuity["carriedByScene"],
                             [{"sceneId": "scene-002", "prop": "apple"}])
            self.assertEqual(continuity["timelineShiftMs"], 0)
            self.assertTrue((out / "preview.mp4").is_file())
            # The next scene's approval is bound to the prior pickup.
            approved = load_plan(plan_file)
            approved["scenes"][0]["narration"] = "Le renard voit une pomme rouge."
            _write_json(plan_file, approved)
            with self.assertRaisesRegex(ValueError, "Artwork brief changed"):
                render(plan_path=plan_file, output=root / "tampered",
                       limit=2)


if __name__ == "__main__":
    unittest.main()
