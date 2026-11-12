"""Real original artwork import, independent 2.5D parallax and license gates."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image, ImageDraw

from automate_ytb.universal_art25d import (
    load_art_scenes, render_art_stage, validate_layers)
from automate_ytb.universal_kinetic import (
    frame_image, produce, read_story, timeline_for)


def _layer(name, z, px, py, material):
    return {
        "file": name, "z": z, "parallaxX": px, "parallaxY": py,
        "material": material,
        "rights": "Composed from scratch by this test in PIL; no external media.",
        "rightsConfirmed": True,
    }


def _art(path):
    folder=path/"owned"
    folder.mkdir()
    sky=Image.new("RGBA",(512,400),(17,39,71,255))
    draw=ImageDraw.Draw(sky)
    for y in range(400):
        draw.line((0,y,512,y),fill=(18+y//32,44+y//11,68+y//7,255))
    draw.ellipse((350,40,480,170), fill=(249,189,113,255))
    draw.polygon([(0,340),(150,185),(285,340)],fill=(27,75,82,255))
    draw.polygon([(170,350),(375,157),(512,357)],fill=(35,85,91,255))
    sky.save(folder/"sky.png")
    tree=Image.new("RGBA",(512,400))
    draw=ImageDraw.Draw(tree)
    draw.polygon([(244,365),(225,310),(247,155),(280,160),(290,310),(275,365)],
                 fill=(102,69,42,255))
    for cx,cy,r in ((225,185,93),(295,210,88),(256,123,88)):
        draw.ellipse((cx-r,cy-r,cx+r,cy+r),
                     fill=(51,133+(cx%14),77,240))
    tree.save(folder/"tree.png")
    return [
        _layer("owned/sky.png",5,.17,.09,"none"),
        _layer("owned/tree.png",45,1.1,.62,"foliage"),
    ]


def _story(layers):
    return {
        "schemaVersion":1,
        "topic":"An original illustrated forest journey",
        "language":"en",
        "beats":[
            {"kind":"concept","title":"The forest wakes",
             "narration":"Sunlight reaches a lush forest while a tree moves gently in the morning air.",
             "nodes":["Sunlight","Forest","Tree"],
             "visualLayers":layers},
            {"kind":"sequence","title":"Following the light",
             "narration":"First a warm light appears, then the garden brightens, and the journey continues.",
             "steps":["A light appears","The garden brightens","Journey continues"]},
        ],
    }


class UniversalOriginalLayerTests(unittest.TestCase):
    def test_real_original_assets_and_independent_parallax(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            layers=_art(folder)
            brief=folder/"story.json"
            brief.write_text(json.dumps(_story(layers)),encoding="utf8")
            data=read_story(brief)
            scenes,provenance=load_art_scenes(data,brief,360,640)
            self.assertEqual(len(provenance),2)
            self.assertEqual(set(scenes),{0})
            self.assertTrue(all(len(x["sha256"])==64 for x in provenance))
            a=render_art_stage(scenes[0],20,0,90)
            b=render_art_stage(scenes[0],70,0,90)
            self.assertEqual(a.mode,"RGBA")
            self.assertNotEqual(a.tobytes(),b.tobytes())
            stamps=[0,90,180]
            timeline=timeline_for(data,stamps)
            frame_a=frame_image(data,timeline,stamps,20,360,640,art_scenes=scenes)
            frame_b=frame_image(data,timeline,stamps,70,360,640,art_scenes=scenes)
            self.assertNotEqual(frame_a.tobytes(),frame_b.tobytes())
            self.assertEqual(frame_a.size,(360,640))

    def test_unsafe_assets_and_unconfirmed_rights_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            layers=_art(root)
            for file in ("../../private.png","/tmp/private.png","https://unsafe.com/a.png",
                         "owned/photo.jpg","owned/../sky.png"):
                example=[dict(layers[0],file=file)]
                with self.subTest(file=file),self.assertRaises(ValueError):
                    validate_layers(example)
            for bad in (None,False,"yes"):
                with self.subTest(approved=bad),self.assertRaises(ValueError):
                    validate_layers([dict(layers[0],rightsConfirmed=bad)])
            brief=root/"story.json"
            fake=_story(layers)
            fake["beats"][0]["visualLayers"][0]["file"]="owned/missing.png"
            brief.write_text(json.dumps(fake),encoding="utf8")
            compiled=read_story(brief)
            with self.assertRaises(ValueError):
                load_art_scenes(compiled,brief,360,640)
            fake=_story(layers)
            fake["beats"][0]["kind"]="measure"
            fake["beats"][0]["label"]="Distance"
            fake["beats"][0]["value"]="1"
            fake["beats"][0]["scaleMax"]="10"
            fake["beats"][0]["unit"]="m"
            brief.write_text(json.dumps(fake),encoding="utf8")
            with self.assertRaises(ValueError):
                read_story(brief)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "Open source media tools unavailable")
    def test_encoded_original_illustrated_video(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            layers=_art(folder)
            brief=folder/"story.json"
            brief.write_text(json.dumps(_story(layers)),encoding="utf8")
            target=folder/"art-short.mp4"
            result=produce(brief,target,voice="espeak",width=720)
            self.assertEqual(result["delivery"]["status"],"passed")
            self.assertGreater(target.stat().st_size,10000)
            self.assertEqual(result["artwork"]["scenesWithRealAuthoredArtwork"],1)
            self.assertEqual(len(result["artwork"]["approvedLayerProvenance"]),2)


if __name__=="__main__":
    unittest.main()
