"""Real 1080x1920 ocean-science source-world review without slideshow panels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.science_portrait import PortraitScienceScene


def render(out:Path)->dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    demos=(
        ("solar","The sun heats the surface ocean unevenly."),
        ("coriolis","Earth rotation bends currents through the Coriolis effect."),
        ("sinking","Cold, salty polar water sinks and drives deep circulation."),
    )
    thumbs=[]
    records=[]
    for i,(beat,narration) in enumerate(demos,start=1):
        scene=PortraitScienceScene(topic="Why do ocean currents move?",
                                   narration=narration,scene_index=i)
        if scene.beat!=beat:
            raise RuntimeError(f"Incorrect original ocean beat {beat}")
        frame=scene.frame(2.3,6.8)
        if frame.mode!="RGB" or frame.size!=(1080,1920):
            raise RuntimeError("Wrong native ocean source-frame format")
        path=out/f"ocean-open-world-{beat}.png"
        frame.save(path)
        thumbs.append(frame.resize((270,480),Image.Resampling.LANCZOS))
        records.append({"beat":beat,"file":path.name,
                        "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    contact=Image.new("RGB",(810,480),(9,19,34))
    for i,thumb in enumerate(thumbs):
        contact.paste(thumb,(270*i,0))
    contact.save(out/"ocean-without-slide-panels-25d.jpg",quality=94)
    manifest={"originalSourceSize":[1080,1920],"orientation":"9:16",
              "samples":records,"humanEditorialReview":True,
              "approvedForPublication":False}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
