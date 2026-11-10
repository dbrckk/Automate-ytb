"""Real 9:16 science source-art before/after local relief in three subjects."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from PIL import Image,ImageChops

from automate_ytb.material_relief25d import VERSION
from automate_ytb.science_portrait import PortraitScienceScene


def render(out:Path)->dict:
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    samples=(
        ("ocean","Why do ocean currents move?",
         "Earth rotation bends ocean currents through the Coriolis effect."),
        ("volcano","How do volcanoes erupt?",
         "Rising magma pushes upward through the volcanic vent."),
        ("aurora","Why do auroras glow?",
         "Excited gas atoms emit light as colorful curtains."),
    )
    records=[]
    strips=[]
    for subject,topic,narration in samples:
        video=PortraitScienceScene(
            topic=topic,narration=narration,scene_index=2)
        with patch("automate_ytb.finish25d.sculpt_authored_material",
                   side_effect=lambda img,**kwargs:img):
            control=video.frame(2.6,6.8)
        detailed=video.frame(2.6,6.8)
        if (control.size!=(1080,1920) or control.mode!="RGB"
                or detailed.size!=(1080,1920) or detailed.mode!="RGB"):
            raise RuntimeError("Not the genuine 1080x1920 video source")
        if not ImageChops.difference(
                control.crop((65,585,1015,1495)),
                detailed.crop((65,585,1015,1495))).getbbox():
            raise RuntimeError(f"No actual original material response: {subject}")
        for safe in ((0,0,1080,580),(0,1500,1080,1920)):
            if control.crop(safe).tobytes()!=detailed.crop(safe).tobytes():
                raise RuntimeError(f"Subtitle or title damaged: {subject}")
        for variant,img in (("original",control),("relief",detailed)):
            p=out/f"{subject}-{variant}.png"
            img.save(p)
            strips.append(img.resize((270,480),Image.Resampling.LANCZOS))
            records.append({"subject":subject,"variant":variant,
                            "file":p.name,
                            "sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    sheet=Image.new("RGB",(1620,480),(7,17,31))
    for i,img in enumerate(strips):
        sheet.paste(img,(270*i,0))
    sheet.save(out/"original-material-relief-25d.jpg",quality=94)
    evidence={"version":VERSION,"nativeSize":[1080,1920],
              "subjects":["ocean","volcano","aurora"],
              "comparisonAtSameTimestamp":True,"samples":records,
              "humanVisualReviewRequired":True,"approved":False}
    (out/"manifest.json").write_text(json.dumps(evidence,indent=2)+"\n")
    return evidence


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    print(json.dumps(render(parser.parse_args().out)))
