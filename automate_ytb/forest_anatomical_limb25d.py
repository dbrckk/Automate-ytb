"""Original tapered, curved animal limb anatomy driven by exact world-space IK.

This is a genuine geometric replacement for the straight quadrilateral limbs:
the calf and thigh are painted as continuously curved asymmetric silhouettes,
with directional volumes, knees, toes and grounded contact. Bone endpoints are
never moved; the foot target is still owned by rig25d.
"""
from __future__ import annotations

import math
from PIL import ImageDraw

from .animated_forest import COLORS
from .forest_character_art25d import KINDS, WARM, COOL
from .rig25d import LegPose

VERSION="original-p39-contoured-anatomical-ik-limbs-v1"


def _curve_points(a:tuple[float,float],b:tuple[float,float],
                  *,bulge:float,steps:int=12)->list[tuple[float,float]]:
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    if length<1:
        raise ValueError("Degenerate curved anatomical bone")
    nx,ny=-dy/length,dx/length
    return [(a[0]+dx*i/steps+nx*bulge*math.sin(math.pi*i/steps),
             a[1]+dy*i/steps+ny*bulge*math.sin(math.pi*i/steps))
            for i in range(steps+1)]


def _paint_segment(draw:ImageDraw.ImageDraw,a,b,*,kind:str,
                   radius_start:float,radius_end:float,
                   curve:float,front:bool)->None:
    path=_curve_points(a,b,bulge=curve)
    tangent=(b[0]-a[0],b[1]-a[1])
    d=math.hypot(*tangent)
    nx,ny=-tangent[1]/d,tangent[0]/d
    outline=[]
    highlight=[]
    for i,p in enumerate(path):
        u=i/(len(path)-1)
        # Muscle swelling in the proximal half, tapering to ankle.
        muscle=math.sin(math.pi*u)**2
        width=(1-u)*radius_start+u*radius_end+7*muscle
        outline.append((p[0]+nx*(width+3),p[1]+ny*(width+3)))
        highlight.append((p[0]-nx*(width*.48),p[1]-ny*(width*.48)))
    for i,p in reversed(list(enumerate(path))):
        u=i/(len(path)-1)
        muscle=math.sin(math.pi*u)**2
        width=(1-u)*radius_start+u*radius_end+7*muscle
        outline.append((p[0]-nx*(width+3),p[1]-ny*(width+3)))
    fur=COLORS[kind]["fur"]
    dark=COLORS[kind]["dark"]
    warm=WARM[kind]+(255,)
    cool=COOL[kind]+(255,)
    draw.polygon(outline,fill=dark)
    inner=[]
    for i,p in enumerate(path):
        u=i/(len(path)-1)
        w=(1-u)*radius_start+u*radius_end+7*math.sin(math.pi*u)**2
        inner.append((p[0]+nx*w,p[1]+ny*w))
    for i,p in reversed(list(enumerate(path))):
        u=i/(len(path)-1)
        w=(1-u)*radius_start+u*radius_end+7*math.sin(math.pi*u)**2
        inner.append((p[0]-nx*w,p[1]-ny*w))
    draw.polygon(inner,fill=fur)
    draw.line(highlight,fill=warm,width=4,joint="curve")
    # Inner ambient occlusion at the knee/ankle follows the curved anatomy.
    if front:
        edge=[(p[0]+nx*radius_end*.64,p[1]+ny*radius_end*.64)
              for p in path[7:]]
        draw.line(edge,fill=cool,width=2,joint="curve")


def draw_anatomical_leg(draw:ImageDraw.ImageDraw,*,pose:LegPose,
                        kind:str,side:str)->None:
    """Render curved musculature over a verified two-bone IK skeleton."""
    if (not isinstance(pose,LegPose) or kind not in KINDS
            or side not in ("left","right")):
        raise ValueError("Invalid original anatomical animal rig")
    if not all(math.isfinite(v) for p in (pose.hip,pose.knee,pose.foot) for v in p):
        raise ValueError("Nonfinite anatomical world joint")
    fur=COLORS[kind]["fur"]
    dark=COLORS[kind]["dark"]
    light=WARM[kind]+(255,)
    cool=COOL[kind]+(255,)
    # Opposite curvatures give a soft thigh and distinct inward calf rather
    # than the two straight, uniform-width tubes from P3.7.
    sign=1 if side=="left" else -1
    _paint_segment(draw,pose.hip,pose.knee,kind=kind,
                   radius_start=27,radius_end=20,
                   curve=sign*8,front=False)
    kx,ky=pose.knee
    draw.ellipse((kx-22,ky-21,kx+22,ky+21),fill=dark)
    draw.ellipse((kx-18,ky-18,kx+18,ky+18),fill=fur)
    draw.arc((kx-13,ky-13,kx+12,ky+13),155,255,fill=light,width=3)
    _paint_segment(draw,pose.knee,pose.foot,kind=kind,
                   radius_start=21,radius_end=13,
                   curve=-sign*6,front=True)
    fx,fy=pose.foot
    # Foot is a horizontal organic wedge with a visibly padded arch.
    draw.ellipse((fx-38,fy-13,fx+36,fy+12),fill=dark)
    draw.ellipse((fx-34,fy-13,fx+31,fy+8),fill=fur)
    draw.arc((fx-30,fy-12,fx+19,fy+7),185,327,fill=light,width=3)
    for x in (-18,-3,12):
        draw.arc((fx+x-5,fy-1,fx+x+9,fy+11),
                 175,295,fill=cool,width=2)
