"""Original science-explainer globe visuals, inspired by educational infographics.

Independent opt-in renderer; no third-party artwork or external model. 1080p,
30 fps, scene-level FFmpeg animation, with deterministic seeded starfield.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

VERSION = "science-globe-v1"
W, H = 1920, 1080


def poster(path: Path, *, topic: str, phase: float = 0.0) -> None:
    if not isinstance(topic, str) or not 1 <= len(topic) <= 180:
        raise ValueError("Topic must be 1–180 characters")
    if not isinstance(phase, (float, int)) or not math.isfinite(phase):
        raise ValueError("Invalid orbital phase")
    rng = random.Random(int(hashlib.sha256(topic.encode()).hexdigest()[:16],16))
    im = Image.new("RGB",(W,H),(8,27,49))
    d = ImageDraw.Draw(im)
    for _ in range(540):
        x,y=rng.randrange(W),rng.randrange(H)
        rr=rng.choice((1,1,1,2))
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(48+rng.randrange(70),88+rng.randrange(80),125+rng.randrange(95)))
    # Atmospheric rim and soft light are separate, inexpensive blurred plates.
    glow=Image.new("RGBA",(W,H))
    g=ImageDraw.Draw(glow)
    cx,cy=960,490
    for radius,alpha in ((300,10),(285,18),(270,26),(254,50)):
        g.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),outline=(50,204,239,alpha),width=8)
    glow=glow.filter(ImageFilter.GaussianBlur(23))
    im=Image.alpha_composite(im.convert("RGBA"),glow)
    d=ImageDraw.Draw(im,"RGBA")
    r=246
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(21,105,151,255))
    # Original stylized longitude/latitude grid, not a geographic map.
    for lat in range(-60,61,20):
        yy=cy+int(r*math.sin(math.radians(lat)))
        width=int(r*math.cos(math.radians(lat)))
        d.arc((cx-width,yy-22,cx+width,yy+22),0,180,fill=(103,206,223,65),width=2)
    # Rotating continent-like abstract shapes, intentionally not factual geography.
    for k in range(6):
        a=phase+k*math.tau/6
        px=cx+int(r*.65*math.sin(a))
        py=cy+int(r*.56*math.cos(a*.7))
        if (px-cx)**2+(py-cy)**2 < (r-48)**2:
            pts=[(px+int(38*math.cos(i*math.tau/7)+rng.randint(-13,13)),
                  py+int(28*math.sin(i*math.tau/7)+rng.randint(-12,12))) for i in range(7)]
            d.polygon(pts,fill=(92,184,126,235))
    # Light-facing rim and crescent shadow.
    d.arc((cx-r,cy-r,cx+r,cy+r),95,275,fill=(91,233,244,235),width=9)
    shade=Image.new("RGBA",(W,H))
    sd=ImageDraw.Draw(shade)
    sd.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(4,13,32,180))
    sd.ellipse((cx-r-140,cy-r,cx+r-140,cy+r),fill=(0,0,0,0))
    # Alpha mask crescent by offset intersected ellipses.
    mask=Image.new("L",(W,H),0)
    md=ImageDraw.Draw(mask)
    md.ellipse((cx-r,cy-r,cx+r,cy+r),fill=180)
    md.ellipse((cx-r-145,cy-r,cx+r-145,cy+r),fill=0)
    shadow=Image.new("RGBA",(W,H),(4,13,32,0))
    shadow.putalpha(mask)
    im=Image.alpha_composite(im,shadow)
    d=ImageDraw.Draw(im,"RGBA")
    for ring in range(3):
        rad=290+ring*20
        d.arc((cx-rad,cy-rad*.46,cx+rad,cy+rad*.46),200+ring*15,330+ring*15,
              fill=(144,210,231,125),width=3)
    # Lower-third, with measured font width and truncation.
    d.rounded_rectangle((245,875,1675,995),radius=26,fill=(3,13,31,220))
    try:
        font=ImageFont.truetype("DejaVuSans.ttf",47)
    except OSError:
        font=ImageFont.load_default()
    label=topic.upper()
    while d.textbbox((0,0),label,font=font)[2]>1350 and len(label)>4:
        label=label[:-2].rstrip()+"…"
    bb=d.textbbox((0,0),label,font=font)
    d.text((cx-(bb[2]-bb[0])/2,904),label,font=font,fill=(239,246,253,255))
    path.parent.mkdir(parents=True,exist_ok=True)
    im.convert("RGB").save(path,quality=94)


def render_mp4(path: Path, *, topic: str, seconds: float = 4.0, fps: int = 30) -> None:
    if not 0.5 <= seconds <= 60 or fps not in (24,30,60):
        raise ValueError("Unsupported scene duration or fps")
    frame=path.with_suffix(".science-poster.png")
    poster(frame,topic=topic)
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        subprocess.run(["ffmpeg","-y","-nostdin","-loglevel","error",
            "-loop","1","-framerate",str(fps),"-i",str(frame),
            "-vf","scale=1920:1080,format=yuv420p",
            "-t",str(seconds),"-c:v","libx264","-preset","veryfast",
            "-crf","20","-pix_fmt","yuv420p","-movflags","+faststart",str(path)],
            check=True,timeout=240)
    finally:
        frame.unlink(missing_ok=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--topic",required=True)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--seconds",type=float,default=4)
    a=p.parse_args()
    render_mp4(a.output,topic=a.topic,seconds=a.seconds)
