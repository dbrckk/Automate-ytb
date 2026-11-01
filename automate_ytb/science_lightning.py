"""Original science animation: lightning charge separation, leader, connection,
return stroke and thunder. NOT a planet animation or photograph slideshow.

Diagrams are explanatory, not a quantitative atmospheric electricity simulation.
All visuals are locally drawn, time-based, mobile-safe and deterministic.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter
from .science_motion import _font
from .science_lightning_fx import (
    paint_environment, paint_terrain, bloom_electric_channel,
    paint_foreground_weather,
)

BEATS=("charge","leader","connection","return","thunder")
BADGES={
    "charge":("CHARGE SEPARATION","SÉPARATION DES CHARGES"),
    "leader":("STEPPED LEADER","CANAL DESCENDANT"),
    "connection":("UPWARD STREAMERS","DÉCHARGES ASCENDANTES"),
    "return":("RETURN STROKE","DÉCHARGE LUMINEUSE"),
    "thunder":("SHOCK WAVE & THUNDER","ONDE SONORE · TONNERRE"),
}
BASE=(7,19,39,255)
CYAN=(133,223,255,255)
GOLD=(255,207,111,255)
WHITE=(238,248,255,255)
STAGE_TOP=566
STAGE_BOTTOM=1496
STAGE_HEIGHT=STAGE_BOTTOM-STAGE_TOP


def _plain(value: str) -> str:
    text=unicodedata.normalize("NFKD",value.casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def supports_topic(topic: str) -> bool:
    if not isinstance(topic,str):
        raise ValueError("Lightning needs a real topic")
    return bool(re.search(r"\b(lightning|eclairs?|foudre|orage electrique|"
                          r"thunderstorms?)\b",_plain(topic)))


def classify(topic: str, narration: str) -> str | None:
    if not isinstance(topic,str) or not isinstance(narration,str):
        raise ValueError("Lightning scenes require authored text")
    if not supports_topic(topic):
        return None
    t=_plain(narration)
    if re.search(r"\b(tonnerre|thunder|onde sonore|sound wave|"
                 r"air se rechauffe|heats? the air|dilat\w*)\b",t):
        return "thunder"
    if re.search(r"\b(remonte|retour|return stroke|bright flash|"
                 r"courant intense|intense current|luminous flash)\b",t):
        return "return"
    if re.search(r"\b(ascendant\w*|upward|streamer\w*|rejoign\w*|"
                 r"connect\w*|trajet conducteur)\b",t):
        return "connection"
    if re.search(r"\b(descend\w*|progresse|leader|ionis\w*|"
                 r"champ electrique|electric field|step\w*)\b",t):
        return "leader"
    if re.search(r"\b(charge\w*|collis\w*|separ\w*|cristaux|"
                 r"ice crystal\w*|gouttes|droplet\w*)\b",t):
        return "charge"
    return None


@lru_cache(maxsize=1)
def storm_background() -> Image.Image:
    """A purpose-built rainstorm, without any planet, stars or black bars."""
    img=Image.new("RGBA",(1080,1920))
    d=ImageDraw.Draw(img)
    for y in range(1920):
        f=y/1920
        d.line((0,y,1080,y),fill=(round(6+16*f),
                                round(19+25*f),round(39+40*f),255))
    # Terrain is a distinct physical frame of reference for discharge paths.
    d.polygon(((0,1455),(118,1441),(258,1455),(405,1433),
               (592,1454),(766,1427),(930,1451),(1080,1434),
               (1080,1520),(0,1520)),fill=(17,37,50,255))
    return img


@lru_cache(maxsize=3)
def _cloud_sprite(variant: int) -> Image.Image:
    if type(variant) is not int or not 0<=variant<=2:
        raise ValueError("Invalid storm cloud variant")
    plate=Image.new("RGBA",(540,240))
    d=ImageDraw.Draw(plate)
    for i,(x,y,rx,ry) in enumerate(
        ((74,135,87,54),(168,109,119,78),(303,109,142,87),
         (410,135,102,60),(256,170,207,41))):
        shade=86+variant*8+i*3
        d.ellipse((x-rx,y-ry,x+rx,y+ry),
                  fill=(shade,shade+17,shade+37,135+i*13))
    return plate.filter(ImageFilter.GaussianBlur(13))


def _clouds(layer: Image.Image,t: float):
    for i,(x,y) in enumerate(((-85,70),(320,96),(724,63))):
        offset=round((24+i*7)*math.sin(t*(.16+i*.07)+i))
        layer.alpha_composite(_cloud_sprite(i),(x+offset,y))


def _leader_path():
    # One branching physical channel used in leader, link, return and thunder.
    nodes=[]
    for k in range(57):
        f=k/56
        y=270+510*f
        x=485+138*f+31*math.sin(f*12.8)+16*math.sin(f*37.)
        nodes.append((round(x),round(y)))
    return tuple(nodes)

PATH=_leader_path()


def _trail(d,coords,color,width):
    if len(coords)>=2:
        d.line(coords,fill=color,width=width,joint="curve")


def _ground(d):
    d.polygon([(0,811),(120,805),(270,813),(420,793),
               (591,807),(748,786),(923,803),(1080,787),
               (1080,930),(0,930)],fill=(14,38,44,255))
    for i in range(14):
        x=40+i*81
        d.line((x,826,x-4,844),fill=(53,96,95,205),width=4)


def _label(d,x,y,text,*,color=WHITE,size=31):
    d.text((x,y),text,font=_font(size,True),fill=color)


def _charges(d,t,english):
    rng=random.Random(1783)
    for i in range(56):
        x=190+(i*137)%705
        y=168+(i*61)%173
        # Colliding hydrometeors carry opposite charge in distinct regions.
        sign="+" if y<245 else "−"
        color=GOLD if sign=="+" else CYAN
        dx=16*math.sin(t*(.62+i%5*.1)+i)
        dy=11*math.cos(t*(.45+i%7*.06)+i)
        d.ellipse((x+dx-12,y+dy-12,x+dx+12,y+dy+12),
                  fill=(color[0],color[1],color[2],43))
        if i%3==0:
            d.text((round(x+dx-9),round(y+dy-14)),sign,
                   fill=color,font=_font(30,True))
        else:
            d.ellipse((x+dx-3,y+dy-3,x+dx+3,y+dy+3),fill=color)
    for k in range(18):
        # Ice/water collision traces; no random frame-to-frame jitter.
        x=220+rng.randrange(620)
        y=200+rng.randrange(230)
        vy=(t*(23+k%4*9)+k*19)%128
        d.line((x,y+vy,x-8,y+vy+21),
               fill=(170,226,243,135),width=3)
    _label(d,160,610,"ICE + WATER COLLISIONS" if english else
           "COLLISIONS GLACE · EAU",color=WHITE)
    _label(d,225,695,"+  +  +     −  −  −",color=GOLD,size=38)


def _leader(d,t,duration,english):
    f=min(1.,max(0.,t/duration))
    n=max(2,round(2+54*(f*f*(3-2*f))))
    coords=PATH[:n]
    _trail(d,PATH,(106,161,200,35),4)
    _trail(d,coords,(96,192,247,110),12)
    _trail(d,coords,(192,237,255,225),4)
    for j in (9,20,30,41,49):
        if n>j+1:
            x,y=PATH[j]
            k=min(1.,(n-j)/10)
            branch=((x,y),(x+round(37*k),y+round(24*k)),
                    (x+round(53*k),y+round(49*k)))
            _trail(d,branch,(141,210,251,183),3)
    x,y=coords[-1]
    d.ellipse((x-13,y-13,x+13,y+13),fill=(243,250,255,240))
    _label(d,148,688,"A FAINT CHANNEL MOVES DOWN" if english else
           "LE CANAL PROGRESSE VERS LE SOL",size=29)


def _connection(d,t,duration,english):
    t0=min(1.,max(0.,t/duration))
    lead=PATH[:41]
    _trail(d,lead,(129,210,247,155),8)
    _trail(d,lead,(208,239,255,230),3)
    # Grounded radio tower provides a reproducible clear start location.
    tip=PATH[40]
    tower_x,tower_y=700,770
    d.polygon([(677,812),(700,770),(725,812)],fill=(114,167,185,245))
    d.line((700,769,700,695),fill=(192,217,226,245),width=8)
    start=(700,695)
    points=(start,(start[0]-25,666),(start[0]-41,639),tip)
    n=max(2,round(2+2*t0))
    _trail(d,points[:n],(123,223,253,98),12)
    _trail(d,points[:n],WHITE,4)
    if n==4:
        x,y=tip
        for r in (16,29):
            d.ellipse((x-r,y-r,x+r,y+r),
                      outline=(253,211,121,195),width=3)
    _label(d,110,540,"UPWARD PATHS MAY JOIN" if english else
           "DES DÉCHARGES MONTENT DU SOL",size=29)


def _return(d,t,duration,english):
    # Return stroke brightens the connected channel upward; distinct from
    # the downward, faint stepped leader (not a replay of the same effect).
    p=min(1.,max(0.,t/duration))
    rev=PATH[::-1]
    active=rev[:max(2,round(2+55*min(1.,p*1.5)))]
    for width,alpha,color in (
        (38,38,(145,216,255)),(22,94,(156,226,255)),
        (12,190,(207,238,255)),(5,255,(255,255,255))):
        _trail(d,active,(*color,alpha),width)
    if p<.40:
        radius=round(52+95*p)
        x,y=PATH[-1]
        d.ellipse((x-radius,y-radius,x+radius,y+radius),
                  outline=(251,218,154,round(215*(1-p))),width=9)
    if p>.58:
        for i in range(12):
            x,y=PATH[i*4]
            r=3+(i%3)
            d.ellipse((x-r,y-r,x+r,y+r),fill=(255,248,222,191))
    _label(d,147,634,"CURRENT RUSHES UPWARD" if english else
           "LE COURANT REMONTE LE CANAL",color=GOLD,size=29)


def _thunder(d,t,duration,english):
    progress=min(1.,max(0.,t/duration))
    # Dimming hot channel with independently advancing pressure waves.
    _trail(d,PATH,(134,197,244,round(145*(1-progress)+25)),7)
    center=(621,670)
    for i in range(6):
        p=(progress*1.1-i*.16)
        if p<0 or p>1:
            continue
        radius=38+530*p
        alpha=round(175*(1-p))
        d.arc((center[0]-radius,center[1]-radius*.53,
               center[0]+radius,center[1]+radius*.53),
              188,354,fill=(255,199,111,alpha),width=6)
        d.arc((center[0]-radius,center[1]-radius*.53,
               center[0]+radius,center[1]+radius*.53),
              7,175,fill=(135,220,250,alpha),width=4)
    for i in range(11):
        x=100+i*94
        y=700+12*math.sin(i+progress*10)
        d.line((x,y,x+44,y),fill=(116,204,230,130),width=3)
    _label(d,157,555,"AIR EXPANDS: SOUND TRAVELS" if english else
           "L'AIR SE DILATE · LE SON SE PROPAGE",size=27)


def draw_lightning(picture: Image.Image, beat: str, t: float,
                   duration: float, english: bool) -> None:
    if (picture.mode!="RGBA" or picture.size!=(1080,1920) or beat not in BEATS
            or type(t) not in (float,int) or type(duration) not in (float,int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or duration<=0 or duration>180 or not 0<=t<=duration
            or type(english) is not bool):
        raise ValueError("Invalid lightning science frame")
    layer=Image.new("RGBA",(1080,STAGE_HEIGHT))
    # Original layered animated storm environment. Clouds, wet ground and
    # near/far rain have distinct depth speeds, not a flat background image.
    paint_environment(layer,t,beat,duration)
    terrain=Image.new("RGBA",(1080,STAGE_HEIGHT))
    td=ImageDraw.Draw(terrain,"RGBA")
    paint_terrain(td,t)
    layer.alpha_composite(terrain)
    # Actions must be blended on a separate transparent overlay. Drawing a
    # low-alpha glow directly onto opaque RGBA would overwrite its alpha,
    # darkening cloud faces and producing opaque-looking flat artifacts.
    actions=Image.new("RGBA",(1080,STAGE_HEIGHT))
    d=ImageDraw.Draw(actions,"RGBA")
    if beat=="charge":
        _charges(d,t,english)
    elif beat=="leader":
        _leader(d,t,duration,english)
    elif beat=="connection":
        _connection(d,t,duration,english)
    elif beat=="return":
        _return(d,t,duration,english)
    else:
        _thunder(d,t,duration,english)
    layer.alpha_composite(actions)
    bloom_electric_channel(layer,beat,t,duration,PATH)
    paint_foreground_weather(layer,t,beat)
    picture.alpha_composite(layer,(0,STAGE_TOP))
