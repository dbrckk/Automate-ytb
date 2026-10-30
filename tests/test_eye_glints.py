"""Original gaze-aligned micro-highlights remain attached, safe and decodable."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image
from automate_ytb.eye_glints import (
    ACTORS, GAZES, EYE_VERSION, draw_eye_glints, eye_overlay_expression)
from automate_ytb.animated_forest import render_layers as fox_layers
from automate_ytb.animated_forest import render_motion_clip as fox_clip
from automate_ytb.animated_owl import render_layers as owl_layers
from automate_ytb.animated_owl import render_motion_clip as owl_clip


class EyeMicroActingTests(unittest.TestCase):
    def test_original_gaze_plates_are_deterministic_and_transparent(self):
        self.assertIn("v1", EYE_VERSION)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for actor in ACTORS:
                for gaze in GAZES:
                    with self.subTest(actor=actor, gaze=gaze):
                        a, b = folder/"a.png", folder/"b.png"
                        draw_eye_glints(a, actor=actor, gaze=gaze)
                        draw_eye_glints(b, actor=actor, gaze=gaze)
                        self.assertEqual(a.read_bytes(), b.read_bytes())
                        with Image.open(a) as image:
                            self.assertEqual(image.mode, "RGBA")
                            self.assertEqual(image.size,
                                             (322,430) if actor=="owl" else (350,440))
                            self.assertEqual(image.getpixel((0,0))[3], 0)
                            self.assertGreater(image.getchannel("A").getbbox()[2], 150)
            with self.assertRaises(ValueError):
                draw_eye_glints(folder/"invalid.png",actor="unknown",gaze="forward")
            with self.assertRaises(ValueError):
                draw_eye_glints(folder/"invalid.png",actor="owl",gaze="secret")

    def test_trusted_motion_overlay_and_unsafe_input_rejection(self):
        for label, index in (("c",11),("d",8),("c",14)):
            text = eye_overlay_expression(
                body_x="180+2*sin(t)",body_y="184+2*sin(t*0.6)",
                input_index=index,from_label=label)
            self.assertIn(f"[{label}][{index}:v]overlay=",text)
            self.assertIn("enable='gte(t,0.6)'",text)
            self.assertIn("[eyeacting];",text)
            self.assertNotIn("movie=",text)
        with self.assertRaises(ValueError):
            eye_overlay_expression(body_x="180;movie=secrets",
                    body_y="184",input_index=11,from_label="c")
        with self.assertRaises(ValueError):
            eye_overlay_expression(body_x="180",body_y="184",
                    input_index=25,from_label="c")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Requires a real H.264 encoder and decoder")
    def test_original_owl_and_companion_fox_mp4_encode_and_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            inputs=dict(topic="Original animal story",scene_index=1,
                        scene_count=2,style="cartoon",duration=0.8,
                        width=1280,height=720,fps=24,
                        direction=dict(weather="day",action="idle",
                                       emotion="curious",shot="wide"))
            for animal,renderer,narration in (
                    ("owl",owl_clip,"The owl looks toward the river."),
                    ("fox",fox_clip,"The fox and rabbit explore the forest together.")):
                path=folder/f"{animal}.mp4"
                arguments=dict(inputs,narration=narration,destination=path)
                if animal=="fox":
                    arguments["kind"]="fox"
                renderer(**arguments)
                self.assertGreater(path.stat().st_size,1800)
                checked=subprocess.run(
                    ["ffprobe","-v","error","-count_frames",
                     "-select_streams","v:0",
                     "-show_entries","stream=codec_name,width,height,nb_read_frames",
                     "-of","json",str(path)],
                    capture_output=True,text=True,check=True,timeout=90)
                stream=json.loads(checked.stdout)["streams"][0]
                self.assertEqual(stream["codec_name"],"h264")
                self.assertEqual((stream["width"],stream["height"]), (1280,720))
                self.assertGreaterEqual(int(stream["nb_read_frames"]),19)


if __name__=="__main__":
    unittest.main()
