"""Create genuine 1080×1920 production frame evidence for animated water eddies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.flow_material25d import VERSION


def render(out: Path) -> dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    scene=PortraitScienceScene(
        topic="Why do ocean currents move?",
        narration="Earth rotation bends currents through the Coriolis effect.",
        scene_index=3)
    samples=[]
    thumb=[]
    for time in (.7,2.7):
        frame=scene.frame(time,6.)
        if frame.size!=(1080,1920) or frame.mode!="RGB":
            raise RuntimeError("Invalid native 2.5D output")
        name=f"gyre-t{time:.1f}.png"
        dest=out/name
        frame.save(dest)
        thumb.append(frame.resize((270,480),Image.Resampling.LANCZOS))
        samples.append({"timeSeconds":time,"file":name,
                        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest()})
    if samples[0]["sha256"]==samples[1]["sha256"]:
        raise RuntimeError("Source water motion did not animate")
    contact=Image.new("RGB",(540,480),(8,18,36))
    for index,image in enumerate(thumb):
        contact.paste(image,(index*270,0))
    contact.save(out/"moving-water-original-25d.jpg",quality=94)
    manifest={"version":VERSION,"orientation":"9:16",
              "sourceSize":[1080,1920],"samples":samples,
              "requiresHumanVisualReview":True,"approvedForPublication":False}
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(render(args.out)))


if __name__=="__main__":
    main()
