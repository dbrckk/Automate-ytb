"""Visible story-grounded eyebrow acting in 2D sprites and real encoded scenes."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from automate_ytb.director import ACTIONS, EMOTIONS
from automate_ytb.expressive_face import (
    FACE_VERSION, append_expression, draw_expression, expression_bob)
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_motion_clip as owl_clip


class ExpressiveFaceTests(unittest.TestCase):
    def test_original_emotions_change_translucent_art_without_covering_eyes(self):
        self.assertIn("v1", FACE_VERSION)
        with tempfile.TemporaryDirectory() as temp:
            for actor in ("fox", "rabbit", "cat", "owl"):
                results = {}
                for emotion in EMOTIONS:
                    p = Path(temp) / (actor + "-" + emotion + ".png")
                    draw_expression(p, actor=actor, emotion=emotion)
                    with Image.open(p) as im:
                        self.assertEqual(im.mode, "RGBA")
                        self.assertEqual(im.size, ((322, 430) if actor == "owl"
                                                   else (350, 440)))
                        alpha = im.getchannel("A")
                        bounds = alpha.getbbox()
                        self.assertIsNotNone(bounds)
                        self.assertGreater(bounds[2], 230)
                        # No brow texture on the mouth, pupils or subtitle area.
                        self.assertLess(bounds[3], 190)
                        self.assertEqual(im.getpixel((175, 275))[3], 0)
                    results[emotion] = p.read_bytes()
                self.assertNotEqual(results["surprised"], results["worried"])
                self.assertNotEqual(results["neutral"], results["curious"])
                self.assertEqual(results["neutral"], (
                    Path(temp) / (actor + "-neutral.png")).read_bytes())
            with self.assertRaises(ValueError):
                draw_expression(Path(temp) / "bad.png", actor="dragon", emotion="happy")
            with self.assertRaises(ValueError):
                draw_expression(Path(temp) / "bad.png", actor="fox", emotion="angry")

    def test_trusted_animation_expression_is_bounded_and_tracks_body(self):
        self.assertEqual(expression_bob(action="rest", emotion="neutral"), "0")
        self.assertIn("exp(", expression_bob(action="surprise", emotion="surprised"))
        self.assertEqual(set(ACTIONS), {
            "idle", "fly", "walk", "run", "jump", "talk", "surprise", "rest"})
        for emotion in EMOTIONS:
            graph, label, names = append_expression(
                graph="[0:v]null[ambientnear]", label="ambientnear",
                names=["background"], body_x="180+sin(t)",
                body_y="184+2*sin(t)", action="talk", emotion=emotion)
            self.assertEqual(label, "faceexpressed")
            self.assertEqual(names, ["background", "expression"])
            self.assertIn("[1:v]overlay=x='180+sin(t)'", graph)
            self.assertIn("184+2*sin(t)", graph)
        with self.assertRaises(ValueError):
            append_expression(graph="", label="x", names=["expression"],
                              body_x="180", body_y="184",
                              action="idle", emotion="neutral")
        with self.assertRaises(ValueError):
            append_expression(graph="", label="x", names=["background"],
                              body_x="180';movie=/tmp", body_y="184",
                              action="idle", emotion="neutral")
        with self.assertRaises(ValueError):
            expression_bob(action="untrusted", emotion="happy")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required for encoded character QA")
    def test_fox_and_owl_expression_layers_encode_real_h264(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, renderer in (("fox", forest_clip), ("owl", owl_clip)):
                movie = root / (name + "-emotion.mp4")
                args = dict(topic="Original facial acting scene",
                            narration="Le personnage est soudain très surpris.",
                            scene_index=1, scene_count=3, style="cartoon",
                            duration=0.9, width=1280, height=720, fps=24,
                            destination=movie,
                            direction={"weather": "day", "action": "surprise",
                                       "emotion": "surprised", "shot": "wide"})
                if name == "fox":
                    args["kind"] = "fox"
                renderer(**args)
                self.assertGreater(movie.stat().st_size, 1000)
                p = subprocess.run([
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name,width,height",
                    "-of", "json", str(movie)], capture_output=True,
                    text=True, check=True, timeout=60)
                video = json.loads(p.stdout)["streams"][0]
                self.assertEqual(video["codec_name"], "h264")
                self.assertEqual((video["width"], video["height"]), (1280,720))


if __name__ == "__main__":
    unittest.main()
