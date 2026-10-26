"""Action-follow camera stays inside approved crops and encodes actual H.264."""
from __future__ import annotations

import json
from math import sin
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.cinematic_camera import (
    CAMERA_VERSION, PROFILES, framing_filter, framing_metadata,
)
from automate_ytb.animated_forest import render_motion_clip


class ActionFollowCameraTests(unittest.TestCase):
    def test_authored_run_and_jump_use_bounded_reactive_motion(self):
        self.assertIn("v3", CAMERA_VERSION)
        for shot in PROFILES:
            baseline = framing_filter(
                shot,width=1280,height=720,fps=24,
                scene_index=2,duration=2.8)
            run = framing_filter(
                shot,width=1280,height=720,fps=24,
                scene_index=2,duration=2.8,action="run")
            jump = framing_filter(
                shot,width=1280,height=720,fps=24,
                scene_index=2,duration=2.8,action="jump")
            self.assertNotIn("movie=",run+jump)
            self.assertIn("format=yuv420p",run)
            if shot == "wide":
                self.assertEqual(baseline,run)
                self.assertEqual(baseline,jump)
            else:
                self.assertNotEqual(run,baseline)
                self.assertNotEqual(jump,baseline)
                self.assertIn("sin(n/24*1.40)",run)
                self.assertIn("mod(n/24,1.75)",jump)
                self.assertIn("16*(",run)
                self.assertTrue(framing_metadata(shot)["actionFollowing"])
        self.assertFalse(framing_metadata("wide")["actionFollowing"])

    def test_mathematical_margins_cover_all_frames(self):
        for shot,(cw,ch,x,y,dx,dy) in PROFILES.items():
            if shot == "wide":
                continue
            for scene_index in (1,2):
                for fps in (24,30):
                    nframes=round(4.2*fps)
                    follow_x=min(5,dx//3)
                    follow_y=min(6,dy-1)
                    for frame in range(nframes):
                        p=frame/(nframes-1)
                        eased=3*p*p-2*p*p*p
                        travel=2*eased-1 if scene_index%2 else 1-2*eased
                        envelope=16*p*p*(1-p)*(1-p)
                        sec=frame/fps
                        cx=x+(dx-follow_x)*travel+follow_x*envelope*sin(sec*1.40)
                        clock=sec%1.75
                        rise=min(1,max(0,(clock-.18)/.57))
                        fall=min(1,max(0,(clock-.75)/.64))
                        smooth=lambda v:v*v*(3-2*v)
                        arc=smooth(rise)-smooth(fall)
                        cy=y+(dy-follow_y)*travel-follow_y*envelope*arc
                        self.assertGreaterEqual(cx,-0.0001)
                        self.assertLessEqual(cx+cw,1280.0001)
                        self.assertGreaterEqual(cy,-0.0001)
                        self.assertLessEqual(cy+ch,720.0001)

    def test_invalid_action_cannot_supply_filters(self):
        for action in ("jump;movie=/etc/passwd",{},["run"],123):
            with self.assertRaises(ValueError):
                framing_filter("medium",width=1280,height=720,fps=24,
                               scene_index=1,duration=2,action=action)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real offline H.264 encode needed")
    def test_jump_follow_is_encodable_without_resizing_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"action-camera.mp4"
            render_motion_clip(
                kind="rabbit",topic="Original rabbit leaps by the meadow",
                narration="Le lapin saute dans une prairie.",
                scene_index=1,scene_count=2,style="cartoon",
                duration=1.1,width=1280,height=720,fps=24,
                destination=output,landscape="meadow",
                direction={"weather":"day","action":"jump",
                           "emotion":"happy","shot":"medium"})
            self.assertGreater(output.stat().st_size,1000)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height",
                 "-of","json",str(output)],
                capture_output=True,text=True,check=True,timeout=40)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
