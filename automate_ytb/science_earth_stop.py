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
from functools import lru_cache
from typing import Callable

from PIL import Image, ImageDraw, ImageFilter

from .science_motion import _font
from .earth_kinetic_fx import draw_foreground
from .earth_cinematic_depth import draw_depth_behind, draw_depth_above
from .earth_story_actions import draw_story_actions
from .science_city3d import draw_city_mesh
from .science_people3d import draw_wind_actors3d
from .science_vehicle3d import draw_vehicle3d

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



@lru_cache(maxsize=4)
def _storm_cloud_sprite(kind: int) -> Image.Image:
    """Cached original soft storm cloud; no flat opaque cyan ellipses.

    The alpha mask is blurred before compositing. Tiny color variation in the
    cloud lobes provides depth while keeping the city and gust visible below.
    """
    if type(kind) is not int or not 0 <= kind < 4:
        raise ValueError("Unsafe cloud style")
    plate=Image.new("RGBA",(298,128))
    d=ImageDraw.Draw(plate)
    for k,(cx,cy,rx,ry) in enumerate(
        ((53,75,51,21),(112,64,73,31),(174,70,78,33),(245,82,51,22))):
        shift=(kind*13+k*7)%17
        d.ellipse((cx-rx,cy-ry-shift//3,cx+rx,cy+ry-shift//3),
                  fill=(125+kind*7,167+kind*6,193+kind*5,42+k*5))
    # Add small wisps to avoid four identical round, featureless sheets.
    for k in range(7):
        x=19+k*37
        y=70+10*math.sin(k*1.4+kind)
        d.ellipse((x-24,y-9,x+45,y+10),
                  fill=(173,205,218,21+k%3*4))
    return plate.filter(ImageFilter.GaussianBlur(13))


def _storm_clouds(picture: Image.Image, t: float) -> None:
    """Move cloud masses at independently paced 2.5D atmospheric depths."""
    for i,(x,y) in enumerate(((65,685),(296,768),(506,816),(731,716))):
        dx=round(18*math.sin(t*(.18+i*.07)+i))
        dy=round(8*math.sin(t*(.24+i*.08)+i*1.13))
        picture.alpha_composite(_storm_cloud_sprite(i),(x+dx,y+dy))


def _globe(picture: Image.Image, globe_at: Callable, t: float, duration: float,
           *, stopped: bool = False, frozen: bool = False,
           diameter: int = 620):
    u = t / duration
    # Use the same orientation at the end of deceleration and throughout
    # every later beat. The previous code incorrectly jumped back to yaw 0.
    # All angles are illustrative and not a geophysical simulation.
    final_pose = 15.0
    spin = (final_pose if frozen else
            final_pose*(2*u-u*u) if stopped else t*4)
    planet = globe_at(spin, size=diameter)
    cx = 540 + round(20*math.sin(t*.35))
    cy = 1017 + round(14*math.sin(t*.54))
    picture.alpha_composite(planet, (cx-diameter//2, cy-diameter//2))
    return cx, cy


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
    draw_depth_behind(picture, beat, t, duration)
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
        draw_city_mesh(picture, beat, t, duration)
        d = ImageDraw.Draw(picture, "RGBA")
        draw_vehicle3d(picture,t,duration)
        d = ImageDraw.Draw(picture,"RGBA")
        _arrow(d,166,735,round(500*_ease(u)),GOLD)
    elif beat == "wind":
        draw_city_mesh(picture, beat, t, duration)
        d = ImageDraw.Draw(picture, "RGBA")
        for j in range(7):
            x=(t*(148+j*28)+j*311)%1580-440
            y=717+j*77
            d.arc((x,y-48,x+340,y+72),184,345,
                  fill=(130+j*3,217,250,174),width=6)
            _arrow(d,x+225,y+15,67,CYAN,4)
        _storm_clouds(picture,t)
        for j in range(30):
            x=(j*163+t*(280+j%6*39))%1300-105
            y=930+j%9*33
            d.line((x,y,x+39,y-4),fill=(231,239,238,120),width=3)
    elif beat == "ocean":
        draw_city_mesh(picture, beat, t, duration)
        d = ImageDraw.Draw(picture, "RGBA")
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
    # Story-specific foreground motions depend on the same continuous clock.
    # They materially interact with the shown subject rather than merely
    # panning a generic still image behind subtitles.
    draw_foreground(picture, beat, t, duration)
    draw_story_actions(picture, beat, t, duration)
    if beat == "wind":
        draw_wind_actors3d(picture, t, duration)
    draw_depth_above(picture, beat, t, duration)
    # Non-physical schematic warning stays clear of narration captions.
    d=ImageDraw.Draw(picture,"RGBA")
    notice="SCHEMATIC • NOT TO SCALE" if english else "SCHÉMA • PAS À L'ÉCHELLE"
    d.text((102,1474),notice,font=_font(25,True),
           fill=(173,222,238,210))
