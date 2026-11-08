"""Original, event-dependent 2.5D butterfly response to a planted paw.

The butterfly is not a decorative timer loop: its flight starts only after
the actual world-space flower impact. Its target is the deformed flower tip.
It approaches, hovers and retreats while independently flapping two wings.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image, ImageDraw

from .forest_contact25d import IMPACT_TIME, contact_at

SIZE=(1080,1920)
VERSION="forest-25d-articulated-butterfly-materials-p42-v1"


@dataclass(frozen=True)
class ButterflyPose:
    visible: bool
    x: float
    y: float
    wing_open: float
    phase: str


def _ease(q: float) -> float:
    q=max(0.,min(1.,q))
    return q*q*(3-2*q)


def butterfly_pose(t: float, *, origin_x: float, speed: float,
                   torso_y: float) -> ButterflyPose:
    if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=7.2:
        raise ValueError("Invalid 2.5D butterfly timeline")
    contact=contact_at(t,origin_x=origin_x,speed=speed,torso_y=torso_y)
    dt=t-contact.time
    if not contact.planted or dt<=.12:
        return ButterflyPose(False,0.,0.,0.,"waiting")
    # The target is the flower's anchored world-space position, never a
    # hardcoded screen coordinate unrelated to the actual paw landing.
    tx=contact.x+30
    ty=contact.y-132+57*contact.deformation
    if dt<1.55:
        q=_ease((dt-.12)/1.43)
        x=tx+300*(1-q)
        y=ty-140*(1-q)-18*math.sin(math.pi*q)
        phase="approach"
    elif dt<2.55:
        x=tx+9*math.sin((dt-1.55)*5)
        y=ty-22-11*math.sin((dt-1.55)*9)
        phase="hover"
    else:
        q=_ease((dt-2.55)/1.45)
        x=tx+350*q
        y=ty-24-160*q
        phase="retreat"
    wing_open=.55+.45*math.sin(dt*2*math.pi*9)
    return ButterflyPose(True,x,y,wing_open,phase)


def butterfly_plate(t: float, *, origin_x: float, speed: float,
                    torso_y: float) -> Image.Image:
    pose=butterfly_pose(t,origin_x=origin_x,speed=speed,torso_y=torso_y)
    image=Image.new("RGBA",SIZE)
    if not pose.visible:
        return image
    d=ImageDraw.Draw(image)
    x,y=pose.x,pose.y
    # Original wing silhouettes with layered pigmentation and structural veins.
    # Their actual width varies with the causal 9 Hz wing flap.
    span=10+38*pose.wing_open
    for side in (-1,1):
        center=x+side*(span*.53+5)
        tip=x+side*(span+11)
        inner=x+side*4
        d.ellipse((min(inner,tip),y-37,max(inner,tip),y+8),
                  fill=(243,156,79,244),outline=(83,48,57,255),width=3)
        d.ellipse((min(center-12,center+12),y-30,
                   max(center-12,center+12),y-4),
                  fill=(255,205,117,227))
        d.ellipse((min(x+side*5,x+side*(span*.77+5)),y+2,
                   max(x+side*5,x+side*(span*.77+5)),y+27),
                  fill=(225,111,108,242),outline=(90,49,64,255),width=2)
        # Wing veins converge on the thorax, so articulation reads in motion.
        for vertical in (-22,-9,4):
            d.line(((x+side*5,y-5),(center,y+vertical)),
                   fill=(139,76,63,185),width=2)
        # Light dots travel with the wings, not with the background.
        d.ellipse((center-5,y-24,center+5,y-14),
                  fill=(255,243,181,237))
    d.ellipse((x-6,y-18,x+6,y+21),fill=(50,43,56,255))
    d.ellipse((x-5,y-21,x+5,y-10),fill=(69,54,61,255))
    d.arc((x-13,y-31,x,y-10),205,326,fill=(45,39,52,255),width=2)
    d.arc((x,y-31,x+13,y-10),215,335,fill=(45,39,52,255),width=2)
    return image
