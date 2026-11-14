"""End-to-end premium maglev assets and low-cost cached optical finish."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_subject_illustrations import (
    select_subject, subject_layers)
from automate_ytb.universal_subject_motion import subject_pose
from automate_ytb.universal_vector_art import (
    validate_vector_layers, vector_sha256, render_vector_layer)
from automate_ytb.universal_kinetic import read_story
from automate_ytb.universal_art25d import load_art_scenes, render_art_stage
from automate_ytb.premium_finish25d import VERSION, finish_vector_layer

ROOT=Path(__file__).resolve().parents[1]


class PremiumMaglevWorldTests(unittest.TestCase):
    def test_real_requested_subject_uses_maglev_not_cartoon_rail(self):
        request=json.loads((ROOT/"video_requests"/
            "maglev-floating-train-20261114-original.json").read_text(encoding="utf-8"))
        story=compile_original_script(
            topic=request["topic"],script=request["script"],
            language=request["language"])
        self.assertEqual(story["proceduralVisualFamily"],"maglev")
        self.assertIsNone(story.get("proceduralVisualCompositionFamilies"))
        self.assertIsNone(story.get("proceduralVisualFamilies"))
        self.assertEqual(story["proceduralVisualFinishEngine"],VERSION)
        self.assertEqual(len(story["beats"]),5)
        self.assertTrue(all(beat["visualVectors"]==story["beats"][0]["visualVectors"]
                            for beat in story["beats"]))
        self.assertTrue(all(len(beat["actorTracks"])==4 for beat in story["beats"]))

    def test_detailed_maglev_has_five_valid_layers_with_distinct_rig(self):
        layers=validate_vector_layers(subject_layers("maglev"))
        self.assertEqual([layer["z"] for layer in layers],[5,25,45,65,85])
        self.assertGreaterEqual(sum(len(layer["shapes"]) for layer in layers),85)
        self.assertGreater(len(layers[2]["shapes"]),20)
        self.assertNotEqual(vector_sha256(layers[2]),
                            vector_sha256(validate_vector_layers(subject_layers("rail"))[2]))
        self.assertNotEqual(subject_pose("maglev",45,.8),
                            subject_pose("rail",45,.8))
        self.assertEqual(select_subject("Train","This train has wheels."),"rail")
        self.assertEqual(select_subject("Train","No maglev is present. This train has wheels."),"rail")

    def test_original_provenance_compatible_with_real_art_renderer(self):
        data=compile_original_script(
            topic="What makes superconducting maglev move?",
            script=("A superconducting maglev levitates above a guideway. "
                    "The carriage keeps a visible gap from its track.\n\n"
                    "The maglev train travels along a motor powered guideway. "
                    "The coils propel the vehicle forward."),
            language="en")
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/"story.json"
            source.write_text(json.dumps(data),encoding="utf-8")
            parsed=read_story(source)
            self.assertEqual(parsed["proceduralVisualFinishEngine"],VERSION)
            scenes,manifest=load_art_scenes(parsed,source,360,640)
            self.assertEqual(len(scenes),2)
            self.assertEqual(len(manifest),10)
            frame=render_art_stage(scenes[0],0,0,60)
            self.assertGreaterEqual(frame.width,250)
            self.assertGreaterEqual(frame.height,280)
            rgba=frame.convert("RGBA")
            self.assertIsNotNone(rgba.getbbox())
            next_frame=render_art_stage(scenes[0],30,0,60)
            self.assertNotEqual(frame.tobytes(),next_frame.tobytes())
            forged=dict(data,proceduralVisualFinishEngine="untrusted")
            source.write_text(json.dumps(forged),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"finishing"):
                read_story(source)

    def test_cached_bloom_preserves_source_silhouettes_and_determinism(self):
        layer=Image.new("RGBA",(160,176))
        draw=ImageDraw.Draw(layer)
        draw.line((28,64,130,64),fill=(225,245,242,255),width=3)
        art=finish_vector_layer(layer,45)
        self.assertEqual(art.mode,"RGBA")
        self.assertEqual(art.getpixel((28,64))[3],255)
        self.assertGreater(art.getpixel((75,54))[3],0)
        self.assertEqual(art.tobytes(),finish_vector_layer(layer,45).tobytes())
        self.assertEqual(finish_vector_layer(layer,5).tobytes(),layer.tobytes())
        with self.assertRaises(ValueError):
            finish_vector_layer(layer,101)


if __name__=="__main__":
    unittest.main()
