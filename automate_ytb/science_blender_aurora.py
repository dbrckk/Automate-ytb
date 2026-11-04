"""Strict optional Blender/Cycles aurora plates for 9:16 science episodes.

The 3D stage is computed by a separately launched Blender CPU process,
never by simulated 2D '3D-looking' placeholders. No path or filename comes
from the narration. The five semantic scene frames are verified against a
complete SHA256 manifest before first frame. Failure is explicit; the
legacy 2.5D renderer remains the separate default.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path

from PIL import Image

from .science_aurora import BEATS, STAGE_SIZE

ENV_VAR = "AUTOMATE_YTB_AURORA_3D_DIR"
VERSION = "original-blender-aurora-cycles-v1"


class BlenderAuroraStage:
    def __init__(self, folder: str | Path):
        self.root = Path(folder).resolve()
        manifest_path = self.root / "manifest.json"
        if (not manifest_path.is_file()
                or manifest_path.stat().st_size > 40_000):
            raise ValueError("Blender aurora manifest is missing or oversized")
        raw = json.loads(manifest_path.read_text(encoding="utf8"))
        if (not isinstance(raw, dict) or raw.get("schemaVersion") != 1
                or raw.get("generator") != "blender-cycles-aurora-v1"):
            raise ValueError("Unverified real Blender aurora provenance")
        width, height, count = (raw.get("width"), raw.get("height"),
                                raw.get("framesPerBeat"))
        if (type(width) is not int or type(height) is not int
                or type(count) is not int
                or not 320 <= width <= 1080 or not 410 <= height <= 1380
                or not 2 <= count <= 24
                or abs(width / height - STAGE_SIZE[0] / STAGE_SIZE[1]) > .025):
            raise ValueError("Invalid aurora 3D source aspect ratio or frame count")
        records = raw.get("beats")
        if not isinstance(records, dict) or set(records) != set(BEATS):
            raise ValueError("Blender 3D aurora scenes do not cover all five beats")
        verified = {}
        for beat in BEATS:
            if not isinstance(records[beat], list) or len(records[beat]) != count:
                raise ValueError(f"Incomplete Blender aurora camera poses for {beat}")
            files = []
            for index, item in enumerate(records[beat]):
                relative = f"{beat}/{index:04d}.png"
                if (not isinstance(item, dict) or item.get("path") != relative
                        or not isinstance(item.get("sha256"), str)
                        or len(item["sha256"]) != 64):
                    raise ValueError(f"Invalid Blender aurora frame manifest: {beat}")
                file = self.root / relative
                if (not file.is_file() or not file.resolve().is_relative_to(self.root)
                        or file.stat().st_size > 25_000_000):
                    raise ValueError(f"Missing or unsafe 3D aurora frame: {relative}")
                if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError(f"Corrupt Blender aurora 3D frame: {relative}")
                with Image.open(file) as image:
                    if image.format != "PNG" or image.size != (width, height):
                        raise ValueError(f"Malformed Blender aurora frame: {relative}")
                    image.verify()
                files.append(file)
            verified[beat] = files
        self.frames = verified
        self.count = count
        self.source_size = (width, height)

    @lru_cache(maxsize=4)
    def _pose(self, beat: str, index: int) -> Image.Image:
        with Image.open(self.frames[beat][index]) as source:
            return source.convert("RGBA").resize(
                STAGE_SIZE, Image.Resampling.LANCZOS)

    def frame(self, beat: str, *, t: float, duration: float) -> Image.Image:
        """Smooth pose interpolation; does not claim 30 raytraced FPS.

        The returned image covers ONLY the original 1080x1380 scenic band;
        header, causal diagram and speech captions are composited separately.
        """
        if (beat not in self.frames or type(t) not in (int, float)
                or type(duration) not in (int, float)
                or not math.isfinite(t) or not math.isfinite(duration)
                or not 0 < duration <= 180 or not 0 <= t <= duration):
            raise ValueError("Invalid 3D aurora camera animation request")
        q = (self.count-1) * (t / duration)
        first = min(self.count-1, int(q))
        second = min(self.count-1, first+1)
        portion = q - first
        a = self._pose(beat, first)
        return a if portion < 1e-10 or first == second else Image.blend(
            a, self._pose(beat, second), portion)


def stage_from_environment() -> BlenderAuroraStage | None:
    location = os.environ.get(ENV_VAR, "")
    return BlenderAuroraStage(location) if location else None
