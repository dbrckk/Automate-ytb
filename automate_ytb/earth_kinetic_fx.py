"""Foreground actions for original Earth-stop explainer scenes.

Every element uses deterministic time-dependent geometry; there are no static
video loops, paid assets, random-frame jitter, or hidden API dependencies.
The illustrations are explicitly schematic, not fluid/atmospheric simulations.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

SEA=(106,210,244,230)
FOAM=(228,249,253,205)
ORANGE=(255,191,119,232)


def _moving(value: float, duration: float, speed: float, period: float) -> float:
    return (value*period+duration*speed) % period


def draw_foreground(picture: Image.Image, beat: str, t: float,
                    duration: float) -> None:
    """Mutate original 1080x1920 scene with distinct foreground animations."""
    if picture.mode!="RGBA" or picture.size!=(1080,1920):
        raise ValueError("Kinetic action requires native RGBA portrait")
    if (type(t) not in (float,int) or type(duration) not in (float,int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration == 0):
        raise ValueError("Invalid kinetic-action frame clock")
    if beat not in {"stop","inertia","wind","ocean","poles","day","astronaut"}:
        raise ValueError("Unsupported kinetic-action story beat")

    d=ImageDraw.Draw(picture,"RGBA")
    p=t/duration
    if beat=="inertia":
        # A roadside sign and leaves lag behind the fast-moving car. Separate
        # ground-plane travel from airborne trajectories for visible depth.
        pole=174-21*math.sin(t*1.15)
        d.line((pole,1124,pole+14,1295),fill=(157,205,226,224),width=13)
        d.rounded_rectangle((pole-82,1051,pole+99,1125),radius=14,
                            fill=(29,94,132,244),outline=SEA,width=5)
        d.line((pole-53,1091,pole+58,1091),
               fill=(244,250,252,187),width=8)
        for k in range(22):
            depth=.4+.6*((k%5)/4)
            x=1040-((t*(115+270*depth)+k*193)%1310)
            y=1220-(k*97)%355+32*math.sin(t*2+k*.8)
            tail=round(18+65*depth)
            d.line((x-tail,y,x,y-4),fill=(251,204,146,158),width=2+(k%3))
        for k in range(7):
            x=(k*175+t*(70+k*27))%1040
            y=1285+25*math.sin(t*2+k)
            d.arc((x-46,y-25,x+92,y+23),185,357,
                  fill=(235,208,165,150),width=3)

    elif beat=="wind":
        # Three foreground trees bend and oscillate independently in gusts.
        # Crown, branch and leaf displacements are coupled to trunk motion.
        for k,(x,base,scale) in enumerate(((140,1418,.88),
                                            (517,1458,1.22),
                                            (911,1404,.98))):
            gust=math.sin(t*2.1+k*1.37)*22+(30+24*p)
            tipx=x+gust*scale
            tipy=base-205*scale
            d.polygon(((x-21*scale,base),(x+24*scale,base),
                       (tipx+6,tipy),(tipx-14,tipy)),
                      fill=(83,114,127,240))
            for side in (-1,1):
                by=tipy+72*scale
                d.line((x+gust*.45,by+36*scale,
                        tipx+side*96*scale,by-48*scale),
                       fill=(104,144,140,210),width=max(4,round(13*scale)))
            for j in range(5):
                fx=tipx+math.sin(j*2.1)*82*scale
                fy=tipy+math.cos(j*2.3)*64*scale
                radius=32*scale
                d.ellipse((fx-radius,fy-radius,fx+radius,fy+radius),
                          fill=(59+j*8,143+j*6,127,187))
        for k in range(37):
            # Moving leaves have their own velocities and rolling orientation.
            x=-110+((k*187+t*(130+k%6*34))%1380)
            y=750+(k*79)%628+20*math.sin(t*1.8+k)
            phi=t*3.2+k*1.64
            vx=10*math.cos(phi)
            vy=6*math.sin(phi)
            d.polygon(((x+vx,y+vy),(x+8-vy,y-4+vx),
                       (x-vx,y-vy),(x-8+vy,y+4-vx)),
                      fill=(135,200+(k%4)*10,154,200))
        for i in range(5):
            y=910+i*89+12*math.sin(t*1.15+i)
            x=-350+((i*283+t*196)%1720)
            d.arc((x,y-55,x+490,y+72),190,349,
                  fill=(185,238,246,169),width=5)

    elif beat=="ocean":
        # A small fishing boat floats, pitches and leaves spray as the waves
        # actually rise against the buildings; it is not part of the backdrop.
        surge=p*p*(3-2*p)
        sea_y=1330-305*surge+31*math.sin(t*1.9)
        bx=760+44*math.sin(t*.65)
        by=sea_y-32+15*math.sin(t*2.5)
        tilt=17*math.sin(t*1.6)
        d.polygon(((bx-142,by-9),(bx+111,by-9+tilt),
                   (bx+69,by+43+tilt),(bx-107,by+43)),
                  fill=(197,112,77,245))
        d.line((bx-68,by-13,bx+104,by-13+tilt),
               fill=(245,220,191,245),width=6)
        d.polygon(((bx-10,by-27),(bx-10,by-135),
                   (bx+82,by-27)),fill=(238,239,227,230))
        d.line((bx-10,by-148,bx-10,by-26),
               fill=(145,198,216,240),width=7)
        for k in range(19):
            x=bx-163+(k*27+t*(32+k%3*15))%320
            y=sea_y+8+(k*31)%47+8*math.sin(t*3+k)
            d.ellipse((x-5,y-3,x+5,y+3),fill=FOAM)
        for j in range(30):
            # Spray travels upward and falls back to the moving waterline.
            phase=(j*.173+t*(.38+(j%3)*.08))%1
            x=(j*113+t*31)%1080
            yy=sea_y-22-110*4*phase*(1-phase)
            r=2+j%4
            d.ellipse((x-r,yy-r,x+r,yy+r),fill=(186,239,253,178))

    elif beat=="astronaut":
        cx=540+round(72*math.sin(t*.65))
        cy=1050+round(65*math.sin(t*.9))
        # Articulated astronaut remains visible; animated tether, harness
        # and multiple thruster puffs show environmental interaction.
        d.rounded_rectangle((cx-114,cy+27,cx-92,cy+161),
                            radius=11,fill=(101,153,183,242))
        d.ellipse((cx-134,cy+70,cx-108,cy+102),
                  fill=(255,185,106,230))
        cable=[]
        for k in range(43):
            a=k/42
            cable.append((cx-118-(445*a),
                          cy+81-520*a+48*math.sin(a*math.pi*3+t*.85)))
        d.line(cable,fill=(68,143,199,224),width=10,joint="curve")
        d.line(cable,fill=(216,235,243,220),width=3,joint="curve")
        for k in range(14):
            phase=(k*.211+t*.37)%1
            x=cx-118-445*phase
            y=cy+81-520*phase+48*math.sin(phase*math.pi*3+t*.85)
            d.ellipse((x-4,y-4,x+4,y+4),fill=ORANGE)
        for sign in (-1,1):
            bootx=cx+sign*(60+31*math.sin(t*1.4+sign))
            booty=cy+294+29*math.sin(t*1.2+sign)
            for k in range(4):
                phase=(t*1.05+k*.37)%1
                rr=6+phase*19
                d.ellipse((bootx-rr,booty+22+phase*55-rr,
                           bootx+rr,booty+22+phase*55+rr),
                          outline=(110,220,250,round(145*(1-phase))),
                          width=3)

    elif beat=="stop":
        # Dissipating circular shock ring, small independent orbit fragments.
        # Core planet and rotation marks remain untouched.
        for j in range(3):
            phase=(p*.80-j*.27)%1
            radius=150+phase*435
            opacity=round(125*(1-phase))
            d.ellipse((540-radius,1017-radius,
                       540+radius,1017+radius),
                      outline=(120,216,249,opacity),width=3+j)
        for k in range(17):
            angle=k*math.tau/17+t*(.6*(1-p)) 
            radius=340+24*math.sin(t*1.9+k)
            x=540+radius*math.cos(angle)
            y=1017+radius*math.sin(angle)
            d.line((x,y,x+13*math.cos(angle),y+13*math.sin(angle)),
                   fill=(252,206,123,188),width=3)

    elif beat=="day":
        # A traveling sun flare through the fixed-globe reference frame.
        # The astronomic time scale is schematic (not a numerical ephemeris).
        for k in range(9):
            phase=(t*.12+k*.14)%1
            x=170+phase*740
            y=610+45*math.sin(phase*math.pi*2)
            r=3+k%3
            d.ellipse((x-r,y-r,x+r,y+r),fill=(255,215,137,165))
        for i in range(5):
            a=t*.27+i*math.tau/5
            x=540+434*math.cos(a)
            y=1017+434*math.sin(a)
            d.ellipse((x-6,y-6,x+6,y+6),fill=SEA)

    else:  # poles
        # Two distinct polar stream paths advance around the frozen Earth.
        for side in (-1,1):
            for k in range(20):
                phase=(t*.27+k/20)%1
                angle=phase*math.pi*.79
                x=540+side*310*math.sin(angle)
                y=1017+side*310*math.cos(angle)
                r=2+k%3
                d.ellipse((x-r,y-r,x+r,y+r),
                          fill=(118,220,250,186))
