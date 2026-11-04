"""3D scene manifest, compositing, deterministic interpolation and fail-closed gates.

Fixtures are generated locally; Blender itself is covered by the dedicated
release-candidate workflow, not mocked as a 3D renderer.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from automate_ytb.blender_stage_review import review
from automate_ytb.science_blender_3d import (
    BlenderOceanStage, ENV_VAR, stage_from_environment)
from automate_ytb.science_ocean_depth import PALETTES


def fixture(folder: Path) -> None:
    records = {}
    for index, beat in enumerate(PALETTES):
        (folder / beat).mkdir(parents=True)
        rows = []
        for frame in range(2):
            rel = f"{beat}/{frame:04d}.png"
            path = folder / rel
            image = Image.new("RGB", (320, 320),
                              (14+index*17+frame*9, 55+index*7, 95+frame*13))
            image.save(path)
            rows.append({"path": rel,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        records[beat] = rows
    (folder / "manifest.json").write_text(
        json.dumps({"schemaVersion": 1, "generator": "blender-cycles-cpu",
                    "width": 320, "height": 320, "framesPerBeat": 2,
                    "beats": records}), encoding="utf8")


class BlenderStageTests(unittest.TestCase):
    def test_no_accidental_dependency_or_api_key(self):
        with patch.dict(os.environ, {ENV_VAR: ""}):
            self.assertIsNone(stage_from_environment())

    def test_pre_rendered_frames_are_interpolated_without_occluding_mobile_ui(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            fixture(path)
            stage = BlenderOceanStage(path)
            a = Image.new("RGBA", (1080, 1920), (1, 12, 25, 255))
            b = a.copy()
            stage.composite(a, "solar", t=0, duration=6)
            stage.composite(b, "solar", t=6, duration=6)
            self.assertNotEqual(a.getpixel((500, 1000)), b.getpixel((500, 1000)))
            self.assertEqual(a.getpixel((500, 400)), (1, 12, 25, 255))
            self.assertEqual(a.getpixel((500, 1700)), (1, 12, 25, 255))
            self.assertEqual(a.getpixel((30, 1000)), (1, 12, 25, 255))
            middle = Image.new("RGBA", (1080, 1920), (1, 12, 25, 255))
            stage.composite(middle, "solar", t=3, duration=6)
            self.assertNotEqual(middle.getpixel((500, 1000)),
                                a.getpixel((500, 1000)))
            self.assertNotEqual(middle.getpixel((500, 1000)),
                                b.getpixel((500, 1000)))

    def test_authentic_frame_manifest_never_silently_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            fixture(folder)
            with patch.dict(os.environ, {ENV_VAR: str(folder)}):
                self.assertEqual(stage_from_environment().count, 2)
            (folder/"solar"/"0000.png").write_bytes(b"tampered!")
            with self.assertRaisesRegex(ValueError, "Corrupt"):
                BlenderOceanStage(folder)

    def test_missing_frames_or_unsafe_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            fixture(folder)
            manifest = folder / "manifest.json"
            raw = json.loads(manifest.read_text())
            raw["beats"]["wind"][0]["path"] = "../outside.png"
            manifest.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                BlenderOceanStage(folder)

    def test_contact_sheet_checks_for_actual_animation_without_approving(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            fixture(folder)
            report=review(folder,folder/"review.jpg")
            self.assertEqual(set(report["animated"]),set(PALETTES))
            self.assertTrue(all(report["animated"].values()))
            self.assertFalse(report["humanApproved"])
            self.assertGreater((folder/"review.jpg").stat().st_size,1500)
            self.assertTrue((folder/"review.json").is_file())

    def test_clock_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            fixture(folder)
            stage = BlenderOceanStage(folder)
            canvas=Image.new("RGBA",(1080,1920))
            with self.assertRaises(ValueError):
                stage.composite(canvas,"wind",t=7,duration=6)
            with self.assertRaises(ValueError):
                stage.composite(canvas,"wind",t=0,duration=0)


if __name__ == "__main__":
    unittest.main()
