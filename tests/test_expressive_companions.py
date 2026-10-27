"""Script-grounded second actor must remain original, expressive and independent."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops
from unittest.mock import patch

from automate_ytb.animated_forest import (
    companion_kind, render_layers, render_motion_clip, render_character_poster,
)

NARRATION = "Le renard marche avec le lapin dans la forêt."
DIRECTION = {"weather": "day", "action": "walk",
             "emotion": "curious", "shot": "wide"}


def create_layers(folder: Path, narration: str = NARRATION) -> dict:
    return render_layers(
        folder, kind="fox", topic="Original illustrated scene",
        narration=narration, scene_index=1, scene_count=2,
        style="cartoon", direction=DIRECTION, landscape="forest")


class ExpressiveCompanionTests(unittest.TestCase):
    def test_guest_is_strictly_narration_grounded(self):
        self.assertEqual(companion_kind(NARRATION, primary="fox"), "rabbit")
        self.assertIsNone(companion_kind("Le renard marche dans la forêt.",
                                          primary="fox"))
        with tempfile.TemporaryDirectory() as folder:
            layers=create_layers(Path(folder), "Le renard marche dans la forêt.")
            self.assertNotIn("companion",layers)
            self.assertNotIn("companion_blink",layers)

    def test_closed_eye_plate_only_changes_companion_face(self):
        with tempfile.TemporaryDirectory() as folder:
            layers=create_layers(Path(folder))
            self.assertIn("companion",layers)
            self.assertIn("companion_blink",layers)
            with Image.open(layers["companion"]) as open_image, Image.open(layers["companion_blink"]) as shut_image:
                self.assertEqual(open_image.size, (247, 332))
                self.assertEqual(shut_image.size, open_image.size)
                self.assertEqual(open_image.mode, "RGBA")
                difference=ImageChops.difference(open_image, shut_image)
                self.assertIsNotNone(difference.crop((45, 122, 197, 178)).getbbox())
                self.assertIsNone(difference.crop((0, 225, 247, 332)).getbbox())
            # Identical script, seed and selected actor make reproducible art.
            with tempfile.TemporaryDirectory() as second:
                repeat=create_layers(Path(second))
                self.assertEqual(Path(layers["companion_blink"]).read_bytes(),
                                 Path(repeat["companion_blink"]).read_bytes())

    def test_lead_looks_toward_guest_unless_explicit_prop_focus(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            solo=create_layers(root/"solo","Le renard marche dans la forêt.")
            duet=create_layers(root/"duet")
            with Image.open(solo["body"]) as a, Image.open(duet["body"]) as b:
                self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_animation_graph_uses_identical_positions_and_independent_blink(self):
        captured=[]
        with patch("automate_ytb.production._run", side_effect=lambda argv: captured.append(argv)):
            render_motion_clip(
                kind="fox", topic="Original illustrated scene",
                narration=NARRATION, scene_index=1, scene_count=2,
                style="cartoon", duration=1.0, width=1280,height=720,
                fps=24,destination=Path("/tmp/companion-graph-mock.mp4"),
                direction=DIRECTION,landscape="forest")
        self.assertEqual(len(captured),1)
        command=captured[0]
        graph=command[command.index("-filter_complex")+1]
        self.assertIn("[shadowstage][11:v]overlay",graph)
        self.assertIn("[companions][12:v]overlay",graph)
        self.assertIn("enable='lt(mod(t+0.65,3.4),0.12)'",graph)
        self.assertIn("[guestblink][earleft]",graph)
        self.assertEqual(graph.count("813+6*sin(t*0.58)+1.5*sin(t*1.21)"),2)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg binaries are required")
    def test_actual_two_actor_mp4_is_encoded_with_blink_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            video=Path(folder)/"duet.mp4"
            render_motion_clip(
                kind="fox",topic="Original illustrated scene",
                narration=NARRATION,scene_index=1,scene_count=2,
                style="cartoon",duration=3.0,width=1280,height=720,
                fps=24,destination=video,direction=DIRECTION,
                landscape="forest")
            self.assertGreater(video.stat().st_size,3000)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_frames",
                 "-of","json",str(video)],
                capture_output=True,text=True,check=True,timeout=45)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(int(stream["nb_frames"]),72)


if __name__=="__main__":
    unittest.main()
