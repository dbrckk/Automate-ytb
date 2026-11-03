"""Original continuous volcanic-science 9:16 animations, fully CPU rendered.

Causal schematic: molten magma, gas pressure, ascent, ash/ejecta, and lava.
No stock footage, third-party images, neural rendering or paid model.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter

from .science_stage_director import reframe, VERSION as DIRECTOR_VERSION

SIZE=(1080,1380)
TOP=330
BEATS=("magma","pressure","ascent","eruption","lava")
BADGES={
    "magma":("MOLTEN ROCK","ROCHE FONDUE"),
    "pressure":("GAS PRESSURE","PRESSION DES GAZ"),
    "ascent":("MAGMA ASCENT","MONTÉE DU MAGMA"),
    "eruption":("ERUPTION COLUMN","COLONNE ÉRUPTIVE"),
    "lava":("LAVA FLOWS","COULÉES DE LAVE"),
}


def _plain(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD",s.casefold())
                   if not unicodedata.combining(c))


def supports_topic(topic: str) -> bool:
    if not isinstance(topic,str):
        raise ValueError("Volcano science needs a topic")
    return bool(re.search(r"\b(volcano(?:es)?|volcanic|volcans?)\b",
                          _plain(topic)))


def classify(topic: str, narration: str) -> str | None:
    if not isinstance(topic,str) or not isinstance(narration,str):
        raise ValueError("Volcano scenes need authored text")
    if not supports_topic(topic):
        return None
    s=_plain(narration)
    if re.search(r"\b(lava|flow(?:s|ing)? down|coulees?)\b",s):
        return "lava"
    if re.search(r"\b(erupt(?:ion|s|ing)?|blast(?:s|ing)?|ash|"
                 r"fragment(?:s)?|ejecta)\b",s):
        return "eruption"
    if re.search(r"\b(ris(?:es|ing)|upward|cracks?|vent|remont\w*)\b",s):
        return "ascent"
    if re.search(r"\b(pressure|bubbles?|trapped|chamber fills|pression)\b",s):
        return "pressure"
    if re.search(r"\b(magma|molten|melt(?:s|ing|ed)?|fondue)\b",s):
        return "magma"
    return None


@lru_cache(maxsize=1)
def portrait_background() -> Image.Image:
    frame=Image.new("RGBA",(1080,1920))
    d=ImageDraw.Draw(frame)
    for y in range(1920):
        p=y/1920
        d.line((0,y,1080,y),fill=(int(5+9*p),int(13+16*p),
                                  int(29+21*p),255))
    return frame


@lru_cache(maxsize=2)
def _base(section: bool) -> Image.Image:
    frame=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(frame)
    for y in range(SIZE[1]):
        p=y/SIZE[1]
        d.line((0,y,1080,y),fill=(int(7+19*p),int(16+17*p),
                                  int(35+18*p),255))
    rng=random.Random(1803)
    for i in range(160):
        x,y=rng.randrange(1080),rng.randrange(40,600)
        b=rng.randrange(110,210)
        d.ellipse((x-1,y-1,x+1,y+1),fill=(b//2,b-15,b,175))
    d.polygon([(0,945),(170,862),(335,913),(513,820),
               (689,898),(842,825),(1080,934),(1080,1380),(0,1380)],
              fill=(25,44,61,255))
    # Original symmetrical volcano silhouette with fractured rocky surfaces.
    cone=[(0,988),(127,914),(228,797),(337,621),(448,463),
          (502,347),(522,334),(558,334),(589,419),
          (697,594),(805,769),(940,915),(1080,988),
          (1080,1380),(0,1380)]
    d.polygon(cone,fill=(42,42,50,255))
    d.line([(495,361),(515,336),(561,336),(586,401)],
           fill=(120,106,94,255),width=8,joint="curve")
    for j in range(45):
        x=100+j*21
        y=840-415*max(0,1-abs(x-540)/430)
        d.line((x,y,x+22,y+14),fill=(77+j%3*9,73,74,125),width=2)
    if section:
        d.polygon([(0,823),(170,844),(342,818),(501,843),
                   (700,813),(870,831),(1080,804),
                   (1080,1380),(0,1380)],fill=(27,24,32,246))
        for i in range(5):
            y=875+i*89
            d.line([(0,y),(165,y-19),(335,y+9),(525,y-16),
                    (700,y+13),(900,y-8),(1080,y+11)],
                   fill=(89,66,66,105),width=3)
        d.line((540,1028,540,345),fill=(111,46,37,246),width=59)
        d.line((540,1028,540,345),fill=(35,18,23,255),width=34)
        d.ellipse((327,1004,756,1254),fill=(107,43,28,255),
                  outline=(151,70,43,245),width=12)
    d.polygon([(0,1307),(182,1245),(345,1287),(540,1211),
               (751,1271),(932,1235),(1080,1281),
               (1080,1380),(0,1380)],fill=(14,20,29,245))
    return frame


def _glow(stage:Image.Image,centres:list[tuple[float,float,float]])->None:
    small=Image.new("RGBA",(270,345))
    d=ImageDraw.Draw(small)
    for x,y,radius in centres:
        x,y,r=x*.25,y*.25,radius*.25
        d.ellipse((x-r,y-r,x+r,y+r),fill=(255,91,20,120))
    small=small.filter(ImageFilter.GaussianBlur(9))
    stage.alpha_composite(small.resize(SIZE,Image.Resampling.BILINEAR))


def _underground(stage:Image.Image,beat:str,t:float,duration:float)->None:
    d=ImageDraw.Draw(stage,"RGBA")
    cx,cy=540,1120
    _glow(stage,[(cx,cy,230)])
    pulse=1+.055*math.sin(t*3)
    rx,ry=174*pulse,94*pulse
    d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),
              fill=(230,85,24,255),outline=(255,154,53,255),width=9)
    for i in range(20):
        x=cx-140+(i*47+t*17)%280
        y=cy-38+37*math.sin(i*.83+t*1.19)
        rr=3+i%4*3
        d.ellipse((x-rr,y-rr,x+rr,y+rr),
                  fill=(255,220-(i%4)*14,75,235))
    if beat=="pressure":
        for i in range(5):
            f=(t*.39+i*.2)%1
            rr=177+f*145
            d.ellipse((cx-rr,cy-rr*.58,cx+rr,cy+rr*.58),
                      outline=(255,147,53,round(163*(1-f))),width=5)
        for i in range(24):
            x=cx-120+(i*71)%240
            y=cy+45-((i*41+t*(38+i%3*13))%232)
            d.ellipse((x-5,y-5,x+5,y+5),
                      fill=(255,211,137,184))
    if beat=="ascent":
        advance=min(1.0,t/duration*1.32)
        y=1016-664*advance
        _glow(stage,[(540,y+50,83),(540,760,40)])
        d.line((540,1014,540,y),fill=(244,91,20,255),width=30)
        d.line((540,1014,540,y),fill=(255,217,109,255),width=12)
        for i in range(17):
            yy=1010-((i*31+t*93)%max(80,665*advance))
            if yy>=y:
                xx=540+10*math.sin(i*1.2+t)
                d.ellipse((xx-4,yy-7,xx+4,yy+7),
                          fill=(255,242,157,243))


def _explosion(stage:Image.Image,t:float,duration:float)->None:
    d=ImageDraw.Draw(stage,"RGBA")
    p=min(1.0,t/duration*2)
    _glow(stage,[(540,345,190+45*math.sin(t*2)**2)])
    # Billowing smoke is layered with independently drifting ash particles.
    smoke=Image.new("RGBA",(270,345))
    sd=ImageDraw.Draw(smoke)
    for i in range(36):
        progress=(t*.11+i*.077)%1
        x=135+math.sin(i*1.83+t*.45)*(16+progress*72)
        y=94-progress*78
        radius=(19+progress*31)*p
        if radius>1:
            sd.ellipse((x-radius,y-radius*.64,x+radius,y+radius*.64),
                       fill=(110+i%4*6,98+i%3*7,93+i%5*6,
                             round(84*(1-progress))))
    stage.alpha_composite(smoke.filter(
        ImageFilter.GaussianBlur(9)).resize(SIZE,
                                            Image.Resampling.BILINEAR))
    d=ImageDraw.Draw(stage,"RGBA")
    d.polygon([(492,366),(525,300),(540,203),(555,303),(593,366)],
              fill=(255,102,27,247))
    d.line((540,353,540,206),fill=(255,233,141,239),width=13)
    for i in range(74):
        f=(t*(.20+i%4*.025)+i*.127)%1
        dx=(-1 if i%2 else 1)*(85+i%11*39)
        x=540+dx*f
        y=355-340*math.sin(f*math.pi)*(0.56+i%5*.13)
        rr=2+i%5*2
        d.line((x-5,y+13,x,y),fill=(255,78,24,149),width=2)
        d.ellipse((x-rr,y-rr,x+rr,y+rr),
                  fill=(255,173+i%3*16,58,232))
    for i in range(34):
        f=(t*.22+i*.103)%1
        x=540+math.sin(i*1.44+t*.3)*(80+f*210)
        y=345-f*340
        rr=7+i%4*8
        d.ellipse((x-rr,y-rr*.75,x+rr,y+rr*.75),
                  fill=(124,107,99,round(122*(1-f))))


def _lava(stage:Image.Image,t:float,duration:float)->None:
    d=ImageDraw.Draw(stage,"RGBA")
    routes=(
        [(540,356),(588,436),(642,518),(699,605),(754,696),
         (813,785),(893,876),(993,967),(1080,1028)],
        [(530,355),(490,444),(442,528),(380,620),(322,712),
         (251,811),(164,910),(65,988),(0,1043)],
    )
    for i,route in enumerate(routes):
        f=min(1,t/duration*(1.13+i*.11))
        index=(len(route)-1)*f
        k=int(index)
        points=route[:k+1]
        if k<len(route)-1:
            a,b=route[k:k+2]
            z=index-k
            points.append((a[0]*(1-z)+b[0]*z,
                           a[1]*(1-z)+b[1]*z))
        if len(points)<2:
            continue
        # Dimensional lava: dark cooling crust around a glowing inner river.
        d.line(points,fill=(113,35,25,255),width=58,joint="curve")
        d.line(points,fill=(234,72,26,250),width=37,joint="curve")
        d.line(points,fill=(255,161,51,243),width=18,joint="curve")
        d.line(points,fill=(255,232,142,225),width=5,joint="curve")
        tipx,tipy=points[-1]
        _glow(stage,[(tipx,tipy,72)])
    for i in range(24):
        x=(i*107+t*22)%1080
        y=530+(i*73)%450
        d.ellipse((x-3,y-3,x+3,y+3),
                  fill=(255,153+i%3*17,67,140))


def draw_volcano(picture:Image.Image,beat:str,t:float,duration:float,
                 english:bool)->None:
    if (picture.mode!="RGBA" or picture.size!=(1080,1920)
            or beat not in BEATS or type(english) is not bool
            or type(t) not in (int,float) or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0<duration<=180 or not 0<=t<=duration):
        raise ValueError("Invalid original volcano frame")
    stage=_base(section=beat in ("magma","pressure","ascent")).copy()
    if beat in ("magma","pressure","ascent"):
        _underground(stage,beat,t,duration)
    elif beat=="eruption":
        _explosion(stage,t,duration)
    else:
        _lava(stage,t,duration)
    # Camera movement follows the narrated geological event; UI remains fixed.
    picture.alpha_composite(reframe(stage, "volcano", beat, t, duration), (0,TOP))
