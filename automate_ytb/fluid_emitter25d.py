"""Reusable original 2.5D moving fluid emitter for lava fountains and sea spray.

An authored jet is a bundle of evolving, connected, tapering material
paths with a diffuse underlayer, directional highlights and flowing flecks.
It has no disconnected straight orange pillar, screen-wide stock sprite,
per-frame randomness, 3D mesh, network or paid inference requirement.
This is editorial fluid illustration, not a fluid-dynamics simulation.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

VERSION = "original-shared-fluid-emitter-25d-p520-v1"
MATERIALS = ("magma", "spray")


def _safe(size: tuple[int,int], t:float, duration:float,
          material:str, seed:int)->None:
    if (not isinstance(size,tuple) or len(size)!=2
            or any(type(q) is not int or not 128<=q<=900 for q in size)
            or type(t) not in (int,float) or not math.isfinite(t)
            or type(duration) not in (int,float) or not math.isfinite(duration)
            or not 0<duration<=180 or not 0<=t<=duration
            or type(material) is not str or material not in MATERIALS
            or type(seed) is not int or not 0<=seed<=1_000_000):
        raise ValueError("Invalid original source fluid emission")


def emitter_anchor(size:tuple[int,int], material:str)->tuple[int,int]:
    if (not isinstance(size,tuple) or len(size)!=2
            or any(type(v) is not int or not 128<=v<=900 for v in size)
            or type(material) is not str or material not in MATERIALS):
        raise ValueError("Invalid reusable fluid-source anchor")
    w,h=size
    return ((w//2,h-17) if material=="magma" else (21,h//2))


def _paths(size: tuple[int,int], t:float,duration:float,
           material:str,seed:int)->list[list[tuple[float,float]]]:
    """Causal source paths; connected to one anchor, direction by material."""
    w,h=size
    ax,ay=emitter_anchor(size,material)
    strength=min(1.,max(0.,3.1*t/duration)) if material=="magma" else 1.
    if strength<=.001:
        return []
    rng=random.Random(seed)
    count=13 if material=="magma" else 15
    paths=[]
    for lane in range(count):
        wave=rng.uniform(-math.pi,math.pi)
        bend=rng.uniform(-.9,.9)
        lateral=(lane-(count-1)/2)/((count-1)/2)
        pts=[]
        for j in range(29):
            u=j/28
            if material=="magma":
                q=u*strength
                x=(ax+lateral*19*q+(9+15*q)*math.sin(q*5.4+t*.9+wave)*q
                   +12*bend*q*q)
                y=ay-h*.66*q
                y+=3.1*q*math.sin(q*12+t*1.3+wave)
            else:
                q=u
                x=ax+(w*.84)*q
                y=(ay+lateral*(5+18*q)
                   +(.5+q)*9*math.sin(q*9.4+t*.83+wave)
                   +bend*6*q*q)
            pts.append((x,y))
        paths.append(pts)
    return paths


def emitter_frame(size:tuple[int,int],t:float,duration:float, *,
                  material:str,seed:int=17719)->Image.Image:
    """Original local-space RGBA material source for a native video scene.

    Source material is built from continuous sweep trajectories; quarter-
    resolution bloom is computed once then sharp tapering source ridges are
    drawn on top. Stable time functions support arbitrary seeks/replays.
    """
    _safe(size,t,duration,material,seed)
    w,h=size
    result=Image.new("RGBA",size)
    paths=_paths(size,t,duration,material,seed)
    if not paths:
        return result
    glow=Image.new("RGBA",(max(64,w//3),max(64,h//3)))
    g=ImageDraw.Draw(glow,"RGBA")
    sx,sy=glow.width/w,glow.height/h
    color=(246,95,32) if material=="magma" else (113,208,239)
    for i,points in enumerate(paths):
        low=[(x*sx,y*sy) for x,y in points]
        g.line(low,fill=(*color,30+i%4*8),
               width=7 if material=="magma" else 5,joint="curve")
    glow=glow.filter(ImageFilter.GaussianBlur(5))
    result.alpha_composite(glow.resize(size,Image.Resampling.BILINEAR))
    d=ImageDraw.Draw(result,"RGBA")
    for lane,points in enumerate(paths):
        # Taper each connected jet along its own causal trajectory.
        for i in range(0,28,4):
            section=points[i:min(i+5,29)]
            f=(i+2)/28
            major=max(1,round((17 if material=="magma" else 9)*(1-.76*f)))
            core=max(1,round(major*.43))
            if material=="magma":
                shadow=(77,29,26,132)
                ink=((255,100+lane%3*23,42,227) if lane%3
                     else (255,191,73,234))
            else:
                shadow=(24,73,111,94)
                ink=((119,218,247,137) if lane%3 else
                     (213,248,255,151))
            d.line(section,fill=shadow,width=major+3,joint="curve")
            d.line(section,fill=ink,width=major,joint="curve")
            if lane%3==0:
                d.line(section,fill=(255,234,145,153) if material=="magma"
                       else (240,253,255,123),width=core,joint="curve")
        # Small advected source particles follow the same curve. They never
        # teleport into the surrounding sky independently of the jet.
        if lane%2==0:
            travel=(.14+lane*.071+t*(.09+lane*.004))%1.
            index=min(27,round(travel*27))
            x,y=points[index]
            radius=2+(lane%3)
            d.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(255,242,181,204) if material=="magma"
                      else (211,250,255,157))
    return result
