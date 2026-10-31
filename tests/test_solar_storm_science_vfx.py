"""Real original scientific animation inserts, not motion on stock images."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from production.solar_storm import render_short as solar
from production.solar_storm.science_vfx import (
    ENGINE, INSERTS, FPS, W, H, render_frame, render_insert,
)


class OriginalScienceAnimationTests(unittest.TestCase):
    def test_five_original_shots_match_correct_narrated_sources(self):
        flattened=[(scene,key) for scene,plan in enumerate(solar.SHOT_PLAN)
                   for key,_,_ in plan]
        self.assertEqual(len(flattened),13)
        self.assertEqual(set(INSERTS), {1,5,7,9,12})
        expected=("flare","cme","shield","satellite","connection")
        self.assertEqual(tuple(INSERTS[i][0] for i in sorted(INSERTS)),
                         expected)
        expected_scenes={1:0,5:2,7:3,9:4,12:5}
        for i,(kind,key) in INSERTS.items():
            with self.subTest(shot=i+1):
                self.assertEqual(flattened[i],(expected_scenes[i],key))
        solar.validate_storyboard()

    def test_each_frame_is_unique_art_not_a_zoomed_still(self):
        data=[]
        for kind,_ in INSERTS.values():
            with self.subTest(kind=kind):
                a=render_frame(kind,.1,3.1)
                b=render_frame(kind,1.6,3.1)
                c=render_frame(kind,.1,3.1)
                self.assertEqual((a.size,a.mode),((W,H),"RGB"))
                self.assertEqual(a.tobytes(),c.tobytes())
                self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
                small=ImageChops.difference(
                    a.crop((60,300,480,747)),
                    b.crop((60,300,480,747)))
                self.assertGreater(max(ImageStat.Stat(small).mean),.3)
                data.append(a.crop((95,350,450,760)).tobytes())
        self.assertEqual(len(set(data)),5)

    def test_invalid_animation_times_and_sources_are_blocked(self):
        for kind,t,duration in (("fake",0,3),("cme",-1,3),
                                ("shield",float("nan"),3),
                                ("satellite",1,0),("flare",5,3),
                                ("cme",True,3),("connection",0,True)):
            with self.subTest(kind=kind,t=t),self.assertRaises(ValueError):
                render_frame(kind,t,duration)
        with self.assertRaises(ValueError):
            render_insert("cme",0,Path("discard.mp4"))
        with self.assertRaises(ValueError):
            render_insert("unsupported",2,Path("discard.mp4"))

    def test_real_ffmpeg_encodes_not_stills_and_preserves_native_timing(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"real-original-science.mp4"
            report=render_insert("cme",.87,path,preset="ultrafast")
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size,10000)
            self.assertEqual(report["engine"],ENGINE)
            self.assertTrue(report["original_art"])
            self.assertFalse(report["publish_approved"])
            details=subprocess.run([
                "ffprobe","-v","error","-of","json",
                "-show_entries","stream=codec_name,width,height,r_frame_rate:"
                                "format=duration",str(path)
            ],check=True,capture_output=True,text=True,timeout=12)
            info=json.loads(details.stdout)
            video=info["streams"][0]
            self.assertEqual(video["codec_name"],"h264")
            self.assertEqual((video["width"],video["height"]),(1080,1920))
            self.assertEqual(video["r_frame_rate"],"30/1")
            self.assertAlmostEqual(float(info["format"]["duration"]),.87,
                                   delta=.06)
            decoded=[]
            for t in (.05,.64):
                png=Path(tmp)/f"frame_{t:.2f}.png"
                subprocess.run([
                    "ffmpeg","-y","-v","error","-ss",str(t),"-i",str(path),
                    "-frames:v","1",str(png)
                ],check=True,timeout=25)
                with Image.open(png) as image:
                    decoded.append(image.convert("RGB").resize((135,240)))
            self.assertGreater(
                max(ImageStat.Stat(ImageChops.difference(*decoded)).mean),
                .4,"Encoded original science video must genuinely animate")

if __name__=="__main__":
    unittest.main()
