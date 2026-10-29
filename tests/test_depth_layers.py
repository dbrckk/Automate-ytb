"""Actual layered parallax and deterministic original foreground regression."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image, ImageChops, ImageStat

from automate_ytb.depth_layers import draw_foreground, split_foreground, overlay_foreground, WEATHER_SWAY
from automate_ytb.animated_forest import render_motion_clip, render_character_poster


class LayeredDepthTests(unittest.TestCase):
    def test_deterministic_distinct_translucent_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a,b,c=[root/(v+".png") for v in ("a","b","c")]
            draw_foreground(a,landscape="meadow",seed="one")
            draw_foreground(b,landscape="meadow",seed="one")
            draw_foreground(c,landscape="river",seed="one")
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertNotEqual(a.read_bytes(),c.read_bytes())
            with Image.open(a) as im:
                self.assertEqual(im.size,(1280,720))
                self.assertEqual(im.mode,"RGBA")
                self.assertEqual(im.getpixel((400,300))[3],0)
                self.assertGreater(im.getchannel("A").getbbox()[2],1100)
            with self.assertRaises(ValueError):
                draw_foreground(root/"bad.png",landscape="invalid",seed="safe")

    def test_overlay_does_not_shift_timeline(self):
        graph,label,inputs=overlay_foreground(
            graph="[0:v]null[g]",label="g",names=["background"],
            scene_index=2,duration=3.5)
        self.assertEqual(label,"fgdone")
        self.assertEqual(inputs,["background","foreground_left","foreground_right"])
        self.assertIn("sin(t*0.63)",graph)
        self.assertIn("[2:v]overlay",graph)
        self.assertIn("[fgleftrender]",graph)
        self.assertIn("[1:v]",graph)
        with self.assertRaises(ValueError):
            overlay_foreground(graph="",label="g",names=[],scene_index=0,duration=2)

    def test_split_rebuilds_identical_plate_without_seams(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            original, left, right = (folder / f"{name}.png"
                                      for name in ("original", "left", "right"))
            draw_foreground(original, landscape="forest", seed="split-test")
            split_foreground(original, left, right)
            with Image.open(original) as source, Image.open(left) as lhs, Image.open(right) as rhs:
                self.assertEqual(lhs.size, (1280,720))
                self.assertEqual(rhs.size, (1280,720))
                self.assertIsNone(lhs.getchannel("A").crop((640,0,1280,720)).getbbox())
                self.assertIsNone(rhs.getchannel("A").crop((0,0,640,720)).getbbox())
                combined = lhs.copy()
                combined.alpha_composite(rhs)
                self.assertIsNone(ImageChops.difference(source, combined).getbbox())
            with self.assertRaises(ValueError):
                split_foreground(original, left, left)

    def test_storm_wind_is_stronger_and_independent_of_calm(self):
        args = dict(graph="[0:v]null[g]", label="g", names=["background"],
                    scene_index=3, duration=2.8)
        clear, _, _ = overlay_foreground(**args, weather="day")
        storm, _, _ = overlay_foreground(**args, weather="storm")
        self.assertNotEqual(clear, storm)
        self.assertIn("8*sin(t*1.72)", storm)
        self.assertIn("sin(t*1.428)", storm)
        self.assertEqual(set(WEATHER_SWAY),
                         {"day","night","cloudy","rain","wind","storm"})
        with self.assertRaises(ValueError):
            overlay_foreground(**args, weather="storm;movie=secret")
        with self.assertRaises(ValueError):
            overlay_foreground(**args, weather="day", scene_index=0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real encoded FFmpeg video required")
    def test_real_mp4_foreground_has_natural_motion(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"river.mp4"
            render_motion_clip(
                kind="fox",topic="Original river story",
                narration="The fox walks along the river.",
                scene_index=1,scene_count=3,style="cartoon",
                duration=1.8,width=1280,height=720,fps=24,
                destination=p,landscape="river",
                direction={"weather":"day","action":"idle",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(p.stat().st_size,1200)
            def frame(t):
                result=subprocess.run(
                    ["ffmpeg","-nostdin","-loglevel","error","-ss",str(t),
                     "-i",str(p),"-frames:v","1","-f","image2pipe",
                     "-vcodec","png","-"],
                    check=True,capture_output=True,timeout=90)
                with Image.open(io.BytesIO(result.stdout)) as im:
                    return im.convert("RGB")
            first,last=frame(.20),frame(1.45)
            self.assertEqual(first.size,(1280,720))
            delta=ImageChops.difference(first.crop((1140,530,1280,710)),
                                        last.crop((1140,530,1280,710)))
            self.assertGreater(sum(ImageStat.Stat(delta).mean),0.2)


if __name__=="__main__":
    unittest.main()
