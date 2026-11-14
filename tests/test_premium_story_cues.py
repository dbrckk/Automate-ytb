"""Source-only mechanism cues that alter real rendered video frames.

No visual is selected from the topic alone, no numerical facts invented,
and a saved pictorial storyboard remains a deterministic source of truth.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from PIL import Image, ImageChops

from automate_ytb.premium_story_cues import (
    VERSION, cue_for_narration, action_sequence, render_maglev_action)
from automate_ytb.universal_script import compile_original_script
from automate_ytb.premium_request import validate_request

ROOT=Path(__file__).resolve().parents[1]


class PremiumNarrativeActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request=json.loads(
            (ROOT/"video_requests"/"maglev-floating-train-20261114-original.json")
            .read_text(encoding="utf-8"))
        cls.story=compile_original_script(
            topic=cls.request["topic"],script=cls.request["script"],
            language=cls.request["language"])

    def test_five_real_beats_create_five_different_source_actions(self):
        self.assertEqual(
            action_sequence(self.story["beats"]),
            ["gap","wheels","levitation","propulsion","airflow"],
        )
        self.assertTrue(VERSION.startswith("original-"))
        self.assertEqual(
            validate_request(event_name="workflow_dispatch",**self.request),
            self.request,
        )

    def test_air_resistance_precedence_and_no_fabricated_objects(self):
        self.assertEqual(cue_for_narration(
            "Without wheel contact the train still faces air resistance."),
            "airflow")
        self.assertEqual(cue_for_narration(
            "This train uses no wheels touching the track at high speed."),
            "gap")
        self.assertEqual(cue_for_narration(
            "A maglev train glides through its guideway."),"glide")
        self.assertIsNone(cue_for_narration(
            "The artist describes an abstract composition without a machine."))
        with self.assertRaises(ValueError):
            cue_for_narration("")

    def test_real_pixels_are_visibly_distinct_per_mechanism(self):
        source=Image.new("RGBA",(296,326),(15,26,44,255))
        images=[]
        for scene in self.story["beats"]:
            img=render_maglev_action(source,scene["narration"],
                                     frame=55,first=0,last=120)
            self.assertEqual(img.size,source.size)
            self.assertEqual(img.mode,"RGBA")
            self.assertNotEqual(img.tobytes(),source.tobytes())
            self.assertEqual(img.tobytes(),
                             render_maglev_action(source,scene["narration"],
                                  frame=55,first=0,last=120).tobytes())
            images.append(img)
        for a,b in zip(images,images[1:]):
            self.assertIsNotNone(
                ImageChops.difference(a,b).getbbox(),
                "Two adjacent source mechanisms must not look identical")

    def test_same_scene_has_true_frame_motion_not_a_still(self):
        source=Image.new("RGBA",(296,326),(14,22,41,255))
        for scene in self.story["beats"]:
            early=render_maglev_action(source,scene["narration"],
                                      frame=15,first=0,last=120)
            late=render_maglev_action(source,scene["narration"],
                                     frame=90,first=0,last=120)
            self.assertIsNotNone(
                ImageChops.difference(early,late).getbbox(),
                f"No dynamic pixel changes for {cue_for_narration(scene['narration'])}")

    def test_unillustrated_repetitive_script_fails_before_neural_download(self):
        bad=("A maglev train glides along its track in a long straight line. "
             "The train continues moving forward.\n\n"
             "The maglev train glides along its track once again while "
             "the carriages continue moving through the scene.")
        with self.assertRaisesRegex(ValueError,"distinct visual actions"):
            validate_request(
                event_name="workflow_dispatch",topic="Maglev story",
                script=bad,language="en")

    def test_invalid_frame_bounds_and_content_rejected(self):
        image=Image.new("RGBA",(296,326))
        for frame,first,last in ((-1,0,10),(10,0,10),(3,4,7)):
            with self.assertRaises(ValueError):
                render_maglev_action(image,"A train glides.",frame=frame,
                                     first=first,last=last)
        with self.assertRaises(ValueError):
            render_maglev_action(Image.new("RGB",(296,326)),
                                 "A train glides.",frame=2,first=0,last=10)


if __name__=="__main__":
    unittest.main()
