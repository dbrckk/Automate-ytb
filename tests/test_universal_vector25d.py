"""Original inline-vector subject geometry, 2.5D source safety and real MP4."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import ImageChops, ImageStat

from automate_ytb.universal_vector25d import (
    validate_vector_layers,render_vector_layer,vector_fingerprint)
from automate_ytb.universal_art25d import (
    load_art_scenes,bind_actor_camera_world,render_art_stage)
from automate_ytb.universal_kinetic import (
    read_story,timeline_for,frame_image,produce)


def shape(kind, geometry, fill="#40B6DB", stroke=None,
          stroke_width=0, opacity=1.0,glow=0.0):
    return {"type":kind,"geometry":geometry,"fill":fill,"stroke":stroke,
            "strokeWidth":stroke_width,"opacity":opacity,"glow":glow}


def layer(z,name,shapes):
    return {"name":name,"z":z,"parallaxX":.4 if z<10 else 1.1,
            "parallaxY":.2 if z<10 else .7,"material":"none",
            "shapes":shapes}


def original_world():
    return [
        layer(4,"cinematic-sky",[
            shape("ellipse",[0,0,1,1],
                  {"top":"#091326","bottom":"#21557A"}),
            shape("ellipse",[.20,.09,.81,.70],
                  "#0B406E",glow=.017),
            shape("path",[
                {"op":"M","p":[.07,.75]},
                {"op":"C","c1":[.2,.53],"c2":[.6,.50],"p":[.94,.76]},
                {"op":"L","p":[.92,1]},
                {"op":"L","p":[.10,1]},
                {"op":"Z"}],
                  {"top":"#20717C","bottom":"#071E38"},
                  stroke="#75B7B5",stroke_width=.005,opacity=.94),
        ]),
        layer(45,"owned-bezier-seed",[
            shape("path",[
                {"op":"M","p":[.42,.55]},
                {"op":"C","c1":[.34,.30],"c2":[.61,.27],"p":[.66,.50]},
                {"op":"C","c1":[.71,.70],"c2":[.53,.73],"p":[.42,.55]},
                {"op":"Z"}],
                  {"top":"#F3B77B","bottom":"#985034"},
                  stroke="#FFE1AE",stroke_width=.008,glow=.018),
            shape("ellipse",[.45,.37,.51,.41],"#FFF1CA",opacity=.7),
            shape("path",[
                {"op":"M","p":[.45,.49]},
                {"op":"C","c1":[.50,.60],"c2":[.56,.61],"p":[.60,.61]}
            ],None,stroke="#FFE5AA",stroke_width=.005,opacity=.8)
        ]),
        layer(78,"new-growth",[
            shape("path",[
                {"op":"M","p":[.53,.56]},
                {"op":"C","c1":[.52,.45],"c2":[.48,.30],"p":[.52,.16]},
                {"op":"C","c1":[.55,.31],"c2":[.60,.40],"p":[.59,.55]},
                {"op":"Z"}],
                  {"top":"#B4DB88","bottom":"#36744F"},glow=.010),
            shape("path",[
                {"op":"M","p":[.51,.27]},
                {"op":"C","c1":[.33,.15],"c2":[.22,.27],"p":[.30,.37]},
                {"op":"C","c1":[.45,.39],"c2":[.54,.35],"p":[.51,.27]},
                {"op":"Z"}],
                  {"top":"#BAF186","bottom":"#2D8D62"},
                  stroke="#E1FFC0",stroke_width=.004),
            shape("path",[
                {"op":"M","p":[.52,.25]},
                {"op":"C","c1":[.66,.12],"c2":[.83,.24],"p":[.76,.36]},
                {"op":"C","c1":[.64,.40],"c2":[.54,.33],"p":[.52,.25]},
                {"op":"Z"}],
                  {"top":"#B5EE79","bottom":"#2F9065"},glow=.009)
        ]),
    ]


def keys(at,x=0.,y=0.,scale=1.,angle=0.):
    return {"at":at,"x":x,"y":y,"scale":scale,"angle":angle}


def story():
    vectors=original_world()
    a={"kind":"concept","title":"Seed and sprout",
       "narration":"A small seed absorbs water. A tiny new shoot begins to unfold.",
       "nodes":["Seed","Water","Shoot"],"visualVectors":vectors,
       "actorTracks":[
           {"z":45,"keys":[keys(0,-.08,.10,.72,-12),
                            keys(1,.02,.04,.99,3)]},
           {"z":78,"keys":[keys(0,.04,.17,.45,-7),
                            keys(1,-.05,.03,.91,5)]},
       ],"actorLinks":[{"fromZ":45,"toZ":78,"at":.62}]}
    b={"kind":"sequence","title":"The sprout changes",
       "narration":"The shoot rises toward the light. Two leaves slowly open above the seed.",
       "steps":["Shoot grows","Leaves open"],"visualVectors":vectors,
       "actorTracks":[
           {"z":45,"keys":[keys(0,.02,.04,.99,3),
                            keys(1,.01,.07,.94,2)]},
           {"z":78,"keys":[keys(0,-.05,.03,.91,5),
                            keys(1,.02,-.11,1.25,0)]},
       ]}
    return {"schemaVersion":1,"topic":"An original botanical diagram",
            "language":"en","beats":[a,b]}


class VectorCinematicTests(unittest.TestCase):
    def test_bezier_supersampling_and_materials_render_actual_rgba(self):
        specs=validate_vector_layers(original_world())
        self.assertEqual(len(specs),3)
        image=render_vector_layer(specs[1],(320,300))
        self.assertEqual(image.size,(320,300))
        self.assertEqual(image.mode,"RGBA")
        self.assertEqual(image.getpixel((0,0))[3],0)
        self.assertGreater(image.getbbox()[2]-image.getbbox()[0],32)
        self.assertEqual(image.tobytes(),
                         render_vector_layer(specs[1],(320,300)).tobytes())
        self.assertEqual(vector_fingerprint(specs[1]),
                         vector_fingerprint(specs[1]))
        bg=render_vector_layer(specs[0],(320,300))
        self.assertNotEqual(bg.getpixel((160,15)),bg.getpixel((160,275)))

    def test_untrusted_structural_content_rejected_without_svg_execution(self):
        base=original_world()[1]
        bad_cases=[
            dict(base,name="<script>alert('x')</script>"),
            dict(base,z=True),
            dict(base,parallaxX=float("nan")),
            dict(base,material="malicious"),
            dict(base,shapes=[dict(base["shapes"][0],type="image")]),
            dict(base,shapes=[dict(base["shapes"][0],fill="url(https://evil.example)")]),
            dict(base,shapes=[dict(base["shapes"][0],glow=999)]),
            dict(base,shapes=[dict(base["shapes"][0],opacity=True)]),
            dict(base,shapes=[dict(base["shapes"][0],
                         geometry=[{"op":"M","p":[0,.5]},
                                   {"op":"Z"},
                                   {"op":"C","c1":[.2,.4],"c2":[.3,.2],"p":[.4,.7]}])]),
            dict(base,shapes=[dict(base["shapes"][0],
                         geometry=[{"op":"M","p":[0,.5]},
                                   {"op":"L","p":[.5,float("inf")]},
                                   {"op":"Z"}])]),
        ]
        for case in bad_cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                validate_vector_layers([case])
        with self.assertRaises(ValueError):
            validate_vector_layers(original_world()*3)
        with self.assertRaises(ValueError):
            validate_vector_layers(original_world()[:1]*2)

    def test_no_external_image_files_and_continuous_original_visual_actor(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"story.json"
            path.write_text(json.dumps(story()),encoding="utf8")
            data=read_story(path)
            scenes,origin=load_art_scenes(data,path,360,640)
            self.assertEqual(sorted(scenes),[0,1])
            self.assertEqual(len(origin),6)
            self.assertTrue(all(p["sourceType"]=="original-inline-vector"
                                for p in origin))
            self.assertTrue(all(p["rightsManuallyConfirmedByAuthor"] is False
                                for p in origin))
            # cached raster should be the same object across the scene cut
            self.assertIs(scenes[0].layers[1].image,
                          scenes[1].layers[1].image)
            groups=bind_actor_camera_world(data,scenes,[0,90,180])
            self.assertEqual(len(groups),1)
            a=render_art_stage(scenes[0],89,0,90)
            b=render_art_stage(scenes[1],90,90,180)
            delta=ImageChops.difference(a,b)
            # One frame crossing the cut should preserve actual object form
            self.assertLess(sum(ImageStat.Stat(delta.convert("RGB")).mean)/3,12)
            timeline=timeline_for(data,[0,90,180])
            picture=frame_image(data,timeline,[0,90,180],105,360,640,
                                art_scenes=scenes)
            self.assertEqual(picture.size,(360,640))
            self.assertNotEqual(a.tobytes(),render_art_stage(
                scenes[0],9,0,90).tobytes())

    def test_numeric_integrity_and_reject_unsafe_mixed_depth(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"story.json"
            data=story()
            data["beats"][0]["visualVectors"][0]["z"]=45
            path.write_text(json.dumps(data),encoding="utf8")
            with self.assertRaises(ValueError):
                read_story(path)
            data=story()
            data["beats"][0]["kind"]="measure"
            data["beats"][0].update(
                {"label":"Quantity","value":2,"scaleMax":5,"unit":"cm"})
            path.write_text(json.dumps(data),encoding="utf8")
            with self.assertRaises(ValueError):
                read_story(path)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "System FFmpeg and speech renderer unavailable")
    def test_real_720p_shorts_with_original_bezier_actors(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            path=root/"story.json"
            path.write_text(json.dumps(story()),encoding="utf8")
            result=produce(path,root/"original-vector.mp4",
                           voice="espeak",width=720)
            self.assertEqual(result["delivery"]["status"],"passed")
            self.assertEqual(result["artwork"]["authoredActionActors"],4)
            self.assertEqual(result["artwork"]["authoredActorLinks"],1)
            self.assertEqual(len(result["artwork"]["continuousCameraGroups"]),1)
            self.assertEqual(result["artwork"]["scenesWithRealAuthoredArtwork"],2)
            self.assertTrue((root/"original-vector.srt").is_file())
            self.assertFalse(result["publicationApproved"])


if __name__=="__main__":
    unittest.main()
