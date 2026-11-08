"""Continuous original 2.5D soft-body mesh, breathing and inertial tail.

The IK feet are rendered in world coordinates by forest25d and are NEVER
warped. This module deforms only the local face/torso/scarf plate with a
continuous inverse-mapped triangular-looking strip mesh. Breathing, stride
mass transfer and a damped *post-contact* impulse determine the geometry.
Pillow MESH uses the actual source pixels every frame; this is not a fake
camera zoom, 3D engine or interpolation between static slides.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image

from .forest_contact25d import IMPACT_TIME
from .rig25d import PERIOD

VERSION="original-p38-world-grounded-organic-character-mesh-v1"
BODY_SIZE=(350,440)
TAIL_SIZE=(230,240)
_STRIP=20


@dataclass(frozen=True)
class SoftBodyPose:
    """Bounded local anatomical offsets; separate from the grounded foot IK."""
    breath: float
    stride: float
    recoil: float
    head_sway: float
    shoulder_drop: float
    belly_width: float
    tail_lag: float
    ear_lag: float


def _ease(a: float,b: float,x: float) -> float:
    q=max(0.,min(1.,(x-a)/(b-a)))
    return q*q*(3-2*q)


def organic_pose(t: float, *, interaction: bool=False) -> SoftBodyPose:
    if (type(t) not in (int,float) or not math.isfinite(t)
            or not 0<=t<=7.2 or type(interaction) is not bool):
        raise ValueError("Invalid original nonrigid forest character clock")
    phase=2*math.pi*t/PERIOD
    stride=math.sin(phase)
    breath=math.sin(2*math.pi*t/2.85+.38)
    delta=t-IMPACT_TIME
    recoil=( (1-math.exp(-16*delta))*math.exp(-2.5*delta)
             if interaction and delta>0 else 0. )
    return SoftBodyPose(
        breath=breath,
        stride=stride,
        recoil=recoil,
        head_sway=6.1*math.sin(phase-.37)+8.2*recoil,
        shoulder_drop=2.3*math.cos(phase*2+.25)+8.1*recoil,
        belly_width=1.+.024*breath+.038*recoil,
        tail_lag=8.4*math.sin(phase-.75)+11.7*recoil,
        ear_lag=3.1*math.sin(phase-1.08)-6.8*recoil,
    )


def _source_quad(y:float, pose:SoftBodyPose,
                 size:tuple[int,int]) -> tuple[float,...]:
    w,h=size
    f=y/h
    head_gate=1.-_ease(.31,.89,f)
    chest_gate=math.exp(-((f-.66)/.245)**2)
    # Hip anchoring: bottom of the torso remains almost fixed, allowing the
    # independent two-bone legs to join naturally as the upper body flexes.
    shift=pose.head_sway*head_gate+.75*pose.stride*chest_gate
    width=1.+(pose.belly_width-1.)*chest_gate
    vertical=pose.shoulder_drop*chest_gate+1.6*pose.breath*head_gate
    mid=w*.5
    left=mid+(-mid-shift)/width
    right=mid+(w-mid-shift)/width
    return left, y-vertical, right, y-vertical


def deform_body(sprite:Image.Image, pose:SoftBodyPose) -> Image.Image:
    """Non-affine multiband mesh with continuous boundary coordinates."""
    if (not isinstance(sprite,Image.Image) or sprite.mode!="RGBA"
            or sprite.size!=BODY_SIZE or not isinstance(pose,SoftBodyPose)):
        raise ValueError("Expected original painted 350x440 RGBA body and pose")
    strips=[]
    w,h=BODY_SIZE
    for y0 in range(0,h,_STRIP):
        y1=min(h,y0+_STRIP)
        left0,sy0,right0,_=_source_quad(y0,pose,BODY_SIZE)
        left1,sy1,right1,_=_source_quad(y1,pose,BODY_SIZE)
        # Pillow QUAD ordering: UL, LL, LR, UR, in source coordinates.
        strips.append(((0,y0,w,y1),(left0,sy0,left1,sy1,
                                    right1,sy1,right0,sy0)))
    return sprite.transform(BODY_SIZE,Image.Transform.MESH,strips,
                            Image.Resampling.BICUBIC)


def deform_tail(sprite:Image.Image, pose:SoftBodyPose) -> Image.Image:
    """A flexible tail whose base at the lower rump stays pinned."""
    if (not isinstance(sprite,Image.Image) or sprite.mode!="RGBA"
            or sprite.size!=TAIL_SIZE or not isinstance(pose,SoftBodyPose)):
        raise ValueError("Expected original painted 230x240 RGBA tail and pose")
    w,h=TAIL_SIZE
    sections=[]
    for y0 in range(0,h,_STRIP):
        y1=min(h,y0+_STRIP)
        def bend(y):
            # End flexes strongly; the actual tail root y~205 does not shift.
            tip=max(0.,min(1.,(209-y)/209))
            return 1.25*pose.tail_lag*tip*tip
        b0,b1=bend(y0),bend(y1)
        sections.append(((0,y0,w,y1),(-b0,y0,-b1,y1,
                                      w-b1,y1,w-b0,y0)))
    return sprite.transform(TAIL_SIZE,Image.Transform.MESH,sections,
                            Image.Resampling.BICUBIC)
