"""Evaluate optional optical-flow frames against ACTUAL held-out Blender renders.

The source frame at index i is not used to interpolate: only i-1 and i+1
are supplied. Its actual Cycles pixels then measure whether local motion
compensation improves or worsens the frame versus the old linear dissolve.
An action keeps the existing dissolve unless flow passes conservative gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

from .motion_interpolation import MotionPair, VERSION, mean_absolute_error
from .science_aurora import BEATS
from .science_blender_aurora import BlenderAuroraStage

SAMPLE_FRACTIONS = (.08, .29, .52, .75, .92)
MIN_GAIN = .045
MIN_HELP_FRACTION = .60
MAX_SINGLE_REGRESSION = .20


def evaluate(folder: Path, destination: Path) -> dict:
    stage = BlenderAuroraStage(folder)
    if stage.count < 6:
        raise ValueError("Need at least six real Blender poses for holdout QA")
    manifest = folder / "manifest.json"
    source_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    stats = {}
    modes = {}
    contact = Image.new("RGB", (3 * 292, len(BEATS) * 260), (8, 17, 32))
    painter = ImageDraw.Draw(contact)

    for row, beat in enumerate(BEATS):
        # Distinct real middle frames are withheld from the flow estimate.
        indices = sorted(set(
            max(1, min(stage.count - 2, round((stage.count - 1) * fraction)))
            for fraction in SAMPLE_FRACTIONS))
        measured = []
        for i in indices:
            with Image.open(stage.paths[beat][i - 1]) as img:
                first = img.convert("RGBA")
            with Image.open(stage.paths[beat][i + 1]) as img:
                second = img.convert("RGBA")
            with Image.open(stage.paths[beat][i]) as img:
                actual = img.convert("RGBA")
            interpolation = MotionPair(first, second)
            motion = interpolation.frame(.5)
            dissolve = Image.blend(first, second, .5)
            old_error = mean_absolute_error(dissolve, actual)
            new_error = mean_absolute_error(motion, actual)
            measured.append({
                "index": i,
                "dissolveMAE": round(old_error, 5),
                "motionMAE": round(new_error, 5),
                "motionP90Px": round(interpolation.p90_displacement_px, 3),
                "reliableFraction": round(interpolation.reliable_fraction, 4),
            })
            if i == indices[len(indices)//2]:
                for col, sample in enumerate((actual, dissolve, motion)):
                    thumbnail = sample.convert("RGB")
                    thumbnail.thumbnail((270, 216), Image.Resampling.LANCZOS)
                    x = col * 292 + (292 - thumbnail.width) // 2
                    y = row * 260 + 4
                    contact.paste(thumbnail, (x, y))

        first_error = sum(item["dissolveMAE"] for item in measured)
        second_error = sum(item["motionMAE"] for item in measured)
        gain = ((first_error - second_error) / first_error
                if first_error > 1e-9 else 0.)
        helped = sum(
            item["motionMAE"] <= item["dissolveMAE"] * .98
            for item in measured)
        severely_worse = any(
            item["motionMAE"] > item["dissolveMAE"] * (1 + MAX_SINGLE_REGRESSION)
            and item["motionMAE"] - item["dissolveMAE"] > .1
            for item in measured)
        selected = (gain >= MIN_GAIN and
                    helped / len(measured) >= MIN_HELP_FRACTION and
                    not severely_worse)
        modes[beat] = "flow" if selected else "dissolve"
        stats[beat] = {
            "holdouts": measured,
            "meanGain": round(gain, 5),
            "holdoutsHelped": helped,
            "mode": modes[beat],
        }
        painter.text((8, row * 260 + 223),
                     f"{beat}: {modes[beat].upper()} ({gain:+.1%} RGB MAE)",
                     fill=(214, 237, 248))
    painter.text((5, 4), "HELDOUT  /  DISSOLVE  /  FLOW",
                 fill=(247, 214, 149))
    contact_path = destination.parent / "motion-comparison.jpg"
    contact.save(contact_path, "JPEG", quality=89, optimize=True)

    payload = {
        "schemaVersion": 1,
        "renderer": "blender-cycles-cpu",
        "algorithm": VERSION,
        "sourceManifestSHA256": source_sha,
        "framesPerBeat": stage.count,
        "holdoutCount": sum(len(row["holdouts"]) for row in stats.values()),
        "gate": {
            "minMeanGain": MIN_GAIN,
            "minHelpFraction": MIN_HELP_FRACTION,
            "maxSingleRegression": MAX_SINGLE_REGRESSION,
        },
        "beatModes": modes,
        "stats": stats,
        "humanApproved": False,
        "publicationApproved": False,
        "limit": ("Optical flow is tested against withheld rendered poses. "
                  "This is 2D pixel inbetweening, NOT genuine 30fps Blender "
                  "geometry; reviewer must inspect moving MP4 for occlusions."),
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(evaluate(args.folder, args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
