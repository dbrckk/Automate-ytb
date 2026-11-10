"""Review original 2.5D fluid jets in real volcano and ocean video scenes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.fluid_emitter25d import VERSION


def render(out:Path)->dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    subjects=(
        ("magma","How do volcanoes erupt?",
         "When magma reaches the surface, expanding gases blast ash and glowing fragments high into the sky."),
        ("spray","Why do ocean currents move?",
         "Global winds push surface waters, driving powerful currents."),
    )
    frames=[]
    records=[]
    for material,topic,narration in subjects:
        scene=PortraitScienceScene(topic=topic,narration=narration,
                                   scene_index=4)
        for t in (1.0,2.8):
            frame=scene.frame(t,6.8)
            if frame.size!=(1080,1920) or frame.mode!="RGB":
                raise RuntimeError("Real original source video isn't native 9:16")
            path=out/f"{material}-{t:.1f}.png"
            frame.save(path)
            records.append({
                "material":material,"timeSeconds":t,"file":path.name,
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
            })
            frames.append(frame.resize((270,480),Image.Resampling.LANCZOS))
    for m in ("magma","spray"):
        if len(set(x["sha256"] for x in records if x["material"]==m))!=2:
            raise RuntimeError(f"Unmoving original fluid material: {m}")
    contact=Image.new("RGB",(1080,480),(8,17,31))
    for i,frame in enumerate(frames):
        contact.paste(frame,(270*i,0))
    contact.save(out/"original-jet-and-surface-spray-25d.jpg",quality=94)
    manifest={
        "version":VERSION,"nativeSource":[1080,1920],
        "orientation":"9:16","frames":records,
        "requiresHumanVisualReview":True,"published":False,
    }
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(p.parse_args().out)))
