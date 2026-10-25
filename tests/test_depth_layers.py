"""Actual layered parallax and deterministic original foreground regression."""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from PIL import Image, ImageChops, ImageStat

from automate_ytb.depth_layers import draw_foreground, overlay_foreground
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
        self.assertEqual(inputs,["background","foreground"])
        self.assertIn("sin(t*0.63)",graph)
        self.assertIn("[1:v]",graph)
        with self.assertRaises(ValueError):
            overlay_foreground(graph="",label="g",names=[],scene_index=0,duration=2)

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
