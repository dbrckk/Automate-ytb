"""Independent animated costume cloth: exact poster/MP4 assets and safety."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.scarf_motion import (
    ANCHORS, CLOTH_VERSION, SCARF_SIZE,
    append_scarf, draw_scarf_tail, scarf_position,
)
from automate_ytb.animated_forest import render_layers as forest_layers
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_layers as owl_layers
from automate_ytb.animated_owl import render_motion_clip as owl_clip


class IndependentScarfTests(unittest.TestCase):
    def test_every_supported_animal_has_original_transparent_cloth(self):
        self.assertIn("v1", CLOTH_VERSION)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for actor in ANCHORS:
                first = root / (actor + "_1.png")
                second = root / (actor + "_2.png")
                draw_scarf_tail(first, actor=actor)
                draw_scarf_tail(second, actor=actor)
                self.assertEqual(first.read_bytes(), second.read_bytes())
                with Image.open(first) as image:
                    self.assertEqual(image.mode, "RGBA")
                    self.assertEqual(image.size, SCARF_SIZE)
                    self.assertEqual(image.getpixel((0,0))[3], 0)
                    self.assertGreater(image.getchannel("A").getbbox()[2], 65)
            with self.assertRaises(ValueError):
                draw_scarf_tail(root/"unknown.png", actor="unlicensed")

    def test_motion_follows_torso_and_reacts_to_action(self):
        for actor in ANCHORS:
            x,y=scarf_position("idle",actor=actor)
            self.assertIn("sin(t*1.1-0.55)", x)
            self.assertIn("sin(t*0.693-0.75)", y)
            self.assertNotIn(";",x+y)
            jump=scarf_position("jump",actor=actor)
            run=scarf_position("run",actor=actor)
            self.assertNotEqual(jump,run)
            self.assertIn("mod(t,1.75)",jump[1])
        with self.assertRaises(ValueError):
            scarf_position("run;movie=foo",actor="fox")
        with self.assertRaises(ValueError):
            scarf_position("run",actor="unlicensed")

    def test_graph_indices_and_no_external_expressions(self):
        graph,label,keys=append_scarf(
            graph="[0:v]null[g]",label="g",names=["background","body"],
            x="180+5*sin(t*2.3)",y="410+sin(t)")
        self.assertEqual(label,"scarfcomposed")
        self.assertEqual(keys,["background","body","scarf_tail"])
        self.assertIn("[g][2:v]overlay=",graph)
        with self.assertRaises(ValueError):
            append_scarf(graph="",label="g",names=["background"],
                         x="200;movie=/etc/passwd",y="400")
        with self.assertRaises(ValueError):
            append_scarf(graph="",label="g",names=["background","scarf_tail"],
                         x="180",y="420")

    def test_original_sprite_layers_include_fabric(self):
        with tempfile.TemporaryDirectory() as tmp:
            common=dict(topic="Original story", narration="The animal talks.",
                        scene_index=1,scene_count=2,style="cartoon")
            for actor in ("fox","rabbit","cat"):
                layers=forest_layers(Path(tmp)/actor,kind=actor,**common)
                self.assertTrue(layers["scarf_tail"].is_file())
            owl=owl_layers(Path(tmp)/"owl",**common)
            self.assertTrue(owl["scarf_tail"].is_file())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg output required")
    def test_real_video_weather_and_fabric_sprite_both_encode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            common=dict(topic="Original scarf story",scene_index=1,
                        scene_count=2,style="cartoon",duration=1.0,
                        width=1280,height=720,fps=24)
            for actor in ("fox","owl"):
                output=root/(actor+".mp4")
                options=dict(
                    narration="The fox runs in the rain." if actor=="fox" else
                              "The owl jumps by moonlight.",
                    direction={"weather":"rain" if actor=="fox" else "night",
                               "action":"run" if actor=="fox" else "jump",
                               "emotion":"happy","shot":"wide"})
                if actor=="fox":
                    forest_clip(kind="fox",destination=output,**common,**options)
                else:
                    owl_clip(destination=output,**common,**options)
                self.assertGreater(output.stat().st_size,1500)
                result=subprocess.run(
                    ["ffprobe","-v","error","-select_streams","v:0",
                     "-show_entries","stream=codec_name,width,height",
                     "-of","json",str(output)],
                    capture_output=True,text=True,check=True,timeout=40)
                stream=json.loads(result.stdout)["streams"][0]
                self.assertEqual(stream["codec_name"],"h264")
                self.assertEqual((stream["width"],stream["height"]),(1280,720))


if __name__=="__main__":
    unittest.main()
