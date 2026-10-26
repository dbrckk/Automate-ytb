"""Timed original ground-response effects for real character animation."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.ground_response import (
    RESPONSE_VERSION, draw_ground_response, reaction_enable, response_stage)
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_layers as owl_layers


class GroundResponseTests(unittest.TestCase):
    def test_original_biome_puffs_are_reproducible_and_transparent(self):
        self.assertIn("v1", RESPONSE_VERSION)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b, river = (root / (name + ".png")
                           for name in ("forest", "duplicate", "river"))
            draw_ground_response(a, biome="forest", weather="day", seed="fox-1")
            draw_ground_response(b, biome="forest", weather="day", seed="fox-1")
            draw_ground_response(river, biome="river", weather="day", seed="fox-1")
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertNotEqual(a.read_bytes(), river.read_bytes())
            with Image.open(a) as img:
                self.assertEqual(img.size, (300, 120))
                self.assertEqual(img.mode, "RGBA")
                self.assertEqual(img.getpixel((0,0))[3], 0)
                self.assertGreater(img.getpixel((130,75))[3], 4)
                self.assertLess(img.getchannel("A").getextrema()[1], 120)
            for bad in ("unknown", "../forest"):
                with self.assertRaises(ValueError):
                    draw_ground_response(root/"bad.png", biome=bad,
                                         weather="day", seed="safe")

    def test_only_authored_contact_actions_make_puffs(self):
        self.assertIn("mod(t,1.75)", reaction_enable("jump"))
        self.assertIn("1.36", reaction_enable("jump"))
        self.assertIn("mod(t,0.62)", reaction_enable("run"))
        self.assertIn("mod(t,1.23)", reaction_enable("walk"))
        for action in ("fly", "rest", "idle", "talk", "surprise"):
            self.assertEqual(reaction_enable(action), "0")
        with self.assertRaises(ValueError):
            reaction_enable("jump;movie=secret")

    def test_safe_graph_keeps_puffs_behind_actor(self):
        graph = response_stage(body_x="180+4*sin(t*0.45)",
                               y=550, image_index=9,
                               enable=reaction_enable("jump"), x_offset=93)
        self.assertIn("[shadowstage][9:v]overlay=", graph)
        self.assertIn("[contactstage];", graph)
        self.assertIn("enable='max(",graph)
        with self.assertRaises(ValueError):
            response_stage(body_x="180;movie=secrets",y=550,image_index=9,
                           enable="1",x_offset=93)
        with self.assertRaises(ValueError):
            response_stage(body_x="180",y=550,image_index=9,
                           enable="1';movie=hidden",x_offset=93)

    def test_owl_layer_has_original_ground_response(self):
        with tempfile.TemporaryDirectory() as folder:
            layers = owl_layers(
                Path(folder),topic="An original story",
                narration="The owl flies above a stream.",
                scene_index=1,scene_count=2,style="cartoon",
                landscape="river")
            self.assertTrue(layers["impact"].is_file())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual h264 render and decode required")
    def test_real_fox_run_video_stays_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder)/"contact-fox.mp4"
            forest_clip(
                kind="fox",topic="Original forest race",
                narration="The fox runs through the woods.",
                scene_index=1,scene_count=2,style="cartoon",
                duration=1.1,width=1280,height=720,fps=24,destination=video,
                direction={"weather":"day","action":"run",
                           "emotion":"happy","shot":"wide"},
                landscape="forest")
            self.assertGreater(video.stat().st_size,1500)
            p = subprocess.run(
                ["ffprobe","-v","error","-count_frames",
                 "-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_read_frames",
                 "-of","json",str(video)],
                check=True,capture_output=True,text=True,timeout=90)
            info=json.loads(p.stdout)["streams"][0]
            self.assertEqual(info["codec_name"],"h264")
            self.assertEqual((info["width"],info["height"]),(1280,720))
            self.assertGreaterEqual(int(info["nb_read_frames"]),24)


if __name__=="__main__":
    unittest.main()
