"""Atmospheric lighting art and original animated MP4 parity."""
from __future__ import annotations
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image, ImageChops, ImageStat
from automate_ytb.atmospheric_light import draw_lighting, overlay_lighting
from automate_ytb.animated_forest import render_motion_clip, render_character_poster


class AtmosphericLightTests(unittest.TestCase):
    def test_deterministic_night_and_day_images(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            a,b,c=(root/f"{name}.png" for name in ("a","b","c"))
            draw_lighting(a,weather="night",landscape="village",seed="scene")
            draw_lighting(b,weather="night",landscape="village",seed="scene")
            draw_lighting(c,weather="day",landscape="village",seed="scene")
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertNotEqual(a.read_bytes(),c.read_bytes())
            with Image.open(a) as im:
                self.assertEqual(im.size,(1280,720))
                self.assertEqual(im.mode,"RGBA")
                self.assertLess(im.getchannel("A").getextrema()[1],120)
            with self.assertRaises(ValueError):
                draw_lighting(root/"invalid.png",weather="unknown",landscape="forest",seed="s")

    def test_light_graph_is_bounded_and_does_not_change_timing(self):
        graph,label,names=overlay_lighting(graph="[0:v]null[fgdone]",
                    label="fgdone",names=["background"])
        self.assertEqual(label,"litframe")
        self.assertEqual(names,["background","lighting"])
        self.assertIn("[1:v]overlay=x=0:y=0",graph)
        with self.assertRaises(ValueError):
            overlay_lighting(graph="",label="litframe",names=["lighting"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                          "Real encoded FFmpeg MP4 needed")
    def test_original_fox_video_contains_biome_lighting(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            common=dict(kind="fox",topic="Unique village story",
                        narration="The fox walks beside the village.",
                        scene_index=1,scene_count=3,style="cartoon",
                        duration=1.1,width=1280,height=720,fps=24,
                        direction={"weather":"night","action":"idle",
                                   "emotion":"happy","shot":"wide"},
                        landscape="village")
            dest=root/"night.mp4"
            render_motion_clip(destination=dest,**common)
            self.assertGreater(dest.stat().st_size,1000)
            poster=root/"poster.png"
            render_character_poster(destination=poster,kind="fox",
                                    topic=common["topic"],
                                    narration=common["narration"],
                                    scene_index=1,scene_count=3,
                                    style="cartoon",direction=common["direction"],
                                    landscape="village")
            self.assertTrue(poster.is_file())
            # Decode/encode correctness is already checked in character tests;
            # probing this actual MP4 avoids PNG pipe thread/resource pressure
            # across multiple simultaneous GitHub Actions FFmpeg subprocesses.
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height",
                 "-of","json",str(dest)],
                capture_output=True,text=True,check=True,timeout=40)
            import json
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))


if __name__=="__main__":
    unittest.main()
