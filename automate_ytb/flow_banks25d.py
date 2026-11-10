"""Connected source-space 2.5D banks and moving crust shared by lava/water.

One physically located route drives the irregular banks, interior channel,
temperature/refraction ribbons and advected material islands. Banks are
anchored to *arc length* in the source world (rather than frame number or
number of currently visible vertices), avoiding morphing rock boundaries.
Small full-resolution polygons cost no new 1080x1920 intermediate buffers.
This is original schematic animation, not fluid dynamics or 3D.
"""
from __future__ import annotations

import math

from PIL import ImageDraw

VERSION="original-source-grounded-flow-banks25d-p522-v1"
MATERIALS=("magma","water")


def _validated(path, material, width, seed):
    if (not isinstance(path,(tuple,list)) or not 2<=len(path)<=512
            or any(not isinstance(point,(tuple,list)) or len(point)!=2
                   or any(type(v) not in (int,float)
                          or not math.isfinite(v) or abs(v)>4000
                          for v in point) for point in path)
            or type(material) is not str or material not in MATERIALS
            or type(width) is not int or not 2<=width<=120
            or type(seed) is not int or not 0<=seed<=1_000_000):
        raise ValueError("Invalid original source-based 2.5D fluid flow")
    nodes=tuple((float(x),float(y)) for x,y in path)
    segments=[math.dist(a,b) for a,b in zip(nodes,nodes[1:])]
    total=sum(segments)
    if total<=1e-4:
        raise ValueError("No valid physical flow trajectory")
    return nodes,segments,total


def advancing_path(path, progress:float)->tuple[tuple[float,float],...]:
    """Monotone arc-length front; does not jump between uneven route nodes."""
    nodes,segments,total=_validated(path,"magma",12,0)
    if (type(progress) not in (int,float)
            or not math.isfinite(progress) or not 0<=progress<=1):
        raise ValueError("Invalid advancing fluid front")
    if progress==0:
        return ()
    if progress==1:
        return nodes
    target=total*progress
    result=[nodes[0]]
    length=0.
    for start,end,segment in zip(nodes,nodes[1:],segments):
        if length+segment>=target:
            delta=(target-length)/max(segment,1e-7)
            result.append((start[0]+(end[0]-start[0])*delta,
                           start[1]+(end[1]-start[1])*delta))
            return tuple(result)
        result.append(end)
        length+=segment
    return nodes


def flow_banks(path, *, material:str, width:int, seed:int=8031):
    """Deterministic asymmetric river edges, connected to the same centerline.

    Each coordinate's width samples traveled distance from the *origin*.
    Upstream geometry is independent of animation clock and visible front.
    """
    nodes,segments,total=_validated(path,material,width,seed)
    distances=[0.]
    for length in segments:
        distances.append(distances[-1]+length)
    left=[]
    right=[]
    for i,((x,y),s) in enumerate(zip(nodes,distances)):
        a=nodes[max(0,i-1)]
        b=nodes[min(len(nodes)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=max(.0001,math.hypot(dx,dy))
        nx,ny=-dy/length,dx/length
        # Stationary lateral river-bank erosion, measured in world units.
        # The two banks are staggered; no perfectly mirrored tubes.
        left_width=(.80+.13*math.sin(s*.037+seed*.003)
                    +.079*math.sin(s*.097+.6))
        right_width=(.83+.16*math.sin(s*.030+seed*.002+1.9)
                     +.069*math.cos(s*.113-1.2))
        origin_factor=.55+.45*min(1.,s/85)
        front_factor=.42+.58*min(1.,(total-s)/23.)
        left_offset=.5*width*left_width*origin_factor*front_factor
        right_offset=.5*width*right_width*origin_factor*front_factor
        left.append((x+nx*left_offset,y+ny*left_offset))
        right.append((x-nx*right_offset,y-ny*right_offset))
    return tuple(left),tuple(right)


def _at_distance(nodes,segments,distance):
    length=0.
    for a,b,size in zip(nodes,nodes[1:],segments):
        if length+size>=distance:
            f=(distance-length)/max(size,1e-6)
            tangent=((b[0]-a[0])/max(size,1e-6),
                     (b[1]-a[1])/max(size,1e-6))
            return ((a[0]*(1-f)+b[0]*f,
                     a[1]*(1-f)+b[1]*f),tangent)
        length+=size
    last=nodes[-1]
    a=nodes[-2]
    size=max(1e-6,math.dist(a,last))
    return last,((last[0]-a[0])/size,(last[1]-a[1])/size)


def draw_organic_flow(draw:ImageDraw.ImageDraw,path,*,material:str,width:int,
                      t:float,duration:float,seed:int=8031)->None:
    """Draw original heat/water banks and a causally moving interior shear."""
    if not isinstance(draw,ImageDraw.ImageDraw):
        raise ValueError("Flow drawing requires Pillow context")
    nodes,segments,total=_validated(path,material,width,seed)
    if (type(t) not in (int,float) or not math.isfinite(t)
            or type(duration) not in (int,float)
            or not math.isfinite(duration) or not 0<duration<=180
            or not 0<=t<=duration):
        raise ValueError("Invalid flowing material animation clock")
    left,right=flow_banks(nodes,material=material,width=width,seed=seed)
    boundaries=list(left)+list(reversed(right))
    if material=="magma":
        shadow=(30,17,23,246)
        rock=(78,35,28,245)
        body=(177,62,29,251)
        hot=(240,102,29,232)
        core=(255,196,80,208)
        rim=(30,25,33,229)
        flakes=(57,28,27,199)
    else:
        shadow=(17,51,82,149)
        rock=(30,87,121,153)
        body=(46,141,177,168)
        hot=(119,211,232,131)
        core=(214,251,253,144)
        rim=(14,57,94,125)
        flakes=(22,90,130,108)
    # The physical channel itself is a polygon; no giant equal-width line.
    draw.polygon(boundaries,fill=shadow)
    inner_left,inner_right=flow_banks(
        nodes,material=material,width=max(2,round(width*.84)),seed=seed)
    draw.polygon(list(inner_left)+list(reversed(inner_right)),fill=rock)
    body_left,body_right=flow_banks(
        nodes,material=material,width=max(2,round(width*.62)),seed=seed)
    draw.polygon(list(body_left)+list(reversed(body_right)),fill=body)
    bright_left,bright_right=flow_banks(
        nodes,material=material,width=max(2,round(width*.30)),seed=seed)
    draw.polygon(list(bright_left)+list(reversed(bright_right)),fill=hot)
    draw.line(nodes,fill=core,width=max(1,round(width*.08)),joint="curve")
    draw.line(left,fill=rim,width=4 if material=="magma" else 2,
              joint="curve")
    draw.line(right,fill=rim,width=5 if material=="magma" else 2,
              joint="curve")
    # Animated crust/shear follows arc length in the same channel. Nothing
    # spawns independently in the sky or outside the physically visible flow.
    count=23 if material=="magma" else 15
    for i in range(count):
        phase=(i*.073+t*(.031+(i%4)*.003))%1.
        d=phase*total
        if d<=3 or d>=total-3:
            continue
        (x,y),(tx,ty)=_at_distance(nodes,segments,d)
        nx,ny=-ty,tx
        lateral=math.sin(i*2.07+seed*.03)*width*.10
        x+=nx*lateral
        y+=ny*lateral
        long=width*(.10+.02*(i%3))
        side=width*(.045+.011*(i%4))
        # A polygonal cooled plate or thin water shear fold, not a disc.
        points=(
            (x-tx*long-nx*side,y-ty*long-ny*side),
            (x+tx*long*.2-nx*side*.8,y+ty*long*.2-ny*side*.8),
            (x+tx*long+nx*side,y+ty*long+ny*side),
            (x-tx*long*.31+nx*side*.7,y-ty*long*.31+ny*side*.7),
        )
        draw.polygon(points,fill=flakes if i%3 else core)
    # Sharp, irregular leading tongue attached to the last centerline node.
    # It inherits river direction and narrows with front_factors above.
    tip=nodes[-1]
    if material=="magma":
        draw.line((nodes[-2],tip),fill=(255,167,55,190),
                  width=max(2,round(width*.11)),joint="curve")
