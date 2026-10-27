"""Genuine second actor with independently moving original body parts."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from automate_ytb.animated_forest import (
    companion_kind, render_layers, render_motion_clip, render_character_poster)
from automate_ytb.companion_motion import (
    COMPANION_RIG_VERSION, guest_action, guest_animation_graph)


class IndependentCompanionTests(unittest.TestCase):
    def test_explicit_shared_travel_only(self):
        self.assertIn("v1", COMPANION_RIG_VERSION)
        samples = {
            "The fox runs with the rabbit.": "run",
            "The fox and rabbit run together.": "run",
            "Le renard et le lapin courent ensemble.": "run",
            "Le renard marche avec le lapin.": "walk",
            "The fox walks alongside the cat.": "walk",
            "The fox runs to meet the rabbit.": "idle",
            "Le renard rencontre le lapin.": "idle",
            "The fox sits with the rabbit.": "idle",
        }
        for narration, action in samples.items():
            self.assertEqual(
                guest_action(narration, has_companion=True),
                action, msg=narration)
            self.assertEqual(
                guest_action(narration, has_companion=False),
                "idle", msg=narration)
        with self.assertRaises(ValueError):
            guest_action(None, has_companion=True)
        with self.assertRaises(ValueError):
            guest_action("Hello", has_companion="yes")

    def test_safe_independent_armature_filter(self):
        for action in ("idle", "walk", "run"):
            script = guest_animation_graph(
                prior="shadowstage", first_input=11, action=action)
            self.assertEqual(script.count("overlay="), 4)
            self.assertTrue(script.endswith("[companions]"))
            for idx in range(11, 15):
                self.assertIn(f"[{idx}:v]", script)
            self.assertNotIn("movie=", script)
            if action != "idle":
                self.assertIn("max(0,sin(t*", script)
                self.assertIn("max(0,0-sin(t*", script)
                self.assertIn("[guestleft]", script)
            else:
                self.assertNotIn("max(0", script)
        with self.assertRaises(ValueError):
            guest_animation_graph(prior="[0:v];movie=/x", first_input=11, action="run")
        with self.assertRaises(ValueError):
            guest_animation_graph(prior="shadowstage", first_input=11,
                                  action="talk")

    def test_transparent_guest_rig_parts_and_static_poster(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            narration = "Le renard et le lapin courent ensemble."
            self.assertEqual(companion_kind(narration, primary="fox"), "rabbit")
            opts=dict(kind="fox", topic="Notre forêt",
                      narration=narration, scene_index=1, scene_count=3,
                      style="cartoon")
            parts = render_layers(root / "parts", **opts)
            for item in ("companion_tail", "companion_body",
                         "companion_left_leg", "companion_right_leg"):
                self.assertIn(item, parts)
                with Image.open(parts[item]) as sprite:
                    self.assertEqual(sprite.mode, "RGBA")
                    self.assertGreater(sprite.getchannel("A").getbbox()[2], 20)
            with Image.open(parts["companion_body"]) as actor:
                self.assertEqual(actor.size, (247,311))
            poster = root / "approved.png"
            render_character_poster(destination=poster, **opts)
            with Image.open(poster) as out:
                self.assertEqual(out.size, (1280,720))
            isolated = render_layers(
                root / "single",**(opts | {"narration":"Le renard court seul."}))
            self.assertNotIn("companion_body", isolated)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real MP4 encoder and decoder required")
    def test_real_h264_with_animated_second_animal(self):
        with tempfile.TemporaryDirectory() as folder:
            mp4=Path(folder)/"two-real-animals.mp4"
            render_motion_clip(
                kind="fox",topic="La promenade des animaux",
                narration="Le renard et le lapin courent ensemble.",
                scene_index=1,scene_count=3,style="cartoon",
                duration=1.2,width=1280,height=720,fps=24,
                destination=mp4,
                direction={"weather":"day","action":"run",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(mp4.stat().st_size,1500)
            probe=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,nb_frames",
                 "-of","json",str(mp4)],
                capture_output=True,text=True,check=True,timeout=60)
            stream=json.loads(probe.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(int(stream["nb_frames"]),29)
            decoded=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-i",str(mp4),
                 "-an","-f","null","-"],
                capture_output=True,text=True,timeout=90)
            self.assertEqual(decoded.returncode,0,decoded.stderr[-600:])
