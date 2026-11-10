"""Render genuine multi-topic 2.5D production frames to inspect new editorial UI.

Original RGB frames come from PortraitScienceScene, not fabricated posters.
This is a *frame review* artifact, not a narrated MP4 or aesthetic approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image,ImageDraw
from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.finish25d import frame_layout_diagnostics, artwork_diagnostics

SAMPLES=(
    ("rainbow","How do rainbows form?",
     "White sunlight contains many colors, even though it often looks colorless."),
    ("volcano","How do volcanoes erupt?",
     "Gas pressure builds inside hot magma, before rock fractures."),
    ("ocean","Why do Earth's ocean currents move?",
     "Ocean currents move warm surface water around the planet."),
)

def render(folder: Path)->dict:
    folder=folder.resolve()
    folder.mkdir(parents=True,exist_ok=True)
    columns=[]
    rows=[]
    for index,(name,topic,narration) in enumerate(SAMPLES):
        subject=PortraitScienceScene(topic=topic,narration=narration,
                                     scene_index=index+1)
        frame=subject.frame(1.3,6.0)
        if frame.size!=(1080,1920) or frame.mode!="RGB":
            raise ValueError("Invalid native 2.5D rendered stage")
        file=folder/(name+".png")
        frame.save(file,format="PNG")
        thumb=frame.resize((270,480),Image.Resampling.LANCZOS)
        columns.append(thumb)
        report={
            "topic":name,"file":file.name,
            "sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
            "orientation":"9:16",
            "exactCaption":subject.active_caption(1.3,6.0),
            "layout":frame_layout_diagnostics(frame),
            "art":artwork_diagnostics(frame,bounds=(65,585,1015,1495)),
            "publicationApproved":False,
        }
        rows.append(report)
    review=Image.new("RGB",(3*270,480),(9,18,27))
    for index,thumb in enumerate(columns):
        review.paste(thumb,(index*270,0))
    review.save(folder/"multi-topic-25d-contact.jpg",quality=92)
    result={"schemaVersion":1,"engine":"shared-2p5d-actual-portrait",
            "sourceRenderCount":len(rows),"examples":rows,
            "humanReviewRequired":True,"publicationApproved":False}
    (folder/"manifest.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=render(args.out)
    print(json.dumps({"scenes":result["sourceRenderCount"],
        "topics":[s["topic"] for s in result["examples"]],
        "publicationApproved":False}))


if __name__=="__main__":
    main()
