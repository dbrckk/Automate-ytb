"""Original cinematic depth cues for the Earth-stop explainer.

This is an intentionally modest 2.5D lighting/perspective pass, not a
photorealistic renderer or physical atmospheric model. It affects the action
area only: fixed title and audio-derived captions remain unobstructed.

Light sprites are cached once; per-frame geometry is deterministic and uses
only Pillow. No copyrighted assets, remote model or paid API.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFilter

SCENES=frozenset({"stop","inertia","wind","ocean","poles","day","astronaut"})
LIGHT=(247,216,151,160)
MIST=(75,153,185,42)


@lru_cache(maxsize=6)
def _soft_light(size: int, rgb: tuple[int,int,int]) -> Image.Image:
    """Blur an actual alpha mask; not an opaque rectangle over source artwork."""
    mask=Image.new("L",(size,size),0)
    d=ImageDraw.Draw(mask)
    pad=max(12,size//6)
    d.ellipse((pad,pad,size-pad,size-pad),fill=150)
    mask=mask.filter(ImageFilter.GaussianBlur(max(8,size//9)))
    sprite=Image.new("RGBA",(size,size),(*rgb,0))
    sprite.putalpha(mask)
    return sprite


def _validate(picture: Image.Image, beat: str, t: float, duration: float):
    if (picture.mode!="RGBA" or picture.size!=(1080,1920)
            or beat not in SCENES or type(t) not in (int,float)
            or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0<=t<=duration<=180 or duration==0):
        raise ValueError("Invalid native Earth cinematic depth frame")


def draw_depth_behind(picture: Image.Image, beat: str,
                      t: float, duration: float) -> None:
    """Behind foreground subjects, create light falloff and distant parallax."""
    _validate(picture,beat,t,duration)
    p=t/duration
    is_earth=beat in {"stop","poles","day"}
    if is_earth:
        rgb=(39,148,238) if beat!="day" else (243,168,73)
        # True alpha glow behind the projected globe, not a large flat disc.
        cx=540+round(20*math.sin(t*.35))
        cy=1017+round(14*math.sin(t*.54))
        picture.alpha_composite(_soft_light(936,rgb),(cx-468,cy-468))
    elif beat=="astronaut":
        cx=540+round(72*math.sin(t*.65))
        cy=1050+round(65*math.sin(t*.9))
        picture.alpha_composite(_soft_light(700,(58,151,241)),
                                (cx-350,cy-350))
    else:
        # The sky's illuminated center moves independently of buildings;
        # near and distant ridges move at different camera/parallax speeds.
        drift=round(44*math.sin(t*.35))
        picture.alpha_composite(_soft_light(850,(65,152,207)),
                                (110+drift,655))
        d=ImageDraw.Draw(picture,"RGBA")
        for layer in range(3):
            y=1052+layer*85
            speed=(5,10,19)[layer]
            off=round(t*speed)
            color=((12,53,86,118),(19,75,106,130),
                   (23,69,94,155))[layer]
            pts=[(-100,1453)]
            for x in range(-100,1221,96):
                altitude=75+33*math.sin((x+off)/170+layer*1.7)
                altitude+=15*math.sin((x+off)/83)
                pts.append((x,round(y-altitude)))
            pts.extend([(1220,1453)])
            d.polygon(pts,fill=color)
        # Fog cuts across multiple depth layers but never across captions.
        for k in range(4):
            yy=1020+k*90+round(9*math.sin(t*.6+k))
            opacity=24+k*6
            d.rounded_rectangle((0,yy,1080,yy+45),radius=20,
                                fill=(89,175,194,opacity))
        if beat=="wind":
            # Cold gust light streaks travel across the distant skyline.
            for j in range(7):
                x=(j*241+t*(92+j*8))%1580-500
                y=773+j*79
                d.polygon(((x,y),(x+220,y-18),(x+190,y+10),(x-20,y+35)),
                          fill=(126,222,240,28+j%3*8))


def draw_depth_above(picture: Image.Image, beat: str,
                     t: float, duration: float) -> None:
    """Focal highlights, material reflections and projected light cues."""
    _validate(picture,beat,t,duration)
    d=ImageDraw.Draw(picture,"RGBA")
    p=t/duration
    if beat in {"inertia","wind","ocean"}:
        # Perspective pavement lines: distant narrow marks, wider near marks.
        # A separate moving offset creates a tracking-camera effect.
        vanishing=(540+round(33*math.sin(t*.28)),1120)
        for lane in (-2,-1,1,2):
            bottom=540+lane*275
            d.line((vanishing[0]+lane*27,vanishing[1],bottom,1447),
                   fill=(95,159,171,82),width=3+abs(lane))
        for k in range(7):
            depth=((k*.188+t*.13)%1)**1.65
            y=1309+depth*131
            span=14+46*depth
            x=540+(22*math.sin(t*.28))
            d.line((x-span,y,x+span,y),fill=(175,227,230,92),
                   width=max(1,round(2+depth*5)))
        for j in range(5):
            # Building edges catch moving intermittent side light.
            x=71+j*224+round(17*math.sin(t*.45+j))
            level=1008+(j%3)*46
            d.polygon(((x,level),(x+9,level-7),
                       (x+9,1312),(x,1327)),
                      fill=(128,206,220,38+j%2*19))
    if beat=="ocean":
        # Specular reflection shifts with the advancing wavefront. Multiple
        # short irregular bands read as surface material rather than flat fill.
        surge=p*p*(3-2*p)
        base=1325-286*surge
        for row in range(13):
            y=base+row*18
            for col in range(9):
                x=50+col*120+round(22*math.sin(t*2+row*.77+col))
                length=12+((row*5+col*11)%37)
                alpha=52+((row+col)%4)*18
                d.line((x,y,x+length,y+3*math.sin(t*1.6+row)),
                       fill=(221,249,254,alpha),width=2+(row%2))
    elif beat=="astronaut":
        cx=540+round(72*math.sin(t*.65))
        cy=1050+round(65*math.sin(t*.9))
        # Visor Fresnel highlight: narrow animated curved streak, not an
        # opaque white sticker across the face.
        offset=round(9*math.sin(t*1.1))
        d.arc((cx-74+offset,cy-155,cx+66+offset,cy-35),
              209,270,fill=(234,253,255,175),width=7)
        d.arc((cx-92,cy-170,cx+92,cy-16),195,277,
              fill=(226,247,255,86),width=3)
        d.rounded_rectangle((cx-47,cy+42,cx+34,cy+61),
                            radius=8,fill=(138,228,253,56))
        for k in range(12):
            phase=(t*.27+k*.137)%1
            xx=cx+math.sin(k*1.91)*380
            yy=cy+math.cos(k*1.31)*260-125*phase
            radius=2+k%4
            d.ellipse((xx-radius,yy-radius,xx+radius,yy+radius),
                      fill=(158,224,253,round(150*(1-phase))))
    elif beat in {"stop","poles","day"}:
        cx=540+round(20*math.sin(t*.35))
        cy=1017+round(14*math.sin(t*.54))
        # Rotating little orbital glints give depth without implying the
        # stopped globe itself is still rotating.
        for k in range(13):
            phi=k*math.tau/13+t*.22
            radius=362+((k*11)%28)
            x=cx+radius*math.cos(phi)
            y=cy+radius*math.sin(phi)
            r=2+(k%3)
            d.ellipse((x-r,y-r,x+r,y+r),
                      fill=(230,246,255,106+k%4*18))
        if beat=="day":
            # Animated warm sunlight, spatially limited to the planet
            # vicinity. Contrast remains high in the caption box below.
            x=263+round(37*math.sin(t*.31))
            for rad in (105,149,191):
                d.arc((x-rad,805-rad,x+rad,805+rad),
                      280,65,fill=(255,208,119,68),width=3)
