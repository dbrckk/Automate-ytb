"""Load real Cycles-rendered aurora frames with fail-closed provenance checks.

The Blender executable is used in a separate GH Actions stage. This reader
never claims that a cached PNG is 3D without a verified original manifest.
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
VERSION = "cycles-aurora-stage-v1"


class BlenderAuroraStage:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        manifest = self.root / "manifest.json"
        if not manifest.is_file() or not 0 < manifest.stat().st_size < 160_000:
            raise ValueError("Missing or oversized real Blender aurora manifest")
        data = json.loads(manifest.read_text(encoding="utf8"))
        if (data.get("schemaVersion") != 1
                or data.get("domain") != "aurora"
                or data.get("generator") != "blender-cycles-cpu"):
            raise ValueError("Unverified 3D aurora renderer or source domain")
        w,h,count = data.get("width"),data.get("height"),data.get("framesPerBeat")
        if (type(w) is not int or type(h) is not int or type(count) is not int
                or not 320 <= w <= 1080 or not 320 <= h <= 1380
                or not 2 <= count <= 24):
            raise ValueError("Unsafe 3D aurora image dimensions/keyframe count")
        records = data.get("beats")
        if not isinstance(records, dict) or set(records) != set(BEATS):
            raise ValueError("Missing distinct 3D aurora action scenes")
        validated={}
        for beat in BEATS:
            list_ = records[beat]
            if not isinstance(list_,list) or len(list_) != count:
                raise ValueError("Incomplete 3D aurora scene keyframes")
            paths=[]
            for i,item in enumerate(list_):
                expected=f"{beat}/{i:04d}.png"
                if (not isinstance(item,dict) or item.get("path") != expected
                        or not isinstance(item.get("sha256"),str)
                        or len(item["sha256"]) != 64
                        or any(ch not in "0123456789abcdef" for ch in item["sha256"])):
                    raise ValueError("Invalid 3D aurora frame path or hash")
                file=self.root/expected
                if (not file.is_file() or not 1500 <= file.stat().st_size <= 30_000_000
                        or file.is_symlink()):
                    raise ValueError("Missing or unsafe 3D aurora frame")
                if hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError(f"Tampered 3D aurora frame {expected}")
                with Image.open(file) as image:
                    if image.format != "PNG" or image.size != (w,h):
                        raise ValueError("Invalid 3D aurora frame encoding")
                    image.verify()
                paths.append(file)
            validated[beat] = paths
        self.paths = validated
        self.count = count
        self.source_size = (w,h)

    @lru_cache(maxsize=4)
    def _pose(self, beat:str, index:int) -> Image.Image:
        with Image.open(self.paths[beat][index]) as file:
            return file.convert("RGBA").resize(
                STAGE_SIZE,Image.Resampling.LANCZOS)

    def frame(self, beat:str, *,t:float,duration:float) -> Image.Image:
        if (beat not in self.paths or type(t) not in (int,float)
                or type(duration) not in (int,float)
                or not math.isfinite(t) or not math.isfinite(duration)
                or not 0 < duration <= 180 or not 0 <= t <= duration):
            raise ValueError("Invalid Blender aurora beat/animation clock")
        pos=(self.count-1)*t/duration
        lo=min(self.count-1,int(pos))
        hi=min(self.count-1,lo+1)
        delta=pos-lo
        a=self._pose(beat,lo)
        if hi == lo or delta <= 1e-9:
            return a.copy()
        return Image.blend(a,self._pose(beat,hi),delta)


def stage_from_environment() -> BlenderAuroraStage | None:
    path=os.environ.get(ENV_VAR,"")
    return BlenderAuroraStage(path) if path else None
