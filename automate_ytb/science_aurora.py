"""Original animated aurora-borealis science for native 9:16 shorts.

Five causal beats, rendered locally with Pillow: solar wind, magnetosphere,
atmospheric collision, photon emission and visibly rippling auroral curtains.
Illustrations are qualitative, not numerical particle simulation or real photos.
No third-party visual assets, cloud APIs, GPUs or paid inference credits.
"""
from __future__ import annotations
from functools import lru_cache
import math
import random
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter

from .science_stage_director import reframe, VERSION as DIRECTOR_VERSION

BEATS = ("solar_wind", "magnetic_field", "collisions", "emission", "curtains")
BADGES = {
    "solar_wind": ("SOLAR WIND", "VENT SOLAIRE"),
    "magnetic_field": ("EARTH'S MAGNETIC FIELD", "CHAMP MAGNÉTIQUE"),
    "collisions": ("ATMOSPHERIC COLLISIONS", "COLLISIONS"),
    "emission": ("GLOWING GASES", "GAZ LUMINEUX"),
    "curtains": ("DANCING AURORA", "AURORE DANSANTE"),
}
STAGE_SIZE = (1080, 1380)
STAGE_TOP = 330


def _plain(s: str) -> str:
    normalized = unicodedata.normalize("NFKD", s.casefold())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def supports_topic(topic: str) -> bool:
    if not isinstance(topic, str):
        raise ValueError("Aurora science needs an authored topic")
    return bool(re.search(r"\b(auroras?|northern[- ]lights?|southern[- ]lights?|"
                          r"aurores?[- ]boreales?|aurores?[- ]australes?)\b",
                          _plain(topic)))


def classify(topic: str, narration: str) -> str | None:
    if not isinstance(topic, str) or not isinstance(narration, str):
        raise ValueError("Aurora science needs authored text")
    if not supports_topic(topic):
        return None
    s = _plain(narration)
    if re.search(r"\b(solar wind|vent solaire|sun releases|sun sends)\b", s):
        return "solar_wind"
    if re.search(r"\b(magnetic|magnetosphere|magnetique)\b", s):
        return "magnetic_field"
    if re.search(r"\b(collid\w*|collision\w*|heurt\w*)\b", s):
        return "collisions"
    if re.search(r"\b(excit\w*|emit\w*|release.*light|colored light|"
                 r"light as|lumiere|glowing gas)\b", s):
        return "emission"
    if re.search(r"\b(curtain\w*|ripple\w*|dance|dancing|aurora\w*|"
                 r"northern lights|southern lights|rideau\w*)\b", s):
        return "curtains"
    return None


@lru_cache(maxsize=1)
def portrait_background() -> Image.Image:
    """Full-height dark navy plate under shot and fixed editorial overlays."""
    frame = Image.new("RGBA", (1080, 1920), (3, 12, 33, 255))
    d = ImageDraw.Draw(frame)
    for y in range(1920):
        p = y / 1919
        d.line((0, y, 1080, y),
               fill=(round(3+10*p), round(12+16*p),
                     round(33+28*p), 255))
    return frame


@lru_cache(maxsize=2)
def _plate(night: bool) -> Image.Image:
    """Expensive static gradients, star field and mountain silhouettes cached."""
    w, h = STAGE_SIZE
    frame = Image.new("RGBA", STAGE_SIZE)
    d = ImageDraw.Draw(frame)
    for y in range(h):
        p = y / h
        if night:
            color = (round(2+6*p), round(9+21*p), round(30+33*p),255)
        else:
            color = (round(3+9*p), round(9+19*p), round(26+45*p),255)
        d.line((0,y,w,y),fill=color)
    rng = random.Random(1001 if night else 710)
    for i in range(230 if night else 150):
        x, y = rng.randrange(1080),rng.randrange(50,1100)
        radius = 1 if i%7 else 2
        b = rng.randint(105,225)
        d.ellipse((x-radius,y-radius,x+radius,y+radius),
                  fill=(b//2,b-12,b,200))
    if night:
        d.polygon(((0,1095),(130,1040),(205,1068),(318,980),
                   (421,1049),(530,1006),(660,1110),(765,1049),
                   (893,1001),(1018,1077),(1080,1020),(1080,1380),
                   (0,1380)),fill=(9,27,37,255))
        d.polygon(((0,1220),(120,1194),(220,1243),(365,1150),
                   (466,1180),(614,1142),(742,1210),(859,1169),
                   (972,1250),(1080,1186),(1080,1380),(0,1380)),
                  fill=(3,14,25,255))
        d.line((0,1292,1080,1292),fill=(24,97,93,90),width=3)
    return frame


def _sphere(stage: Image.Image, cx: int, cy: int, radius: int,
            *, sunlight: bool = False) -> None:
    """Shaded schematic Sun or Earth, consistent across consecutive shots."""
    overlay = Image.new("RGBA", STAGE_SIZE)
    d = ImageDraw.Draw(overlay)
    if sunlight:
        for add,alpha in ((105,12),(68,25),(32,48)):
            d.ellipse((cx-radius-add,cy-radius-add,cx+radius+add,cy+radius+add),
                      fill=(254,140,44,alpha))
        for i in range(10):
            angle=i*math.tau/10
            sx=cx+math.cos(angle)*(radius+4)
            sy=cy+math.sin(angle)*(radius+4)
            ex=cx+math.cos(angle)*(radius+25+(i%3)*12)
            ey=cy+math.sin(angle)*(radius+25+(i%3)*12)
            d.line((sx,sy,ex,ey),fill=(255,174,84,150),width=3)
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                  fill=(255,179,72,255),outline=(255,235,155,255),width=4)
        d.arc((cx-radius+20,cy-radius+20,cx+radius-20,cy+radius-20),
              215,320,fill=(255,245,195,172),width=11)
    else:
        for add,alpha in ((75,16),(38,27),(11,52)):
            d.ellipse((cx-radius-add,cy-radius-add,cx+radius+add,cy+radius+add),
                      fill=(46,162,222,alpha))
        d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                  fill=(13,78,125,255),outline=(138,231,245,230),width=4)
        d.polygon(((cx-68,cy-60),(cx-15,cy-90),(cx+14,cy-28),
                   (cx-17,cy+10),(cx+21,cy+61),(cx-48,cy+53),
                   (cx-80,cy+4)),fill=(32,155,126,205))
        d.arc((cx-radius+12,cy-radius+12,cx+radius-12,cy+radius-12),
              200,310,fill=(203,245,246,196),width=9)
    stage.alpha_composite(overlay)


def _stream(stage: Image.Image, t: float, *, bend: bool = False) -> None:
    d = ImageDraw.Draw(stage, "RGBA")
    for i in range(75):
        phase = (i*.11+t*(.35+i%5*.027))%1.0
        x = round(90+phase*990)
        y = round(380+(i%13)*45+19*math.sin(phase*6+i*.63))
        if bend:
            y += round(155*math.sin(phase*math.pi))
        colour = ((128,228,255,175) if i%3 else (219,176,255,186))
        d.line((x-26,y-7,x,y),fill=colour,width=2)
        d.ellipse((x-3,y-3,x+3,y+3),fill=(232,249,255,230))


def _field(stage: Image.Image,t:float) -> None:
    d=ImageDraw.Draw(stage,"RGBA")
    cx,cy=660,660
    for ring in range(5):
        rx=round(185+ring*73)
        ry=round(270+ring*70)
        d.arc((cx-rx,cy-ry,cx+rx,cy+ry),
              57,303,fill=(90,205,238,103-ring*13),width=3)
        d.arc((cx-rx,cy-ry,cx+rx,cy+ry),
              236,487,fill=(118,209,240,103-ring*13),width=3)
    for i in range(34):
        theta=i*.38+t*.93
        radius=250+i%7*35
        x=cx+radius*math.cos(theta)
        y=cy+min(365,radius*1.35)*math.sin(theta)
        d.ellipse((x-4,y-4,x+4,y+4),
                  fill=(151,242,229,235))


def _molecules(stage:Image.Image,t:float, *, photons:bool=False) -> None:
    glows=Image.new("RGBA",STAGE_SIZE)
    gd=ImageDraw.Draw(glows)
    for index in range(13):
        x=120+(index%5)*209+29*math.sin(t*.35+index)
        y=365+(index//5)*265+38*math.sin(t*.73+index*.72)
        q=math.sin(t*3.2+index*1.31)
        radius=21+(index%3)*6
        tint=((91,240,143) if index%4 else (159,98,246))
        strength=max(0.,q)**2
        if photons:
            gd.ellipse((x-84,y-84,x+84,y+84),
                       fill=(*tint,round(55+110*strength)))
        gd.ellipse((x-radius,y-radius,x+radius,y+radius),
                   fill=(*tint,175+round(60*strength)))
        gd.ellipse((x-9,y-9,x+9,y+9),fill=(228,255,239,235))
        if photons:
            for j in range(3):
                theta=(j*2.09+index*.2)
                rr=30+((t*78+index*19+j*32)%145)
                xx=x+math.cos(theta)*rr
                yy=y+math.sin(theta)*rr
                gd.ellipse((xx-4,yy-4,xx+4,yy+4),
                           fill=(*tint,165))
    blurred=glows.filter(ImageFilter.GaussianBlur(16))
    stage.alpha_composite(blurred)
    stage.alpha_composite(glows)
    if not photons:
        _stream(stage,t,bend=True)


def _curtains(stage:Image.Image,t:float, duration:float) -> None:
    """Several smooth colored curtains, flowing independently at 30 FPS."""
    # Low-res glow field permits smooth volumetric light on free CPU runners.
    field=Image.new("RGBA",(540,690))
    fd=ImageDraw.Draw(field,"RGBA")
    palettes=((31,207,140),(55,247,158),(34,154,218),
              (111,79,221),(48,219,162),(30,165,190))
    for layer in range(6):
        points=[]
        head=[]
        upper=75+layer*48
        phase=t*(.25+layer*.026)+layer*.69
        for x in range(-32,574,12):
            sway=43*math.sin(x*.0088+phase)+18*math.sin(x*.018-phase*.76)
            y=upper+sway+13*math.cos(x*.004+layer)
            depth=155+layer*8+22*math.sin(x*.013+t*.41+layer)
            head.append((round(x),round(y)))
            points.append((round(x),round(y+depth)))
        shade=palettes[layer]
        fd.polygon(head+list(reversed(points)),
                   fill=(*shade,29 if layer%2 else 45))
        fd.line(head,fill=(*shade,112),width=4)
        for j in range(16):
            xx=-22+j*37
            yy=upper+43*math.sin(xx*.0088+phase)+13*math.cos(xx*.004+layer)
            fd.line((xx,yy,xx+14,yy+140+24*math.sin(t*.6+j)),
                    fill=(*shade,53),width=1)
    # A blurred volumetric base + crisp translucent filaments for depth.
    haze=field.filter(ImageFilter.GaussianBlur(15))
    stage.alpha_composite(haze.resize(STAGE_SIZE,Image.Resampling.BILINEAR))
    stage.alpha_composite(field.resize(STAGE_SIZE,Image.Resampling.BILINEAR))
    # Moving foreground stars / reflected lake highlights beneath curtains.
    d=ImageDraw.Draw(stage,"RGBA")
    for i in range(24):
        x=(i*113+t*(10+i%3*6))%1180-50
        y=1030+(i%4)*25
        length=8+(i*7)%32
        d.line((x,y,x+length,y),fill=(76,208,167,66),width=2)


def draw_aurora(picture: Image.Image,beat:str,t:float,duration:float,
                english:bool) -> None:
    if (picture.mode!="RGBA" or picture.size!=(1080,1920)
            or beat not in BEATS or type(english) is not bool
            or type(t) not in (int,float) or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0<duration<=180 or not 0<=t<=duration):
        raise ValueError("Invalid aurora science frame")
    stage = _plate(night=beat=="curtains").copy()
    if beat=="solar_wind":
        _sphere(stage,214,530,128,sunlight=True)
        _stream(stage,t)
        _sphere(stage,930,650,102)
    elif beat=="magnetic_field":
        _sphere(stage,660,660,149)
        _field(stage,t)
        _stream(stage,t,bend=True)
    elif beat=="collisions":
        _molecules(stage,t)
    elif beat=="emission":
        _molecules(stage,t,photons=True)
    else:
        _curtains(stage,t,duration)
    picture.alpha_composite(reframe(stage, "aurora", beat, t, duration),
                            (0,STAGE_TOP))
