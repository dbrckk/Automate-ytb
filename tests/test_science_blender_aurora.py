"""Aurora Blender 3D integration: provenance, motion, format and UI-safe bands.

Fixture images are intentionally flat and only test the consumer. The
dedicated workflow actually executes Blender/Cycles to prove real geometry.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops

from automate_ytb.blender_aurora_review import review
from automate_ytb.science_aurora import BEATS, STAGE_SIZE, draw_aurora
from automate_ytb.science_blender_aurora import (
    BlenderAuroraStage, ENV_VAR, stage_from_environment)
from automate_ytb.science_portrait import PortraitScienceScene


def make_fixture(root: Path) -> None:
    records={}
    for beat_number, beat in enumerate(BEATS):
        (root/beat).mkdir(parents=True, exist_ok=True)
        frames=[]
        for i in range(2):
            rel=f"{beat}/{i:04d}.png"
            file=root/rel
            color=(20+beat_number*22+i*12,37+beat_number*12,74+i*20)
            Image.new("RGB",(320,410),color).save(file)
            frames.append({"path":rel,
                           "sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
        records[beat]=frames
    (root/"manifest.json").write_text(json.dumps({
        "schemaVersion":1,"generator":"blender-cycles-aurora-v1",
        "width":320,"height":410,"framesPerBeat":2,
        "beats":records}),encoding="utf8")


class RealAuroraStageTests(unittest.TestCase):
    def test_disabled_by_default_legacy_aurora_remains_functional(self):
        with patch.dict(os.environ,{ENV_VAR:""}):
            self.assertIsNone(stage_from_environment())
            shot=PortraitScienceScene(
                topic="Why Do Northern Lights Dance?",
                narration="The solar wind sends charged particles outward.",
                scene_index=1)
            self.assertIsNone(shot._blender_aurora_stage)
            image=shot.frame(0.2,1.0)
            self.assertEqual(image.size,(1080,1920))

    def test_five_distinct_3d_beats_interpolate_and_preserve_ui_bands(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_fixture(root)
            stage=BlenderAuroraStage(root)
            self.assertEqual(stage.count,2)
            self.assertEqual(set(stage.frames),set(BEATS))
            images=[stage.frame(beat,t=0,duration=6)
                    for beat in BEATS]
            self.assertEqual(len({x.getpixel((500,600)) for x in images}),5)
            for beat in BEATS:
                before=stage.frame(beat,t=0,duration=6)
                after=stage.frame(beat,t=6,duration=6)
                mid=stage.frame(beat,t=3,duration=6)
                self.assertEqual(mid.size, STAGE_SIZE)
                self.assertNotEqual(before.getpixel((500,600)),
                                    after.getpixel((500,600)))
                self.assertNotEqual(mid.getpixel((500,600)),
                                    before.getpixel((500,600)))
            canvas=Image.new("RGBA",(1080,1920),(3,12,33,255))
            plate=stage.frame("solar_wind",t=3,duration=6)
            draw_aurora(canvas,"solar_wind",t=3,duration=6,
                        english=True,stage_plate=plate)
            self.assertEqual(canvas.getpixel((500,180)),(3,12,33,255))
            self.assertEqual(canvas.getpixel((500,1800)),(3,12,33,255))
            self.assertNotEqual(canvas.getpixel((500,800)),(3,12,33,255))

    def test_complete_sha256_provenance_is_mandatory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_fixture(root)
            with patch.dict(os.environ,{ENV_VAR:str(root)}):
                self.assertIsInstance(stage_from_environment(),BlenderAuroraStage)
                shot=PortraitScienceScene(
                    topic="Why Do Northern Lights Dance?",
                    narration="Charged particles collide with gases in the upper sky.",
                    scene_index=1)
                self.assertIsInstance(shot._blender_aurora_stage,BlenderAuroraStage)
                self.assertEqual(shot.frame(.3,1.0).size,(1080,1920))
            (root/"curtains"/"0001.png").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"Corrupt"):
                BlenderAuroraStage(root)

    def test_manifest_traversal_missing_and_wrong_aspect_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_fixture(root)
            path=root/"manifest.json"
            manifest=json.loads(path.read_text())
            manifest["beats"]["solar_wind"][0]["path"]="../../etc/passwd"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,"manifest"):
                BlenderAuroraStage(root)
            make_fixture(root)
            manifest=json.loads(path.read_text())
            manifest["height"]=800
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,"aspect ratio"):
                BlenderAuroraStage(root)
            make_fixture(root)
            (root/"emission"/"0001.png").unlink()
            with self.assertRaisesRegex(ValueError,"Missing"):
                BlenderAuroraStage(root)

    def test_real_3d_review_sheet_remains_editorially_unapproved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_fixture(root)
            result=review(root,root/"review.jpg")
            self.assertEqual(set(result["animated"]),set(BEATS))
            self.assertTrue(result["distinctScenes"])
            self.assertFalse(result["humanApproved"])
            self.assertFalse(result["publicationApproved"])
            self.assertGreater((root/"review.jpg").stat().st_size,1000)

    def test_professional_highlight_gate_rejects_overexposed_3d_curtains(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_fixture(root)
            manifest=root/"manifest.json"
            data=json.loads(manifest.read_text())
            for i in range(2):
                file=root/"curtains"/f"{i:04d}.png"
                Image.new("RGB",(320,410),(250+i,250,249)).save(file)
                data["beats"]["curtains"][i]["sha256"]=hashlib.sha256(
                    file.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"Overexposed"):
                review(root,root/"not-approved.jpg")

    def test_time_and_input_bounds(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_fixture(root)
            stage=BlenderAuroraStage(root)
            for when,length in ((-1,6),(7,6),(0,0),(float("nan"),6)):
                with self.assertRaises(ValueError):
                    stage.frame("curtains",t=when,duration=length)
            with self.assertRaises(ValueError):
                stage.frame("unknown",t=0,duration=6)
            with self.assertRaises(ValueError):
                draw_aurora(Image.new("RGBA",(1080,1920)),
                            "curtains",1,6,True,
                            stage_plate=Image.new("RGB",(100,100)))


if __name__=="__main__":
    unittest.main()
