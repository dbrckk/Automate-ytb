"""Review true main versus P5.27 causal 9:16 source frames at equal times.

This script requires two real repository checkouts. No mock renderer or
reference screenshot: both invoke the actual production PortraitScienceScene.
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

EPISODE=(
    "White sunlight reaches falling raindrops, carrying many colors even though the beam looks perfectly white.",
    "Entering a raindrop, each color refracts and bends by a slightly different angle inside water.",
    "Some light reflects from the curved inside back surface, turning toward the front of the drop.",
    "Leaving the drop, the colors bend again, sending selected rays toward your eyes at precise viewing angles.",
    "Millions of droplets create the rainbow each observer sees; when you move, its apparent end moves too.",
)
SOURCE_CODE=r"""
import sys
from pathlib import Path
from automate_ytb.science_portrait import PortraitScienceScene
topic="Why Can't You Reach the End of a Rainbow?"
scripts=__import__("json").loads(sys.argv[2])
out=Path(sys.argv[1])
out.mkdir(parents=True,exist_ok=True)
for i,line in enumerate(scripts,1):
    scene=PortraitScienceScene(topic=topic,narration=line,scene_index=i)
    scene.frame(4.1,6.6).save(out/f"scene-{i}.png")
arc=PortraitScienceScene(topic=topic,narration=scripts[4],scene_index=5)
arc.frame(.6,6.6).save(out/"arc-start.png")
arc.frame(6.0,6.6).save(out/"arc-end.png")
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(*, baseline: Path, output: Path) -> dict:
    root=Path(__file__).resolve().parents[1]
    baseline=baseline.resolve(strict=True)
    output=output.resolve()
    if baseline==root or not (baseline/"automate_ytb"/"science_rainbow.py").is_file():
        raise ValueError("Needs a real independently checked out main source")
    output.mkdir(parents=True,exist_ok=True)
    seconds={}
    for name,work in (("before",baseline),("after",root)):
        target=output/name
        started=time.perf_counter()
        subprocess.run([sys.executable,"-c",SOURCE_CODE,str(target),
                        json.dumps(EPISODE)],cwd=work,check=True,timeout=180)
        seconds[name]=round(time.perf_counter()-started,3)
    contact=Image.new("RGB",(700,5*622),(12,25,43))
    changed={}
    files=[]
    for i in range(1,6):
        a=Image.open(output/"before"/f"scene-{i}.png").convert("RGB")
        b=Image.open(output/"after"/f"scene-{i}.png").convert("RGB")
        if a.size!=(1080,1920) or b.size!=(1080,1920):
            raise RuntimeError("Expected real native 1080x1920 source videos")
        for rect in ((0,0,1080,520),(0,1522,1080,1920)):
            if a.crop(rect).tobytes()!=b.crop(rect).tobytes():
                raise RuntimeError(f"Scene {i}: title/subtitle safe pixels modified")
        for j,frame in enumerate((a,b)):
            contact.paste(frame.resize((350,622),Image.Resampling.LANCZOS),
                          (350*j,622*(i-1)))
        crop=(90,780,1000,1495)
        diff=ImageChops.difference(a.crop(crop),b.crop(crop))
        changed[i]=round(sum(1 for r,g,bl in diff.getdata()
                             if max(r,g,bl)>4)/(910*715),4)
        if i>1 and changed[i]<.012:
            raise RuntimeError(f"Source interaction not visibly changed in scene {i}: {changed[i]}")
        files.extend(({"path":f"before/scene-{i}.png","sha256":_sha(output/"before"/f"scene-{i}.png")},
                      {"path":f"after/scene-{i}.png","sha256":_sha(output/"after"/f"scene-{i}.png")}))
    start=Image.open(output/"after"/"arc-start.png").convert("RGB")
    end=Image.open(output/"after"/"arc-end.png").convert("RGB")
    if ImageChops.difference(start.crop((300,1290,750,1495)),
                             end.crop((300,1290,750,1495))).getbbox() is None:
        raise RuntimeError("Viewer and ray interactions did not animate")
    contact.save(output/"p527-real-rainbow-before-after.jpg",quality=91)
    summary={"method":"production-renderer-real-main-vs-feature-branch",
             "frameSize":[1080,1920],
             "timestamp":4.1,
             "sameNarrationAndTopic":True,
             "changedWorldFractionByScene":changed,
             "cameraAndObserverMotionChecked":True,
             "cpuRenderSeconds":seconds,"sha256Files":files,
             "humanEditorialReviewRequired":True,
             "publicationApproved":False}
    (output/"manifest.json").write_text(json.dumps(summary,indent=2)+"\n",
                                        encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--baseline",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(review(baseline=args.baseline,output=args.output)))
