"""Render inspectable genuine three-domain 2.5D ribbon scenes at 1080x1920."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.material_ribbons25d import VERSION

SAMPLES=(
    ("rainbow","How do rainbows form?",
     "Entering a raindrop, sunlight bends in water and separates into colors.",
     "refraction"),
    ("ocean","Why do Earth's ocean currents move?",
     "Global winds push warm surface ocean water, driving currents.", "wind"),
    ("volcano","How do volcanoes erupt?",
     "Escaping lava flows down the volcanic slopes while rocks cool.", "lava"),
)


def render(folder:Path)->dict:
    folder=folder.resolve()
    folder.mkdir(parents=True,exist_ok=True)
    previews=[]
    report=[]
    for index,(name,topic,narration,expected_beat) in enumerate(SAMPLES,1):
        scene=PortraitScienceScene(
            topic=topic,narration=narration,scene_index=index)
        actual=scene.rainbow_beat if name=="rainbow" else (
            scene.volcano_beat if name=="volcano" else scene.beat)
        if actual!=expected_beat:
            raise RuntimeError("Wrong semantic production action: "+name+
                               " expected "+expected_beat+" got "+str(actual))
        screenshot=scene.frame(1.8,6.)
        if screenshot.mode!="RGB" or screenshot.size!=(1080,1920):
            raise RuntimeError("Bad real 2.5D video source frame")
        path=folder/(name+"-real-25d.png")
        screenshot.save(path,format="PNG")
        previews.append(screenshot.resize((270,480),Image.Resampling.LANCZOS))
        report.append({"topic":name,"beat":actual,"frame":path.name,
                       "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                       "sourceWidth":1080,"sourceHeight":1920})
    contact=Image.new("RGB",(len(previews)*270,480))
    for index,img in enumerate(previews):
        contact.paste(img,(index*270,0))
    contact.save(folder/"material-ribbons-contact.jpg",quality=92)
    manifest={"schemaVersion":1,"pipeline":"original-25d-three-domain",
              "materialsVersion":VERSION,"frameCount":3,
              "samples":report,"published":False,"humanReviewRequired":True}
    (folder/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    return manifest


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=render(args.out)
    print(json.dumps({"renderedTopics":[x["topic"] for x in result["samples"]],
                      "materialVersion":result["materialsVersion"],
                      "humanReviewRequired":True}))


if __name__=="__main__":
    main()
