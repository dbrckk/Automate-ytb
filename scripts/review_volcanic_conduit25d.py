"""Review two real 1080x1920 narrated volcano cutaway frames with one conduit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.science_portrait import PortraitScienceScene


def render(destination:Path)->dict:
    out=destination.resolve()
    out.mkdir(parents=True,exist_ok=True)
    scene=PortraitScienceScene(
        topic="How do volcanoes erupt?",
        narration="Rising pressure pushes magma up a rocky vent toward the summit.",
        scene_index=3)
    if scene.volcano_beat!="ascent":
        raise RuntimeError("Expected a real authored magma ascent frame")
    records=[]
    images=[]
    for t in (.9,5.6):
        frame=scene.frame(t,6.8)
        if frame.size!=(1080,1920) or frame.mode!="RGB":
            raise RuntimeError("Incorrect real production framing")
        path=out/f"magma-ascent-{t:.1f}.png"
        frame.save(path)
        records.append({"seconds":t,"file":path.name,
                        "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        images.append(frame.resize((270,480),Image.Resampling.LANCZOS))
    if records[0]["sha256"]==records[1]["sha256"]:
        raise RuntimeError("Ascent must visibly progress through actual rock")
    sheet=Image.new("RGB",(540,480),(7,17,30))
    sheet.paste(images[0],(0,0))
    sheet.paste(images[1],(270,0))
    sheet.save(out/"magma-conduit-source-frames.jpg",quality=94)
    manifest={"samples":records,"orientation":"9:16",
              "sourceSize":[1080,1920],"humanReviewRequired":True,
              "publicationApproved":False}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
