"""Airborne actors cast smaller soft shadows while staying ground-anchored."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.ground_contact import (
    GROUND_VERSION, draw_contact_shadow, shadow_stage, shadow_lift)
from automate_ytb.action_timeline import choreograph


class DynamicShadowTests(unittest.TestCase):
    def test_jump_clearance_matches_authored_timebase(self):
        self.assertIn("v2", GROUND_VERSION)
        j = shadow_lift("jump")
        self.assertIn("mod(t,1.75)", j)
        self.assertIn("0.18", j)
        self.assertIn("0.75", j)
        self.assertIn("0.64", j)
        self.assertNotIn(";", j)
        self.assertEqual(j, shadow_lift("jump"))
        self.assertIn("sin(t*5.3)", shadow_lift("fly"))
        for action in ("idle", "walk", "run", "rest", "talk", "surprise"):
            self.assertEqual(shadow_lift(action), "0")
        with self.assertRaises(ValueError):
            shadow_lift("jump;movie=/tmp/secret")

    def test_kinetic_shadow_graph_and_static_fast_path(self):
        plain = shadow_stage(body_x="180",ground_y=608,offset_x=45,image_index=8)
        self.assertNotIn("scale=", plain)
        animated = shadow_stage(body_x="180",ground_y=608,offset_x=45,
                                image_index=8,lift=shadow_lift("jump"))
        self.assertIn("scale=w=",animated)
        self.assertIn("eval=frame[shadowresized]",animated)
        self.assertIn("(280-overlay_w)/2",animated)
        self.assertIn("(92-overlay_h)/2",animated)
        self.assertIn("[shadowstage];",animated)
        for bad in ("1;movie=hack", "1:[evil]", "1'"):
            with self.assertRaises(ValueError):
                shadow_stage(body_x="180",ground_y=608,offset_x=45,
                             image_index=8,lift=bad)

    def test_narration_action_phases_blend_shadow_clearance(self):
        (lift,) = choreograph(
            narration="The fox walks, then jumps.",
            duration=3.0, fallback_action="walk",
            pose=lambda a: (shadow_lift(a),))
        self.assertIn("mod((t-",lift)
        self.assertIn("3-2*",lift)
        stage=shadow_stage(body_x="180",ground_y=608,
                           offset_x=45,image_index=8,lift=lift)
        self.assertIn("[shadowresized]",stage)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg encode is required")
    def test_shadow_footprint_visibly_shrinks_in_air(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            bg=root/"bg.png"
            shadow=root/"shadow.png"
            video=root/"height-aware.mp4"
            Image.new("RGB",(1280,720),(190,210,224)).save(bg)
            draw_contact_shadow(shadow,actor="fox",weather="day",action="jump")
            stage=shadow_stage(body_x="180",ground_y=608,offset_x=45,
                               image_index=1,lift=shadow_lift("jump"))
            graph=stage+"[shadowstage]format=yuv420p[out]"
            subprocess.run(
                ["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                 "-loop","1","-framerate","24","-i",str(bg),
                 "-loop","1","-framerate","24","-i",str(shadow),
                 "-filter_complex",graph,"-map","[out]",
                 "-frames:v","28","-r","24","-c:v","libx264",
                 "-threads","2","-pix_fmt","yuv420p",str(video)],
                check=True,capture_output=True,timeout=90)
            probe=subprocess.run(
                ["ffprobe","-v","error","-count_frames",
                 "-select_streams","v:0","-show_entries",
                 "stream=codec_name,width,height,nb_read_frames",
                 "-of","json",str(video)],
                check=True,capture_output=True,text=True,timeout=45)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual(int(stream["nb_read_frames"]),28)
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            def pixel_at(sec):
                png=root/f"frame-{sec}.png"
                subprocess.run(["ffmpeg","-nostdin","-v","error",
                    "-ss",str(sec),"-i",str(video),"-frames:v","1",
                    "-y",str(png)],check=True,capture_output=True,timeout=45)
                with Image.open(png) as img:
                    return img.convert("RGB").getpixel((460,654))
            # Airborne ellipse is narrower, so its original outer rim
            # returns to the unshadowed background tone near the apex.
            on_ground=pixel_at(.03)
            airborne=pixel_at(.75)
            self.assertGreater(sum(airborne)-sum(on_ground),35)


if __name__ == "__main__":
    unittest.main()
