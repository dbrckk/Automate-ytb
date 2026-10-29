"""Timed run contacts must match the planted-paw gait, not an unrelated loop."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.choreography import LEG_MOTION
from automate_ytb.motion_accents import (
    KINETIC_VERSION, append_motion_accent, draw_motion_accent)
from automate_ytb.animated_forest import render_motion_clip


class FootfallAccentTests(unittest.TestCase):
    def test_two_touchdowns_share_exact_gait_frequency(self):
        self.assertIn("v2", KINETIC_VERSION)
        graph, label, names = append_motion_accent(
            graph="[0:v]null[rig]", label="rig", names=["background"],
            action="run", body_x="180+27*sin(t*1.40)", foot_origin_x=180,
            ground_y=586)
        period=2*math.pi/LEG_MOTION["run"][2]
        self.assertEqual((label,names), ("motiondone",["background","motion"]))
        self.assertIn("split=2[footpuffleft][footpuffright]",graph)
        self.assertIn("[runstepA]",graph)
        self.assertIn(f"mod(t,{period:.6f})",graph)
        self.assertIn(f"mod(t+{period/2:.6f},{period:.6f})",graph)
        self.assertIn("x='(180)+68-125'",graph)
        self.assertIn("x='(180)+186-125'",graph)
        # The contact puffs do not inherit any oscillation from the torso.
        self.assertEqual(graph.count("180+27"),0)
        self.assertNotIn("0.55",graph)
        self.assertEqual(graph.count("enable="),2)
        for bad in (-1,901,True,"180;movie=secret"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                append_motion_accent(
                    graph="graph",label="rig",names=["background"],
                    action="run",body_x="180",foot_origin_x=bad,ground_y=586)

    def test_run_particles_are_centered_and_weather_specific(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            dry,wet=root/"dry.png",root/"wet.png"
            draw_motion_accent(dry,action="run",weather="day",
                               landscape="forest",seed="original fox")
            draw_motion_accent(wet,action="run",weather="rain",
                               landscape="river",seed="original fox")
            self.assertNotEqual(dry.read_bytes(),wet.read_bytes())
            with Image.open(dry) as im:
                alpha=im.getchannel("A")
                self.assertEqual(im.size,(300,110))
                box=alpha.getbbox()
                self.assertIsNotNone(box)
                self.assertGreater(box[0],40)
                self.assertLess(box[2],225)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real H.264 encoder and decoded video probe required")
    def test_real_running_fox_footfall_particle_video(self):
        with tempfile.TemporaryDirectory() as folder:
            destination=Path(folder)/"synchronized-fox-run.mp4"
            render_motion_clip(
                kind="fox",topic="Original forest sprint",
                narration="The fox runs through the forest.",
                scene_index=1,scene_count=2,style="cartoon",
                duration=0.9,width=1280,height=720,fps=24,
                destination=destination,landscape="forest",
                direction={"weather":"day","action":"run",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(destination.stat().st_size,1500)
            proc=subprocess.run(
                ["ffprobe","-v","error","-count_frames","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_read_frames",
                 "-of","json",str(destination)],
                check=True,capture_output=True,text=True,timeout=90)
            video=json.loads(proc.stdout)["streams"][0]
            self.assertEqual(video["codec_name"],"h264")
            self.assertEqual((video["width"],video["height"]),(1280,720))
            self.assertEqual(int(video["nb_read_frames"]),22)


if __name__=="__main__":
    unittest.main()
