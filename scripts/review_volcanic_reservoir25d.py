"""Review real native 9:16 animated volcanic reservoirs, not stock images."""
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
    narrated=(
        ("magma","Molten rock forms a chamber beneath the volcano."),
        ("pressure","Trapped gas bubbles increase pressure inside the chamber."),
        ("ascent","Rising magma pushes upward through the vent toward the summit."),
    )
    images=[]
    records=[]
    for i,(beat,words) in enumerate(narrated,start=1):
        scene=PortraitScienceScene(
            topic="How do volcanoes erupt?",narration=words,scene_index=i)
        if scene.volcano_beat!=beat:
            raise RuntimeError("Wrong scientific storyboard scene routing")
        frame=scene.frame(3.3,6.8)
        if frame.mode!="RGB" or frame.size!=(1080,1920):
            raise RuntimeError("Incorrect original 9:16 production scene")
        file=out/f"volcanic-reservoir-{beat}.png"
        frame.save(file)
        images.append(frame.resize((270,480),Image.Resampling.LANCZOS))
        records.append({"beat":beat,"file":file.name,
                        "sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
    if len({x["sha256"] for x in records})!=len(records):
        raise RuntimeError("Narrated volcanic scenes failed visual diversity check")
    contact=Image.new("RGB",(810,480),(9,19,34))
    for i,im in enumerate(images):
        contact.paste(im,(i*270,0))
    contact.save(out/"organic-magma-source-25d.jpg",quality=94)
    manifest={"originalSourceSize":[1080,1920],"orientation":"9:16",
              "samples":records,"requiresHumanVisualReview":True,
              "publicationApproved":False}
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
