"""Render matched real 9:16 source frames, with/without P5.25 geometry."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.semantic_geometry25d import VERSION


SCENES = (
    ("aurora", "Why do auroras glow?",
     "These glowing curtains of aurora ripple across the sky.",
     "automate_ytb.science_aurora.render_material_sheet"),
    ("ocean", "Why Do Ocean Currents Move?",
     "Global winds push surface waters, driving powerful currents.",
     "automate_ytb.science_ocean_depth.render_material_sheet"),
    ("volcano", "How do volcanoes erupt?",
     "An eruption sends an ash plume above the volcano.",
     "automate_ytb.science_volcano.render_material_sheet"),
)


def render(out: Path) -> dict:
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    records = []
    tiles = []
    for subject, topic, narration, target in SCENES:
        scene = PortraitScienceScene(topic=topic, narration=narration,
                                     scene_index=2)
        with patch(target, side_effect=lambda size, **kw: Image.new("RGBA",size)):
            before = scene.frame(2.3,6.4)
        after = scene.frame(2.3,6.4)
        if before.size != (1080,1920) or after.size != (1080,1920):
            raise RuntimeError("Comparison is not genuine 1080x1920 source")
        if not ImageChops.difference(
                before.crop((85,495,995,1465)),
                after.crop((85,495,995,1465))).getbbox():
            raise RuntimeError(f"No actual source geometry in {subject}")
        for safe in ((0,0,1080,320),(0,1510,1080,1920)):
            if before.crop(safe).tobytes() != after.crop(safe).tobytes():
                raise RuntimeError(f"Title or subtitles changed: {subject}")
        for version, image in (("before",before),("after",after)):
            path = out / f"{subject}-{version}.png"
            image.save(path)
            tiles.append(image.resize((270,480),Image.Resampling.LANCZOS))
            records.append({"subject":subject,"variant":version,
                            "filename":path.name,
                            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    board = Image.new("RGB",(1620,480),(9,17,26))
    for i,tile in enumerate(tiles):
        board.paste(tile,(270*i,0))
    board.save(out / "semantic-geometry-p525-contact.jpg",quality=94)
    report={"engine":VERSION,"subjects":[r[0] for r in SCENES],
            "frameSize":[1080,1920],"comparisonTimestampSeconds":2.3,
            "records":records,"humanEditorialReviewRequired":True,
            "editoriallyApproved":False}
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",
                                      encoding="utf-8")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    print(json.dumps(render(parser.parse_args().out)))
