"""Narration-directed Earth rotation hypothetical: actual changing scene geometry.

These are original explanatory animations, not a numerical geophysics model.
The visible city, ocean, air, people and globe respond to narrated phenomena,
rather than looping stock photographs or generic zooms. All geometry is
deterministic and stays inside the portrait 9:16 editorial safe area.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Callable

from PIL import Image, ImageDraw

from .science_motion import _font

LABELS = {
    "stop": ("ROTATION STOPS", "ARRÊT DE LA ROTATION"),
    "inertia": ("MOMENTUM CONTINUES", "L'INERTIE CONTINUE"),
    "wind": ("AIR KEEPS MOVING", "L'AIR CONTINUE"),
    "ocean": ("OCEANS REACT", "RÉACTION DES OCÉANS"),
    "poles": ("OCEANS SHIFT POLEWARD", "LES OCÉANS VERS LES PÔLES"),
    "day": ("A VERY LONG DAY", "UN JOUR TRÈS LONG"),
    "astronaut": ("WHAT HAPPENS NEXT?", "ET ENSUITE ?"),
}
WHITE = (230, 248, 253, 245)
CYAN = (116, 224, 249, 225)
GOLD = (255, 202, 113, 240)
WATER = (36, 139, 205, 225)


def _plain(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def classify(topic: str, narration: str) -> str | None:
    """Require a topic about a stopped Earth, then match an authored cause."""
    if not isinstance(topic, str) or not isinstance(narration, str):
        raise ValueError("Earth animation needs original authored text")
    name, words = _plain(topic), _plain(narration)
    if not re.search(r"\b(earth|terre)\b", name):
        return None
    if not re.search(r"\b(stop|stops|stopped|stopping|halt|arret|arrete|cess|immobil|spin|spinning|rotation|tourner)\b", name):
        return None
    if re.search(r"\b(astronauts?|space suit|combinaison|survivors?|survival|survive|survived|safety|advice|conseil)\b", words):
        return "astronaut"
    if re.search(r"\b(poles?|polar|poleward|equatorial bulge|geoid|polaire|poles?|bourrelet|redistribut)\b", words):
        return "poles"
    if re.search(r"\b(oceans?|sea|seas|waves?|tsunami|flood|eaux?|vagues?|marees?)\b", words):
        return "ocean"
    if re.search(r"\b(air|winds?|atmosphere|vents?|tempete|storm)\b", words):
        return "wind"
    if re.search(r"\b(day|night|daylight|year|months?|jour|nuit|annee|mois|soleil)\b", words):
        return "day"
    if re.search(r"\b(equator|equateur|km|kilomet|speed|miles?|inertia|inertie|ground|sol|surface|momentum)\b", words):
        return "inertia"
    return "stop"


def _ease(u: float) -> float:
    u = min(1., max(0., u))
    return u*u*(3-2*u)


def _poly(d: ImageDraw.ImageDraw, pts, color, width: int = 4):
    d.line([(round(x), round(y)) for x, y in pts],
           fill=color, width=width, joint="curve")


def _star_motion(d: ImageDraw.ImageDraw, t: float, speed: float = 1.):
    # Small independent tracers move through the actual foreground, not a
    # panning still-photo plate.
    for i in range(28):
        x = 50 + (i*147 + t*(17+i%5*9)*speed) % 975
        y = 627 + (i*83) % 792
        d.ellipse((x-2,y-2,x+2,y+2),
                  fill=(162, 225, 253, 90+i%4*23))


def _globe(picture: Image.Image, globe_at: Callable, t: float, duration: float,
           *, stopped: bool = False, frozen: bool = False,
           diameter: int = 620):
    u = t / duration
    # Animated orientation integrates a slowing angular velocity, ending at
    # zero for an instantaneous-stop *visual analogy*, not a dynamics model.
    spin = (0.0 if frozen else
            5*duration*(u - .5*u*u) if stopped else t*4)
    planet = globe_at(spin, size=diameter)
    cx = 540 + round(20*math.sin(t*.35))
    cy = 1017 + round(14*math.sin(t*.54))
    picture.alpha_composite(planet, (cx-diameter//2, cy-diameter//2))
    return cx, cy


def _city(d: ImageDraw.ImageDraw, t: float, *, wind: bool = False):
    # Layer-specific translation supplies a continuous background/foreground
    # parallax without distorting the buildings themselves.
    for layer in range(2):
        shift = (t*(28 if layer else 10)) % 180
        floor = 1198 if layer == 0 else 1310
        color = (24, 58, 91, 210) if layer == 0 else (35, 95, 130, 243)
        for j in range(-2, 10):
            x = j*160 - shift
            h = 112 + ((j*53+layer*117) % 174)
            d.rectangle((x, floor-h, x+95+(j%3)*13, floor), fill=color)
            for wy in range(int(floor-h+25), int(floor-15), 36):
                for wx in range(int(x+15), int(x+82), 29):
                    d.rectangle((wx,wy,wx+8,wy+13),
                                fill=(173, 213, 224, 85))
    d.rectangle((0, 1310, 1080, 1450), fill=(15, 44, 66, 255))
    for i in range(9):
        x = (i*158 - t*210) % 1250 - 120
        d.rounded_rectangle((x,1381,x+75,1389),radius=3,
                            fill=(196, 235, 231, 125))


def _arrow(d: ImageDraw.ImageDraw, x, y, dx, color=GOLD, width: int = 8):
    d.line((x,y,x+dx,y),fill=color,width=width)
    s=1 if dx>=0 else -1
    d.polygon([(x+dx,y),(x+dx-s*23,y-13),(x+dx-s*23,y+13)],fill=color)


def draw(picture: Image.Image, beat: str, t: float, duration: float,
         english: bool, globe_at: Callable):
    """Mutate one RGBA native-portrait frame with a causally animated scene."""
    if (beat not in LABELS or type(t) not in (int,float) or
            type(duration) not in (int,float) or
            not math.isfinite(t) or not math.isfinite(duration) or
            not 0 <= t <= duration <= 180 or duration == 0 or
            picture.mode != "RGBA" or picture.size != (1080, 1920)):
        raise ValueError("Invalid Earth cinematic animation frame")
    d = ImageDraw.Draw(picture, "RGBA")
    u = t/duration
    _star_motion(d,t, .45 if beat in ("day", "poles") else 1.)
    if beat == "stop":
        cx,cy = _globe(picture,globe_at,t,duration,stopped=True)
        d = ImageDraw.Draw(picture,"RGBA")
        # Rotation gauge contracts at the same time that globe pose slows.
        for j in range(3):
            radius=338+j*28
            a=round(50+250*_ease(u))
            d.arc((cx-radius,cy-radius,cx+radius,cy+radius),
                  270+a, 440+a, fill=CYAN, width=max(2,6-j))
        for j in range(24):
            angle=(j/24)*math.tau + 4*u - 2*u*u
            r=382
            x,y=cx+r*math.cos(angle),cy+r*math.sin(angle)
            d.ellipse((x-4,y-4,x+4,y+4),fill=GOLD)
        _arrow(d,216,1433,round(600*(1-_ease(u))),GOLD)
    elif beat == "inertia":
        _city(d,t)
        dx = 160 + 570*_ease(u)
        yy = 1264 - 18*math.sin(t*5)
        # Moving object has relative motion to a moving city, not a zoom.
        d.rounded_rectangle((dx-81,yy-47,dx+85,yy+4),radius=13,
                            fill=(227, 154, 91, 248))
        d.polygon([(dx-39,yy-47),(dx-7,yy-77),(dx+48,yy-77),
                   (dx+77,yy-47)],fill=(107,206,227,248))
        for offset in (-46,48):
            d.ellipse((dx+offset-17,yy-7,dx+offset+17,yy+27),
                      fill=(13,22,35,255))
        for j in range(11):
            x=dx-120-j*45*(.5+u)
            y=yy-35+j%3*15
            d.line((x,y,x-35-j*3,y),
                   fill=(248,207,151,160),width=4)
        _arrow(d,166,735,round(500*_ease(u)),GOLD)
    elif beat == "wind":
        _city(d,t,wind=True)
        for j in range(7):
            x=(t*(148+j*28)+j*311)%1580-440
            y=717+j*77
            d.arc((x,y-48,x+340,y+72),184,345,
                  fill=(130+j*3,217,250,174),width=6)
            _arrow(d,x+225,y+15,67,CYAN,4)
        for j in range(4):
            cx=(j*380+t*(89+j*17))%1670-370
            cy=792+j%2*130
            d.ellipse((cx,cy,cx+300,cy+93),
                      fill=(115,160,191,110))
        for j in range(30):
            x=(j*163+t*(280+j%6*39))%1300-105
            y=930+j%9*33
            d.line((x,y,x+39,y-4),fill=(231,239,238,120),width=3)
    elif beat == "ocean":
        _city(d,t*.14)
        surge=_ease(u)
        for layer in range(3):
            base=1435-layer*52 - (385-layer*70)*surge
            points=[(0,1494)]
            amp=43+layer*12
            for x in range(0,1081,12):
                y=base + amp*math.sin(x/113 + t*(1.7+layer*.22)+layer)
                points.append((x,round(y)))
            points.append((1080,1494))
            c=[(19,87,165,231),(31,124,194,224),(77,187,226,190)][layer]
            d.polygon(points,fill=c)
            _poly(d,points[1:-1],(188,244,255,155),4)
        for j in range(26):
            x=(j*77+t*(42+j%4*17))%1050+10
            y=1293 - 300*surge +(j*83)%170
            d.ellipse((x,y,x+3+j%4,y+3+j%4),
                      fill=(221,250,251,150))
    elif beat == "poles":
        cx,cy=_globe(picture,globe_at,t,duration,frozen=True,diameter=600)
        d=ImageDraw.Draw(picture, "RGBA")
        # A deliberately schematic cross-section: arrows and water bands
        # converge toward two polar ends. Not a hydrodynamic prediction.
        for side in (-1,1):
            pole_y=cy+side*304
            d.arc((cx-317,cy-317,cx+317,cy+317),
                  (186 if side < 0 else 8),
                  (353 if side < 0 else 173),
                  fill=CYAN,width=7)
            for i in range(8):
                phase=(u*.88+i*.13)%1.
                theta=(1-phase)*math.pi*.40
                py=cy+side*(42+252*_ease(phase))
                px=cx+round((170+55*math.sin(i*1.75))*math.sin(theta))
                r=5+(i%3)
                d.ellipse((px-r,py-r,px+r,py+r),
                          fill=(135,235,253,220))
                d.ellipse((2*cx-px-r,py-r,2*cx-px+r,py+r),
                          fill=(135,235,253,220))
            tip_y=pole_y-side*47
            for offset in (-137,137):
                a_y=cy+side*106
                d.line((cx+offset,a_y,cx+offset*.35,tip_y),
                       fill=(172,240,248,180),width=5)
                d.polygon([(cx+offset*.35,tip_y),
                           (cx+offset*.35-13,tip_y-side*24),
                           (cx+offset*.35+13,tip_y-side*24)],fill=GOLD)
        for j in range(22):
            wave=(t*.31+j*.101)%1
            theta=(j%2)*math.pi
            y=cy+(-1 if j%2 else 1)*(80+wave*222)
            x=cx+round(300*math.sin(j*.33))*.42
            d.ellipse((x-3,y-3,x+3,y+3),fill=CYAN)
        d.text((175,1407),
               "LONG-TERM REDISTRIBUTION" if english else "DÉPLACEMENT À LONG TERME",
               font=_font(29,True),fill=WHITE)
    elif beat == "day":
        # After a stopped rotation, preserve the fixed orientation: orbital
        # illumination can change, but the globe must not keep spinning.
        cx,cy=_globe(picture,globe_at,t,duration,frozen=True,diameter=560)
        d=ImageDraw.Draw(picture,"RGBA")
        r=280
        d.pieslice((cx-r,cy-r,cx+r,cy+r),270,90,
                   fill=(4,12,29,120))
        sunx=210+int(60*math.sin(.6*t))
        d.ellipse((sunx-64,742,sunx+64,870),fill=GOLD)
        for k in range(12):
            angle=k*math.tau/12
            x1,y1=540+385*math.cos(angle),1017+385*math.sin(angle)
            x2,y2=540+410*math.cos(angle),1017+410*math.sin(angle)
            d.line((x1,y1,x2,y2),fill=CYAN,width=5)
        d.arc((123,595,953,1445),40,315,fill=CYAN,width=4)
        a=-math.pi/2 + .21*u
        _arrow(d,280,1411,round(440*(1-.38*u)),GOLD)
        d.line((540,1017,540+360*math.cos(a),1017+360*math.sin(a)),
               fill=GOLD,width=7)
    else:
        # Fully articulated, weightless astronaut instead of a static icon.
        cx=540+round(72*math.sin(t*.65))
        cy=1050+round(65*math.sin(t*.9))
        d.ellipse((cx-103,cy-182,cx+103,cy+23),fill=(232,245,254,235))
        d.ellipse((cx-80,cy-157,cx+80,cy-31),fill=(34,112,162,242))
        d.ellipse((cx-55,cy-132,cx-8,cy-111),fill=(200,248,255,180))
        d.rounded_rectangle((cx-95,cy-5,cx+95,cy+199),radius=40,
                            fill=(222,230,237,255),
                            outline=CYAN,width=5)
        d.rounded_rectangle((cx-52,cy+32,cx+52,cy+102),radius=18,
                            fill=(35,111,149,255))
        for side in (-1,1):
            angle=math.sin(t*1.7+side)*.6
            hx=cx+side*(155+27*math.sin(angle))
            hy=cy+42+53*math.cos(angle)
            d.line((cx+side*74,cy+42,hx,hy),
                   fill=(235,239,250,255),width=32)
            d.ellipse((hx-23,hy-23,hx+23,hy+23),fill=GOLD)
            footx=cx+side*(60+31*math.sin(t*1.4+side))
            footy=cy+294+29*math.sin(t*1.2+side)
            d.line((cx+side*46,cy+170,footx,footy),
                   fill=(228,239,248,255),width=39)
            d.rounded_rectangle((footx-31,footy-17,footx+31,footy+23),
                                radius=12,fill=(91,151,189,255))
    # Non-physical schematic warning stays clear of narration captions.
    d=ImageDraw.Draw(picture,"RGBA")
    notice="SCHEMATIC • NOT TO SCALE" if english else "SCHÉMA • PAS À L'ÉCHELLE"
    d.text((102,1474),notice,font=_font(25,True),
           fill=(173,222,238,210))
