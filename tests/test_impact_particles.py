"""Offline deterministic footsteps and jump landing puffs."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from automate_ytb.impact_particles import draw_impact_plate, overlay_impact


class ImpactTests(unittest.TestCase):
    def test_original_rgba_plate_is_deterministic_and_subtle(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/"a.png",Path(folder)/"b.png"
            draw_impact_plate(a,weather="day")
            draw_impact_plate(b,weather="day")
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with Image.open(a) as img:
                self.assertEqual(img.size,(188,88))
                self.assertEqual(img.mode,"RGBA")
                self.assertLess(img.getchannel("A").getextrema()[1],125)
            with self.assertRaises(ValueError):
                draw_impact_plate(a,weather="unknown")

    def test_jump_impact_matches_phase_and_benign_actions_stay_unaltered(self):
        for action in ("jump","walk","run"):
            graph,label,names=overlay_impact(
                graph="[a]null[previous]",label="previous",
                names=["background"],action=action,body_x="180+sin(t)")
            self.assertEqual(label,"impactdone")
            self.assertEqual(names,["background","impact"])
            self.assertIn("y=570",graph)
            self.assertIn("enable=",graph)
            self.assertNotIn("movie=",graph)
        graph,label,names=overlay_impact(
            graph="safe",label="prev",names=["background"],
            action="rest",body_x="180")
        self.assertEqual((graph,label,names),("safe","prev",["background"]))
        with self.assertRaises(ValueError):
            overlay_impact(graph="",label="x",names=[],action="run",
                           body_x="1;movie=/tmp/attack")
