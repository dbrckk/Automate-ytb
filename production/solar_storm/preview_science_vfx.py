"""Generate a reviewable real moving MP4, not a sequence of illustrations.

This visual-only QA asset is distinct from the complete Kokoro final master.
It is never published and intentionally contains no synthetic narration.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

if __package__:
    from .science_vfx import ENGINE, INSERTS, render_insert, render_frame
else:
    from science_vfx import ENGINE, INSERTS, render_insert, render_frame

ROOT=Path(__file__).resolve().parent
REVIEW=ROOT/"out"/"science_motion_review"


def main():
    REVIEW.mkdir(parents=True,exist_ok=True)
    kinds=[INSERTS[i][0] for i in sorted(INSERTS)]
    if kinds!=["flare","cme","shield","satellite","connection"]:
        raise RuntimeError("The reviewed scientific story must have all five original beats")
    duration=1.65
    clips=[]
    for i,kind in enumerate(kinds,1):
        path=REVIEW/f"chapter_{i:02}_{kind}.mp4"
        data=render_insert(kind,duration,path)
        clips.append({"name":kind,"video":path.name,"frames":data["frames"],
                      "durationSeconds":data["duration_seconds"]})
    listing=REVIEW/"chapters.txt"
    listing.write_text("".join(
        f"file '{(REVIEW/r['video']).resolve()}'\n" for r in clips),
        encoding="utf-8")
    output=REVIEW/"Original_Science_Motion_Review_1080x1920.mp4"
    subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0",
                    "-i",str(listing),"-c","copy","-movflags","+faststart",
                    str(output)],check=True,timeout=80)

    # Representative actual programmatic frames, large enough for visual QA.
    contact=Image.new("RGB",(540*5,960),(8,17,34))
    for i,kind in enumerate(kinds):
        frame=render_frame(kind,duration*.56,duration)
        contact.paste(frame,(i*540,0))
    contact.save(REVIEW/"science_motion_contact_sheet.jpg",quality=91)

    result={"engine":ENGINE,"video":output.name,"format":"1080x1920 H264 30fps",
            "durationSeconds":len(kinds)*round(duration*30)/30,
            "chapters":clips,"original_frame_animation":True,
            "audio":"none (visual QA only, complete final film uses real Kokoro)",
            "source":"fully original schematic science diagrams",
            "editorial_approved":False,"publication_approved":False}
    (REVIEW/"visual_qa.json").write_text(
        json.dumps(result,indent=2),encoding="utf-8")
    print("ORIGINAL_ANIMATION_VISUAL_QA_OK",json.dumps(result),flush=True)


if __name__=="__main__":
    main()
