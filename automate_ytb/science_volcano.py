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
from .science_volcano_mesh import CONE_OUTLINE, shaded_terrain, TERRAIN_VERSION

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
    # Properly projected 3D terrain, computed once. The dark solid core
    # remains behind it to keep underground/cutaway shots watertight.
    d.polygon(CONE_OUTLINE, fill=(27, 29, 39, 255))
    frame.alpha_composite(shaded_terrain())
    d = ImageDraw.Draw(frame)
    # Dark inner crater and an irregular illuminated rock rim.
    d.ellipse((507, 335, 569, 355), fill=(19, 17, 22, 255))
    d.arc((500, 331, 576, 366), 185, 350,
          fill=(143, 108, 92, 234), width=5)
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
    """Advancing, rock-guided meandering molten rivers with animated hot cores.

    Meanders are *spatially stable* while molten fronts advance: the terrain
    never warps to pretend it is liquid. Independent incandescent tracers and
    spreading heat run along the same authored tracks.
    """
    d=ImageDraw.Draw(stage,"RGBA")
    rough_routes=(
        [(540,356),(584,429),(635,505),(670,589),(731,660),
         (770,727),(823,797),(871,873),(937,941),(1020,1002),
         (1080,1030)],
        [(530,355),(493,430),(459,493),(414,578),(374,655),
         (316,729),(276,794),(215,863),(145,929),(72,993),(0,1040)],
    )
    for side,route in enumerate(rough_routes):
        # Smooth curves with bounded local variations (4 samples/segment).
        # This prevents the previous long, straight glowing staircases.
        track=[route[0]]
        for segment,(a,b) in enumerate(zip(route,route[1:])):
            dx,dy=b[0]-a[0],b[1]-a[1]
            length=max(1,math.hypot(dx,dy))
            normal=(-dy/length,dx/length)
            for sub in range(1,6):
                u=sub/5
                wiggle=(8.4+side*3)*math.sin(math.pi*u)*math.sin(
                    (segment+u)*1.68+side*.63)
                track.append((
                    a[0]+dx*u+normal[0]*wiggle,
                    a[1]+dy*u+normal[1]*wiggle))
        amount=min(1.,t/duration*(1.07+side*.06))
        float_index=(len(track)-1)*amount
        index=int(float_index)
        visible=track[:index+1]
        if index<len(track)-1:
            p,q=track[index:index+2]
            u=float_index-index
            visible.append((p[0]+(q[0]-p[0])*u,
                            p[1]+(q[1]-p[1])*u))
        if len(visible)<2:
            continue
        # Light into the ground before painting sharp layered lava contours.
        leading=visible[-1]
        lights=[(*leading,67)]
        lights.extend((*visible[j],42)
                      for j in range(0,len(visible),max(1,len(visible)//6)))
        _glow(stage,lights)
        d=ImageDraw.Draw(stage,"RGBA")
        d.line(visible,fill=(15,12,19,253),width=73,joint="curve")
        d.line(visible,fill=(111,37,26,250),width=63,joint="curve")
        d.line(visible,fill=(209,64,21,252),width=47,joint="curve")
        d.line(visible,fill=(255,144,40,242),width=23,joint="curve")
        d.line(visible,fill=(255,231,132,220),width=7,joint="curve")
        # Cooling plates and glossy hot spots travel along existing channels,
        # never independently across the sky or outside the volcano.
        for grain in range(17):
            travel=(grain*.082+t*(.085+side*.018))%1.
            pos=travel*(len(visible)-1)
            j=min(int(pos),len(visible)-2)
            f=pos-j
            x=visible[j][0]*(1-f)+visible[j+1][0]*f
            y=visible[j][1]*(1-f)+visible[j+1][1]*f
            radius=2+(grain%4)
            d.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(255,237,151,200+grain%3*14))
            if grain%3==0:
                d.line((x-10,y-6,x+9,y+5),
                       fill=(48,22,24,145),width=4)
        # An expanding nose of magma has a bright cap and cooled edges.
        cx,cy=leading
        d.ellipse((cx-23,cy-22,cx+23,cy+22),
                  fill=(248,111,36,246))
        d.ellipse((cx-11,cy-10,cx+11,cy+10),
                  fill=(255,215,106,232))
    # A few localized heat flecks above the moving lava (not uniform noise).
    for i in range(30):
        progress=(t*(.06+i%5*.013)+i*.117)%1
        side=-1 if i%2 else 1
        x=540+side*progress*430
        y=355+progress*540-16-16*math.sin(t*.9+i)
        radius=2+i%3
        d.ellipse((x-radius,y-radius,x+radius,y+radius),
                  fill=(255,155+i%3*17,66,108))

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
