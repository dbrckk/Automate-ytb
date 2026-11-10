"""Original shared 2.5D material ribbons for light, water and molten flows.

Authored curves are spatial trajectories, not a 3D spline/mesh or a still
image translated around the screen. A causal tracer advances by real arc
length along the SAME path as its soft scattering, occluded edge and hot
material core. Independent reusable for science, nature and explanatory art.
"""
from __future__ import annotations

import math

from PIL import ImageDraw

VERSION = "causal-material-ribbon-25d-p510-v1"
MATERIALS = ("light", "water", "magma")


def _rgb(rgb, factor: float) -> tuple[int, int, int]:
    return tuple(max(0,min(255,round(int(channel)*factor)))
                 for channel in rgb)


def _mix(a, b, factor: float) -> tuple[int, int, int]:
    return tuple(round(x*(1-factor)+y*factor) for x,y in zip(a,b))


def _safe(path, material, rgba, width, progress):
    if (not isinstance(path,(list,tuple)) or not 2<=len(path)<=512
            or any(not isinstance(p,(list,tuple)) or len(p)!=2
                   or any(type(v) not in (int,float) or
                          not math.isfinite(v) or abs(v)>4000
                          for v in p) for p in path)
            or material not in MATERIALS
            or not isinstance(rgba,(list,tuple)) or len(rgba)!=4
            or any(type(c) is not int or not 0<=c<=255 for c in rgba)
            or type(width) is not int or not 1<=width<=120
            or type(progress) not in (int,float) or
            not math.isfinite(progress) or not 0<=progress<=1):
        raise ValueError("Invalid shared 2.5D material ribbon")


def _position(path, fraction:float):
    lengths=[math.hypot(x1-x0,y1-y0)
             for (x0,y0),(x1,y1) in zip(path,path[1:])]
    total=sum(lengths)
    if total<=.001:
        raise ValueError("Degenerate visual path")
    offset=fraction*total
    passed=0.
    for (x0,y0),(x1,y1),length in zip(path,path[1:],lengths):
        if passed+length>=offset or passed+length>=total-.001:
            f=max(0,min(1,(offset-passed)/max(.001,length)))
            return (x0+(x1-x0)*f,y0+(y1-y0)*f),total
        passed+=length
    return tuple(path[-1]),total


def _segment(path:list[tuple[float,float]], from_fraction:float,
             to_fraction:float)->list[tuple[float,float]]:
    if from_fraction>=to_fraction:
        return []
    start,total=_position(path,from_fraction)
    finish,_=_position(path,to_fraction)
    dist=0.
    nodes=[start]
    for a,b in zip(path,path[1:]):
        d=math.dist(a,b)
        dist+=d
        f=dist/total
        if from_fraction+1e-10<f<to_fraction-1e-10:
            nodes.append(tuple(b))
    nodes.append(finish)
    return nodes


def draw_material_ribbon(draw:ImageDraw.ImageDraw,
                         path:list[tuple[float,float]]|tuple[tuple[float,float],...],
                         *, material:str, color:tuple[int,int,int,int],
                         width:int,progress:float)->None:
    """Layer tinted volume, localized rim and an in-path moving highlight.

    The source's real geometry is never modified: straight optical rays stay
    straight, authored ocean currents stay sinusoidally displaced, and lava
    advances only along its physically existing route. No frame random seeds.
    """
    if not isinstance(draw,ImageDraw.ImageDraw):
        raise ValueError("Need a Pillow 2.5D drawing context")
    _safe(path,material,color,width,progress)
    points=[(float(x),float(y)) for x,y in path]
    _,total=_position(points,1.)
    r,g,b,a=color
    rgb=(r,g,b)
    darkness=(13,27,43) if material=="water" else (
        (30,10,16) if material=="magma" else (33,60,86))
    halo=_mix(rgb,(255,255,255),.18 if material=="light" else .03)
    inner=(_mix(rgb,(255,255,255),.42) if material=="light"
           else _mix(rgb,(255,241,181),.52) if material=="magma"
           else _mix(rgb,(215,249,251),.42))
    # Source-space offset darkens the underside while the uppermost
    # scattering line remains fine. True 2.5D painter's layers.
    underside=[(x,y+max(1,width*.10)) for x,y in points]
    draw.line(underside,fill=(*darkness,min(220,round(a*.46))),
              width=width+max(2,width//4),joint="curve")
    draw.line(points,fill=(*halo,round(a*.21)),
              width=width+max(5,width//2),joint="curve")
    draw.line(points,fill=(*rgb,min(255,round(a*.82))),
              width=width,joint="curve")
    draw.line([(x,y-max(1,width*.07)) for x,y in points],
              fill=(*inner,min(255,round(a*.79))),
              width=max(1,round(width*.23)),joint="curve")
    # A continuous short in-curve signal propagates in the real direction;
    # its position is arc-length based rather than a jump between nodes.
    # Hide the particle at the very beginning/end to avoid a cut flash.
    fade=min(1.,progress/.055,(1-progress)/.055)
    if fade<=0:
        return
    pos,_=_position(points,progress)
    trail_length=min(.14,max(.028,(width*2.6)/total))
    tail=_segment(points,max(0,progress-trail_length),progress)
    if len(tail)>=2:
        draw.line(tail,fill=(*inner,round(225*fade)),
                  width=max(1,round(width*.27)),joint="curve")
    dot=max(2,round(width*.14))
    x,y=pos
    draw.ellipse((x-dot,y-dot,x+dot,y+dot),
                 fill=(*_mix(inner,(255,255,255),.62),round(232*fade)))
