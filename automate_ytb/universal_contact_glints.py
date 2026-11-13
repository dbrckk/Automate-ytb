"""Localized authored contact glints: no fake lines between unrelated actors.

Event timing remains authored and is synchronized to the causal Foley track.
A nearby pair can briefly glint at the meeting point; distant performers
receive two independent subtle local cues, never a teleporting beam.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

VERSION = "localized-causal-glints-without-connector-beams-v1"


def paint_contact_glints(canvas: Image.Image, point_a, point_b,
                         intensity: float, *, stage_width: int) -> None:
    """Alpha-composite tiny event surfaces in place, no full-frame allocations."""
    if (not isinstance(canvas,Image.Image) or canvas.mode!="RGBA"
            or type(stage_width) is not int or not 64<=stage_width<=1920
            or type(intensity) not in (int,float)
            or not math.isfinite(intensity) or not 0<=intensity<=1
            or any(type(p) not in (list,tuple) or len(p)!=2
                   for p in (point_a,point_b))
            or not all(type(c) in (int,float) and math.isfinite(c)
                       for point in (point_a,point_b) for c in point)):
        raise ValueError("Invalid bounded visual contact parameters")
    if intensity==0:
        return
    ax,ay=point_a
    bx,by=point_b
    distance=math.hypot(ax-bx,ay-by)
    if distance<=stage_width*.24:
        targets=[((ax+bx)/2,(ay+by)/2)]
        gain=1.
    else:
        targets=[(ax,ay),(bx,by)]
        gain=.68
    extent=max(9,round(stage_width*.064))
    size=extent*2+1
    for cx,cy in targets:
        patch=Image.new("RGBA",(size,size))
        d=ImageDraw.Draw(patch)
        alpha=round(255*intensity*gain)
        for radius,opacity in (
                (round(extent*.55),round(alpha*.12)),
                (round(extent*.33),round(alpha*.27)),
                (round(extent*.14),round(alpha*.66))):
            d.ellipse((extent-radius,extent-radius,
                       extent+radius,extent+radius),
                      fill=(255,224,163,opacity))
        core=max(1,round(stage_width*.0034))
        d.ellipse((extent-core,extent-core,extent+core,extent+core),
                  fill=(255,248,225,alpha))
        scatter=(1-intensity)*extent*.63
        for i in range(5):
            theta=i*math.tau/5+0.31
            x=extent+round(math.cos(theta)*scatter)
            y=extent+round(math.sin(theta)*scatter*.66)
            radius=max(1,round(stage_width*.0022))
            d.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(255,239,204,round(alpha*.49)))
        x0=round(cx)-extent
        y0=round(cy)-extent
        x1=max(0,x0); y1=max(0,y0)
        x2=min(canvas.width,x0+size); y2=min(canvas.height,y0+size)
        if x2>x1 and y2>y1:
            canvas.alpha_composite(
                patch.crop((x1-x0,y1-y0,x2-x0,y2-y0)),(x1,y1))
