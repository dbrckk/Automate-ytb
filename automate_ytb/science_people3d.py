"""Deterministic 3D articulated wind actors for science city scenes.

This is genuine world-space geometry, sharing science_city3d's pinhole camera
and action_state wind clock. Bodies, joints, scarf and umbrella are projected
from 3D vertices instead of pasted 2D drawings. The simplified shapes and
movement are original stylized illustrations, NOT photorealism or CFD.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw

from .science_city3d import camera_pose, SCENE_TOP, SCENE_BOTTOM
from .earth_story_actions import action_state

WORLD_SIZE=(1080,1920)


def actor_pose(t: float, duration: float, index: int) -> dict:
    """All actor joints depend on one gust and planted, world-space feet."""
    if index not in (0,1):
        raise ValueError("Unknown 3D performer")
    state=action_state("wind",t,duration)
    gust=state["gust"]
    lean=state["lean"]*.0037*(1 if index==0 else .72)
    x,z=(-1.57,2.8) if index==0 else (1.55,5.1)
    shoulder=(x+lean,1.43,z)
    head=(x+lean*1.17,1.83+.024*math.sin(t*2+index),z)
    hip=(x+lean*.36,.85,z)
    foot_l=(x-.28,.09,z-.17)
    foot_r=(x+.31,.09,z+.16)
    elbow_l=(shoulder[0]-.37,1.08+.08*math.sin(t*1.4+index),z-.08)
    elbow_r=(shoulder[0]+.43,1.16+.045*math.sin(t*1.9),z+.1)
    hand_l=(shoulder[0]-.49,.85,z-.08)
    hand_r=(shoulder[0]+.58,1.22,z+.11)
    return {"index":index,"gust":gust,"lean":lean,"hip":hip,
            "shoulder":shoulder,"head":head,
            "knee_l":(x-.18-lean*.12,.47,z-.19),
            "knee_r":(x+.25-lean*.12,.49,z+.18),
            "foot_l":foot_l,"foot_r":foot_r,
            "elbow_l":elbow_l,"elbow_r":elbow_r,
            "hand_l":hand_l,"hand_r":hand_r}


def _project(cam, point):
    sample=cam.project(tuple(float(v) for v in point))
    if sample is None:
        return None
    return round(sample[0]),round(sample[1]-SCENE_TOP)


def _poly(draw,cam,points,fill):
    pts=[_project(cam,p) for p in points]
    if all(p is not None for p in pts):
        draw.polygon(pts,fill=fill)


def _line(draw,cam,points,fill,width=3):
    pts=[_project(cam,p) for p in points]
    if all(p is not None for p in pts):
        draw.line(pts,fill=fill,width=width,joint="curve")


def _tube(draw,cam,start,end,radius,shade):
    """Eight-sided tube around an articulated 3D bone, lit by face normal."""
    dx=end[0]-start[0]
    dy=end[1]-start[1]
    dz=end[2]-start[2]
    length=math.sqrt(dx*dx+dy*dy+dz*dz)
    if length<.04:
        raise ValueError("Degenerate 3D bone")
    # World-up projected into bone-orthogonal plane, and a side vector.
    if abs(dy)/length>.97:
        u=(1.,0.,0.)
    else:
        ax=(-dz,0.,dx)
        mag=math.hypot(ax[0],ax[2])
        u=(ax[0]/mag,0.,ax[2]/mag)
    v=(dy*u[2]-dz*u[1],dz*u[0]-dx*u[2],dx*u[1]-dy*u[0])
    v=tuple(k/length for k in v)
    base=[]
    top=[]
    for i in range(9):
        phi=i*math.tau/8
        delta=[radius*(u[k]*math.cos(phi)+v[k]*math.sin(phi))
               for k in range(3)]
        base.append(tuple(start[k]+delta[k] for k in range(3)))
        top.append(tuple(end[k]+delta[k] for k in range(3)))
    # Always draw the camera-facing half of the curved surface last.
    for i in (0,1,7,6,2,5,3,4):
        light=.68+.31*math.cos((i+.5)*math.tau/8-.6)
        fill=tuple(round(channel*light) for channel in shade[:3])+(shade[3],)
        _poly(draw,cam,[base[i],base[i+1],top[i+1],top[i]],fill)


def _head(draw,cam,center,index):
    """Three rings of a mesh head: real volume with varying surface shade."""
    x,y,z=center
    for band in range(5):
        theta1=band*math.pi/5
        theta2=(band+1)*math.pi/5
        ring1=[]
        ring2=[]
        for j in range(13):
            phi=j*math.tau/12
            for angle, ring in ((theta1,ring1),(theta2,ring2)):
                ring.append((x+.21*math.sin(angle)*math.cos(phi),
                             y+.24*math.cos(angle),
                             z+.19*math.sin(angle)*math.sin(phi)))
        for j in range(12):
            n=.70+.25*math.sin(j*math.tau/12+.3)
            skin=(round(242*n),round(206*n),round(172*n),255)
            _poly(draw,cam,[ring1[j],ring1[j+1],ring2[j+1],ring2[j]],skin)
    # Tiny visor/eye contour carries material highlights with camera movement.
    front=z-.194
    _poly(draw,cam,[
        (x-.15,y+.04,front),(x+.15,y+.04,front),
        (x+.145,y-.06,front),(x-.145,y-.06,front)],
        (53,98,119,254))
    _line(draw,cam,[(x-.12,y+.036,front-.006),
                    (x+.08,y+.036,front-.006)],(176,230,242,235),2)


def _umbrella(draw,cam,pose,t):
    """Conical canopy with twelve planar facets, ribs, shaft and wind tilt."""
    hand=pose["hand_r"]
    gust=pose["gust"]
    cx=hand[0]+.11+gust*.007
    cy=hand[1]+1.16
    cz=hand[2]-.13
    tip=(cx+.13,cy+.2,cz)
    handle=(hand[0]+.04,hand[1]-.17,hand[2])
    _tube(draw,cam,handle,tip,.026,(224,234,237,255))
    radius=1.02
    edge=[]
    for i in range(13):
        a=i*math.tau/12
        edge.append((cx+radius*math.cos(a)+gust*.0016,
                     cy-.34-.08*math.sin(a+t*.8),
                     cz+radius*.80*math.sin(a)))
    # Render far-facing half first and near-facing front facets last.
    for j in list(range(6,12))+list(range(6)):
        light=.76+.18*math.cos(j*math.tau/12+.5)
        fill=(round(244*light),round(112*light),round(84*light),251)
        _poly(draw,cam,[tip,edge[j],edge[j+1]],fill)
        _line(draw,cam,[tip,edge[j+1]],(249,199,169,171),2)
    _line(draw,cam,edge,(240,225,205,206),3)
    _line(draw,cam,[handle,hand],(235,239,242,245),3)


def _performer(draw,cam,pose,t):
    hip=pose["hip"]
    shoulder=pose["shoulder"]
    color=(64,159,179,255) if pose["index"]==0 else (200,107,92,255)
    # Correct near/far occlusion order: legs, torso, arms, head.
    _tube(draw,cam,hip,pose["knee_l"],.115,(128,160,178,255))
    _tube(draw,cam,pose["knee_l"],pose["foot_l"],.116,(127,163,186,255))
    _tube(draw,cam,hip,pose["knee_r"],.115,(145,170,185,255))
    _tube(draw,cam,pose["knee_r"],pose["foot_r"],.116,(137,172,193,255))
    _tube(draw,cam,(hip[0],.84,hip[2]),shoulder,.23,color)
    _tube(draw,cam,shoulder,pose["elbow_l"],.091,(222,230,236,255))
    _tube(draw,cam,pose["elbow_l"],pose["hand_l"],.075,(225,200,178,255))
    _tube(draw,cam,shoulder,pose["elbow_r"],.09,(232,229,231,255))
    _tube(draw,cam,pose["elbow_r"],pose["hand_r"],.074,(231,199,167,255))
    _head(draw,cam,pose["head"],pose["index"])
    if pose["index"]==0:
        _umbrella(draw,cam,pose,t)
    else:
        scarf_root=(shoulder[0]-.07,shoulder[1]+.03,shoulder[2]-.1)
        gust=pose["gust"]
        ribbon=[
            scarf_root,
            (scarf_root[0]-.29-gust*.002,scarf_root[1]+.12,scarf_root[2]-.03),
            (scarf_root[0]-.83-gust*.003,scarf_root[1]+.12+
             .18*math.sin(t*2.1),scarf_root[2]-.20),
            (scarf_root[0]-.79-gust*.003,scarf_root[1]-.12+
             .18*math.sin(t*2.1),scarf_root[2]-.20)]
        _poly(draw,cam,ribbon,(254,205,122,255))


def draw_wind_actors3d(picture: Image.Image,t: float,duration: float) -> None:
    if picture.mode!="RGBA" or picture.size!=WORLD_SIZE:
        raise ValueError("3D wind performers require native portrait RGBA")
    a=actor_pose(t,duration,0)
    b=actor_pose(t,duration,1)
    camera=camera_pose(t,duration,"wind")
    layer=Image.new("RGBA",(1080,SCENE_BOTTOM-SCENE_TOP))
    d=ImageDraw.Draw(layer,"RGBA")
    # Distant performer first for painter's order.
    _performer(d,camera,b,t)
    _performer(d,camera,a,t)
    picture.alpha_composite(layer,(0,SCENE_TOP))
