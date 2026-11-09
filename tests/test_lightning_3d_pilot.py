"""P5.3: strict isolated test of Blender PBR pilot deliverable contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image

from scripts.verify_lightning_3d_pilot import validate


class BlenderMaterialPilotTests(unittest.TestCase):
    def make_fixture(self, root: Path):
        rng = random.Random(1009)
        frame = Image.frombytes(
            "RGB", (320, 400),
            bytes(rng.randrange(256) for _ in range(320*400*3)))
        file = root / "storm-pbr-pilot.png"
        frame.save(file)
        record = {
            "schemaVersion": 1,
            "generator": "blender-cycles-cpu",
            "domain": "original-storm-pbr-pilot",
            "file": file.name,
            "width": 320, "height": 400, "samples": 8,
            "meshObjects": 150, "lightObjects": 3,
            "proceduralMaterials": 11, "actual3dCloudMeshes": 3,\n            "actual3dCloudLobes": 42, "actual3dCloudVertices": 5000,
            "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
        }
        (root / "manifest.json").write_text(json.dumps(record), encoding="utf8")
        return record

    def test_valid_source_metadata_and_visual_diversity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            result = validate(root)
            self.assertEqual(result["actual3dCloudMeshes"], 3)\n            self.assertEqual(result["actual3dCloudLobes"], 42)
            self.assertGreater(min(result["visualChannelStddev"]), 30)

    def test_pixel_modifications_are_rejected_even_with_valid_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            with Image.open(root / "storm-pbr-pilot.png") as image:
                corrected = image.copy()
            corrected.putpixel((10,10), (0, 0, 0))
            corrected.save(root / "storm-pbr-pilot.png")
            with self.assertRaises(ValueError):
                validate(root)

    def test_wrong_source_or_fake_geometry_is_not_mistaken_for_3d(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = self.make_fixture(root)
            data["generator"] = "made-up"
            (root / "manifest.json").write_text(json.dumps(data),encoding="utf8")
            with self.assertRaises(ValueError):
                validate(root)
            data["generator"] = "blender-cycles-cpu"
            data["meshObjects"] = 3
            (root / "manifest.json").write_text(json.dumps(data),encoding="utf8")
            with self.assertRaises(ValueError):
                validate(root)

    def test_a_solid_color_frame_cannot_pass_visual_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = self.make_fixture(root)
            Image.new("RGB",(320,400),(25,32,42)).save(
                root/"storm-pbr-pilot.png")
            data["sha256"] = hashlib.sha256(
                (root/"storm-pbr-pilot.png").read_bytes()).hexdigest()
            (root/"manifest.json").write_text(json.dumps(data),encoding="utf8")
            with self.assertRaises(ValueError):
                validate(root)


if __name__ == "__main__":
    unittest.main()
