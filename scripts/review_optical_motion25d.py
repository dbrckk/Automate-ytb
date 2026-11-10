"""Actual 9:16 cross-topic original graphics engine motion evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from PIL import Image,ImageChops

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.optical_motion25d import VERSION


def render(out:Path)->dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    topics=(
        ("ocean","Why do ocean currents move?",
         "Earth rotation bends ocean currents through the Coriolis effect."),
        ("volcano","How do volcanoes erupt?",
         "Rising magma pushes upward through the volcanic vent."),
        ("aurora","Why do auroras glow?",
         "Excited gas atoms emit light as colorful curtains."),
    )
    frames=[]
    records=[]
    for kind,topic,narration in topics:
        scene=PortraitScienceScene(
            topic=topic,narration=narration,scene_index=2)
        # One real unchanged source frame (control) and the identical
        # source and timestamp through the new shared motion engine.
        with patch("automate_ytb.finish25d.refract_source",
                   side_effect=lambda image,**kwargs:image):
            plain=scene.frame(2.6,6.8)
        finished=scene.frame(2.6,6.8)
        if plain.size!=(1080,1920) or finished.mode!="RGB":
            raise RuntimeError("Actual source frame is not native Short")
        roi=(65,585,1015,1495)
        if not ImageChops.difference(plain.crop(roi),
                                     finished.crop(roi)).getbbox():
            raise RuntimeError(f"Motion engine did not change authored {kind}")
        if (plain.crop((0,0,1080,580)).tobytes() !=
                finished.crop((0,0,1080,580)).tobytes() or
            plain.crop((0,1500,1080,1920)).tobytes() !=
                finished.crop((0,1500,1080,1920)).tobytes()):
            raise RuntimeError("New optical source modified title or subtitles")
        for variant,image in (("control",plain),("motion",finished)):
            path=out/f"{kind}-{variant}.png"
            image.save(path)
            frames.append(image.resize((270,480),Image.Resampling.LANCZOS))
            records.append({"subject":kind,"variant":variant,
                            "filename":path.name,
                            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    sheet=Image.new("RGB",(1620,480),(7,17,31))
    for i,frame in enumerate(frames):
        sheet.paste(frame,(270*i,0))
    sheet.save(out/"cross-topic-original-optical-motion-25d.jpg",quality=94)
    evidence={"engine":VERSION,"originalSize":[1080,1920],
              "portrait":"9:16","subjects":["ocean","volcano","aurora"],
              "controlVsEnhancedSameTime":True,"samples":records,
              "requiresHumanReview":True,"publicationApproved":False}
    (out/"manifest.json").write_text(
        json.dumps(evidence,indent=2)+"\n",encoding="utf8")
    return evidence


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    print(json.dumps(render(parser.parse_args().out)))
