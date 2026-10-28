"""Original animal walk/run ground planting and real H.264 regression.

This tests an important continuity property: grounded paw positions must
not inherit the body's breathing/bounce, while legs alternate swing phases.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.choreography import (
    CHOREOGRAPHY_VERSION, leg_position, body_position)
from automate_ytb.animated_forest import render_motion_clip


class GroundedPawsTests(unittest.TestCase):
    def test_stance_is_world_anchored_and_swing_alternates(self):
        self.assertIn("v7", CHOREOGRAPHY_VERSION)
        for action in ("walk", "run"):
            left_x, left_y = leg_position(action, side="left")
            right_x, right_y = leg_position(action, side="right")
            self.assertTrue(left_x.startswith("248+"))
            self.assertTrue(right_x.startswith("366+"))
            self.assertTrue(left_y.startswith("519-"))
            self.assertTrue(right_y.startswith("519-"))
            self.assertIn("max(0,sin(t*", left_x)
            self.assertIn("+0)", left_x)
            self.assertIn("+3.141593)", right_x)
            self.assertNotIn("sin(t*0.37)", left_x + right_x)
            self.assertNotIn("abs(sin(", left_y + right_y)
            self.assertNotEqual((left_x,left_y),(right_x,right_y))
            self.assertEqual((left_x,left_y),leg_position(action,side="left"))
            for value in (left_x,left_y,right_x,right_y):
                self.assertNotIn(";",value)
                self.assertNotIn("\n",value)
        # The torso continues moving independently while the feet plant.
        x,y=body_position("walk",x=180,y=184)
        self.assertIn("sin(t*0.37)",x)
        self.assertIn("abs(sin(",y)

    def test_non_gait_actions_remain_attached_to_body(self):
        for action in ("jump", "fly", "rest", "surprise", "talk"):
            x,y=leg_position(action,side="left")
            self.assertIn("(",x)
            self.assertIn("(",y)
            self.assertFalse(x.startswith("248+"))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Original video encoding requires FFmpeg")
    def test_24fps_gait_mp4_is_really_decodable(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"fox-run.mp4"
            render_motion_clip(
                kind="fox",topic="Original forest journey",
                narration="The fox runs through the forest.",
                scene_index=1,scene_count=3,style="cartoon",
                duration=1.05,width=1280,height=720,fps=24,
                destination=output,landscape="forest",
                direction={"weather":"day","action":"run",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(output.stat().st_size,1500)
            result=subprocess.run(
                ["ffprobe","-v","error","-count_frames",
                 "-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_read_frames",
                 "-of","json",str(output)],
                capture_output=True,text=True,check=True,timeout=50)
            stream=json.loads(result.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(int(stream["nb_read_frames"]),25)


if __name__=="__main__":
    unittest.main()
