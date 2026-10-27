"""Real, original movement accents stay synchronized with authored action."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from automate_ytb.motion_accents import (
    KINETIC_VERSION, draw_motion_accent, append_motion_accent)
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_layers as owl_layers


class KineticEffectsTests(unittest.TestCase):
    def test_original_deterministic_weather_sensitive_transparency(self):
        self.assertIn("v1", KINETIC_VERSION)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b, c = [root / f"{i}.png" for i in range(3)]
            draw_motion_accent(a, action="jump", weather="day",
                               landscape="forest", seed="original script")
            draw_motion_accent(b, action="jump", weather="day",
                               landscape="forest", seed="original script")
            draw_motion_accent(c, action="jump", weather="rain",
                               landscape="river", seed="original script")
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertNotEqual(a.read_bytes(), c.read_bytes())
            with Image.open(a) as im:
                self.assertEqual(im.mode, "RGBA")
                self.assertEqual(im.size, (300, 110))
                self.assertEqual(im.getpixel((150, 0))[3], 0)
                self.assertIsNotNone(im.getchannel("A").getbbox())
            with self.assertRaises(ValueError):
                draw_motion_accent(root/"bad.png", action="idle",
                                   weather="day", landscape="forest", seed="text")
            with self.assertRaises(ValueError):
                draw_motion_accent(root/"bad.png", action="jump",
                                   weather="day", landscape="forest", seed="")

    def test_safe_time_locked_takeoff_landing_and_run(self):
        for action in ("jump", "run"):
            with self.subTest(action=action):
                graph, label, names = append_motion_accent(
                    graph="[0:v]null[g]", label="g", names=["background"],
                    action=action, body_x="180+15*sin(t*1.1)", ground_y=586)
                self.assertEqual(label, "motiondone")
                self.assertEqual(names, ["background", "motion"])
                self.assertIn("overlay=", graph)
                self.assertNotIn("movie=", graph)
                self.assertIn("enable=", graph)
                if action == "jump":
                    self.assertIn("0.18,0.43", graph)
                    self.assertIn("1.39,1.65", graph)
                    self.assertIn("split=2", graph)
                else:
                    self.assertIn("mod(t,0.55)", graph)
        graph, label, names = append_motion_accent(
            graph="start", label="g", names=["background"],
            action="idle", body_x="180", ground_y=586)
        self.assertEqual((graph, label, names), ("start", "g", ["background"]))
        with self.assertRaises(ValueError):
            append_motion_accent(graph="", label="g", names=[],
                                 action="jump", body_x="180;movie=/etc/passwd",
                                 ground_y=586)

    def test_original_owl_idle_scene_does_not_get_unmentioned_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            kw = dict(topic="The sleepy owl", narration="The owl rests.",
                      scene_index=1, scene_count=2, style="cartoon",
                      direction={"weather":"day", "action":"rest",
                                 "emotion":"neutral","shot":"wide"})
            layers = owl_layers(Path(folder), **kw)
            self.assertNotIn("motion", layers)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg encoder and probe required")
    def test_real_720p_jump_includes_kinetic_effect_layer(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/"jump-with-ground-effect.mp4"
            forest_clip(
                kind="rabbit", topic="La course du lapin",
                narration="Le lapin saute dans la prairie.",
                scene_index=1, scene_count=2, style="cartoon",
                duration=1.8, width=1280, height=720, fps=24,
                destination=destination, landscape="meadow",
                direction={"weather":"day","action":"jump",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(destination.stat().st_size, 1500)
            check = subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_frames",
                 "-of","json",str(destination)],
                check=True, capture_output=True, text=True, timeout=40)
            stream = json.loads(check.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"], "h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(int(stream["nb_frames"]),43)


if __name__=="__main__":
    unittest.main()
