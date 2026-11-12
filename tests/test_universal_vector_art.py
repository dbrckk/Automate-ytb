"""Original vector illustrations: real pixels, actors, rights and MP4 encoding."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.universal_vector_art import (
    render_vector_layer, validate_vector_layers, vector_sha256)
from automate_ytb.universal_actor_rig import same_authored_actor_world
from automate_ytb.universal_art25d import (
    bind_actor_camera_world, load_art_scenes, render_art_stage)
from automate_ytb.universal_kinetic import (
    frame_image, produce, read_story, timeline_for)

SAMPLE=Path(__file__).resolve().parents[1]/"examples"/"build_original_vector_story.py"
_spec=importlib.util.spec_from_file_location("original_vector_story_sample",SAMPLE)
_example=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_example)


class OriginalVectorArtTests(unittest.TestCase):
    def test_full_original_flower_scene_and_reproducible_alpha(self):
        background,stem,leaf,other,flower=_example.layers()
        shapes=validate_vector_layers([background,stem,leaf,other,flower])
        self.assertEqual(len(shapes),5)
        self.assertEqual(len(shapes[0]["shapes"]),25)
        self.assertEqual(len(vector_sha256(shapes[4])),64)
        a=render_vector_layer(shapes[4],(400,450))
        b=render_vector_layer(shapes[4],(400,450))
        self.assertEqual(a.mode,"RGBA")
        self.assertEqual(a.size,(400,450))
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertIsNotNone(a.getbbox())
        # The generated flower is transparent and internally color-gradated,
        # not a generic solid circle/card masquerading as semantic artwork.
        self.assertLess(len(a.getchannel("A").getextrema()),3)
        colors=a.convert("RGB").getcolors(maxcolors=1000000)
        self.assertIsNotNone(colors)
        self.assertGreater(len(colors),150)
        self.assertLess(a.getchannel("A").getbbox()[2],a.width)
        self.assertNotEqual(vector_sha256(shapes[0]),vector_sha256(shapes[4]))

    def test_bad_shapes_and_explicit_original_rights_fail_closed(self):
        layer=_example.blossom()
        for bad in (
            {"rightsConfirmed":False},
            {"rights":"unknown"},
            {"id":"../../local"},
            {"z":True},
            {"parallaxX":float("nan")},
            {"z":102},
            {"shapes":[]},
        ):
            record=dict(layer,**bad)
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_vector_layers([record])
        shape=layer["shapes"][0]
        for broken in (
            dict(shape,fill="#XYZXYZ"),
            dict(shape,fill=["#FFFFFF"]),
            dict(shape,strokeWidth=.9),
            dict(shape,points=[[.5,.5],[.7,.9]]),
            dict(shape,closed="yes"),
            dict(shape,url="https://evil.example/p.png"),
        ):
            record=deepcopy(layer)
            record["shapes"][0]=broken
            with self.subTest(broken=broken),self.assertRaises(ValueError):
                validate_vector_layers([record])
        with self.assertRaises(ValueError):
            validate_vector_layers([layer,layer])
        with self.assertRaises(ValueError):
            validate_vector_layers([layer],[{"z":layer["z"]}])
        with self.assertRaises(ValueError):
            validate_vector_layers([layer]*7)
        with self.assertRaises(ValueError):
            render_vector_layer(layer,(9999,9999))

    def test_lines_paths_and_gradients_all_create_real_pixels(self):
        art=_example.blossom()
        one=render_vector_layer(validate_vector_layers([art])[0],(360,540))
        self.assertGreater(one.getchannel("A").getextrema()[1],0)
        self.assertEqual(one.getchannel("A").getextrema()[0],0)
        # Empty shapes and unsafe paths do not reach the compositor.
        sample=_example.left_leaf()
        specimen=validate_vector_layers([sample])[0]
        img=render_vector_layer(specimen,(360,540))
        self.assertNotEqual(img.tobytes(),one.tobytes())

    def test_two_real_original_vector_shots_follow_one_camera(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            request=_example.build(folder)
            story=read_story(request)
            self.assertEqual(len(story["beats"]),2)
            self.assertEqual(len(story["beats"][0]["visualVectors"]),5)
            self.assertEqual(len(story["beats"][0]["actorTracks"]),4)
            self.assertTrue(same_authored_actor_world(
                story["beats"][0],story["beats"][1]))
            scenes,provenance=load_art_scenes(story,request,360,640)
            self.assertEqual(len(provenance),10)
            self.assertTrue(all(x["generatedLocallyWithoutSourceImage"]
                                for x in provenance))
            self.assertTrue(all(len(x["sha256"])==64 for x in provenance))
            groups=bind_actor_camera_world(story,scenes,[0,90,180])
            self.assertEqual(len(groups),1)
            self.assertEqual(scenes[0].camera_window,(0,180))
            self.assertEqual(scenes[1].camera_window,(0,180))
            a=render_art_stage(scenes[0],20,0,90)
            b=render_art_stage(scenes[1],115,90,180)
            self.assertEqual(a.mode,"RGBA")
            self.assertNotEqual(a.tobytes(),b.tobytes())
            clock=timeline_for(story,[0,90,180])
            fa=frame_image(story,clock,[0,90,180],20,360,640,
                           art_scenes=scenes)
            fb=frame_image(story,clock,[0,90,180],115,360,640,
                           art_scenes=scenes)
            self.assertEqual(fa.size,(360,640))
            self.assertNotEqual(fa.tobytes(),fb.tobytes())
            self.assertEqual(
                frame_image(story,clock,[0,90,180],115,360,640,
                            art_scenes=scenes).tobytes(),fb.tobytes())
            changed=deepcopy(story["beats"][1])
            changed["visualVectors"][0]["shapes"][0]["fill"]="#AACCFF"
            self.assertFalse(same_authored_actor_world(
                story["beats"][0],changed))

    def test_numeric_truth_not_hidden_by_original_vector_decoration(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            story={"schemaVersion":1,"topic":"An authored measured example",
                   "language":"en","beats":[{
                       "kind":"measure","title":"A numeric scene",
                       "narration":"An original sentence with an explicit number.",
                       "label":"Length","unit":"cm","value":"1",
                       "scaleMax":"5","visualVectors":[_example.blossom()],
                   },{
                       "kind":"concept","title":"The next scene",
                       "narration":"The other scene still has source words.",
                       "nodes":["test","label"]
                   }]}
            path=root/"bad-numeric.json"
            path.write_text(json.dumps(story),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"Numeric"):
                read_story(path)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "Real free media encoding required")
    def test_real_two_scene_vector_short_mp4_with_pcm_foley(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            request=_example.build(root)
            video=root/"original-vector.mp4"
            report=produce(request,video,voice="espeak",width=720)
            self.assertEqual(report["delivery"]["status"],"passed")
            self.assertGreater(video.stat().st_size,10000)
            self.assertEqual(report["artwork"]["originalVectorLayers"],10)
            self.assertGreater(report["artwork"]["originalVectorShapes"],65)
            self.assertEqual(report["artwork"]["attachedActorParts"],6)
            self.assertEqual(len(report["artwork"]["continuousCameraGroups"]),1)
            self.assertFalse(report["publicationApproved"])
            self.assertTrue(video.with_suffix(".srt").is_file())


if __name__=="__main__":
    unittest.main()
