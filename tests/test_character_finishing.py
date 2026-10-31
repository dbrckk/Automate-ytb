"""V2 facial polish and natural scene-indexed blink regression."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image
from automate_ytb.character_finishing import (
    DETAIL_VERSION, finish_forest_face, finish_owl_feathers)
from automate_ytb.choreography import blink_enable, CHOREOGRAPHY_VERSION
from automate_ytb.animated_forest import _sprite_body, render_motion_clip


class CharacterFinishingTests(unittest.TestCase):
    def test_original_fur_and_feather_accents_are_soft_and_deterministic(self):
        self.assertIn("v1", DETAIL_VERSION)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p1,p2 = root/"fox1.png",root/"fox2.png"
            _sprite_body(p1,kind="fox",blink=False,emotion="happy",gaze="forward")
            _sprite_body(p2,kind="fox",blink=False,emotion="happy",gaze="forward")
            self.assertEqual(p1.read_bytes(),p2.read_bytes())
            with Image.open(p1) as im:
                self.assertEqual(im.mode,"RGBA")
                self.assertEqual(im.size,(350,440))
            blank=Image.new("RGBA",(350,440))
            finish_forest_face(blank,kind="rabbit")
            self.assertEqual(blank.getpixel((0,0))[3],0)
            self.assertGreater(blank.getchannel("A").getbbox()[2],200)
            with self.assertRaises(ValueError):
                finish_forest_face(blank,kind="owl")
            owl=Image.new("RGBA",(322,430))
            finish_owl_feathers(owl)
            self.assertEqual(owl.getpixel((0,0))[3],0)
            self.assertGreater(owl.getchannel("A").getbbox()[3],350)

    def test_variable_blinks_and_reaction_double_blink_are_safe(self):
        self.assertIn("v10", CHOREOGRAPHY_VERSION)
        initial=blink_enable("idle",scene_index=1)
        other=blink_enable("idle",scene_index=2)
        self.assertNotEqual(initial,other)
        self.assertEqual(initial,blink_enable("idle",scene_index=1))
        self.assertIn("mod(t+",initial)
        self.assertNotIn(";",initial)
        surprise=blink_enable("surprise",scene_index=1)
        self.assertIn("between(t,0.10,0.20)",surprise)
        self.assertIn("between(t,0.33,0.42)",surprise)
        self.assertIn("0.18",blink_enable("rest",scene_index=2))
        for bad in (0,-1,1201,True):
            with self.assertRaises(ValueError):
                blink_enable("walk",scene_index=bad)
        with self.assertRaises(ValueError):
            blink_enable("run;movie=private",scene_index=2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Must validate FFmpeg expressions with a real encoded MP4")
    def test_surprise_blink_and_character_detail_encode(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"expressive-cat.mp4"
            render_motion_clip(
                kind="cat",topic="An original expressive cartoon",
                narration="Le chat est surpris dans le jardin.",
                scene_index=3,scene_count=4,style="cartoon",
                duration=0.9,width=1280,height=720,fps=24,destination=output,
                direction={"weather":"day","action":"surprise",
                           "emotion":"surprised","shot":"wide"})
            self.assertGreater(output.stat().st_size,1000)
            result=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height",
                 "-of","json",str(output)],check=True,capture_output=True,
                text=True,timeout=60)
            stream=json.loads(result.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))


if __name__=="__main__":
    unittest.main()
