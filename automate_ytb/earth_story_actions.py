"""Narration-specific actor interactions in the Earth-stop science short.

Unlike an ambient overlay, each action reacts to the underlying scene:
- inertia: car wheel rotation and a roadside cone thrown by its passage;
- wind: people lean, brace and hold a wind-loaded umbrella;
- ocean: a tethered rescue buoy rises with the same accelerating flood.

These are explicitly stylized original 2D drawings, not a physical simulation.
Every pose is a pure function of the scene clock: reproducible and frame-rate
independent, without frame history, stock video, APIs or paid dependencies.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

ACTOR_BEATS = frozenset({"inertia", "wind", "ocean"})
ALL_BEATS = frozenset({"stop", "inertia", "wind", "ocean",
                       "poles", "day", "astronaut"})
SUN = (255, 205, 128, 236)
FOAM = (203, 248, 255, 220)
SHADOW = (11, 37, 64, 238)


def _ease(x: float) -> float:
    x = min(1., max(0., x))
    return x*x*(3-2*x)


def _rotate(points, x: float, y: float, degrees: float):
    """Rotate a local polygon as one rigid actor rather than moving vertices independently."""
    a = math.radians(degrees)
    cs, sn = math.cos(a), math.sin(a)
    return [(x + px*cs-py*sn, y + px*sn+py*cs)
            for px, py in points]


def action_state(beat: str, t: float, duration: float) -> dict:
    """Inspectable collision, wind and tide state shared by each character."""
    if (beat not in ALL_BEATS or type(t) not in (float, int)
            or type(duration) not in (float, int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not (0 <= t <= duration <= 180) or duration == 0):
        raise ValueError("Invalid original science actor clock")
    u = t / duration
    if beat == "inertia":
        # Same car trajectory as science_earth_stop.draw, so contact starts
        # when the bumper approaches the cone. Then it is launched and falls.
        car_x = 160 + 570*_ease(u)
        impact = _ease((car_x - 411) / 205)
        return {"car_x": car_x, "cone_flight": impact,
                "cone_x": 529 + 154*impact,
                "cone_y": 1286 - 108*math.sin(impact*math.pi),
                "cone_angle": 103*impact}
    if beat == "wind":
        gust = (30 + 55*_ease(u)) + 18*math.sin(2.5*t)
        return {"gust": gust, "lean": min(92., gust*.7),
                "umbrella_bend": min(40., gust*.31)}
    if beat == "ocean":
        flood = _ease(u)
        sea_y = 1330 - 305*flood + 31*math.sin(t*1.9)
        return {"sea_y": sea_y,
                "buoy_x": 278 + 27*math.sin(t*.95),
                "buoy_y": sea_y - 29 + 9*math.sin(2.4*t),
                "flood": flood}
    return {}


def _inertia(d: ImageDraw.ImageDraw, state: dict, t: float):
    cx = state["car_x"]
    yy = 1264 - 18*math.sin(t*5)
    # Car and rolling spokes now live in the same projected 3D geometry as
    # the road; this 2D foreground pass only handles the roadside impact.
    # A physical contact event: the standing cone stays still until the
    # car's front approaches it; it then flies, tumbles and lands.
    phase = state["cone_flight"]
    px, py = state["cone_x"], state["cone_y"]
    angle = state["cone_angle"]
    d.ellipse((px-35,1293,px+37,1306),
              fill=(4,24,40,round(125-72*phase)))
    d.polygon(_rotate([(-30,1),(-17,-10),(17,-10),(30,1)],
                      px,py,angle),fill=(49,64,82,240))
    d.polygon(_rotate([(-19,-10),(0,-77),(19,-10)],
                      px,py,angle),fill=(250,135,70,249))
    d.line(_rotate([(-13,-24),(13,-24)],px,py,angle),
           fill=(255,249,218,240),width=8)
    d.line(_rotate([(-8,-44),(8,-44)],px,py,angle),
           fill=(245,229,197,232),width=6)
    if 0 < phase < 1:
        for j in range(9):
            phi = j*math.tau/9 + t*1.1
            rad = 19 + 28*phase
            x = px + rad*math.cos(phi)
            y = py + rad*math.sin(phi)
            d.ellipse((x-3,y-3,x+3,y+3),
                      fill=(255,224,177,round(140*(1-phase))+25))


def _person(d: ImageDraw.ImageDraw, x: float, ground: float,
            lean: float, phase: float, jacket: tuple,
            *, holding_umbrella: bool):
    """One articulated person; ankles stay planted while upper body braces."""
    torso_x = x + lean*.48
    shoulder_y = ground - 176
    head_x = torso_x + lean*.32
    head_y = shoulder_y - 37 + 4*math.sin(phase*1.4)
    # Feet and joint positions are linked to the body trajectory.
    for side in (-1, 1):
        knee_x = x + side*29 - lean*.20
        knee_y = ground - 77 + 5*math.sin(phase*1.1+side)
        foot_x = x + side*44 - lean*.30
        d.line([(torso_x+side*20,ground-114),(knee_x,knee_y),
                (foot_x,ground)],fill=(166,195,212,245),width=19,joint="curve")
        d.rounded_rectangle((foot_x-23,ground-12,foot_x+25,ground+3),
                            radius=6,fill=(29,68,100,248))
    d.polygon([
        (torso_x-39,shoulder_y+13),
        (torso_x+39,shoulder_y+13),
        (torso_x+26,ground-112),
        (torso_x-26,ground-112)],
        fill=jacket)
    d.line((torso_x+4,shoulder_y+27,torso_x+8,ground-125),
           fill=(232,246,250,126),width=5)
    d.ellipse((head_x-30,head_y-34,head_x+30,head_y+29),
              fill=(236,197,158,252))
    d.arc((head_x-31,head_y-35,head_x+31,head_y+25),
          182,356,fill=(34,69,92,240),width=8)
    # The hands remain attached to the shoulder and react to the same gust.
    left_hand = (torso_x-93-lean*.24, shoulder_y+117)
    d.line((torso_x-30,shoulder_y+29,left_hand[0],left_hand[1]),
           fill=(223,231,240,248),width=18)
    d.ellipse((left_hand[0]-11,left_hand[1]-11,
               left_hand[0]+11,left_hand[1]+11),
              fill=(237,194,155,252))
    if holding_umbrella:
        # The curved canopy and handle share a single overloaded pole.
        # Umbrella pitch and shaft displacement are coupled to wind lean.
        ux = torso_x + 113 + lean*.7
        uy = shoulder_y - 130 - lean*.12
        hand = (torso_x+57,shoulder_y+66)
        d.line((torso_x+29,shoulder_y+27,*hand),
               fill=(220,236,244,249),width=18)
        d.line((hand[0],hand[1],ux,uy+5),
               fill=(224,234,239,245),width=7)
        d.line((ux-16,uy+106,ux+20,uy-28),
               fill=(218,240,249,240),width=6)
        dome = [(ux-117,uy+31),
                (ux-85,uy-22),
                (ux-31,uy-76),
                (ux+44,uy-84),
                (ux+114,uy-17),
                (ux+132,uy+28),
                (ux+68,uy+14),
                (ux+3,uy+26),
                (ux-61,uy+18)]
        d.polygon(dome,fill=(240,122,91,240))
        d.line(dome[:6],fill=(255,213,155,235),width=7,joint="curve")
        d.line([(ux-110,uy+31),(ux+15,uy-38),(ux+129,uy+28)],
               fill=(211,86,79,190),width=3,joint="curve")
        d.ellipse((hand[0]-12,hand[1]-12,hand[0]+12,hand[1]+12),
                  fill=(237,194,155,255))
    else:
        right_hand = (torso_x+96+lean*.30,
                      shoulder_y+42+24*math.sin(phase*1.7))
        d.line((torso_x+29,shoulder_y+29,*right_hand),
               fill=(219,235,242,246),width=18)
        d.ellipse((right_hand[0]-12,right_hand[1]-12,
                   right_hand[0]+12,right_hand[1]+12),
                  fill=(237,194,155,252))
        # Scarf trails opposite the braced feet, with its own inertia.
        tip_x = torso_x-159-lean*.7
        tip_y = shoulder_y+24+15*math.sin(phase*2.3)
        d.polygon([(torso_x-24,shoulder_y+25),
                   (torso_x+11,shoulder_y+15),
                   (tip_x,tip_y-18),(tip_x-22,tip_y+13)],
                  fill=(249,200,112,234))


def _wind(d: ImageDraw.ImageDraw, state: dict, t: float):
    lean = state["lean"]
    _person(d,244,1305,lean,t,(78,187,201,255),
            holding_umbrella=True)
    _person(d,779,1297,lean*.78,t+1.2,(226,123,98,248),
            holding_umbrella=False)
    # Roadside sign twists and bends with the same gust as the people.
    topx=976+state["gust"]*.35
    d.line((969,1306,topx,1148),fill=(129,173,196,230),width=13)
    d.polygon([(topx-34,1121),(topx+47,1114),
               (topx+57,1160),(topx-30,1167)],
              fill=(235,179,92,240))
    d.line((topx-15,1146,topx+30,1142),
           fill=(36,87,112,242),width=8)
    for j in range(19):
        x=(j*151 + t*(84+j%4*28))%1290-120
        y=824+(j*57)%366
        size=4+j%4
        d.line((x-size*2,y+size,x+size*3,y-size),
               fill=(242,225,170,155),width=2)


def _ocean(d: ImageDraw.ImageDraw, state: dict, t: float):
    water=state["sea_y"]
    x,y=state["buoy_x"],state["buoy_y"]
    # A partly submerged pier and a tether create a clear spatial reference
    # for the rising water line, unlike free-floating decorative spray.
    for px in (100,234,362):
        d.polygon([(px-15,1218),(px+12,1218),
                   (px+25,1434),(px-24,1434)],
                  fill=(96,100,103,226))
    d.polygon([(57,1174),(369,1180),(396,1218),(72,1229)],
              fill=(178,128,87,246))
    for j in range(5):
        pl=83+j*60
        d.line((pl,1183,pl+10,1222),fill=(100,64,52,204),width=5)
    # Anchor rope has discrete curved control points and stretches with
    # flood surge; its endpoints are exactly on pier and buoy.
    anchor=(367,1195)
    cable=[]
    for i in range(25):
        f=i/24
        sag=32*math.sin(math.pi*f)*(1-state["flood"])
        cable.append((anchor[0]*(1-f)+x*f,
                      anchor[1]*(1-f)+(y+15)*f+sag))
    d.line(cable,fill=(28,48,60,239),width=8,joint="curve")
    d.line(cable,fill=(238,224,179,237),width=4,joint="curve")
    # Ring silhouette occludes the rope where it meets the actual float.
    d.ellipse((x-46,y-44,x+46,y+44),
              fill=(255,159,94,242),outline=(242,231,213,245),width=6)
    d.ellipse((x-25,y-23,x+25,y+23),
              fill=(36,134,193,238),outline=(240,248,244,242),width=5)
    for angle in (0,90,180,270):
        a=math.radians(angle+7*math.sin(t*.8))
        xx=x+36*math.cos(a)
        yy=y+31*math.sin(a)
        d.ellipse((xx-9,yy-8,xx+9,yy+8),fill=(249,244,233,232))
    # Foam must travel with the rising sea boundary.
    for j in range(13):
        xx=x-77+j*13+6*math.sin(t*2+j)
        yy=water+9+((j*7)%18)
        d.line((xx-5,yy,xx+8,yy+3),
               fill=FOAM,width=3)


def draw_story_actions(picture: Image.Image, beat: str,
                       t: float, duration: float) -> None:
    """Paint three original acting sequences inside science mobile-safe region."""
    if picture.mode != "RGBA" or picture.size != (1080, 1920):
        raise ValueError("Science action renderer requires RGBA 1080x1920")
    state=action_state(beat,t,duration)
    if beat not in ACTOR_BEATS:
        return
    d=ImageDraw.Draw(picture,"RGBA")
    if beat=="inertia":
        _inertia(d,state,t)
    elif beat=="wind":
        _wind(d,state,t)
    else:
        _ocean(d,state,t)
