"""Optional real Blender/Cycles 3D plates for science ocean Shorts.

Blender is not imported here. This package-side loader validates the exact
pre-rendered frame set before any expensive video render starts, then blends
adjacent real 3D camera poses behind the existing lossless titles, labels and
audio-aligned action animations. The normal free Pillow scene stays unchanged
when the explicit opt-in environment variable is absent.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw

from .science_ocean_depth import ORIGIN, SIZE, PALETTES

ENV_VAR = "AUTOMATE_YTB_OCEAN_3D_DIR"
VERSION = "blender-cycles-3d-ocean-v1"


class BlenderOceanStage:
    def __init__(self, folder: str | Path):
        self.root = Path(folder).resolve()
        manifest = self.root / "manifest.json"
        if not manifest.is_file():
            raise ValueError("3D ocean stage is missing its Blender render manifest")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("schemaVersion") != 1
                or data.get("generator") != "blender-cycles-cpu"):
            raise ValueError("Unverified Blender 3D render provenance")
        width, height, frames = (data.get("width"), data.get("height"),
                                 data.get("framesPerBeat"))
        if (type(width) is not int or type(height) is not int
                or type(frames) is not int or not 320 <= width <= SIZE[0]
                or not 320 <= height <= SIZE[1] or not 2 <= frames <= 24):
            raise ValueError("Unsafe Blender 3D render frame dimensions")
        beats = data.get("beats")
        if not isinstance(beats, dict) or set(beats) != set(PALETTES):
            raise ValueError("Incomplete 3D ocean semantic shots")
        checked = {}
        for beat, records in beats.items():
            if not isinstance(records, list) or len(records) != frames:
                raise ValueError("Incomplete 3D camera keyframes")
            checked[beat] = []
            for i, rec in enumerate(records):
                expected = f"{beat}/{i:04d}.png"
                if (not isinstance(rec, dict) or rec.get("path") != expected
                        or not isinstance(rec.get("sha256"), str)
                        or len(rec["sha256"]) != 64):
                    raise ValueError("Unsafe Blender frame manifest path/hash")
                frame = self.root / expected
                if not frame.is_file():
                    raise ValueError(f"Missing 3D frame: {expected}")
                digest = hashlib.sha256(frame.read_bytes()).hexdigest()
                if digest != rec["sha256"]:
                    raise ValueError(f"Corrupt 3D frame: {expected}")
                with Image.open(frame) as img:
                    if img.size != (width, height) or img.format != "PNG":
                        raise ValueError(f"Invalid 3D frame: {expected}")
                checked[beat].append(frame)
        self.frames = checked
        self.count = frames
        self.source_size = (width, height)

    @lru_cache(maxsize=4)
    def _pose(self, beat: str, index: int) -> Image.Image:
        with Image.open(self.frames[beat][index]) as source:
            plate = source.convert("RGBA").resize(
                SIZE, Image.Resampling.LANCZOS)
        alpha = Image.new("L", SIZE)
        ImageDraw.Draw(alpha).rounded_rectangle(
            (0, 0, SIZE[0]-1, SIZE[1]-1), radius=39, fill=255)
        plate.putalpha(alpha)
        return plate

    def composite(self, canvas: Image.Image, beat: str, *,
                  t: float, duration: float) -> None:
        if (canvas.mode != "RGBA" or canvas.size != (1080, 1920)
                or beat not in self.frames or type(t) not in (int, float)
                or type(duration) not in (int, float) or not math.isfinite(t)
                or not math.isfinite(duration)
                or not 0 < duration <= 180 or not 0 <= t <= duration):
            raise ValueError("Invalid Blender 3D stage clock/portrait canvas")
        progress = (self.count - 1) * (t / duration)
        lower = min(self.count - 1, int(progress))
        upper = min(self.count - 1, lower + 1)
        q = progress - lower
        first = self._pose(beat, lower)
        frame = first if q < 1e-9 or lower == upper else Image.blend(
            first, self._pose(beat, upper), q)
        canvas.alpha_composite(frame, ORIGIN)


def stage_from_environment() -> BlenderOceanStage | None:
    """Explicit opt-in: absent means legacy 2.5D, invalid means hard fail."""
    root = os.environ.get(ENV_VAR, "")
    return BlenderOceanStage(root) if root else None
