"""Real video rendering checks for the original animated owl (not just camera zoom)."""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_owl import render_motion_clip, render_character_poster
from automate_ytb.episode import build_preview, create_local_art
from automate_ytb.production import load_plan, audit
from automate_ytb.scene_plan import plan


def _frame(mp4: Path, timestamp: str) -> Image.Image:
    p = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", timestamp,
         "-i", str(mp4), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"],
        check=True, capture_output=True)
    with Image.open(io.BytesIO(p.stdout)) as im:
        return im.convert("RGB")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg required for actual visual motion tests")
class AnimatedOwlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.scene_plan = self.root / "scene-plan.json"
        script = " ".join([
            "La chouette découvre une carte céleste.",
            "Elle observe des lucioles dans la forêt.",
            "Un oiseau lui montre un nouvel endroit.",
            "Elle ouvre de grands yeux de surprise.",
            "Enfin, elle raconte son incroyable aventure.",
        ])
        p = plan(topic="Le voyage de la petite chouette",
                 script=script, duration=30, shot_seconds=6,
                 character="Chouette violette avec des lunettes turquoise")
        self.scene_plan.write_text(json.dumps(p), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_real_movement_visible_independent_of_background(self):
        mp4 = self.root / "rig.mp4"
        render_motion_clip(
            topic="Le voyage de la chouette", narration="Elle bat doucement des ailes.",
            scene_index=1, scene_count=5, style="cartoon",
            duration=2, width=1280, height=720, fps=24, destination=mp4)
        a, b = _frame(mp4, "0.20"), _frame(mp4, "1.10")
        body = ImageChops.difference(a.crop((80, 200, 650, 650)),
                                     b.crop((80, 200, 650, 650)))
        backdrop = ImageChops.difference(a.crop((900, 40, 1150, 75)),
                                         b.crop((900, 40, 1150, 75)))
        # The sprite rig changes where the subject is, while scenery stays put.
        self.assertGreater(sum(ImageStat.Stat(body).mean), 3.0)
        self.assertLess(sum(ImageStat.Stat(backdrop).mean), 1.5)
        info = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                               "stream=nb_frames,width,height", "-of", "json",
                               str(mp4)], capture_output=True, text=True, check=True)
        stream = json.loads(info.stdout)["streams"][0]
        self.assertEqual(stream["nb_frames"], "48")
        self.assertEqual(stream["width"], 1280)

    def test_approved_poster_is_actual_sprite_composite(self):
        original = self.root / "approved.png"
        again = self.root / "repeat.png"
        render_character_poster(
            topic="La chouette originale", narration="Elle marche.",
            scene_index=2, scene_count=5, style="cartoon",
            destination=original)
        render_character_poster(
            topic="La chouette originale", narration="Elle marche.",
            scene_index=2, scene_count=5, style="cartoon",
            destination=again)
        self.assertEqual(original.read_bytes(), again.read_bytes())
        with Image.open(original) as image:
            self.assertEqual(image.size, (1280, 720))

    def test_android_preview_marks_and_renders_animation(self):
        preview = build_preview(plan_path=self.scene_plan,
                                output=self.root / "preview", limit=1,
                                style="cartoon", voice="none")
        self.assertEqual(preview["render"]["animatedOwlScenes"], 1)
        self.assertEqual(preview["art"]["characterRig"], "original-owl-v1")
        self.assertEqual(load_plan(self.scene_plan)["scenes"][0]["motionRig"],
                         "original-owl-v1")
        self.assertTrue(preview["render"]["previewOnly"])
        self.assertFalse(preview["publicationApproved"])
        self.assertTrue(audit(self.scene_plan, limit=1)["readyForPreview"])
        first_clip = sorted((self.root/"preview"/".clip-cache").glob("*.mp4"))[0]
        timestamp = first_clip.stat().st_mtime_ns
        preview2 = build_preview(plan_path=self.scene_plan,
                                 output=self.root / "preview", limit=1,
                                 style="cartoon", voice="none")
        self.assertEqual(preview2["art"]["reused"], 1)
        self.assertEqual(first_clip.stat().st_mtime_ns, timestamp)
        self.assertEqual(preview["render"]["videoSha256"],
                         preview2["render"]["videoSha256"])

    def test_changed_story_cannot_reuse_approved_character_art(self):
        create_local_art(self.scene_plan, style="cartoon", limit=1)
        data = load_plan(self.scene_plan)
        data["originalCharacterBible"] = "A new unauthorized purple owl"
        self.scene_plan.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "another story/character"):
            create_local_art(self.scene_plan, style="cartoon", limit=1)
        from automate_ytb.production import render
        with self.assertRaisesRegex(ValueError, "brief changed"):
            render(plan_path=self.scene_plan, output=self.root/"unsafe",
                   limit=1)

    def test_switching_style_requires_fresh_artwork(self):
        create_local_art(self.scene_plan, style="cartoon", limit=1)
        with self.assertRaisesRegex(ValueError, "another style"):
            create_local_art(self.scene_plan, style="documentary", limit=1)

    def test_non_owl_uses_dedicated_forest_rig_not_owl(self):
        data = load_plan(self.scene_plan)
        data["originalCharacterBible"] = "Un renard roux original et souriant"
        self.scene_plan.write_text(json.dumps(data), encoding="utf-8")
        result = create_local_art(self.scene_plan, style="cartoon", limit=1)
        self.assertEqual(result["characterRig"], "original-forest-fox-v1")
        self.assertEqual(load_plan(self.scene_plan)["scenes"][0]["motionRig"],
                         "original-forest-fox-v1")


if __name__ == "__main__":
    unittest.main()
