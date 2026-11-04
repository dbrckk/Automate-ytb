"""Actual CPU motion compensation and holdout safety gate for Blender aurora."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np
from PIL import Image

from automate_ytb.aurora_motion_review import evaluate
from automate_ytb.motion_interpolation import MotionPair, mean_absolute_error
from automate_ytb.science_aurora import BEATS
from automate_ytb.science_blender_aurora import BlenderAuroraStage


def _source_frame(source: np.ndarray, offset: float) -> Image.Image:
    h,w=source.shape[:2]
    shifted=cv2.warpAffine(
        source, np.float32([[1,0,offset],[0,1,0]]),
        (w,h), flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT101)
    return Image.fromarray(cv2.cvtColor(shifted,cv2.COLOR_RGB2RGBA))


def _fixture(folder: Path, *, count=7) -> None:
    rng=np.random.default_rng(247)
    base=rng.integers(8,231,(240,320,3),dtype=np.uint8)
    cv2.circle(base,(108,103),31,(246,83,32),-1,cv2.LINE_AA)
    cv2.rectangle(base,(209,64),(278,157),(51,237,118),-1)
    manifest={"schemaVersion":1,"domain":"aurora",
              "generator":"blender-cycles-cpu",
              "width":320,"height":240,"framesPerBeat":count,"beats":{}}
    for beat in BEATS:
        directory=folder/beat
        directory.mkdir()
        records=[]
        for i in range(count):
            movement=4*i if beat in ("solar_wind","curtains") else 0
            image=_source_frame(base,movement)
            name=f"{i:04d}.png"
            path=directory/name
            image.save(path)
            records.append({
                "path":f"{beat}/{name}",
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        manifest["beats"][beat]=records
    (folder/"manifest.json").write_text(json.dumps(manifest),encoding="utf8")


class MotionInterpolationTests(unittest.TestCase):
    def test_motion_reconstruction_improves_known_translation(self):
        rng=np.random.default_rng(42)
        base=rng.integers(10,229,(240,320,3),dtype=np.uint8)
        cv2.rectangle(base,(105,51),(198,150),(228,62,39),-1)
        first,middle,last=(_source_frame(base,i) for i in (0,7,14))
        pair=MotionPair(first,last)
        predicted=pair.frame(.5)
        baseline=Image.blend(first,last,.5)
        self.assertLess(mean_absolute_error(predicted,middle),
                        mean_absolute_error(baseline,middle)*.85)
        self.assertEqual(pair.frame(0).tobytes(),first.tobytes())
        self.assertEqual(pair.frame(1).tobytes(),last.tobytes())
        self.assertGreater(pair.reliable_fraction,0)
        self.assertTrue(np.isfinite(pair.p90_displacement_px))

    def test_bad_inputs_cannot_silently_degrade_video(self):
        first=Image.new("RGBA",(240,320),(0,100,200,255))
        with self.assertRaises(ValueError):
            MotionPair(first,Image.new("RGBA",(320,240)))
        pair=MotionPair(first,first)
        with self.assertRaises(ValueError):
            pair.frame(float("nan"))
        with self.assertRaises(ValueError):
            pair.frame(1.01)

    def test_real_source_heldouts_select_motion_only_when_measurably_better(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            _fixture(root)
            report=evaluate(root,root/"motion-review.json")
            self.assertEqual(report["holdoutCount"],25)
            self.assertEqual(report["beatModes"]["solar_wind"],"flow")
            self.assertEqual(report["beatModes"]["curtains"],"flow")
            self.assertEqual(report["beatModes"]["collisions"],"dissolve")
            self.assertFalse(report["publicationApproved"])
            self.assertTrue((root/"motion-comparison.jpg").is_file())
            stage=BlenderAuroraStage(root)
            self.assertEqual(stage.motion_modes,report["beatModes"])
            first=stage.frame("solar_wind",t=0,duration=6)
            middle=stage.frame("solar_wind",t=.5,duration=6)
            self.assertEqual(first.size,(1080,1380))
            self.assertEqual(middle.mode,"RGBA")
            self.assertNotEqual(middle.tobytes(),first.tobytes())
            self.assertEqual(stage.motion_modes["emission"],"dissolve")

    def test_invalid_qa_is_rejected_and_no_report_keeps_legacy_dissolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            _fixture(root)
            stage=BlenderAuroraStage(root)
            self.assertEqual(set(stage.motion_modes.values()),{"dissolve"})
            evaluate(root,root/"motion-review.json")
            report_file=root/"motion-review.json"
            doc=json.loads(report_file.read_text())
            doc["sourceManifestSHA256"]="0"*64
            report_file.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"does not match"):
                BlenderAuroraStage(root)
            doc["sourceManifestSHA256"]=hashlib.sha256(
                (root/"manifest.json").read_bytes()).hexdigest()
            doc["beatModes"]["curtains"]="unproven-superresolution"
            report_file.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"Invalid per-scene"):
                BlenderAuroraStage(root)


if __name__=="__main__":
    unittest.main()
