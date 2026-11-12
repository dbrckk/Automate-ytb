"""Generate original rights-owned layered artwork to exercise the universal actor rig.

This is a reproducible cross-topic *integration sample* for authored actions:
the same actorTracks schema accepts any properly licensed PNG/WebP subjects.
No downloaded image, user file, AI provider or paid media dependency.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 720, 660
RIGHTS = "Original synthetic illustration authored by this project's source code using Pillow."


def background(path: Path):
    im=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H
        d.line((0,y,W,y),fill=(int(6+9*t),int(14+13*t),int(34+22*t),255))
    random_source=random.Random(1001)
    for i in range(240):
        x=random_source.randrange(W)
        y=random_source.randrange(H)
        r=1 if i%7 else 2
        brightness=random_source.randint(110,225)
        d.ellipse((x-r,y-r,x+r,y+r),
                  fill=(brightness-39,brightness-26,brightness,120 if r==1 else 200))
    for i in range(6):
        r=100+i*54
        d.arc((W*.42-r,H*.52-r*.72,W*.42+r,H*.52+r*.72),
              211,342,fill=(61+i*7,92+i*6,130+i*7,55),width=2)
    im.save(path)


def source(path: Path):
    im=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(im)
    x,y=250,325
    # Four independently shaded panel wings, each bounded and original.
    for side in (-1,1):
        x0=x+side*90
        x1=x+side*182
        left,right=sorted((x0,x1))
        d.polygon([(left,y-78),(right,y-63),(right,y+76),(left,y+57)],
                  fill=(30,80,136,249),outline=(177,220,240,255))
        for column in range(5):
            xx=left+(right-left)*(column+1)/6
            d.line((round(xx),y-72,round(xx),y+70),
                   fill=(62,174,204,174),width=3)
        for row in range(5):
            yy=y-54+row*25
            d.line((left+4,yy,right-4,yy),fill=(38,129,189,177),width=2)
    for radius in range(80,0,-2):
        t=radius/80
        col=(round(54+(1-t)*138),round(83+(1-t)*123),round(110+(1-t)*117),255)
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=col)
    d.ellipse((x-57,y-65,x-2,y-20),fill=(238,244,239,150))
    d.arc((x-66,y-64,x+69,y+68),195,357,fill=(201,237,246,218),width=8)
    d.rounded_rectangle((x-24,y-100,x+24,y-78),radius=6,
                        fill=(204,205,176,255),outline=(254,240,205,255),width=4)
    d.line((x,y-96,x,y-140),fill=(177,218,229,255),width=8)
    d.ellipse((x-10,y-155,x+10,y-135),fill=(248,187,100,255))
    im.save(path)


def receiver(path: Path):
    im=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(im)
    x,y=490,335
    # Elliptical high-gain receiver, a deliberately illustrative instrument.
    d.polygon([(x-33,y+28),(x+40,y+25),(x+26,y+115),(x-5,y+120)],
              fill=(63,100,134,255),outline=(164,210,222,255))
    for k in range(14):
        r=90-k*5
        d.ellipse((x-r,y-r*.43,x+r,y+r*.43),
                  fill=(int(34+k*7),int(66+k*10),int(100+k*10),235),
                  outline=(185,217,232,160))
    d.arc((x-91,y-41,x+91,y+44),9,177,fill=(238,237,218,255),width=9)
    d.ellipse((x-28,y-20,x+28,y+21),fill=(212,220,212,255))
    d.ellipse((x-11,y-11,x+11,y+10),fill=(244,184,118,255))
    for theta in range(0,360,30):
        ang=math.radians(theta)
        cx=x+math.cos(ang)*60
        cy=y+math.sin(ang)*30
        d.ellipse((cx-3,cy-3,cx+3,cy+3),fill=(229,232,205,200))
    im.save(path)


def layer(filename,z,px,py):
    return {"file":f"original/{filename}.png","z":z,
            "parallaxX":px,"parallaxY":py,"material":"none",
            "rights":RIGHTS,"rightsConfirmed":True}


def key(at,x,y,scale,angle):
    return {"at":at,"x":x,"y":y,"scale":scale,"angle":angle}


def build(out: Path) -> Path:
    art=out/"original"
    art.mkdir(parents=True,exist_ok=True)
    background(art/"background.png")
    source(art/"source.png")
    receiver(art/"receiver.png")
    story={
        "schemaVersion":1,
        "topic":"A fictional signal exchange in orbit",
        "language":"en",
        "beats":[
            {"kind":"concept","title":"The transmitting spacecraft",
             "narration":"A fictional spacecraft approaches an orbiting receiver. We follow their original instruments as the signal begins.",
             "nodes":["Craft","Receiver","Signal"],
             "visualLayers":[layer("background",5,.15,.06),
                             layer("source",45,.72,.38),
                             layer("receiver",78,1.1,.62)],
             "actorTracks":[
                 {"z":45,"keys":[
                     key(0,-.13,-.02,.72,-12),
                     key(.50,-.02,-.08,1.07,2),
                     key(1,.06,-.06,1.01,9)]},
                 {"z":78,"keys":[
                     key(0,.14,.02,.78,16),
                     key(.50,.015,-.04,1.04,-2),
                     key(1,-.035,.00,.96,-10)]},
             ],
             "actorLinks":[{"fromZ":45,"toZ":78,"at":.53}]},
            {"kind":"sequence","title":"What happens next",
             "narration":"A burst of light marks a connection. The example then continues with a response and a finished message.",
             "steps":["Connection","Response","Complete"]},
        ],
    }
    path=out/"actor-rig-story.json"
    path.write_text(json.dumps(story,indent=2,ensure_ascii=False)+"\n",
                    encoding="utf8")
    return path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out-dir",type=Path,required=True)
    opts=parser.parse_args()
    path=build(opts.out_dir)
    print(path)


if __name__=="__main__":
    main()
