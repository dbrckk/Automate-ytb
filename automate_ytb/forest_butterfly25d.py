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
VERSION="forest-25d-causal-clear-silhouette-butterfly-p42-v1"


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
        # Arrive from the open right-hand sky and touch the real flower tip.
        q=_ease((dt-.12)/1.43)
        x=tx+320*(1-q)
        y=ty-155*(1-q)-16*math.sin(math.pi*q)
        phase="approach"
    elif dt<2.55:
        # On contact, rise toward the open space to the right of the face.
        # The pose is continuous at the approach/hover boundary; the animal's
        # eyes can follow it without the butterfly masking facial acting.
        q=_ease((dt-1.55)/.70)
        x=tx+165*q+8*math.sin(math.pi*q)
        y=ty-155*q-12*math.sin(math.pi*q)
        phase="hover"
    else:
        # Leave from the exact final hover position, no teleport or cut.
        q=_ease((dt-2.55)/1.65)
        x=tx+165+360*q
        y=ty-155-155*q
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
    # Two independently animated original wing planes, layered for depth.
    # A larger cool-hued silhouette remains legible against the orange actor.
    span=16+34*pose.wing_open
    d.ellipse((x-span*.88-10,y+1,x-7,y+30),
              fill=(111,157,217,231),outline=(33,77,101,255),width=2)
    d.ellipse((x+7,y+1,x+span*.88+10,y+30),
              fill=(126,168,217,231),outline=(33,77,101,255),width=2)
    d.ellipse((x-span-12,y-34,x-4,y+10),
              fill=(90,215,216,240),outline=(29,78,102,255),width=3)
    d.ellipse((x+4,y-34,x+span+12,y+10),
              fill=(114,224,205,240),outline=(29,78,102,255),width=3)
    for side in (-1,1):
        mark_x=x+side*(span*.49+7)
        d.ellipse((mark_x-7,y-18,mark_x+7,y-3),
                  fill=(248,239,192,240))
        d.ellipse((mark_x-3,y-14,mark_x+3,y-7),
                  fill=(47,102,126,237))
        d.line(((x+side*4,y+6),
                (x+side*(span*.73+5),y-13)),
               fill=(232,250,221,155),width=2)
    d.ellipse((x-6,y-17,x+6,y+21),fill=(43,57,76,255))
    d.ellipse((x-4,y-21,x+4,y-12),fill=(53,68,76,255))
    d.arc((x-15,y-32,x,y-11),206,323,fill=(43,57,76,255),width=2)
    d.arc((x,y-32,x+15,y-11),215,333,fill=(43,57,76,255),width=2)
    return image
