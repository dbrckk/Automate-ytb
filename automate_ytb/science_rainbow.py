"""Original native-portrait atmospheric-optics storyboards for rainbow science.

The primary rainbow is illustrated qualitatively: white sunlight disperses
on entering spherical water droplets, part reflects internally, rays refract
again as they emerge, and the observer sees an angular color distribution.
No optical ray-tracing simulation or geographically correct observation is
claimed. No external assets, models, network requests or paid API credits.
"""
from __future__ import annotations

import math
import random
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter

from .science_motion import _font

BEATS = ("sunlight", "refraction", "reflection", "emergence", "arc")
BADGES = {
    "sunlight": ("WHITE SUNLIGHT", "LUMIÈRE BLANCHE"),
    "refraction": ("FIRST REFRACTION", "PREMIÈRE RÉFRACTION"),
    "reflection": ("INTERNAL REFLECTION", "RÉFLEXION INTERNE"),
    "emergence": ("SECOND REFRACTION", "SECONDE RÉFRACTION"),
    "arc": ("THE RAINBOW ARC", "L'ARC-EN-CIEL"),
}
SPECTRUM = (
    (254, 102, 103, 240), (251, 158, 82, 240),
    (253, 226, 115, 240), (137, 231, 147, 240),
    (107, 195, 255, 240), (118, 129, 247, 240),
    (183, 130, 252, 240),
)
ICE = (192, 239, 251, 238)
WHITE = (235, 249, 255, 255)
INK = (9, 24, 48, 255)
GOLD = (254, 201, 109, 245)


def daylight_background(seed: int) -> Image.Image:
    """One-time atmospheric blue-sky plate: no stars behind daytime optics."""
    if type(seed) is not int:
        raise ValueError("Rainbow background needs a deterministic integer seed")
    w,h=1080,1920
    plate=Image.new("RGBA",(w,h))
    draw=ImageDraw.Draw(plate)
    for y in range(h):
        p=y/(h-1)
        draw.line((0,y,w,y),
                  fill=(round(9+27*p),round(56+68*p),
                        round(110+56*p),255),width=1)
    rng=random.Random(seed)
    haze=Image.new("RGBA",(w,h))
    hd=ImageDraw.Draw(haze)
    for index in range(9):
        cx=rng.randint(70,w-70)
        cy=rng.randint(480,1590)
        rx=rng.randint(98,205)
        ry=rng.randint(29,67)
        hd.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),
                   fill=(215,245,253,22+index%3*6))
    return Image.alpha_composite(
        plate,haze.filter(ImageFilter.GaussianBlur(35)))


def _plain(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def supports_topic(topic: str) -> bool:
    """Only visibly supported rainbows, not arbitrary sky/space questions."""
    if not isinstance(topic, str):
        raise ValueError("Rainbow science requires an authored topic")
    return bool(re.search(r"\b(rainbows?|arcs?[- ]en[- ]ciel)\b",
                          _plain(topic)))


def classify(topic: str, narration: str) -> str | None:
    """Select a known optical concept by narration semantics, not scene index.

    Only a literal authored rainbow topic is opted in. Unknown or vague
    phrases return None and must not silently turn into invented physics.
    """
    if not isinstance(topic, str) or not isinstance(narration, str):
        raise ValueError("Rainbow science requires authored text")
    if not supports_topic(topic):
        return None
    text = _plain(narration)
    # Explicit phase verbs outrank incidental past-tense words: a ray can
    # be "reflected" yet be currently LEAVING the drop.
    if re.search(r"\b(leav\w*|exit\w*|emerg\w*|second|sort\w*|ressort\w*)\b", text):
        return "emergence"
    if re.search(r"\b(reflect\w*|reflection|reflech\w*|reflexion)\b", text):
        return "reflection"
    if re.search(r"\b(enter\w*|refract\w*|bend\w*|bends|entre\w*|penetre\w*)\b", text):
        return "refraction"
    # A million droplets or an explicit rainbow/observer identifies the
    # final observed arc, even when the sentence also mentions sunlight.
    if re.search(r"\b(million\w*|rainbows?|arcs?|observer|observat\w*)\b", text):
        return "arc"
    # A sentence about WHITE sunlight can mention our EYES without being
    # a scene about the rainbow arc. Eyes alone are the weakest clue.
    if re.search(r"\b(sun\w*|white|color\w*|light|soleil|blanc\w*|couleur\w*|lumiere)\b", text):
        return "sunlight"
    if re.search(r"\b(eyes?|yeux)\b", text):
        return "arc"
    return None


def _label(draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
           *, color=WHITE, size: int = 35) -> None:
    draw.text((x, y), text, fill=color, font=_font(size, True))


def _ray(draw: ImageDraw.ImageDraw, start: tuple[float, float],
         finish: tuple[float, float], color, *,
         t: float, speed: float = .25, phase: float = 0., width: int = 8) -> None:
    """Layer a beam and a continuously moving photon tracer on the same line."""
    x0, y0 = start
    x1, y1 = finish
    draw.line((x0, y0, x1, y1),
              fill=(color[0], color[1], color[2], 46), width=width+12)
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    position = (t*speed+phase)%1.
    px, py = round(x0+(x1-x0)*position), round(y0+(y1-y0)*position)
    draw.ellipse((px-8, py-8, px+8, py+8), fill=WHITE)


def _drop(draw: ImageDraw.ImageDraw, x: int, y: int, r: int = 230) -> None:
    """Spherical water droplet, not a teardrop or a flat prism."""
    draw.ellipse((x-r-18,y-r-18,x+r+18,y+r+18),
                 fill=(56, 169, 211, 23))
    draw.ellipse((x-r,y-r,x+r,y+r), fill=(21, 89, 147, 105),
                 outline=(174, 239, 252, 225), width=7)
    draw.arc((x-r+18,y-r+18,x+r-18,y+r-18), 195, 292,
             fill=(246, 254, 255, 170), width=9)
    draw.arc((x-r+33,y-r+33,x+r-33,y+r-33), 5, 76,
             fill=(73, 173, 241, 170), width=10)
    for ox,oy,rr in ((-74,-112,8),(-57,-116,4),(100,86,5)):
        xx, yy=x+ox,y+oy
        draw.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=WHITE)


def _sunlight(draw: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    sunx,suny=252,1013
    for radius,alpha in ((190,23),(152,40),(119,83)):
        draw.ellipse((sunx-radius,suny-radius,sunx+radius,suny+radius),
                     fill=(255,193,99,alpha))
    draw.ellipse((sunx-86,suny-86,sunx+86,suny+86),
                 fill=(255,220,130,255))
    for n in range(14):
        angle=math.tau*n/14+t*.18
        a=(sunx+105*math.cos(angle),suny+105*math.sin(angle))
        b=(sunx+135*math.cos(angle),suny+135*math.sin(angle))
        draw.line((*a,*b),fill=GOLD,width=5)
    _ray(draw,(357,1013),(626,1013),WHITE,t=t,speed=.29,width=11)
    # White light contains a continuum of visible wavelengths. The seven
    # discrete stripes communicate dispersion but do not claim seven
    # physically separate frequencies.
    draw.rounded_rectangle((627,953,716,1075),radius=19,
                           fill=(84,161,220,60),outline=ICE,width=4)
    for i,color in enumerate(SPECTRUM):
        y=884+i*57
        _ray(draw,(716,1013),(924,y),color,t=t,speed=.18,phase=i/10,width=5)
    _label(draw,146,1378,
           "WHITE LIGHT CONTAINS COLORS" if english else
           "LA LUMIÈRE CONTIENT DES COULEURS",size=32)


def _refraction(draw: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    _drop(draw,630,1070,229)
    _ray(draw,(137,935),(410,965),WHITE,t=t,speed=.28,width=11)
    for i,color in enumerate(SPECTRUM):
        # Refraction inside water is schematic: wavelengths deviate
        # slightly differently, never crossing the subtitle band.
        _ray(draw,(414,962),(819,1045+(i-3)*16),color,
             t=t,speed=.27,phase=i*.11,width=5)
    draw.ellipse((403,949,426,972),fill=GOLD)
    _label(draw,143,1365,"LIGHT BENDS IN WATER" if english else
           "LA LUMIÈRE SE COURBE DANS L'EAU",size=33)


def _reflection(draw: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    _drop(draw,603,1068,234)
    for i,color in enumerate(SPECTRUM):
        sy=918+i*11
        _ray(draw,(386,sy),(798,1000+i*9),color,t=t,
             speed=.24,phase=i*.07,width=4)
        # Partial internal reflection on the far, back interface.
        _ray(draw,(798,1000+i*9),(474,1232-i*5),color,t=t,
             speed=.22,phase=.43+i*.08,width=4)
    _label(draw,152,1380,"LIGHT REFLECTS INSIDE" if english else
           "LA LUMIÈRE SE RÉFLÉCHIT",size=34)


def _emergence(draw: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    _drop(draw,615,1065,226)
    for i,color in enumerate(SPECTRUM):
        _ray(draw,(796,999+i*10),(441,1188-i*8),color,
             t=t,speed=.22,phase=i*.09,width=5)
        # Emerging diverging colored rays face the observer's side.
        _ray(draw,(441,1188-i*8),(146,1244+(i-3)*25),color,
             t=t,speed=.24,phase=.25+i*.1,width=6)
    draw.ellipse((424,1168,455,1199),outline=WHITE,width=4)
    _label(draw,145,1380,"COLORS EXIT AT DIFFERENT ANGLES" if english else
           "SORTIE À DES ANGLES DIFFÉRENTS",size=30)


def _arc(draw: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    center_x,center_y=540,1296
    # A primary rainbow is a cone around the antisolar direction. The
    # arch is a visual projection of that cone, not a literal rainbow
    # object situated at a single distance.
    for i,color in enumerate(SPECTRUM):
        radius=475-i*19
        draw.arc((center_x-radius,center_y-radius,
                  center_x+radius,center_y+radius),
                 197,343,fill=color,width=15)
    for k in range(8):
        radius=475-(k%7)*19
        theta=math.radians(197+(146*((t*.08+k*.13)%1)))
        x=center_x+radius*math.cos(theta)
        y=center_y+radius*math.sin(theta)
        draw.ellipse((x-5,y-5,x+5,y+5),fill=WHITE)
    # Observer whose eyes receive selected angles from different drops.
    draw.ellipse((513,1335,567,1389),
                 fill=(184,218,243,240))
    draw.line((540,1385,540,1470),fill=ICE,width=15)
    draw.line((540,1418,510,1462),fill=ICE,width=9)
    draw.line((540,1418,570,1462),fill=ICE,width=9)
    for dx,dy in ((-314,-252),(294,-247)):
        _drop_small_x,_drop_small_y=center_x+dx,center_y+dy
        draw.ellipse((_drop_small_x-18,_drop_small_y-18,
                      _drop_small_x+18,_drop_small_y+18),
                     fill=(96,193,241,170),outline=ICE,width=3)
        _ray(draw,(_drop_small_x,_drop_small_y),(540,1353),
             SPECTRUM[0] if dx<0 else SPECTRUM[-1],
             t=t,speed=.21,phase=.35,width=3)
    _label(draw,147,1408,
           "MANY DROPS · ONE ARC" if english else
           "DES GOUTTES · UN ARC",size=31)


def draw_rainbow(draw: ImageDraw.ImageDraw, beat: str,
                 t: float, duration: float, english: bool) -> None:
    """Draw one of five original rainbow mechanisms at native 9:16 resolution."""
    if (beat not in BEATS or type(t) not in (int,float)
            or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration
            or type(english) is not bool):
        raise ValueError("Invalid rainbow storyboard time or concept")
    draw.rounded_rectangle((80,600,1000,1490),radius=41,
                           fill=(6,34,64,238),
                           outline=(108,200,239,157),width=3)
    for n in range(8):
        x=156+n*108
        draw.line((x,696,x,1467),fill=(99,164,202,25),width=1)
    for n in range(7):
        y=770+n*100
        draw.line((102,y,978,y),fill=(99,164,202,25),width=1)
    _label(draw,115,630,
           "OPTICS · SCHEMATIC · NOT TO SCALE" if english else
           "OPTIQUE · SCHÉMA · HORS ÉCHELLE",size=27,
           color=(170,211,231,235))
    if beat=="sunlight":
        _sunlight(draw,t,english)
    elif beat=="refraction":
        _refraction(draw,t,english)
    elif beat=="reflection":
        _reflection(draw,t,english)
    elif beat=="emergence":
        _emergence(draw,t,english)
    else:
        _arc(draw,t,english)
