"""Regression coverage for articulated original animal ears and owl crests."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image
from automate_ytb.ear_motion import EAR_VERSION, EAR_AMPLITUDES, ear_position
from automate_ytb.animated_forest import render_layers as forest_layers
from automate_ytb.animated_forest import render_character_poster as forest_poster
from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_layers as owl_layers
from automate_ytb.animated_owl import render_character_poster as owl_poster
from automate_ytb.animated_owl import render_motion_clip as owl_clip
from automate_ytb.director import ACTIONS


class ArticulatedEarsTests(unittest.TestCase):
    def test_all_actions_keep_ear_offsets_bounded_and_deterministic(self):
        self.assertIn("v1", EAR_VERSION)
        self.assertEqual(set(EAR_AMPLITUDES), ACTIONS)
        for action in ACTIONS:
            x,y = ear_position(action,body_x=180,body_y=184)
            self.assertEqual((x,y),ear_position(action,body_x=180,body_y=184))
            self.assertIn("180",x)
            self.assertIn("184",y)
            self.assertIn("0.42",x)
            self.assertIn("0.91",y)
            self.assertNotIn(";",x+y)
        with self.assertRaises(ValueError):
            ear_position("jump;movie=secret",body_x=180,body_y=184)

    def test_separate_layers_and_approved_stills_remain_present(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            common=dict(topic="Original woodland",narration="The cat runs.",
                        scene_index=1,scene_count=2,style="cartoon",
                        direction={"weather":"day","action":"run",
                                   "emotion":"happy","shot":"wide"})
            for animal in ("fox","rabbit","cat"):
                output=forest_layers(base/animal,kind=animal,**common)
                with Image.open(output["ears"]) as ear:
                    self.assertEqual(ear.mode,"RGBA")
                    self.assertEqual(ear.size,(350,440))
                    self.assertIsNotNone(ear.getchannel("A").getbbox())
                path=base/(animal+"-poster.png")
                forest_poster(kind=animal,destination=path,**common)
                with Image.open(path) as im:
                    self.assertEqual(im.size,(1280,720))
            output=owl_layers(base/"owl",**common)
            with Image.open(output["crest"]) as crest:
                self.assertEqual(crest.size,(322,430))
                self.assertIsNotNone(crest.getchannel("A").getbbox())
            path=base/"owl-poster.png"
            owl_poster(destination=path,**common)
            with Image.open(path) as im:
                self.assertEqual(im.size,(1280,720))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Need real FFmpeg MP4 rendering")
    def test_new_ear_and_crest_inputs_encode_in_real_mp4(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            common=dict(topic="Original actions",narration="The animal jumps.",
                        scene_index=1,scene_count=2,style="cartoon",
                        duration=.8,width=1280,height=720,fps=24,
                        direction={"weather":"day","action":"jump",
                                   "emotion":"happy","shot":"wide"})
            for kind in ("forest","owl"):
                dest=base/(kind+".mp4")
                if kind=="forest":
                    forest_clip(kind="rabbit",destination=dest,**common)
                else:
                    owl_clip(destination=dest,**common)
                self.assertGreater(dest.stat().st_size,1000)
                probe=subprocess.run(
                    ["ffprobe","-v","error","-select_streams","v:0",
                     "-show_entries","stream=codec_name,width,height",
                     "-of","json",str(dest)],capture_output=True,
                    text=True,check=True,timeout=40)
                stream=json.loads(probe.stdout)["streams"][0]
                self.assertEqual(stream["codec_name"],"h264")
                self.assertEqual((stream["width"],stream["height"]),(1280,720))


if __name__ == "__main__":
    unittest.main()
