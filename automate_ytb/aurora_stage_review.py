"""Produce a compact independent editorial contact sheet for REAL aurora 3D frames.

The five scene mid-poses come from verified Blender PNGs. The file itself
does not claim publication rights, artistic excellence or physical accuracy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from .science_aurora import BEATS
from .science_blender_aurora import BlenderAuroraStage


def review(folder: Path, destination: Path) -> dict:
    stage = BlenderAuroraStage(folder)
    sheet=Image.new("RGB",(5*305,360),(7,14,29))
    draw=ImageDraw.Draw(sheet)
    changes={}
    for i,beat in enumerate(BEATS):
        first=stage._pose(beat,0)
        last=stage._pose(beat,stage.count-1)
        # RGBA difference alpha is zero when both frames are opaque; Pillow
        # getbbox() defaults to alpha-only and would falsely mark every
        # genuine 3D camera movement as frozen. Inspect RGB differences.
        active=ImageChops.difference(first.convert("RGB"),last.convert("RGB")).getbbox() is not None
        changes[beat]=bool(active)
        if not active:
            raise ValueError(f"Frozen genuine 3D Blender aurora shot: {beat}")
        still=stage._pose(beat,stage.count//2).convert("RGB")
        still.thumbnail((288,310),Image.Resampling.LANCZOS)
        sheet.paste(still,(i*305+(305-still.width)//2,5))
        draw.text((i*305+12,321),beat.upper().replace("_"," "),fill=(221,242,255))
    destination.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(destination,format="JPEG",quality=88,optimize=True)
    report={
        "schemaVersion":1,"renderer":"blender-cycles-cpu",
        "domain":"aurora","scenesReviewed":len(BEATS),
        "framesPerBeat":stage.count,"allAnimated":all(changes.values()),
        "motionEvidence":changes,"humanApproved":False,
        "publicationApproved":False,
        "limit":"Two sampled source 3D poses per beat do not certify full temporal quality",
    }
    (destination.parent/"review.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf8")
    return report


def main(argv=None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--folder",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(argv)
    print(json.dumps(review(args.folder,args.out),indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
