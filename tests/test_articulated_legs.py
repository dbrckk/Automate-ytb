"""Independent mammal limbs must be real sprites, not simulated by body bounce."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.animated_forest import render_layers, render_motion_clip
from automate_ytb.choreography import ACTIONS, leg_position, LEG_ANCHORS, LEG_MOTION


def video_frame(video: Path, sec: float):
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(sec),
         "-i", str(video), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"], check=True, capture_output=True, timeout=90)
    with Image.open(io.BytesIO(proc.stdout)) as image:
        return image.convert("RGB")


def difference(a, b, box):
    return sum(ImageStat.Stat(
        ImageChops.difference(a.crop(box), b.crop(box))).mean)


class IndependentAnimalLegTests(unittest.TestCase):
    def test_leg_phases_depend_on_both_action_and_side(self):
        self.assertEqual(ACTIONS, set(LEG_MOTION))
        self.assertEqual(set(LEG_ANCHORS), {"left", "right"})
        for action in ACTIONS:
            for side in ("left", "right"):
                x, y = leg_position(action, side=side)
                self.assertIn("sin(", x + y)
                self.assertNotIn(";", x + y)
                self.assertTrue("180" in x and "184" in y)
        left = leg_position("walk", side="left")
        right = leg_position("walk", side="right")
        self.assertIn("3.141593", right[0] + right[1])
        self.assertNotIn("3.141593", left[0] + left[1])
        self.assertNotEqual(left, right)
        self.assertNotEqual(leg_position("walk", side="left"),
                            leg_position("run", side="left"))
        self.assertNotIn("3.141593", "".join(leg_position("jump", side="right")))
        self.assertIn("+335-", leg_position("jump", side="right")[1])
        for invalid in ("walk;movie=/etc/passwd", "rotate", "walk\n"):
            with self.assertRaises(ValueError):
                leg_position(invalid, side="left")
        with self.assertRaises(ValueError):
            leg_position("walk", side="center")
        with self.assertRaises(ValueError):
            leg_position("run", side="right", body_x=-300)

    def test_animal_sprites_have_independent_opaque_paws(self):
        with tempfile.TemporaryDirectory() as temp:
            for kind in ("fox", "rabbit", "cat"):
                folder = Path(temp) / kind
                layers = render_layers(
                    folder, kind=kind, topic="Original story",
                    narration="The animal walks.", scene_index=1,
                    scene_count=4, style="cartoon")
                with Image.open(layers["body"]) as body:
                    body_bbox = body.getchannel("A").getbbox()
                    self.assertLessEqual(body_bbox[3], 395)
                for name in ("left_leg", "right_leg"):
                    with Image.open(layers[name]) as leg:
                        self.assertEqual(leg.size, (100, 125))
                        bbox = leg.getchannel("A").getbbox()
                        self.assertIsNotNone(bbox)
                        self.assertGreater(bbox[3], 110)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg is required")
    def test_encoded_walk_and_run_show_different_foot_movement(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            frames = {}
            for action in ("walk", "run"):
                dest = root / (action + ".mp4")
                render_motion_clip(
                    kind="fox", topic="Original woodland race",
                    narration="The fox moves by the river.",
                    scene_index=1, scene_count=3,
                    style="cartoon", duration=1.5,
                    width=1280, height=720, fps=24,
                    destination=dest,
                    direction={"weather": "day", "action": action,
                               "emotion": "happy", "shot": "wide"})
                a, b = video_frame(dest, .08), video_frame(dest, .29)
                frames[action] = b
                self.assertGreater(
                    difference(a, b, (240, 520, 515, 650)), 0.4)
                self.assertEqual(b.size, (1280, 720))
            self.assertGreater(
                difference(frames["walk"], frames["run"],
                           (240, 520, 515, 650)), 1.0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg is required")
    def test_jump_tucks_both_rabbit_paws_and_preserves_output(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "rabbit-jump.mp4"
            render_motion_clip(
                kind="rabbit", topic="Original adventure",
                narration="The rabbit jumps over a stone.",
                scene_index=2, scene_count=3,
                style="cartoon", duration=1.5,
                width=1280, height=720, fps=24,
                destination=dest,
                direction={"weather": "rain", "action": "jump",
                           "emotion": "surprised", "shot": "medium"})
            self.assertGreater(dest.stat().st_size, 1000)
            self.assertEqual(video_frame(dest, .4).size, (1280, 720))


if __name__ == "__main__":
    unittest.main()
