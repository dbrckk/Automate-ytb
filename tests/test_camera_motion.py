"""Universal non-rig camera direction with actual FFmpeg/H.264 proof."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from automate_ytb.camera_motion import (
    ACTION_SPEED, SHOT_PATHS, VERSION, camera_filter,
)


class CameraMotionTests(unittest.TestCase):
    def test_all_authored_shots_and_actions_produce_distinct_safe_paths(self):
        paths = {}
        for shot in SHOT_PATHS:
            for action in ACTION_SPEED:
                expression = camera_filter(
                    1280, 720, fps=30, duration=6.1,
                    direction={"shot": shot, "action": action})
                self.assertIn("zoompan=", expression)
                self.assertIn("format=yuv420p", expression)
                self.assertNotIn("eval", expression)
                paths[(shot, action)] = expression
        self.assertGreaterEqual(len(set(paths.values())), len(SHOT_PATHS)*4)
        self.assertNotEqual(paths[("wide","walk")],
                            paths[("macro","walk")])
        self.assertIn("v1", VERSION)

    def test_bad_or_untrusted_director_data_is_rejected(self):
        for invalid in (
            {"shot":"../../etc/passwd"}, {"shot":"medium","action":"zoom=10"},
            {"action":None}, "medium"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    camera_filter(640,360,fps=24,duration=4,direction=invalid)
        for invalid in (float("nan"),float("inf"),0,-1,4000,True):
            with self.assertRaises(ValueError):
                camera_filter(640,360,fps=24,duration=invalid)
        with self.assertRaises(ValueError):
            camera_filter(640,360,fps=0,duration=4)
        with self.assertRaises(ValueError):
            camera_filter(0,360,fps=24,duration=4)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual local FFmpeg/H.264 required")
    def test_real_encoded_camera_move_keeps_all_frames_and_moves_subject(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            still=root/"original.png"
            mp4=root/"directed.mp4"
            image=Image.new("RGB",(480,270),(13,28,48))
            draw=ImageDraw.Draw(image)
            for x in range(0,480,32):
                draw.rectangle((x,0,x+12,269),fill=(x//2,180,50))
            draw.ellipse((165,70,280,190),fill=(255,220,40))
            image.save(still)
            cmd=[
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                "-loop","1","-framerate","12","-i",str(still),
                "-t","3","-vf",camera_filter(
                    480,270,fps=12,duration=3,
                    direction={"shot":"wide","action":"fly"}),
                "-threads","1","-c:v","libx264","-preset","ultrafast",
                "-pix_fmt","yuv420p",str(mp4)]
            subprocess.run(cmd,capture_output=True,check=True,timeout=45)
            meta=subprocess.run([
                "ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=width,height,nb_frames",
                "-of","default=noprint_wrappers=1",str(mp4)],
                capture_output=True,text=True,check=True,timeout=15).stdout
            self.assertIn("width=480",meta)
            self.assertIn("height=270",meta)
            self.assertIn("nb_frames=36",meta)
            frames=subprocess.run([
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                "-i",str(mp4),"-vf","scale=96:54,format=gray",
                "-f","rawvideo","-pix_fmt","gray","pipe:1"],
                capture_output=True,check=True,timeout=30).stdout
            frame_bytes=96*54
            self.assertEqual(len(frames),36*frame_bytes)
            self.assertNotEqual(frames[:frame_bytes],
                                frames[-frame_bytes:])
            # Reject any full black output from malformed zoompan coordinates.
            self.assertTrue(all(
                sum(frames[i:i+frame_bytes])/frame_bytes>12
                for i in range(0,len(frames),frame_bytes)))


if __name__=="__main__":
    unittest.main()
