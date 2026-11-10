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
from .flow_banks25d import advancing_path, draw_organic_flow
from .fluid_emitter25d import emitter_frame
from .semantic_geometry25d import render_material_sheet

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

_LAVA_ROUTES=(
        [(540,356),(584,429),(635,505),(670,589),(731,660),
         (770,727),(823,797),(871,873),(937,941),(1020,1002),
         (1080,1030)],
        [(530,355),(493,430),(459,493),(414,578),(374,655),
         (316,729),(276,794),(215,863),(145,929),(72,993),(0,1040)],
    )


@lru_cache(maxsize=2)
def _lava_track(side:int)->tuple[tuple[float,float],...]:
    """Precompute authored physical channels once, not 30 times a second."""
    if type(side) is not int or side not in (0,1):
        raise ValueError("Invalid original lava drainage branch")
    route=_LAVA_ROUTES[side]
    track=[route[0]]
    for segment,(a,b) in enumerate(zip(route,route[1:])):
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=max(1.,math.hypot(dx,dy))
        normal=(-dy/length,dx/length)
        for sub in range(1,6):
            u=sub/5
            wiggle=(8.4+side*3)*math.sin(math.pi*u)*math.sin(
                (segment+u)*1.68+side*.63)
            track.append((
                a[0]+dx*u+normal[0]*wiggle,
                a[1]+dy*u+normal[1]*wiggle))
    return tuple(track)


def _lava(stage:Image.Image,t:float,duration:float)->None:
    """Eroded rock-bound magma flow with fully shared causal surface banks."""
    d=ImageDraw.Draw(stage,"RGBA")
    for side in (0,1):
        track=_lava_track(side)
        amount=min(1.,t/duration*(1.07+side*.06))
        visible=advancing_path(track,amount)
        # No fictional molten flow has emerged at the start of this beat.
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
        # Source-anchored, nonuniform rock banks and moving crust replace
        # equal-width presentation ribbons and circular painted flow caps.
        # Identical geometry is reused by actual ocean current shear below.
        draw_organic_flow(d,visible,material="magma",width=63,
                          t=t,duration=duration,seed=8031+side*287)

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
        # Atmospheric ash becomes a distinct, slowly evolving foreground
        # source silhouette only during the eruption (never in calm beats).
        # It is behind the crater-origin plume and causal incandescent jets.
        stage.alpha_composite(render_material_sheet(
            SIZE,material="ash",color=(112,123,134),
            seed=44801,t=t,duration=duration,
            baseline=144,thickness=205,
            opacity=round(14+49*t/duration)))
        _explosion(stage,t,duration)
    else:
        _lava(stage,t,duration)
    # Camera movement follows the narrated geological event; UI remains fixed.
    picture.alpha_composite(reframe(stage, "volcano", beat, t, duration,
                                    event_progress=event_progress), (0,TOP))
