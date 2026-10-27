"""Selective background focus, character sharpness and real encoding regressions."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

from automate_ytb.focus_depth import (
    FOCUS_RADII, FOCUS_VERSION, focus_metadata,
    focus_radius, soften_environment_plate,
)
from automate_ytb.animated_forest import render_layers as forest_layers
from automate_ytb.animated_owl import render_layers as owl_layers
from automate_ytb.animated_forest import render_motion_clip
from automate_ytb.cinematic_camera import PROFILES, framing_metadata


class CinematicFocusTests(unittest.TestCase):
    def test_all_camera_shots_have_safe_monotonic_focus(self):
        self.assertEqual(set(FOCUS_RADII), set(PROFILES))
        self.assertEqual(focus_radius("wide"), 0)
        self.assertLess(focus_radius("medium"), focus_radius("closeup"))
        self.assertLess(focus_radius("closeup"), focus_radius("macro"))
        for shot in PROFILES:
            self.assertLessEqual(focus_radius(shot), 7.2)
            self.assertLessEqual(focus_radius(shot, plane="ambient_far"),
                                 focus_radius(shot))
            record=focus_metadata(shot)
            self.assertEqual(record["version"], FOCUS_VERSION)
            self.assertEqual(framing_metadata(shot)["depthOfField"], record)
        for shot in ("macro;movie=/etc/passwd", "", "invalid"):
            with self.assertRaises(ValueError):
                focus_radius(shot)
        with self.assertRaises(ValueError):
            focus_radius("wide", plane="actor")

    def test_wide_plate_unchanged_macro_reduces_detail(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"painted.png"
            original=Image.new("RGB",(1280,720),(235,235,235))
            d=ImageDraw.Draw(original)
            for x in range(0,1280,16):
                d.rectangle((x,0,x+7,719),fill=(18,55,89))
            original.save(path,"PNG")
            raw=path.read_bytes()
            self.assertFalse(soften_environment_plate(path,shot="wide"))
            self.assertEqual(path.read_bytes(),raw)
            self.assertTrue(soften_environment_plate(path,shot="macro"))
            with Image.open(path) as img:
                processed=img.copy()
            self.assertEqual(processed.size,original.size)
            edges_before=original.filter(ImageFilter.FIND_EDGES)
            edges_after=processed.filter(ImageFilter.FIND_EDGES)
            before=sum(ImageStat.Stat(edges_before).mean)
            after=sum(ImageStat.Stat(edges_after).mean)
            self.assertLess(after,before*0.7)
            self.assertGreater(sum(ImageStat.Stat(
                ImageChops.difference(original,processed)).mean),4)

    def test_only_far_environment_blurs_original_actor_remains_identical(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            direction=dict(weather="day",action="idle",
                           emotion="happy",shot="wide")
            options=dict(topic="A fox near a river",
                         narration="The fox stands beside a river.",
                         scene_index=1,scene_count=3,
                         style="cartoon",direction=direction,
                         landscape="river")
            wide=forest_layers(root/"wide",kind="fox",**options)
            direction["shot"]="macro"
            macro=forest_layers(root/"macro",kind="fox",**options)
            for key in ("body","left_leg","right_leg","tail","foreground","lighting"):
                self.assertEqual(wide[key].read_bytes(),macro[key].read_bytes(),key)
            for key in ("background","ambient_far"):
                self.assertNotEqual(wide[key].read_bytes(),macro[key].read_bytes(),key)
            # Same focus behavior also applies to the original owl art rig.
            direction["shot"]="wide"
            owl_wide=owl_layers(root/"owl-wide",**options)
            direction["shot"]="closeup"
            owl_close=owl_layers(root/"owl-close",**options)
            self.assertEqual(owl_wide["body"].read_bytes(),owl_close["body"].read_bytes())
            self.assertNotEqual(owl_wide["background"].read_bytes(),owl_close["background"].read_bytes())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Need real encoded MP4 and FFmpeg probe")
    def test_closeup_focus_preserves_real_video_stream(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"focused.mp4"
            render_motion_clip(
                kind="rabbit",topic="Original focus story",
                narration="A rabbit listens beside a small river.",
                scene_index=1,scene_count=3,style="cartoon",
                duration=.7,width=1280,height=720,fps=24,destination=path,
                direction=dict(weather="day",action="rest",
                               emotion="curious",shot="macro"),
                landscape="river")
            self.assertGreater(path.stat().st_size,1000)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_frames",
                 "-of","json",str(path)],check=True,capture_output=True,
                text=True,timeout=30)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(int(stream["nb_frames"]),round(.7*24))


if __name__=="__main__":
    unittest.main()
