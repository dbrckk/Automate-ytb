"""Reproducible real-video cross-commit P5.26 before/after visual evidence.

The control is rendered by an actual checkout of main, not a mock, a fake
comparison, or a hand-painted reference. Both run at identical narration,
scene index, frame clock, dimensions, and native 9:16 compositor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image, ImageChops, ImageStat

SHOT = """
from pathlib import Path
import sys
from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.flow_material25d import vortex_source
out=Path(sys.argv[1])
out.mkdir(parents=True,exist_ok=True)
shot=PortraitScienceScene(
    topic="Why Do Ocean Currents Move?",
    narration="Earth rotation bends currents through the Coriolis effect.",
    scene_index=3)
shot.frame(2.3,6.4).save(out/"frame.png")
vortex_source(670,palette="ocean",seed=377).save(out/"gyre.png")
"""


def render(out: Path, baseline: Path) -> dict:
    out=out.resolve()
    baseline=baseline.resolve()
    root=Path(__file__).resolve().parents[1]
    if not (baseline/"automate_ytb"/"flow_material25d.py").is_file():
        raise ValueError("Must supply real checked-out main source")
    if baseline==root:
        raise ValueError("Baseline cannot be the modified source")
    out.mkdir(parents=True,exist_ok=True)
    durations={}
    for variant,cwd in (("before",baseline),("after",root)):
        target=out/variant
        target.mkdir(parents=True,exist_ok=True)
        started=time.perf_counter()
        subprocess.run([sys.executable,"-c",SHOT,str(target)],
                       cwd=cwd,check=True,timeout=180)
        durations[variant]=round(time.perf_counter()-started,3)
    before=Image.open(out/"before"/"frame.png").convert("RGB")
    after=Image.open(out/"after"/"frame.png").convert("RGB")
    if before.size!=(1080,1920) or after.size!=(1080,1920):
        raise RuntimeError("Not real 9:16 1080x1920 video source frames")
    bounds=(205,755,875,1425)
    diff=ImageChops.difference(before.crop(bounds),after.crop(bounds))
    if diff.getbbox() is None:
        raise RuntimeError("New vortex geometry has no actual scene effect")
    for safe in ((0,0,1080,520),(0,1522,1080,1920)):
        if before.crop(safe).tobytes()!=after.crop(safe).tobytes():
            raise RuntimeError("Narration, title or mobile subtitle area modified")
    opaque_old=Image.open(out/"before"/"gyre.png").convert("RGBA")
    opaque_new=Image.open(out/"after"/"gyre.png").convert("RGBA")
    if opaque_old.getpixel((335,335))[3]<=100 or opaque_new.getpixel((335,335))[3]<=100:
        raise RuntimeError("Water source unexpectedly vanished")
    count=sum(1 for a,b in zip(
        opaque_old.getchannel("A").getdata(),
        opaque_new.getchannel("A").getdata()) if a!=b)
    if count<1000:
        raise RuntimeError("Organic water silhouette was not changed")
    board=Image.new("RGB",(1080,480),(6,16,31))
    for i,picture in enumerate((before,after)):
        board.paste(picture.resize((270,480),Image.Resampling.LANCZOS),
                    (i*270,0))
    for i,picture in enumerate((opaque_old,opaque_new)):
        inset=Image.new("RGBA",picture.size,(9,40,70,255))
        inset.alpha_composite(picture)
        board.paste(inset.convert("RGB").resize(
            (270,270),Image.Resampling.LANCZOS),(540+i*270,105))
    board.save(out/"organic-water-source-before-after.jpg",quality=94)
    files=[]
    for relative in ("before/frame.png","after/frame.png",
                     "before/gyre.png","after/gyre.png"):
        path=out/relative
        files.append({"file":relative,
                      "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    data={"method":"real-main-vs-pr-Pillow-source-comparison",
          "nativeFrame":[1080,1920],
          "sameNarration":True,"sameFrameClockSeconds":2.3,
          "changedGyreAlphaPixels":count,
          "sceneChangeMean":round(ImageStat.Stat(diff).mean[0],3),
          "renderSeconds":durations,
          "files":files,
          "humanVisualReviewRequired":True,
          "editoriallyApproved":False}
    (out/"manifest.json").write_text(json.dumps(data,indent=2)+"\n",
                                    encoding="utf-8")
    return data


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--baseline",type=Path,required=True)
    print(json.dumps(render(parser.parse_args().out,parser.parse_args().baseline)))
