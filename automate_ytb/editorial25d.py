"""Shared open cinematic typography for original portrait 2.5D worlds.

This replaces recurring slide-card framing, not any subject-specific art.
No 3D scene, AI imagery, external fonts, text truncation, or extra video time.
Narration timing and the full original caption glyphs are supplied upstream.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw

VERSION="shared-open-science-editorial-25d-v1"
SIZE=(1080,1920)

@lru_cache(maxsize=8)
def _atmospheric_scrim(top:int, height:int, strength:int)->Image.Image:
    """A feathered light-absorbing field, without rectangular card rails."""
    if not (0<=top<1920 and 40<=height<=640 and top+height<=1920
            and 1<=strength<=210):
        raise ValueError("Invalid 2.5D editorial shade")
    shade=Image.new("RGBA",(1080,height))
    draw=ImageDraw.Draw(shade,"RGBA")
    center=(height-1)*.52
    sigma=height*.34
    for y in range(height):
        alpha=round(strength*math.exp(-.5*((y-center)/sigma)**2))
        # Explicit cosine falloff to full transparency at both endpoints.
        taper=math.sin(math.pi*y/(height-1))**2
        alpha=round(alpha*taper)
        draw.line((0,y,1079,y),fill=(4,13,27,alpha),width=1)
    return shade


def _lines(content:tuple[str,...], font_size:int, *, maximum:int)->None:
    if (not isinstance(content,tuple) or not 1<=len(content)<=maximum
            or not all(type(v) is str and v.strip() for v in content)
            or type(font_size) is not int or not 20<=font_size<=80):
        raise ValueError("Invalid measured caption/title lines")


def paint_header(picture:Image.Image, *, title:tuple[str,...],
                 font_size:int, badge:str, compact:bool=False)->None:
    """Keep original title characters but remove persistent slide panels."""
    if (not isinstance(picture,Image.Image) or
            picture.mode!="RGBA" or picture.size!=SIZE
            or type(badge) is not str or not badge.strip()
            or len(badge)>120 or type(compact) is not bool):
        raise ValueError("Invalid open science header")
    _lines(title,font_size,maximum=2)
    from .science_motion import _font
    top,height,strength=(70,330,138) if compact else (165,430,160)
    picture.alpha_composite(_atmospheric_scrim(top,height,strength),(0,top))
    d=ImageDraw.Draw(picture,"RGBA")
    # One fine unilateral narrative accent, never paired full-height rails.
    y0=134 if compact else 230
    d.line((91,y0+4,91,y0+(108 if len(title)>1 else 51)),
           fill=(247,202,117,225),width=5)
    for i,line in enumerate(title):
        y=(125+53*i) if compact else (221+68*i)
        d.text((109,y),line,font=_font(font_size,True),
               fill=(245,250,252,255),
               stroke_width=2,stroke_fill=(3,11,22,224))
    badge_y=283 if compact else 480
    d.text((110,badge_y),badge,
           font=_font(30 if compact else 34,True),
           fill=(253,201,115,255),
           stroke_width=1,stroke_fill=(2,8,17,195))


def paint_caption(picture:Image.Image, *, lines:tuple[str,...],
                  font_size:int)->None:
    """Position real speech-timed captions without a permanent text card."""
    if (not isinstance(picture,Image.Image) or
            picture.mode!="RGBA" or picture.size!=SIZE):
        raise ValueError("Invalid open science subtitle canvas")
    _lines(lines,font_size,maximum=3)
    from .science_motion import _font
    picture.alpha_composite(_atmospheric_scrim(1490,318,172),(0,1490))
    d=ImageDraw.Draw(picture,"RGBA")
    d.line((91,1550,91,1718),fill=(152,226,244,210),width=4)
    for i,line in enumerate(lines):
        d.text((108,1564+48*i),line,
               font=_font(font_size,True),fill=(245,249,252,255),
               stroke_width=3,stroke_fill=(3,10,20,245))
