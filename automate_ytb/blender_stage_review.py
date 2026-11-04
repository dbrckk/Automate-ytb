"""Validate and create a compact review sheet of real Blender scene exports.

This must fail on incomplete/identical frames. It never generates a fake 3D
fallback or marks artistic approval as passed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from .science_blender_3d import BlenderOceanStage
from .science_ocean_depth import PALETTES


def review(folder: Path, destination: Path) -> dict:
    stage = BlenderOceanStage(folder)
    canvas = Image.new("RGB", (5 * 310, 345), (13, 22, 35))
    draw = ImageDraw.Draw(canvas)
    changes = {}
    for n, beat in enumerate(PALETTES):
        a = stage._pose(beat, 0).convert("RGB")
        b = stage._pose(beat, stage.count-1).convert("RGB")
        changes[beat] = ImageChops.difference(a, b).getbbox() is not None
        if not changes[beat]:
            raise ValueError(f"3D camera animation frozen for {beat}")
        thumbnail = stage._pose(beat, stage.count//2).convert("RGB")
        thumbnail.thumbnail((292, 285), Image.Resampling.LANCZOS)
        canvas.paste(thumbnail, (n*310+9, 8))
        draw.text((n*310+13, 310), beat.upper(), fill=(238, 245, 255))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=88, optimize=True)
    report = {"engine": "real-blender-cycles-cpu",
              "version": "review-3d-v1", "framesPerBeat": stage.count,
              "animated": changes, "humanApproved": False}
    (destination.parent/"review.json").write_text(
        json.dumps(report, indent=2)+"\n",encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(review(args.folder, args.out), indent=2))


if __name__ == "__main__":
    main()
