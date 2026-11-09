"""Offline contract tests for verified five-shot Blender motion evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image

from scripts.verify_lightning_3d_motion import BEATS,verify


class RealMotionArtifactContractTests(unittest.TestCase):
    def _fixture(self,root: Path):
        records=[]
        rng=random.Random(8177)
        for i in range(10):
            path=root/("frame-%04d.png"%i)
            source=rng.randbytes(320*400*3)
            Image.frombytes("RGB",(320,400),source).save(path)
            beat=BEATS[i//2]
            records.append({"file":path.name,"beat":beat,
                            "progress":round((i%2+.35)/2.1,4),
                            "visibleChannelFraction":
                            0 if beat=="charge" else
                            1 if beat in ("return","thunder") else .48,
                            "electricalLightPower":.2,
                            "cameraPosition":[3.+i*.05,-10.,7.],
                            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        record={"schemaVersion":1,"version":"storm-3d-causal-motion-p54-v1",
                "generator":"blender-cycles-cpu-animated",
                "beatOrder":list(BEATS),"width":320,"height":400,
                "fps":8,"samples":8,"framesPerBeat":2,
                "cloudVertices":4400,"meshObjects":215,
                "actual3dCloudMeshes":3,"frameCount":10,
                "frameEvidence":records}
        (root/"manifest.json").write_text(json.dumps(record),encoding="utf8")
        return record

    def test_five_causal_shots_with_distinct_source_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self._fixture(root)
            result=verify(root,require_movie=False)
            self.assertEqual(result["frames"],10)
            self.assertEqual(result["beats"],list(BEATS))
            self.assertGreater(result["minChange"],20)

    def test_forged_single_frame_or_incomplete_story_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            doc=self._fixture(root)
            doc["frameEvidence"]=doc["frameEvidence"][:-1]
            (root/"manifest.json").write_text(json.dumps(doc),encoding="utf8")
            with self.assertRaises(ValueError):
                verify(root,require_movie=False)

    def test_altered_frame_is_rejected_by_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self._fixture(root)
            file=root/"frame-0007.png"
            Image.new("RGB",(320,400),(200,12,12)).save(file)
            with self.assertRaises(ValueError):
                verify(root,require_movie=False)

    def test_frozen_frame_is_rejected_even_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            doc=self._fixture(root)
            path=root/"frame-0001.png"
            path.write_bytes((root/"frame-0000.png").read_bytes())
            doc["frameEvidence"][1]["sha256"]=hashlib.sha256(
                path.read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(doc),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"frozen"):
                verify(root,require_movie=False)


if __name__=="__main__":
    unittest.main()
