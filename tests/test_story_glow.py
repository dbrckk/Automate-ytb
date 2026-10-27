"""Narration controls which original glowing light sprites appear."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.story_glow import draw_story_glow, has_fireflies, append_story_glow
from automate_ytb.animated_forest import render_motion_clip, render_layers


class StoryGlowTests(unittest.TestCase):
    def test_multilingual_explicit_cues_not_vague_light(self):
        self.assertTrue(has_fireflies("Les lucioles brillent dans la prairie."))
        self.assertTrue(has_fireflies("Une luciole s'approche."))
        self.assertTrue(has_fireflies("The fireflies shimmer over water."))
        self.assertTrue(has_fireflies("The firefly circles the lantern."))
        self.assertFalse(has_fireflies("La lumière danse dans les arbres."))
        self.assertFalse(has_fireflies("The stars sparkle above the forest."))
        with self.assertRaises(ValueError):
            has_fireflies(None)

    def test_deterministic_light_plate_and_no_unsupported_actors(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            a,b,c=(root/x for x in ("a.png","b.png","c.png"))
            args=dict(narration="Des lucioles dans la rivière.",
                      seed="original-one",landscape="river")
            self.assertTrue(draw_story_glow(a,**args))
            self.assertTrue(draw_story_glow(b,**args))
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with Image.open(a) as img:
                self.assertEqual(img.size,(1280,720))
                self.assertEqual(img.mode,"RGBA")
                self.assertEqual(img.getpixel((400,290))[3],0)
                self.assertGreater(img.getchannel("A").getbbox()[2],680)
            self.assertFalse(draw_story_glow(c,narration="Une étoile apparaît.",
                                              seed="original-one"))
            self.assertFalse(c.exists())
            with self.assertRaises(ValueError):
                draw_story_glow(c,narration="Lucioles",seed="x",
                                landscape="unknown")

    def test_ffmpeg_glow_only_when_script_supports_it(self):
        initial="[0:v]null[base]"
        graph,label,inputs=append_story_glow(graph=initial,label="base",
                  names=["background"],enabled=False)
        self.assertEqual((graph,label,inputs),(initial,"base",["background"]))
        graph,label,inputs=append_story_glow(graph=initial,label="base",
                  names=["background"],enabled=True)
        self.assertEqual(label,"storyglowdone")
        self.assertEqual(inputs,["background","story_glow"])
        self.assertIn("[1:v]overlay=",graph)
        self.assertIn("sin(t*1.13)",graph)
        self.assertNotIn("movie=",graph)
        with self.assertRaises(ValueError):
            append_story_glow(graph=graph,label=label,names=inputs,enabled=True)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual H.264 encode requires FFmpeg")
    def test_original_animal_real_video_contains_script_light(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            args=dict(kind="fox",topic="Conte des lucioles",
                      narration="Les lucioles dansent au bord de la rivière.",
                      scene_index=1,scene_count=2,style="cartoon",
                      direction={"weather":"night","action":"idle",
                                 "emotion":"happy","shot":"wide"},
                      landscape="river")
            layers=render_layers(root/"layers",**args)
            self.assertIn("story_glow",layers)
            self.assertTrue(layers["story_glow"].is_file())
            video=root/"glowing.mp4"
            render_motion_clip(duration=1.0,width=1280,height=720,fps=24,
                               destination=video,**args)
            self.assertGreater(video.stat().st_size,1400)
            result=subprocess.run([
                "ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=codec_name,width,height",
                "-of","json",str(video)],
                capture_output=True,text=True,check=True,timeout=30)
            stream=json.loads(result.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))


if __name__=="__main__":
    unittest.main()
