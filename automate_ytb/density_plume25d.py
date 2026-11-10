"""Deterministic original 2.5D descending cold-water source with soft depth.

Continuous moving pigment and refraction tracks replace a colored diagram
card. This is an original scientific illustration, not a fluid simulation.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .world_volume25d import world_volume_alpha

VERSION="original-cold-water-advection-p519-v2"


def sinking_plume_frame(size:tuple[int,int],t:float,*,
                        seed:int=71341)->Image.Image:
    if (not isinstance(size,tuple) or len(size)!=2 or
            any(type(s) is not int or not 128<=s<=900 for s in size)
            or type(t) not in (int,float) or not math.isfinite(t)
            or not 0<=t<=180 or type(seed) is not int
            or not 0<=seed<=1_000_000):
        raise ValueError("Invalid 2.5D cold water source")
    w,h=size
    low=(max(48,w//4),max(48,h//4))
    bloom=Image.new("RGBA",low)
    soft=ImageDraw.Draw(bloom,"RGBA")
    fluid=Image.new("RGBA",size)
    detailed=ImageDraw.Draw(fluid,"RGBA")
    for lane in range(14):
        phase=lane*.63+seed*.00013+t*.36
        pts=[]
        for i in range(58):
            q=i/57
            y=h*(.32+.57*q+.012*(lane%3))
            x=w*(.77+.024*math.sin(lane*1.4)
                 -.17*q*q-.029*q*math.sin(9.7*q+phase))
            x+=(lane-6.5)*4.1
            pts.append((x,y))
        soft.line([(x*low[0]/w,y*low[1]/h) for x,y in pts],
                  fill=(42,132,200,42+lane%4*8),
                  width=8+lane%4,joint="curve")
        detailed.line(pts,fill=(41,121,183,30+lane%4*8),
                      width=15+lane%3*3,joint="curve")
        detailed.line(pts,fill=(138,224,249,48+lane%3*10),
                      width=2+lane%3,joint="curve")
    soft=bloom.filter(ImageFilter.GaussianBlur(8)).resize(
        size,Image.Resampling.BICUBIC)
    result=Image.alpha_composite(soft,fluid)
    alpha=ImageChops.multiply(
        result.getchannel("A"),
        world_volume_alpha(size,kind="water",seed=seed))
    result.putalpha(alpha)
    return result
