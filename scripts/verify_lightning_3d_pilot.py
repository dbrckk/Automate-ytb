"""Fail-closed provenance and visual diversity gate for one real Cycles storm frame."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageStat


def validate(folder: Path) -> dict:
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Invalid storm pilot folder")
    manifest = folder / "manifest.json"
    if (not manifest.is_file() or manifest.is_symlink()
            or not 0 < manifest.stat().st_size < 16000):
        raise ValueError("Missing or unsafe source Cycles manifest")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or data.get("schemaVersion") != 1
            or data.get("generator") != "blender-cycles-cpu"
            or data.get("domain") != "original-storm-pbr-pilot"
            or data.get("file") != "storm-pbr-pilot.png"):
        raise ValueError("Wrong renderer or source domain")
    for name, minimum, maximum in (
        ("width", 320, 900), ("height", 400, 1380),
        ("samples", 4, 64), ("meshObjects", 100, 2000),
        ("lightObjects", 3, 16), ("proceduralMaterials", 8, 64),
        ("actual3dCloudMeshes", 3, 3),\n        ("actual3dCloudLobes", 42, 42),\n        ("actual3dCloudVertices", 1000, 500000),
    ):
        value = data.get(name)
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError("Incomplete or implausible 3D geometry evidence: "+name)
    digest = data.get("sha256")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)):
        raise ValueError("Invalid Blender image digest")
    picture = folder / "storm-pbr-pilot.png"
    if (not picture.is_file() or picture.is_symlink()
            or not 10000 <= picture.stat().st_size <= 40_000_000):
        raise ValueError("Missing or unsafe PBR pilot image")
    if hashlib.sha256(picture.read_bytes()).hexdigest() != digest:
        raise ValueError("Altered Blender 3D evidence")
    with Image.open(picture) as image:
        if image.format != "PNG" or image.size != (data["width"], data["height"]):
            raise ValueError("Wrong source-render dimensions or format")
        rgb = image.convert("RGB")
    # Prevent passing a fake all-black, solid-color, or very dark blank
    # render as a verified 3D visual; structure metrics alone are not enough.
    stats = ImageStat.Stat(rgb)
    if (min(stats.stddev) < 7 or max(stats.mean) < 16
            or min(stats.mean) > 180):
        raise ValueError("Unusable or flat 3D render")
    data["visualChannelMeans"] = [round(x,2) for x in stats.mean]
    data["visualChannelStddev"] = [round(x,2) for x in stats.stddev]
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.folder.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
