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

    def test_translucent_overlays_blend_without_erasing_underlying_art(self):
        # Reusable material grammar: shadow, translucent glass, reflection.
        base=_example.blossom()
        base["shapes"]=[
            {"kind":"roundedRect","box":[.1,.1,.9,.9],"radius":.04,
             "fill":"#203040","stroke":None,"strokeWidth":0},
            {"kind":"ellipse","box":[.2,.2,.8,.8],
             "fill":"#FFFFFF","stroke":None,"strokeWidth":0,
             "opacity":.25},
        ]
        approved=validate_vector_layers([base])[0]
        self.assertEqual(approved["shapes"][0]["opacity"],1.)
        self.assertEqual(approved["shapes"][1]["opacity"],.25)
        a=render_vector_layer(approved,(240,240))
        b=render_vector_layer(approved,(240,240))
        self.assertEqual(a.tobytes(),b.tobytes())
        center=a.getpixel((120,120))
        outside=a.getpixel((40,40))
        self.assertEqual(center[3],255)
        self.assertGreater(center[0],outside[0])
        self.assertLess(center[0],255)
        self.assertEqual(a.getpixel((0,0))[3],0)
        self.assertNotEqual(vector_sha256(approved),vector_sha256(
            validate_vector_layers([dict(base,shapes=base["shapes"][:1])])[0]))
        # On a transparent layer, translucent ink must keep its own alpha.
        isolated=dict(base,shapes=[base["shapes"][1]])
        alpha=render_vector_layer(validate_vector_layers([isolated])[0],
                                  (240,240)).getpixel((120,120))[3]
        self.assertTrue(50<=alpha<=80)

    def test_transparency_validation_rejects_invalid_opacity(self):
        for opacity in (0,-.1,1.01,True,"0.5",float("nan"),
                        float("inf"),None):
            layer=_example.blossom()
            layer["shapes"][0]["opacity"]=opacity
            with self.subTest(opacity=opacity),self.assertRaises(ValueError):
                validate_vector_layers([layer])

    def test_shape_local_multistop_surface_lighting_is_real_and_repeatable(self):
        flower=_example.blossom()
        shape={"kind":"roundedRect","box":[.25,.25,.75,.75],
               "radius":.03,"stroke":None,"strokeWidth":0,
               "fill":{"colors":["#112233","#326699","#D3F3FF"],
                       "direction":"horizontal","space":"shape"}}
        flower["shapes"]=[shape]
        original=validate_vector_layers([flower])[0]
        a=render_vector_layer(original,(400,400))
        b=render_vector_layer(original,(400,400))
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.getpixel((30,30))[3],0)
        self.assertEqual(a.getpixel((200,200))[3],255)
        self.assertNotEqual(a.getpixel((110,200)),a.getpixel((290,200)))
        self.assertEqual(a.getpixel((110,140)),a.getpixel((110,260)))
        # A radial four-stop source has materially different center / edge.
        radial=deepcopy(flower)
        radial["shapes"][0]["fill"]={
            "colors":["#FFEAC4","#E4AF88","#7D5B75","#1B284B"],
            "direction":"radial","space":"shape"}
        valid=validate_vector_layers([radial])[0]
        render=render_vector_layer(valid,(400,400))
        self.assertNotEqual(render.getpixel((200,200)),
                            render.getpixel((120,200)))
        self.assertNotEqual(vector_sha256(original),vector_sha256(valid))
        # Five color stops and stage-relative lighting are supported without
        # silently interpreting spatial layout as a new factual assertion.
        global_shading=deepcopy(flower)
        global_shading["shapes"][0]["fill"]={
            "colors":["#111111","#393939","#777777","#BBBBBB","#FFFFFF"],
            "direction":"diagonal","space":"stage"}
        shade=render_vector_layer(
            validate_vector_layers([global_shading])[0],(400,400))
        self.assertNotEqual(shade.getpixel((120,120)),
                            shade.getpixel((280,280)))

    def test_multistop_shading_invalid_inputs_are_rejected(self):
        normal={"colors":["#112233","#445566","#DDEEFF"],
                "direction":"horizontal","space":"shape"}
        for bad in (
                {"colors":["#000000"],"direction":"vertical","space":"shape"},
                {"colors":["#000000"]*6,"direction":"vertical","space":"shape"},
                {"colors":"#FFFFFF","direction":"vertical","space":"shape"},
                dict(normal,direction="backward"),
                dict(normal,space="unknown"),
                dict(normal,extra="unsafe"),
                dict(normal,colors=["#FFFFFF","not-a-color"]),
                dict(normal,colors=["#FFFFFF",None]),
                dict(normal,colors=[1,2]),
        ):
            layer=_example.blossom()
            layer["shapes"][0]["fill"]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_vector_layers([layer])

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
