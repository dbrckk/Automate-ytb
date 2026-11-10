"""Original continuous volcanic-science 9:16 animations, fully CPU rendered.

Causal schematic: molten magma, gas pressure, ascent, ash/ejecta, and lava.
No stock footage, third-party images, neural rendering or paid model.
"""
from __future__ import annotations

from functools import lru_cache
import math
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter

from .science_stage_director import reframe, VERSION as DIRECTOR_VERSION
from .science_volcano_mesh import CONE_OUTLINE, shaded_terrain, TERRAIN_VERSION
from .science_volcano_lighting import illuminate_rock, VERSION as LIGHTING_VERSION
from .science_volcano_plume import draw_ash, draw_ejecta, VERSION as PLUME_VERSION
from .science_volcano_magma import draw_magma, VERSION as MAGMA_VERSION
from .volcanic_conduit25d import draw_rock_conduit
from .volcanic_reservoir25d import reservoir_rock_source
from .organic_environment25d import terrain_strata, cloud_bank, drifting_cloud_bank
from .material_ribbons25d import draw_material_ribbon
from .fluid_emitter25d import emitter_frame

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
    # An actual volcanic sky contains diffuse ash haze and dust rather than
    # the tiny stars used in orbital scenes. Build this source plane once.
    haze=Image.new("RGBA",SIZE)
    hd=ImageDraw.Draw(haze,"RGBA")
    hd.ellipse((-220,40,670,535),fill=(91,105,119,46))
    hd.ellipse((460,0,1330,470),fill=(124,104,102,28))
    hd.ellipse((40,185,950,680),fill=(64,82,96,34))
    frame.alpha_composite(haze.filter(ImageFilter.GaussianBlur(95)))
    # Independent distant eroded strata replace the zig-zag background
    # hillside. The exact same reusable original 2.5D asset family also
    # appears in underwater geology and future natural landscapes.
    frame.alpha_composite(terrain_strata(
        (1080,560),seed=18401,color=(55,73,82),opacity=165),(0,530))
    frame.alpha_composite(cloud_bank(
        (1080,370),seed=18437,color=(93,114,130),opacity=56),(0,100))
    # Properly projected 3D terrain, computed once. The dark solid core
    # remains behind it to keep underground/cutaway shots watertight.
    # The mountain merges into the established distant rocky foothills.
    # Do not extrude a flat opaque cone all the way to the bottom of frame.
    foundation = (*CONE_OUTLINE[:-2], (1080, 1080), (0, 1080))
    d.polygon(foundation, fill=(28, 31, 41, 255))
    frame.alpha_composite(shaded_terrain())
    d = ImageDraw.Draw(frame)
    if not section:
        # This foreground occlusion conceals the open 3D shell's lower rim,
        # preserving rock depth and leaving the erupting summit exposed.
        d.polygon([(0, 1054), (122, 1017), (247, 1056),
                   (371, 1029), (491, 1051), (622, 1016),
                   (750, 1058), (870, 1032), (993, 1059),
                   (1080, 1038), (1080, 1380), (0, 1380)],
                  fill=(17, 25, 37, 255))
        d.line([(0, 1054), (122, 1017), (247, 1056),
                (371, 1029), (491, 1051), (622, 1016),
                (750, 1058), (870, 1032), (993, 1059),
                (1080, 1038)], fill=(75, 68, 66, 106), width=2)
    # Material-aware crater rim rather than a perfectly elliptical icon.
    # The centered opening remains at 540,345 for every magma/ash effect.
    crater=[]
    for k in range(40):
        angle=k*math.tau/40
        x=540+(34+2.5*math.sin(7*angle))*math.cos(angle)
        y=345+(11+1.8*math.sin(9*angle+.4))*math.sin(angle)
        crater.append((round(x),round(y)))
    d.polygon(crater,fill=(20,18,23,255))
    d.line(crater[:22],fill=(169,124,101,223),width=4,joint="curve")
    d.line(crater[19:37],fill=(68,56,55,255),width=3,joint="curve")
    if section:
        d.polygon([(0,823),(170,844),(342,818),(501,843),
                   (700,813),(870,831),(1080,804),
                   (1080,1380),(0,1380)],fill=(27,24,32,246))
        for i in range(5):
            y=875+i*89
            d.line([(0,y),(165,y-19),(335,y+9),(525,y-16),
                    (700,y+13),(900,y-8),(1080,y+11)],
                   fill=(89,66,66,105),width=3)
        # This curved rock channel and the ascending molten material are
        # generated from a single shared physical centerline and mask.
        draw_rock_conduit(d)
        # Original volcanic reservoir and its molten/gas interior share the
        # same irregular authored source boundary. No perfect ellipse.
        frame.alpha_composite(reservoir_rock_source())
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


def _explosion(stage:Image.Image,t:float,duration:float)->None:
    """Crater-origin glowing vent, continuously turbulent ash and tephra."""
    illuminate_rock(stage,[(540,345,330,.78+.22*math.sin(t*3.8)**2)])
    _glow(stage,[(540,345,182+34*math.sin(t*2.2)**2)])
    # Billows rise from the same summit as the red-hot vent, gradually
    # evolving into a drifting column; distant soft layers underlay ejecta.
    draw_ash(stage,t,duration)
    # Same original moving-fluid source engine as wind-driven sea spray.
    # The magma jet anchor (150,263) maps precisely to the (540,345)
    # volcanic crater, rather than three impossible rigid vertical lines.
    stage.alpha_composite(
        emitter_frame((300,280),t,duration,material="magma",seed=3207),
        (390,82))
    draw_ejecta(stage,t,duration)

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
        # At t=0 the eruption has no visible flowing length. A zero-length
        # path is not a real illuminated ribbon and must not be fabricated.
        if len(visible)<2 or math.dist(visible[0],visible[-1])<.001:
            continue
        # Moving incandescent lava illuminates only actual 3D rock faces.
        sources=[(*visible[j],88,.71)
                 for j in range(0,len(visible),max(1,len(visible)//5))]
        sources.append((*visible[-1],164,1.0))
        illuminate_rock(stage,sources)
        # Light into the ground before painting sharp layered lava contours.
        leading=visible[-1]
        lights=[(*leading,67)]
        lights.extend((*visible[j],42)
                      for j in range(0,len(visible),max(1,len(visible)//6)))
        _glow(stage,lights)
        d=ImageDraw.Draw(stage,"RGBA")
        # The advancing magma ribbon uses the SAME renderer as rainbow
        # rays and ocean currents, with heat-colored painter's depth,
        # a molten core and a short bright front attached to its path.
        draw_material_ribbon(d,visible,material="magma",
                             color=(246,118,39,253),width=63,
                             progress=.98)
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
                 english:bool, *, event_progress:float|None=None)->None:
    if (picture.mode!="RGBA" or picture.size!=(1080,1920)
            or beat not in BEATS or type(english) is not bool
            or type(t) not in (int,float) or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0<duration<=180 or not 0<=t<=duration):
        raise ValueError("Invalid original volcano frame")
    stage=_base(section=beat in ("magma","pressure","ascent")).copy()
    # A separate foreground atmosphere layer moves independently of the
    # cached far-off cloud strata; it stays ABOVE the mountain summit only
    # in the source sky and BELOW the eruption/plume and other physical FX.
    stage.alpha_composite(drifting_cloud_bank(
        (1080, 250), 19147, t, color=(112, 139, 156),
        opacity=72, speed=.74, phase=1.26), (0, 26))
    if beat in ("magma","pressure","ascent"):
        draw_magma(stage,beat,t,duration)
    elif beat=="eruption":
        _explosion(stage,t,duration)
    else:
        _lava(stage,t,duration)
    # Camera movement follows the narrated geological event; UI remains fixed.
    picture.alpha_composite(reframe(stage, "volcano", beat, t, duration,
                                    event_progress=event_progress), (0,TOP))
