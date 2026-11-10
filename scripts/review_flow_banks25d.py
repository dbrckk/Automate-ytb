"""Inspect source-grounded lava channel and ocean flow on actual Shorts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.flow_banks25d import VERSION
from automate_ytb.science_portrait import PortraitScienceScene


def render(out:Path)->dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    examples=(
        ("lava","How do volcanoes erupt?",
         "Escaping lava flows down the slopes while ash settles."),
        ("water","Why do ocean currents move?",
         "Global winds push surface waters and drive strong surface currents."),
    )
    images=[]
    samples=[]
    for name,topic,narration in examples:
        scene=PortraitScienceScene(topic=topic,narration=narration,
                                   scene_index=3)
        for t in (1.1,4.7):
            frame=scene.frame(t,6.8)
            if frame.mode!="RGB" or frame.size!=(1080,1920):
                raise RuntimeError("Invalid original production frame")
            target=out/f"{name}-{t:.1f}.png"
            frame.save(target)
            images.append(frame.resize((270,480),Image.Resampling.LANCZOS))
            samples.append({"source":name,"second":t,"file":target.name,
                            "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    if len({v["sha256"] for v in samples})!=4:
        raise RuntimeError("Original material streams did not change by scene/time")
    contact=Image.new("RGB",(1080,480),(7,17,31))
    for i,frame in enumerate(images):
        contact.paste(frame,(270*i,0))
    contact.save(out/"original-lava-water-banks-25d.jpg",quality=94)
    manifest={"version":VERSION,"originalSize":[1080,1920],
              "portrait":"9:16","samples":samples,
              "requiresHumanReview":True,"published":False}
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
