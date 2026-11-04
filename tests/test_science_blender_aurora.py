"""Safety and integration of real Blender aurora source-frame pipeline."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from automate_ytb.science_aurora import BEATS, draw_aurora
from automate_ytb.science_blender_aurora import (
    BlenderAuroraStage, ENV_VAR, stage_from_environment)
from automate_ytb.aurora_stage_review import review


def fixture(folder):
    beats={}
    for n,beat in enumerate(BEATS):
        (folder/beat).mkdir()
        frames=[]
        for i in range(2):
            path=folder/beat/f"{i:04d}.png"
            im=Image.effect_noise((320,320),22).convert("RGB")
            im.paste((n*21+30,i*80+38,92+n*22),(30,30,250,250))
            im.save(path)
            frames.append({"path":f"{beat}/{i:04d}.png",
                           "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        beats[beat]=frames
    (folder/"manifest.json").write_text(json.dumps({
        "schemaVersion":1,"domain":"aurora","generator":"blender-cycles-cpu",
        "width":320,"height":320,"framesPerBeat":2,"beats":beats
    }),encoding="utf8")


class BlenderAuroraTests(unittest.TestCase):
    def test_absent_opt_in_does_not_change_2d_pipeline(self):
        with patch.dict(os.environ,{ENV_VAR:""}):
            self.assertIsNone(stage_from_environment())

    def test_real_3d_frame_manifest_is_verified_and_interpolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            stage=BlenderAuroraStage(folder)
            a=stage.frame("curtains",t=0,duration=6)
            middle=stage.frame("curtains",t=3,duration=6)
            b=stage.frame("curtains",t=6,duration=6)
            self.assertEqual(a.size,(1080,1380))
            self.assertEqual(a.mode,"RGBA")
            self.assertNotEqual(a.getpixel((500,500)),b.getpixel((500,500)))
            self.assertNotEqual(a.getpixel((500,500)),middle.getpixel((500,500)))
            self.assertNotEqual(b.getpixel((500,500)),middle.getpixel((500,500)))
            with patch.dict(os.environ,{ENV_VAR:str(folder)}):
                self.assertEqual(stage_from_environment().count,2)

    def test_tampering_never_silently_falls_back_to_2d(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            (folder/"emission"/"0001.png").write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError,"Tampered|unsafe"):
                BlenderAuroraStage(folder)

    def test_wrong_domain_and_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            file=folder/"manifest.json"
            doc=json.loads(file.read_text())
            doc["beats"]["collisions"][0]["path"]="../host.png"
            file.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"path"):
                BlenderAuroraStage(folder)
            doc["beats"]["collisions"][0]["path"]="collisions/0000.png"
            doc["domain"]="ocean"
            file.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"source domain"):
                BlenderAuroraStage(folder)

    def test_explanatory_overlays_and_safe_9_16_title_bands(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            stage=BlenderAuroraStage(folder)
            picture=Image.new("RGBA",(1080,1920),(3,12,33,255))
            draw_aurora(picture,"curtains",2,6,True,
                        rendered_stage=stage.frame("curtains",t=2,duration=6))
            self.assertEqual(picture.size,(1080,1920))
            self.assertEqual(picture.getpixel((300,100)),(3,12,33,255))
            self.assertEqual(picture.getpixel((300,1800)),(3,12,33,255))

    def test_real_3d_scene_never_paints_original_2d_rigs_over_it(self):
        # Regression: previously a complete 2D curtain was painted over
        # Blender's actual volumetric-looking translucent geometry. This
        # also duplicated the two physically rendered planetary props.
        artist_names=("_sphere","_stream","_field","_molecules","_curtains")
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            stage=BlenderAuroraStage(folder)
            for beat in BEATS:
                with self.subTest(beat=beat):
                    picture=Image.new("RGBA",(1080,1920),(3,12,33,255))
                    from contextlib import ExitStack
                    with ExitStack() as stack:
                        artists=[stack.enter_context(
                            patch("automate_ytb.science_aurora."+name))
                            for name in artist_names]
                        draw_aurora(picture,beat,2,6,True,
                                    rendered_stage=stage.frame(beat,t=2,duration=6))
                        for artist in artists:
                            artist.assert_not_called()
                    self.assertNotEqual(picture.getpixel((540,900)),
                                        (3,12,33,255))

    def test_2d_curtailed_mode_retains_original_animated_effect(self):
        from automate_ytb.science_aurora import _curtains
        picture=Image.new("RGBA",(1080,1920),(3,12,33,255))
        with patch("automate_ytb.science_aurora._curtains",wraps=_curtains) as effect:
            draw_aurora(picture,"curtains",2,6,True)
            effect.assert_called_once()

    def test_contact_sheet_does_not_falsely_approve(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            result=review(folder,folder/"review.jpg")
            self.assertEqual(result["scenesReviewed"],5)
            self.assertTrue(result["allAnimated"])
            self.assertFalse(result["publicationApproved"])
            self.assertGreater((folder/"review.jpg").stat().st_size,1000)

    def test_invalid_clock_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            stage=BlenderAuroraStage(folder)
            with self.assertRaises(ValueError):
                stage.frame("curtains",t=9,duration=6)
            with self.assertRaises(ValueError):
                stage.frame("curtains",t=float("nan"),duration=6)


if __name__=="__main__":
    unittest.main()
