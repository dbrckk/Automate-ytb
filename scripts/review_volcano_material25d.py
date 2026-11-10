"""Render actual original volcano Shorts frames for before/after art QA."""
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
        ("cutaway","Gas pressure grows in the magma chamber."),
        ("eruption","Ash erupts upward as the volcano releases trapped gases."),
    )
    images=[]
    records=[]
    for i,(name,narration) in enumerate(demos,start=1):
        scene=PortraitScienceScene(topic="How do volcanoes erupt?",
                                    narration=narration,scene_index=i)
        frame=scene.frame(2.1,6.8)
        if frame.size!=(1080,1920) or frame.mode!="RGB":
            raise RuntimeError("Invalid native volcano evidence frame")
        filename=f"{name}-source.png"
        target=out/filename
        frame.save(target)
        images.append(frame.resize((270,480),Image.Resampling.LANCZOS))
        records.append({"name":name,"filename":filename,
                        "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    if records[0]["sha256"]==records[1]["sha256"]:
        raise RuntimeError("Two story subjects must not share a flat poster")
    montage=Image.new("RGB",(540,480),(7,17,36))
    for idx,img in enumerate(images):
        montage.paste(img,(idx*270,0))
    montage.save(out/"original-weathered-volcano-25d.jpg",quality=94)
    manifest={"orientation":"9:16","sourceSize":[1080,1920],
              "shots":records,"humanReviewRequired":True,
              "publicationApproved":False}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
