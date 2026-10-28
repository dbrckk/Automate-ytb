"""Script-driven eye glances without invented animation directions or assets."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageChops

from automate_ytb.scene_props import GAZE_VERSION, gaze_target
from automate_ytb.animated_owl import _body as owl_body, render_motion_clip
from automate_ytb.animated_forest import _sprite_body as forest_body


class StoryDirectedGazeTests(unittest.TestCase):
    def test_gazes_follow_only_explicit_looking_verbs_in_two_languages(self):
        self.assertIn("v1", GAZE_VERSION)
        cases = (
            ("The owl looks up at the sky.", "up"),
            ("Le renard regarde les étoiles.", "up"),
            ("La chouette regarde à gauche.", "left"),
            ("The little fox glances left.", "left"),
            ("The rabbit looks down at the ground.", "down"),
            ("Le chat observe le sol.", "down"),
            ("The owl looks right.", "right"),
            ("Le hibou regarde vers la droite.", "right"),
            ("The fox walks left through the field.", "forward"),
            ("Les étoiles brillent dans le ciel.", "forward"),
            ("The owl looks around. The fox goes left.", "forward"),
        )
        for narration, expected in cases:
            with self.subTest(narration=narration):
                self.assertEqual(gaze_target(narration), expected)

    def test_props_take_precedence_and_input_is_validated(self):
        self.assertEqual(gaze_target("The owl looks up at the sky.", held_prop="book"),
                         "down-right")
        self.assertEqual(gaze_target("The owl looks left at an apple."), "right")
        with self.assertRaises(ValueError):
            gaze_target(None)
        with self.assertRaises(ValueError):
            gaze_target("x" * 150001)

    def test_illustrated_owl_and_forest_eye_poses_are_visibly_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for animal, maker in (
                ("owl",lambda p,g: owl_body(p,blink=False,emotion="neutral",gaze=g)),
                ("fox",lambda p,g: forest_body(p,kind="fox",blink=False,
                                               emotion="neutral",gaze=g,include_ears=False)),
            ):
                with self.subTest(animal=animal):
                    forward,up,left=[root/f"{animal}-{g}.png"
                                     for g in ("forward","up","left")]
                    for p,g in ((forward,"forward"),(up,"up"),(left,"left")):
                        maker(p,g)
                    with Image.open(forward) as a, Image.open(up) as b, Image.open(left) as c:
                        self.assertEqual(a.size,b.size)
                        self.assertIsNotNone(ImageChops.difference(a.convert("RGB"),b.convert("RGB")).getbbox())
                        self.assertIsNotNone(ImageChops.difference(a.convert("RGB"),c.convert("RGB")).getbbox())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real video FFmpeg must be installed")
    def test_upward_gaze_encodes_as_real_animated_video(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"gaze.mp4"
            render_motion_clip(topic="Original stargazing story",
                narration="The owl looks up at the stars.",
                scene_index=1,scene_count=2,style="cartoon",duration=0.85,
                width=1280,height=720,fps=24,destination=output,
                direction={"action":"idle","weather":"night",
                           "emotion":"neutral","shot":"wide"})
            self.assertGreater(output.stat().st_size,1200)
            result=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height",
                 "-of","csv=p=0",str(output)],
                capture_output=True,text=True,check=True,timeout=30)
            self.assertIn("h264",result.stdout)
            self.assertIn("1280",result.stdout)


if __name__ == "__main__":
    unittest.main()
