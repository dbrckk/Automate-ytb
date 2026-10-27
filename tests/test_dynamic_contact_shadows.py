"""A character's soft contact shadow must respond to jump/fly height.

The animated alpha remains on a small original 280x92 sprite rather than
causing a full-resolution per-pixel effect on the 720p video.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automate_ytb.ground_contact import (
    GROUND_VERSION, draw_contact_shadow, shadow_alpha_curve, shadow_stage)


class HeightAwareShadowTests(unittest.TestCase):
    def test_only_airborne_actions_change_shadow_opacity(self):
        self.assertIn("v2", GROUND_VERSION)
        for action in ("walk", "run", "idle", "rest", "talk", "surprise"):
            self.assertIsNone(shadow_alpha_curve(action))
            graph = shadow_stage(
                body_x="180+3*sin(t*2)", ground_y=608,
                offset_x=45, image_index=8, action=action)
            self.assertNotIn("geq=", graph)
        for action in ("jump", "fly"):
            curve = shadow_alpha_curve(action)
            self.assertIsInstance(curve, str)
            self.assertLess(len(curve), 150)
            self.assertNotIn(";", curve)
            graph = shadow_stage(
                body_x="180+3*sin(t*2)", ground_y=608,
                offset_x=45, image_index=8, action=action)
            self.assertIn("geq=", graph)
            self.assertIn("format=rgba[contacttexture]", graph)
            self.assertIn("[shadowstage];", graph)
        self.assertIn("mod(T,1.75)", shadow_alpha_curve("jump"))
        self.assertIn("T*5.3", shadow_alpha_curve("fly"))
        with self.assertRaises(ValueError):
            shadow_alpha_curve("jump;movie=/tmp/leak")
        with self.assertRaises(ValueError):
            shadow_stage(body_x="180",ground_y=608,
                         offset_x=45,image_index=8,action="external")

    @unittest.skipUnless(shutil.which("ffmpeg"),
                         "FFmpeg required to verify real dynamic alpha")
    def test_jump_apex_is_transparently_lighter_than_takeoff_and_landing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            input_png = root/"shadow.png"
            output_raw = root/"frames.rgba"
            draw_contact_shadow(
                input_png, actor="rabbit", weather="day", action="jump")
            curve = shadow_alpha_curve("jump")
            ff_filter = (
                "format=gbrap,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                f"a='alpha(X,Y)*({curve})',format=rgba"
            )
            subprocess.run([
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
                "-y","-threads","1","-filter_threads","1",
                "-loop","1","-framerate","24","-i",str(input_png),
                "-vf",ff_filter,
                "-frames:v","36","-pix_fmt","rgba",
                "-f","rawvideo",str(output_raw)],
                check=True, timeout=90, capture_output=True)
            raw = output_raw.read_bytes()
            width,height = 280,92
            size = width*height*4
            self.assertEqual(len(raw),size*36)
            def opacity(frame):
                return raw[frame*size+(54*width+140)*4+3]
            start, apex, landing = opacity(0),opacity(19),opacity(34)
            self.assertGreater(start,30)
            self.assertLess(apex,start*0.65)
            self.assertGreater(landing,apex*1.8)
            self.assertGreater(landing,start*0.85)


if __name__ == "__main__":
    unittest.main()
