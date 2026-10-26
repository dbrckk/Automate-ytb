"""Ground-contact shadows remain original, deterministic and beneath actors."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image
from automate_ytb.ground_contact import (
    GROUND_VERSION, draw_contact_shadow, shadow_stage)
from automate_ytb.animated_forest import render_layers as forest_layers
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_forest import render_character_poster as forest_poster
from automate_ytb.animated_owl import render_layers as owl_layers
from automate_ytb.animated_owl import render_character_poster as owl_poster


class GroundShadowTests(unittest.TestCase):
    def test_shadow_is_soft_translucent_deterministic(self):
        self.assertIn("v1", GROUND_VERSION)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = [root / name for name in ("first.png","second.png","night.png")]
            draw_contact_shadow(paths[0], actor="fox", weather="day", action="idle")
            draw_contact_shadow(paths[1], actor="fox", weather="day", action="idle")
            draw_contact_shadow(paths[2], actor="fox", weather="night", action="fly")
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            self.assertNotEqual(paths[0].read_bytes(), paths[2].read_bytes())
            with Image.open(paths[0]) as im:
                self.assertEqual(im.mode, "RGBA")
                self.assertEqual(im.size, (280,92))
                self.assertEqual(im.getpixel((0,0))[3], 0)
                self.assertGreater(im.getpixel((140,54))[3], 20)
                self.assertLess(im.getpixel((140,54))[3], 130)
            with self.assertRaises(ValueError):
                draw_contact_shadow(root/"bad.png",actor="external",
                                    weather="day",action="idle")

    def test_only_internal_pose_may_position_grounded_underlay(self):
        result = shadow_stage(body_x="180+16*sin(t*0.7)",
                              ground_y=608,offset_x=45,image_index=8)
        self.assertIn("[0:v][8:v]overlay=",result)
        self.assertIn("[shadowstage];",result)
        self.assertIn("y=608",result)
        with self.assertRaises(ValueError):
            shadow_stage(body_x="180;movie=secret",ground_y=608,
                         offset_x=45,image_index=8)
        with self.assertRaises(ValueError):
            shadow_stage(body_x="180",ground_y=900,
                         offset_x=45,image_index=8)

    def test_original_posters_and_layers_include_contact_shadow(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            kw = dict(topic="Once upon a time",narration="The fox jumps.",
                      scene_index=1,scene_count=2,style="cartoon",
                      direction={"weather":"day","action":"jump",
                                 "emotion":"happy","shot":"wide"})
            fox = forest_layers(root/"fox",kind="fox",**kw)
            owl = owl_layers(root/"owl",**kw)
            self.assertTrue(fox["shadow"].is_file())
            self.assertTrue(owl["shadow"].is_file())
            first, second = root/"fox-poster.png",root/"owl-poster.png"
            forest_poster(kind="fox",destination=first,**kw)
            owl_poster(destination=second,**kw)
            with Image.open(first) as im:
                self.assertEqual(im.size,(1280,720))
            with Image.open(second) as im:
                self.assertEqual(im.size,(1280,720))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real encoded MP4 required")
    def test_fox_jump_with_grounded_layer_encodes(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"contact-jump.mp4"
            forest_clip(
                kind="rabbit",topic="Original story",
                narration="The rabbit jumps.",scene_index=1,
                scene_count=2,style="cartoon",duration=.9,
                width=1280,height=720,fps=24,destination=output,
                direction={"weather":"day","action":"jump",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(output.stat().st_size,1000)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height",
                 "-of","json",str(output)],
                capture_output=True,text=True,check=True,timeout=40)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))


if __name__ == "__main__":
    unittest.main()
