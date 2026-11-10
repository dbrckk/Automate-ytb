"""Inspect native volcano silhouette and physically linked 2.5D action frames."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.science_volcano_mesh import TERRAIN_VERSION


def render(out:Path)->dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    examples=(
        ("eruption","Ash and glowing fragments erupt from the volcanic crater."),
        ("lava","Molten lava flows down volcanic slopes and slowly cools."),
    )
    thumbs=[]
    samples=[]
    for beat,narration in examples:
        shot=PortraitScienceScene(topic="How do volcanoes erupt?",
                                  narration=narration,scene_index=3)
        if shot.volcano_beat!=beat:
            raise RuntimeError(f"Wrong original volcanic narrative: {beat}")
        frame=shot.frame(2.3,6.8)
        if frame.size!=(1080,1920) or frame.mode!="RGB":
            raise RuntimeError("Volcanic source is not true 9:16")
        path=out/f"natural-slope-{beat}.png"
        frame.save(path)
        thumbs.append(frame.resize((270,480),Image.Resampling.LANCZOS))
        samples.append({"beat":beat,"file":path.name,
                        "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    sheet=Image.new("RGB",(540,480),(9,18,32))
    for i,im in enumerate(thumbs):
        sheet.paste(im,(i*270,0))
    sheet.save(out/"original-eroded-volcanic-rock-25d.jpg",quality=95)
    manifest={"terrainVersion":TERRAIN_VERSION,"originalSize":[1080,1920],
              "orientation":"9:16","samples":samples,
              "humanEditorialReviewRequired":True,"publicationApproved":False}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(parser.parse_args().out)))
