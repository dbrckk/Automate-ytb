"""Second original actor: independent limbs, truthful action cues and MP4."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.companion_motion import (
    COMPANION_RIG_VERSION, guest_action, guest_animation_graph)
from automate_ytb.animated_forest import (
    companion_kind, render_layers, render_motion_clip, render_character_poster)


class IndependentCompanionTests(unittest.TestCase):
    def test_shared_actions_only_and_never_invent_speech(self):
        self.assertIn("v2", COMPANION_RIG_VERSION)
        examples = {
            "The fox runs with the rabbit.": "run",
            "The fox and rabbit run together.": "run",
            "Le renard et le lapin courent ensemble.": "run",
            "Le renard marche avec le lapin.": "walk",
            "The fox walks alongside the cat.": "walk",
            "The fox runs to meet the rabbit.": "idle",
            "Le renard rencontre le lapin.": "idle",
            "The fox sits with the rabbit.": "idle",
            "The fox talks with the rabbit.": "idle",
        }
        for narration, expected in examples.items():
            with self.subTest(narration=narration):
                self.assertEqual(guest_action(narration, has_companion=True),expected)
                self.assertEqual(guest_action(narration, has_companion=False),"idle")
        with self.assertRaises(ValueError):
            guest_action(None,has_companion=True)
        with self.assertRaises(ValueError):
            guest_action("text",has_companion="yes")

    def test_safe_guest_graph_stays_behind_main_actor(self):
        for action in ("idle","walk","run"):
            graph=guest_animation_graph(
                prior="shadowstage",first_input=11,action=action)
            self.assertEqual(graph.count("overlay="),6)
            self.assertTrue(graph.endswith("[guestblink]"))
            for i in range(11,17):
                self.assertIn(f"[{i}:v]",graph)
            self.assertIn("y=571",graph)
            self.assertIn("enable='lt(mod(t+0.65,3.4),0.12)'",graph)
            self.assertNotIn("movie=",graph)
            if action != "idle":
                self.assertIn("max(0,sin(t*",graph)
                self.assertIn("max(0,0-sin(t*",graph)
        with self.assertRaises(ValueError):
            guest_animation_graph(prior="malicious",first_input=11,action="run")
        with self.assertRaises(ValueError):
            guest_animation_graph(prior="shadowstage",first_input=11,action="talk")

    def test_original_guest_parts_are_transparent_and_poster_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            narration="Le renard et le lapin courent ensemble."
            self.assertEqual(companion_kind(narration,primary="fox"),"rabbit")
            common=dict(kind="fox",topic="Original forest",
                        narration=narration,scene_index=1,scene_count=3,
                        style="cartoon")
            layers=render_layers(root/"layers",**common)
            for name in ("companion_tail","companion_body",
                         "companion_left_leg","companion_right_leg",
                         "companion_body_blink","companion_shadow"):
                self.assertIn(name,layers)
                with Image.open(layers[name]) as layer:
                    self.assertEqual(layer.mode,"RGBA")
                    self.assertIsNotNone(layer.getchannel("A").getbbox())
            with Image.open(layers["companion_body"]) as body:
                self.assertEqual(body.size,(247,311))
            with Image.open(layers["companion_body_blink"]) as body:
                self.assertEqual(body.size,(247,311))
            render_character_poster(destination=root/"poster.png",**common)
            with Image.open(root/"poster.png") as poster:
                self.assertEqual(poster.size,(1280,720))
            alone=render_layers(root/"single",**(common | {"narration":"Le renard court seul."}))
            self.assertNotIn("companion_body",alone)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required for MP4 quality gate")
    def test_real_animated_companion_mp4(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"two-animals.mp4"
            render_motion_clip(
                kind="fox",topic="La promenade des animaux",
                narration="Le renard et le lapin courent ensemble.",
                scene_index=1,scene_count=3,style="cartoon",
                duration=1.15,width=1280,height=720,fps=24,
                destination=dest,
                direction={"weather":"day","action":"run",
                           "emotion":"happy","shot":"wide"})
            self.assertGreater(dest.stat().st_size,1500)
            result=subprocess.run([
                "ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=codec_name,width,height,nb_frames",
                "-of","json",str(dest)],check=True,capture_output=True,
                text=True,timeout=45)
            stream=json.loads(result.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(int(stream["nb_frames"]),28)
            decoded=subprocess.run(
                ["ffmpeg","-nostdin","-v","error","-i",str(dest),
                 "-an","-f","null","-"],capture_output=True,text=True,timeout=90)
            self.assertEqual(decoded.returncode,0,decoded.stderr[-500:])
