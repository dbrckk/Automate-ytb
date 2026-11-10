"""Review source material motion in genuine volcano and ocean science Shorts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.dynamic_material25d import VERSION
from automate_ytb.science_portrait import PortraitScienceScene


def render(out: Path) -> dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    subjects=(
        ("magma","How do volcanoes erupt?",
         "Trapped gas bubbles build pressure in the magma chamber.",2),
        ("water","Why do ocean currents move?",
         "Earth rotation bends currents through the Coriolis effect.",3),
    )
    thumbs=[]
    records=[]
    for kind,topic,narration,index in subjects:
        shot=PortraitScienceScene(topic=topic,narration=narration,
                                   scene_index=index)
        ids=[]
        for t in (.7,2.9):
            image=shot.frame(t,6.8)
            if image.size!=(1080,1920) or image.mode!="RGB":
                raise RuntimeError("Invalid actual native 2.5D video frame")
            target=out/f"{kind}-{t:.1f}.png"
            image.save(target)
            ids.append(hashlib.sha256(target.read_bytes()).hexdigest())
            thumbs.append(image.resize((270,480),Image.Resampling.LANCZOS))
            records.append({"topic":kind,"timeSeconds":t,
                            "filename":target.name,"sha256":ids[-1]})
        if ids[0]==ids[1]:
            raise RuntimeError(f"Static disguised moving {kind} material")
    sheet=Image.new("RGB",(1080,480),(8,18,36))
    for i,image in enumerate(thumbs):
        sheet.paste(image,(i*270,0))
    sheet.save(out/"water-magma-advected-source-25d.jpg",quality=94)
    manifest={"version":VERSION,"sourceSize":[1080,1920],
              "orientation":"9:16","frames":records,
              "requiresHumanVisualReview":True,
              "publicationApproved":False}
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
