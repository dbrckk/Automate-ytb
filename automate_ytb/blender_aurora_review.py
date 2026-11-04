"""Real Blender aurora review contact sheet and fail-closed motion checks.

Does not generate a synthetic replacement for Blender footage or automatically
approve art direction. The stills come from the SHA256-validated Blender PNGs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from .science_blender_aurora import BlenderAuroraStage
from .science_aurora import BEATS


def review(folder: Path, destination: Path) -> dict:
    stage = BlenderAuroraStage(folder)
    sheet = Image.new("RGB", (5*245, 365), (9, 16, 30))
    draw = ImageDraw.Draw(sheet)
    animated = {}
    thumbprints = []
    highlight_fractions = {}
    for index, beat in enumerate(BEATS):
        first = stage._pose(beat, 0).convert("RGB")
        last = stage._pose(beat, stage.count-1).convert("RGB")
        moving = ImageChops.difference(first, last).getbbox() is not None
        if not moving:
            raise ValueError(f"Frozen real Blender aurora frames for {beat}")
        animated[beat] = moving
        current = stage._pose(beat, stage.count//2).convert("RGB")
        # Detect blown-out broad glow panels; this is a safety bound,
        # not a metric for beauty or correct atmospheric physics.
        tiny = current.convert("L").resize((90, 115), Image.Resampling.BILINEAR)
        bright = sum(1 for value in tiny.getdata() if value >= 210)
        highlight_fractions[beat] = round(bright / (90*115), 4)
        if beat == "curtains" and highlight_fractions[beat] > .25:
            raise ValueError("Overexposed 3D aurora sheets hide atmospheric depth")
        small = current.resize((225, 288), Image.Resampling.LANCZOS)
        sheet.paste(small, (10+index*245, 12))
        draw.text((13+index*245, 317), beat.replace("_", " ").upper(),
                  fill=(221, 244, 250))
        thumbprints.append(small)
    # Detect a completely repeated 3D scene that differs only by a camera
    # keyframe. Real source and target scenes must not reuse one set of images.
    for i, left in enumerate(thumbprints):
        for j in range(i+1, len(thumbprints)):
            right = thumbprints[j]
            if ImageChops.difference(left, right).getbbox() is None:
                raise ValueError(f"Duplicate 3D aurora scene: {BEATS[i]}, {BEATS[j]}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=90, optimize=True)
    result = {
        "version": "real-aurora-3d-review-v1",
        "engine": "blender-cycles-cpu",
        "framesPerBeat": stage.count,
        "semanticBeats": list(BEATS),
        "animated": animated,
        "distinctScenes": True,
        "fractionOfVeryBrightPixelsByBeat": highlight_fractions,
        "humanApproved": False,
        "publicationApproved": False,
    }
    (destination.parent/"review.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    print(json.dumps(review(args.folder, args.out), indent=2))


if __name__=="__main__":
    main()
