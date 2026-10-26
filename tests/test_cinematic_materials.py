"""Premium-style paint regression: verify visible volume, pristine alpha and real MP4."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageStat

from automate_ytb.material_shading import MATERIAL_VERSION, shade_sprite
from automate_ytb.cinematic_paint import (
    SCENIC_GRADE_VERSION, paint_sky_bloom, paint_horizon_mist)
from automate_ytb.animated_forest import (
    _sprite_body, render_motion_clip as forest_clip)
from automate_ytb.animated_owl import _body as owl_body


class CinematicMaterialTests(unittest.TestCase):
    def test_shading_adds_actual_visible_curvature_but_keeps_exact_alpha(self):
        self.assertIn("v1", MATERIAL_VERSION)
        for kind in ("fox", "rabbit", "cat", "owl"):
            with self.subTest(kind=kind):
                size = (322, 430) if kind == "owl" else (350, 440)
                sample = Image.new("RGBA", size)
                d = ImageDraw.Draw(sample)
                d.ellipse((38, 65, size[0]-38, size[1]-41),
                          fill=(160, 110, 91, 215))
                before = sample.copy()
                original_alpha = sample.getchannel("A").tobytes()
                shade_sprite(sample, kind=kind, part="body")
                self.assertEqual(sample.getchannel("A").tobytes(),
                                 original_alpha)
                self.assertEqual(sample.getpixel((0, 0))[3], 0)
                delta = ImageChops.difference(
                    before.convert("RGB"), sample.convert("RGB"))
                self.assertGreater(sum(ImageStat.Stat(delta).mean), 1.5)
                second = before.copy()
                shade_sprite(second, kind=kind, part="body")
                self.assertEqual(sample.tobytes(), second.tobytes())
        with self.assertRaises(ValueError):
            shade_sprite(Image.new("RGB",(350,440)),
                         kind="fox",part="body")
        with self.assertRaises(ValueError):
            shade_sprite(Image.new("RGBA",(350,440)),
                         kind="unknown",part="body")

    def test_original_character_art_uses_shading_on_actual_png(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for kind in ("fox", "rabbit", "cat"):
                p=root/(kind+".png")
                _sprite_body(p,kind=kind,blink=False,
                             emotion="happy",gaze="forward")
                with Image.open(p) as im:
                    self.assertEqual(im.mode,"RGBA")
                    self.assertEqual(im.size,(350,440))
                    self.assertEqual(im.getpixel((0,0))[3],0)
                    self.assertGreater(im.getpixel((173,220))[3],100)
            p=root/"owl.png"
            owl_body(p,blink=False,emotion="happy",gaze="forward")
            with Image.open(p) as im:
                self.assertEqual(im.size,(322,430))
                self.assertEqual(im.getpixel((0,0))[3],0)

    def test_sky_and_distant_haze_change_real_pixels_and_weather_palettes(self):
        self.assertIn("v1",SCENIC_GRADE_VERSION)
        backgrounds=[]
        for weather in ("day","night","rain"):
            im=Image.new("RGB",(1280,720),(36,67,95))
            before=im.copy()
            paint_sky_bloom(im,weather=weather)
            paint_horizon_mist(im,weather=weather)
            self.assertNotEqual(im.getpixel((962,155)),
                                before.getpixel((962,155)))
            self.assertNotEqual(im.getpixel((710,520)),
                                before.getpixel((710,520)))
            backgrounds.append(im.tobytes())
        self.assertNotEqual(backgrounds[0],backgrounds[1])
        self.assertNotEqual(backgrounds[1],backgrounds[2])
        with self.assertRaises(ValueError):
            paint_sky_bloom(Image.new("RGB",(600,400)),
                            weather="day")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real encoded MP4 verification requires FFmpeg")
    def test_shaded_fox_story_renders_a_real_h264_clip(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"shaded-forest.mp4"
            forest_clip(
                kind="fox",topic="An original painted forest",
                narration="Le renard admire la lumière.",
                scene_index=1,scene_count=3,style="cartoon",
                duration=.86,width=1280,height=720,fps=24,
                destination=output,
                direction={"weather":"day","action":"idle",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(output.stat().st_size,1500)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_frames",
                 "-of","json",str(output)],check=True,
                capture_output=True,text=True,timeout=50)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertGreaterEqual(int(stream["nb_frames"]),20)


if __name__ == "__main__":
    unittest.main()
