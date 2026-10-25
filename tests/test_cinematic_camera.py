"""Cinematic camera, real MP4 frames and original storybook art regressions."""
from __future__ import annotations

from pathlib import Path
import io
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_owl import (
    RIG_VERSION, art_brief_sha256, render_character_poster, render_motion_clip)
from automate_ytb.cinematic_camera import (
    PROFILES, CAMERA_VERSION, framing_filter, framing_metadata)
from automate_ytb.director import validate_direction


def _frame(path: Path, seconds: float) -> Image.Image:
    output = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(seconds),
         "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"],
        capture_output=True, check=True, timeout=60)
    with Image.open(io.BytesIO(output.stdout)) as src:
        return src.convert("RGB")


def _difference(first: Image.Image, second: Image.Image, bbox=None) -> float:
    if bbox is not None:
        first, second = first.crop(bbox), second.crop(bbox)
    return sum(ImageStat.Stat(ImageChops.difference(first, second)).mean)


class CameraProfileTests(unittest.TestCase):
    def test_every_director_shot_has_distinct_valid_profile(self):
        self.assertEqual(set(PROFILES), {
            "wide", "medium", "closeup", "macro", "low", "shoulder"})
        seen = set()
        for shot in PROFILES:
            params = PROFILES[shot]
            w, h, x, y, dx, dy = params
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
            self.assertGreaterEqual(x - dx, 0)
            self.assertLessEqual(x + dx + w, 1280)
            self.assertGreaterEqual(y - dy, 0)
            self.assertLessEqual(y + dy + h, 720)
            self.assertNotIn((w, h), seen)
            seen.add((w, h))
            graph = framing_filter(shot, width=1280, height=720, fps=24)
            self.assertIn("format=yuv420p", graph)
            self.assertIn("scale=1280:720", graph)
            self.assertEqual(framing_metadata(shot)["animatedCamera"], shot != "wide")
        self.assertIn("camera", CAMERA_VERSION)

    def test_untrusted_camera_data_cannot_build_ffmpeg_expressions(self):
        with self.assertRaises(ValueError):
            framing_filter("macro;movie=/etc/passwd", width=1280,
                           height=720, fps=24)
        for case in ({"width": 999, "height": 700, "fps": 24},
                     {"width": 1280, "height": 720, "fps": 60}):
            with self.assertRaises(ValueError):
                framing_filter("macro", **case)
        with self.assertRaises(ValueError):
            framing_filter("macro", width=1280, height=720,
                           fps=24, scene_index=0)

    def test_art_brief_binds_to_visual_renderer_revision(self):
        d = {"weather": "day", "action": "fly", "emotion": "happy",
             "shot": "medium"}
        h = art_brief_sha256(
            topic="Original topic", narration="A flying owl",
            character="Original purple owl", style="cartoon",
            scene_id="scene-001", direction=d)
        self.assertIn("v12", RIG_VERSION)
        self.assertEqual(h, art_brief_sha256(
            topic="Original topic", narration="A flying owl",
            character="Original purple owl", style="cartoon",
            scene_id="scene-001", direction=d))
        d["shot"] = "macro"
        self.assertNotEqual(h, art_brief_sha256(
            topic="Original topic", narration="A flying owl",
            character="Original purple owl", style="cartoon",
            scene_id="scene-001", direction=d))

    def test_scenic_posters_stay_deterministic_and_discard_old_text_card(self):
        cue = validate_direction({
            "weather": "day", "action": "fly",
            "emotion": "curious", "shot": "wide"})
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b = root / "one.png", root / "two.png"
            options = {
                "topic": "Voyage original",
                "narration": "La chouette explore les arbres.",
                "scene_index": 1, "scene_count": 5,
                "style": "cartoon", "direction": cue,
            }
            render_character_poster(destination=a, **options)
            render_character_poster(destination=b, **options)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with Image.open(a) as im:
                self.assertEqual(im.size, (1280, 720))
                # Previous version had an opaque rectangular narration card
                # at (666,245)-(1220,607). The new sky is not that solid card.
                self.assertNotEqual(im.convert("RGB").getpixel((680, 275)),
                                    (18, 29, 55))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg required to inspect actual cinematic frames")
    def test_actual_mp4_has_true_closeups_and_camera_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = {
                "topic": "Forêt originale",
                "narration": "La chouette cherche les étoiles.",
                "scene_index": 1, "scene_count": 5,
                "style": "cartoon", "duration": 2.0,
                "width": 1280, "height": 720, "fps": 24
            }
            d = {"weather": "day", "action": "idle",
                 "emotion": "curious", "shot": "wide"}
            wide = root / "wide.mp4"
            render_motion_clip(destination=wide, direction=d, **common)
            d["shot"] = "macro"
            macro = root / "macro.mp4"
            render_motion_clip(destination=macro, direction=d, **common)
            wide_a = _frame(wide, .20)
            macro_a = _frame(macro, .20)
            macro_b = _frame(macro, 1.60)
            self.assertEqual(macro_a.size, (1280, 720))
            self.assertGreater(_difference(wide_a, macro_a), 12)
            self.assertGreater(_difference(macro_a, macro_b, (670, 140, 960, 360)), .12)

if __name__ == "__main__":
    unittest.main()
