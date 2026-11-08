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
VERSION="forest-25d-causal-butterfly-v1"


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
    # Two independently drawn articulated wings (no flattened body sprite).
    span=8+24*pose.wing_open
    d.ellipse((x-span-8,y-23,x-4,y+9),
              fill=(250,169,88,232),outline=(97,55,67,255),width=3)
    d.ellipse((x+4,y-23,x+span+8,y+9),
              fill=(252,198,113,235),outline=(97,55,67,255),width=3)
    d.ellipse((x-span*.75-4,y+3,x-5,y+20),
              fill=(241,139,110,227))
    d.ellipse((x+5,y+3,x+span*.75+4,y+20),
              fill=(241,139,110,227))
    d.ellipse((x-5,y-16,x+5,y+19),fill=(54,48,62,255))
    d.arc((x-11,y-25,x,y-9),210,325,fill=(54,48,62,255),width=2)
    d.arc((x,y-25,x+11,y-9),210,325,fill=(54,48,62,255),width=2)
    return image
