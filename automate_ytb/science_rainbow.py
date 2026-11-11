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
from .organic_environment25d import drifting_cloud_bank
from .material_ribbons25d import draw_material_ribbon
from .hero_materials25d import glass_sphere, solar_disc
from .causal_action25d import action_phase, contributing_sources, ease

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
    backdrop=Image.alpha_composite(
        plate,haze.filter(ImageFilter.GaussianBlur(35)))
    # Sky and diffuse haze are the single cached, unmoving reference plate.
    # Independently animated multi-Z clouds are composited before scene
    # optics on every frame, not baked into this static background.
    return backdrop


def animate_daylight_clouds(picture: Image.Image, seed: int, t: float) -> None:
    """Two independent atmosphere depths; no title or caption repaint."""
    if (not isinstance(picture, Image.Image) or picture.mode != "RGBA"
            or picture.size != (1080, 1920) or type(seed) is not int):
        raise ValueError("Rainbow clouds need an original portrait canvas")
    picture.alpha_composite(drifting_cloud_bank(
        (1080, 480), seed % 900_000, t,
        color=(165, 213, 235), opacity=112, speed=.55, phase=.24), (0, 435))
    picture.alpha_composite(drifting_cloud_bank(
        (1080, 440), (seed + 701) % 900_000, t,
        color=(212, 237, 247), opacity=75, speed=1.27,
        phase=2.1), (0, 1030))


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
    # A shared material-aware renderer keeps this optical ray physically
    # straight while giving it a localized luminous core and a short,
    # direction-following photon packet, instead of a rigid line + dot.
    position=(t*speed+phase)%1.
    draw_material_ribbon(draw,[(x0,y0),(x1,y1)],material="light",
                         color=tuple(color),width=width,progress=position)


def _drop(draw: ImageDraw.ImageDraw, x: int, y: int, r: int = 230,
          *, canvas: Image.Image | None = None) -> None:
    """Use the shared original refractive material when actual pixels exist."""
    if canvas is not None:
        canvas.alpha_composite(
            glass_sphere(2*r, seed=173), (x-r,y-r))
        return
    # Legacy public Pillow-draw API remains usable in direct storyboard tests.
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


def _sunlight(draw: ImageDraw.ImageDraw, t: float, english: bool,
              *, canvas: Image.Image | None = None) -> None:
    sunx,suny=252,1013
    if canvas is not None:
        sun=solar_disc(172, seed=71)
        canvas.alpha_composite(
            sun, (sunx-sun.width//2,suny-sun.height//2))
    else:
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



def _grown_ray(draw: ImageDraw.ImageDraw, start: tuple[float,float],
               finish: tuple[float,float], color, *,
               t: float, phase: float, enter: float, leave: float,
               width: int = 5, offset: float = 0.) -> None:
    """Make the ray's real endpoint propagate through the optical material.

    The source object reacts at a measured narration phase: not simply a
    moving dot over an always fully drawn explanatory diagram.
    """
    if not 0 <= enter < leave <= 1:
        raise ValueError("Invalid physical beam timing")
    fraction=ease((phase-enter)/(leave-enter))
    if fraction <= .02:
        return
    x0,y0=start
    x1,y1=finish
    endpoint=(x0+(x1-x0)*fraction,y0+(y1-y0)*fraction)
    _ray(draw,start,endpoint,color,t=t,speed=.27,phase=offset,width=width)


def _refraction(draw: ImageDraw.ImageDraw, t: float, english: bool,
                duration: float, *, canvas: Image.Image | None = None,
                event_progress: float | None = None) -> None:
    # Near-side refractive medium: wide first-beat entrance view.
    _drop(draw,690,1013,214,canvas=canvas)
    phase=action_phase(t,duration,event_progress=event_progress,
                       trigger=.27,lead=.15)
    _grown_ray(draw,(147,893),(487,946),WHITE,t=t,phase=phase,
               enter=.01,leave=.40,width=11)
    for i,color in enumerate(SPECTRUM):
        # Actual material interaction grows after the incident ray hits the
        # droplet's front, not all colors appearing at the first frame.
        _grown_ray(draw,(490,946),(874,1020+(i-3)*16),color,
                   t=t,phase=phase,enter=.32,leave=.91,
                   width=5,offset=i*.11)
    draw.ellipse((484,937,498,951),fill=GOLD)
    _label(draw,143,1370,"LIGHT BENDS IN WATER" if english else
           "LA LUMIÈRE SE COURBE DANS L'EAU",size=33)


def _reflection(draw: ImageDraw.ImageDraw, t: float, english: bool,
                duration: float, *, canvas: Image.Image | None = None,
                event_progress: float | None = None) -> None:
    # A much closer, left-offset lens deliberately contrasts with the
    # previous wider entrance shot. Original glass source is still shared.
    _drop(draw,471,1046,268,canvas=canvas)
    phase=action_phase(t,duration,event_progress=event_progress,
                       trigger=.32,lead=.16)
    for i,color in enumerate(SPECTRUM):
        sy=913+i*10
        hit=(692,970+i*8)
        _grown_ray(draw,(244,sy),hit,color,t=t,phase=phase,
                   enter=.04,leave=.47,width=4,offset=i*.07)
        # Only AFTER hitting the back interface do the reflected beams grow.
        _grown_ray(draw,hit,(383,1261-i*7),color,t=t,phase=phase,
                   enter=.43,leave=.96,width=4,offset=.43+i*.08)
    _label(draw,152,1400,"LIGHT REFLECTS INSIDE" if english else
           "LA LUMIÈRE SE RÉFLÉCHIT",size=34)


def _emergence(draw: ImageDraw.ImageDraw, t: float, english: bool,
               duration: float, *, canvas: Image.Image | None = None,
               event_progress: float | None = None) -> None:
    # Smaller right-side drop and open outgoing fan: a new framing, not
    # the same giant disc recolored a third time.
    _drop(draw,766,1051,192,canvas=canvas)
    phase=action_phase(t,duration,event_progress=event_progress,
                       trigger=.30,lead=.15)
    for i,color in enumerate(SPECTRUM):
        from_back=(915,1004+i*8)
        exit_point=(611,1162-i*8)
        _grown_ray(draw,from_back,exit_point,color,t=t,phase=phase,
                   enter=.04,leave=.54,width=4,offset=i*.09)
        _grown_ray(draw,exit_point,(165,1220+(i-3)*23),color,
                   t=t,phase=phase,enter=.50,leave=.95,
                   width=6,offset=.25+i*.1)
    _label(draw,145,1379,"COLORS EXIT AT DIFFERENT ANGLES" if english else
           "SORTIE À DES ANGLES DIFFÉRENTS",size=30)



# Rain particles are FIXED in world space. Their contribution changes
# continuously as an observer walks through the optical environment.
RAIN_SOURCES_X=tuple(range(125,1010,59))


def observer_light_paths(t: float, duration: float, *,
                         event_progress: float | None = None
                         ) -> dict[str,object]:
    """Recalculate the viewing geometry; never translate world droplets.

    The primary bow is an angular phenomenon, not a physical target.
    Source selection is a transparent illustrative 2D projection, not a
    quantitative atmospheric optics or complete 3D ray tracer.
    """
    phase=action_phase(t,duration,event_progress=event_progress,
                       trigger=.25,lead=.17)
    observer_x=382+234*phase
    eye=(observer_x+11,1338)
    red_target=observer_x+240
    violet_target=observer_x-218
    return {
        "phase":phase,
        "observer_x":observer_x,
        "eye":eye,
        "arc_center_x":observer_x+3,
        "red":contributing_sources(RAIN_SOURCES_X,red_target),
        "violet":contributing_sources(RAIN_SOURCES_X,violet_target),
    }


def _paint_walker(draw: ImageDraw.ImageDraw, x: float, t: float,
                  phase: float) -> None:
    """Source-painted leg articulation and coat silhouette, not a stick man."""
    q=math.sin(t*5.0)
    swing=q*(.20+.80*math.sin(math.pi*phase))
    ix=round(x)
    # Ground contact shadow remains under the advancing subject.
    draw.ellipse((ix-49,1468,ix+54,1485),fill=(8,38,59,90))
    # Legs/boots independently swing, but never cross title/caption bands.
    for sign,shade in ((-1,(17,49,86,255)),(1,(28,66,103,255))):
        foot=ix+round(sign*11+sign*19*swing)
        knee=ix+round(sign*9-sign*8*swing)
        draw.line(((ix+sign*10,1418),(knee,1440),(foot,1470)),
                  fill=shade,width=12,joint="curve")
        draw.line(((foot-8,1470),(foot+12,1470)),
                  fill=(9,31,54,255),width=8)
    draw.polygon(((ix-23,1361),(ix+20,1361),(ix+29,1418),
                  (ix-25,1422)),fill=(38,87,124,255))
    draw.polygon(((ix-11,1366),(ix+1,1364),(ix+4,1416),
                  (ix-8,1417)),fill=(103,160,183,178))
    # Moving arms and cuffs are part of the silhouette, not UI arrows.
    for sign in (-1,1):
        hand=ix+sign*30+round(-sign*11*swing)
        draw.line(((ix+sign*20,1374),(hand,1404)),
                  fill=(27,66,106,255),width=11)
        draw.ellipse((hand-6,1401,hand+6,1413),
                     fill=(185,209,214,240))
    draw.ellipse((ix-19,1322,ix+19,1360),
                 fill=(195,218,226,255))
    draw.pieslice((ix-20,1320,ix+21,1358),170,348,
                  fill=(30,53,73,255))
    draw.ellipse((ix+9,1338,ix+13,1342),
                 fill=(12,37,51,255))


def _arc(draw: ImageDraw.ImageDraw, t: float, duration: float,
         english: bool, *, event_progress: float | None = None) -> None:
    view=observer_light_paths(t,duration,event_progress=event_progress)
    phase=float(view["phase"])
    ox=float(view["observer_x"])
    eye=view["eye"]
    center_x=float(view["arc_center_x"])
    center_y=1240

    # Static short-scene source markers are a schematic of *which* drops
    # contribute; actual natural rain would fall. Never tell viewers rain
    # droplets are physically stationary.
    # Fixed rain volume occupies two overlapping depths: distant droplets
    # at 865-1115 and a sparse near plane at 1230; never follow the walker.
    for i,x in enumerate(RAIN_SOURCES_X):
        for row,y in enumerate((905,998,1093)):
            dx=round(9*math.sin(i*1.7+row*2.1))
            cy=y+(i*31+row*18)%42
            radius=3+(i+row)%3
            draw.ellipse((x+dx-radius,cy-radius,x+dx+radius,cy+radius),
                         fill=(193,232,251,75+((i+row)%3)*20))
    for i in range(18):
        x=140+((i*137)%790)
        y=1140+((i*47)%110)
        draw.line((x,y,x-4,y+12),fill=(160,214,239,75),width=2)

    # The *appearance* is tied to the current line of sight. It shifts
    # in the viewport while the world raindrops stay at fixed coordinates.
    # Not a painted bow physically sitting over a landscape.
    for i,color in enumerate(SPECTRUM):
        radius=357-i*15
        bbox=(center_x-radius,center_y-radius,
              center_x+radius,center_y+radius)
        draw.arc(bbox,197,343,fill=(*color[:3],74),width=23)
        draw.arc(bbox,197,343,fill=(*color[:3],215),width=11)
    # Moving bright packets are only material light; they do not drag the
    # stationary rain texture through space.
    for i in range(7):
        radius=357-i*15
        theta=math.radians(197+146*((t*.11+i*.13)%1))
        x=center_x+radius*math.cos(theta)
        y=center_y+radius*math.sin(theta)
        draw.ellipse((x-4,y-4,x+4,y+4),fill=WHITE)

    # Recalculate contributing fixed drops for the observer's new view.
    # Two adjacent sources crossfade instead of a ray teleporting at a
    # discrete "nearest droplet" boundary. A real atmospheric rainbow is a
    # continuum; these two rays illustrate that continuously changing set.
    for category,ydrop,color in (
        ("red",998,SPECTRUM[0]),("violet",1093,SPECTRUM[-1])):
        for index,weight in view[category]:
            if weight<=.005:
                continue
            source=(RAIN_SOURCES_X[index],ydrop)
            alpha=round(216*weight)
            draw.line((source,eye),fill=(*color[:3],alpha),
                      width=max(1,round(4*weight)))
            x,y=source
            draw.ellipse((x-7,y-7,x+7,y+7),
                         fill=(*color[:3],min(255,75+alpha//2)))
    _paint_walker(draw,ox,t,phase)
    _label(draw,134,718,
           "THE VIEW CHANGES AS YOU MOVE" if english else
           "LA VUE CHANGE QUAND ON BOUGE",size=32)
    _label(draw,134,765,
           "DIFFERENT DROPS SEND THE LIGHT" if english else
           "D'AUTRES GOUTTES ENVOIENT LA LUMIÈRE",size=27,
           color=(206,238,252,223))


def draw_rainbow(draw: ImageDraw.ImageDraw, beat: str,
                 t: float, duration: float, english: bool,
                 *, canvas: Image.Image | None = None,
                 event_progress: float | None = None) -> None:
    """Draw one of five causal optical mechanisms at native 9:16 resolution."""
    if (beat not in BEATS or type(t) not in (int,float)
            or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration
            or type(english) is not bool
            or (event_progress is not None and
                (type(event_progress) not in (int,float)
                 or not math.isfinite(event_progress)
                 or not 0 <= event_progress <= 1))
            or (canvas is not None and
                (not isinstance(canvas, Image.Image)
                 or canvas.mode != "RGBA"
                 or canvas.size != (1080,1920)))):
        raise ValueError("Invalid rainbow storyboard time or concept")
    # Keep the real changing optics in an open atmospheric 2.5D world.
    # A solid rounded chart border and fixed axis grid made every moving
    # rainbow shot look like a slideshow; preserve scientific labels only.
    _label(draw,115,630,
           "OPTICS · SCHEMATIC · NOT TO SCALE" if english else
           "OPTIQUE · SCHÉMA · HORS ÉCHELLE",size=27,
           color=(170,211,231,235))
    if beat=="sunlight":
        _sunlight(draw,t,english,canvas=canvas)
    elif beat=="refraction":
        _refraction(draw,t,english,duration,canvas=canvas,
                    event_progress=event_progress)
    elif beat=="reflection":
        _reflection(draw,t,english,duration,canvas=canvas,
                    event_progress=event_progress)
    elif beat=="emergence":
        _emergence(draw,t,english,duration,canvas=canvas,
                   event_progress=event_progress)
    else:
        _arc(draw,t,duration,english,event_progress=event_progress)
