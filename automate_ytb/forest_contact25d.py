"""Original 2.5D flower encounter caused by a planted animal paw.

The spring-flower event is placed at the actual world-space right-paw
foothold predicted by the *existing* two-bone walking rig. It deforms and
releases distinct moving petals ONLY after contact. This is a deliberately
authored causal effect, not a generic time-triggered decoration or physics
engine. Layers render behind and in front of the real actor.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image, ImageDraw

from .rig25d import GROUND, PERIOD, walking_leg

VERSION = "25d-world-paw-grounded-spring-flower-face-clear-p43-v1"
IMPACT_TIME = 1.5 * PERIOD
SIZE = (1080, 1920)


@dataclass(frozen=True)
class FlowerContact:
    x: float
    y: float
    time: float
    planted: bool
    deformation: float
    particle_count: int


def _valid(t: float, origin_x: float, speed: float, torso_y: float) -> None:
    if (any(type(v) not in (float, int) or not math.isfinite(v)
            for v in (t, origin_x, speed, torso_y))
            or not 0 <= t <= 20 or not 0 <= origin_x <= 1600
            or not 1 <= speed <= 100 or not 0 <= torso_y <= 1600):
        raise ValueError("Unsafe 2.5D physical-contact animation clock")


def contact_at(t: float, *, origin_x: float, speed: float,
               torso_y: float) -> FlowerContact:
    """Rig-derived contact anchor and strictly post-contact response."""
    _valid(t, origin_x, speed, torso_y)
    paw = walking_leg(IMPACT_TIME + .0001, side="right",
                      origin_x=origin_x, speed=speed, torso_y=torso_y)
    if not paw.planted or abs(paw.foot[1] - GROUND) > .001:
        raise ValueError("Expected grounded paw landing is unreachable")
    dt = t - IMPACT_TIME
    if dt <= 0:
        return FlowerContact(paw.foot[0], GROUND, IMPACT_TIME, False, 0., 0)
    # A bounded spring impulse: rising contact compression, underdamped
    # rebound and smooth decay, with no animation before the paw lands.
    amplitude=(1-math.exp(-18*dt))*math.exp(-1.75*dt)
    deformation=max(0., min(1., amplitude * (0.6+0.4*abs(math.cos(8*dt)))))
    count = 7 if .12 < dt < 3.25 else 0
    return FlowerContact(paw.foot[0], GROUND, IMPACT_TIME, True,
                         deformation, count)


def flower_plates(t: float, *, origin_x: float, speed: float,
                  torso_y: float) -> tuple[Image.Image, Image.Image]:
    """Draw behind-the-paw flower geometry and foreground moving petals."""
    hit = contact_at(t, origin_x=origin_x, speed=speed, torso_y=torso_y)
    back=Image.new("RGBA", SIZE)
    front=Image.new("RGBA", SIZE)
    draw=ImageDraw.Draw(back)
    x,y=hit.x,hit.y
    delta=max(0.,t-hit.time)
    sway=48*math.exp(-1.0*delta)*math.sin(8*delta) if hit.planted else 0.
    squash=57*hit.deformation
    tip_x=x+30+sway
    tip_y=y-114+squash
    # Original grounded stem is permanently connected to the same earth
    # coordinate as the paw's foothold, never floating with the camera.
    draw.ellipse((x-30,y-10,x+30,y+4),fill=(15,45,34,98))
    draw.line(((x,y),(x+10,y-45),(tip_x,tip_y)),
              fill=(21,91,58,255),width=12,joint="curve")
    draw.line(((x-2,y-28),(x-33,y-62-squash*.22)),
              fill=(37,148,80,255),width=7)
    draw.ellipse((x-58,y-76-squash*.22,x-24,y-54-squash*.22),
                 fill=(75,190,91,243))
    draw.line(((x+5,y-42),(x+42,y-73-squash*.15)),
              fill=(47,156,89,245),width=6)
    draw.ellipse((x+35,y-88-squash*.15,x+70,y-61-squash*.15),
                 fill=(63,174,110,245))
    # Petals deform with the actual impact; their centers remain attached
    # to the tip until released (then move on independent trajectories).
    remaining = 4 if hit.planted and delta>.12 else 11
    for j in range(remaining):
        angle=2*math.pi*j/11+.20
        radius=24+9*math.sin(angle*.5)
        px=tip_x+math.cos(angle)*radius
        py=tip_y+math.sin(angle)*radius*.76
        draw.ellipse((px-13,py-21,px+13,py+21),
                     fill=(255,193+int(j%3*9),102+int(j%3*17),240))
    draw.ellipse((tip_x-14,tip_y-14,tip_x+14,tip_y+14),
                 fill=(245,119,81,255))
    if hit.particle_count:
        d=ImageDraw.Draw(front)
        age=delta-.12
        for j in range(hit.particle_count):
            angle=(-.95+j*.19)
            # Released petals have independent horizontal velocities,
            # gravity, drag and a deterministic bounded lifetime.
            # Fan released petals to the right of the fox, not across its
            # eyes and mouth. Origin remains the real flower tip at impact.
            vx=150+18*j
            vy=-85-(j%4)*22
            px=x+30+vx*age+10*math.sin(age*1.3+j)
            py=y-112+vy*age+47*age*age
            alpha=round(210*max(0.,min(1.,(3.25-delta)/1.3)))
            rr=6+j%4
            d.ellipse((px-rr,py-rr*1.6,px+rr,py+rr*1.6),
                      fill=(255,203+5*(j%3),120+7*(j%4),alpha))
        # A contact ring expands at the exact paw position, not arbitrarily
        # elsewhere on the ground or on the actor's torso.
        if delta<.7:
            radius=17+75*delta
            alpha=round(180*(1-delta/.7))
            d.arc((x-radius,y-11,x+radius,y+11),185,355,
                  fill=(247,228,147,alpha),width=3)
    return back,front
