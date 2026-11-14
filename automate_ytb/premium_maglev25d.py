"""Original high-detail superconducting maglev hero art.

A source-grounded premium scene pack, not a generic railway locomotive.
All visuals are original deterministic vector shapes. Magnetic arcs are
illustrative (not a scientific field simulation); no factual values are
generated from the narration.
"""
from __future__ import annotations

from .universal_subject_illustrations import (
    _box, _ell, _line, _poly, _bezier, _multi,
)

VERSION = "original-maglev-multi-plane-design-v1"


def maglev_scene():
    navy = "#070E22"
    violet = "#111D3B"
    teal = "#40D6CF"
    ice = "#DCF6F6"
    gold = "#F2B67D"
    steel = "#203D58"
    # 1. Full-frame world in deep tones; deliberate separation of light pools.
    sky = [
        _box(0, 0, 1, 1, _multi([navy, violet, "#192F45"], "vertical", "stage"), .001),
        _ell(.19,.22,.87,.83,_multi(["#21405A","#101D36",navy],"radial"),
             opacity=.36),
        _ell(.10,.39,.89,.77,_multi(["#1E4E60","#0D1B2C"],"radial"),
             opacity=.23),
    ]
    for i in range(24):
        x=.035+((i*167+11)%895)/1000
        y=.09+((i*173+29)%480)/1000
        r=.0026+(i%3)*.00065
        sky.append(_ell(x,y,x+r,y+r,ice if i%5 else gold,
                        opacity=.21+.1*(i%3)))
    # 2. Grounded physical guideway: ties, center keel, and illuminated
    # linear motor coils. It does not claim that each drawn slab is a
    # physical SCMaglev coil spacing or scale.
    ground=[
        _poly([[0,.738],[1,.738],[1,.881],[0,.881]],
              _multi(["#244558","#0B2137","#060F24"],"vertical")),
        _poly([[0,.849],[1,.849],[1,.925],[0,.925]],
              _multi(["#152D42","#071225"],"vertical")),
        _poly([[0,.918],[1,.918],[1,1],[0,1]],navy),
        _line([[0,.740],[1,.740]],teal,.004,opacity=.67),
        _line([[0,.868],[1,.868]],gold,.004,opacity=.50),
        _line([[0,.920],[1,.920]],"#466D84",.003,opacity=.40),
    ]
    for i in range(9):
        x=.045+i*.115
        # Segmented guideway luminous coils and brackets: each shape has
        # its own physical placement; not a decorative row of circles.
        if x+.055>1:
            break
        ground.extend([
            _box(x,.770,x+.054,.841,_multi(["#35717C","#142E48"],"vertical"),
                 .009,"#59B9B5",.0025),
            _line([[x+.008,.781],[x+.045,.781]],ice,.002,opacity=.43),
        ])
    # 3. Aero nose profile, carriage shell, glass cabins, undercarriage.
    # Cubic Bézier preserves the recognizable tapered high-speed nose.
    shell=[
        _poly([[.135,.502],[.586,.501],[.756,.528],[.852,.562],
               [.933,.635],[.947,.663],[.888,.696],[.682,.719],
               [.16,.712],[.098,.673],[.094,.584]],
              _multi(["#E8F5F2","#A9CCD4","#62899D","#254E6A"],
                     "vertical"),"#D6F7F2",.0025),
        _bezier([[.756,.529],[.824,.537],[.919,.585],[.954,.642],
                 [.960,.679],[.915,.691],[.853,.703],
                 [.858,.679],[.811,.609],[.756,.529]],
                _multi(["#F7FBF6","#B4D6DC","#688E9E"],"diagonal")),
        _poly([[.121,.532],[.588,.531],[.770,.556],[.852,.587],
               [.893,.631],[.817,.616],[.670,.585],[.113,.578]],
              _multi(["#E8F6EF","#89C5D0","#407F95"],"vertical")),
        _poly([[.117,.625],[.886,.660],[.936,.674],[.875,.690],
               [.169,.682]],"#315875",opacity=.87),
        _line([[.141,.515],[.553,.514],[.722,.538],[.817,.575]],
              "#FAFDF7",.003,opacity=.78),
        _line([[.120,.687],[.670,.705],[.850,.685]],
              "#83DED5",.004,opacity=.67),
        _box(.13,.699,.696,.734,_multi(["#1A405B","#102B44"],"vertical"),
             .013),
        _poly([[.701,.690],[.876,.677],[.848,.716],[.706,.726]],
              "#193C55"),
    ]
    # Glass windows: precise sizes and thin highlights rather than
    # opaque toy-like square boxes.
    for i in range(7):
        x=.215+i*.068
        shell.extend([
            _poly([[x,.550],[x+.055,.550],[x+.054,.588],[x+.004,.585]],
                  _multi(["#24576C","#0B263E","#15314B"],"diagonal"),
                  "#A5E2E4",.002),
            _line([[x+.008,.553],[x+.020,.553]],ice,.0018,opacity=.67),
        ])
    # Two real door seams, one running body stripe, small optical headlight.
    shell.extend([
        _line([[.177,.534],[.177,.668]],"#8CA5AE",.0022,opacity=.82),
        _line([[.669,.553],[.669,.695]],"#6C8C98",.0022,opacity=.69),
        _line([[.15,.622],[.868,.653]],teal,.003,opacity=.61),
        _ell(.908,.648,.932,.660,_multi([gold,ice,teal],"radial")),
        _line([[.924,.650],[.965,.650]],gold,.0025,opacity=.75),
    ])
    # 4. Real undercarriage-to-guideway air gap with artistic field arcs.
    details=[
        _poly([[.168,.727],[.746,.735],[.708,.745],[.185,.743]],
              "#0D3045",opacity=.9),
        _line([[.17,.752],[.773,.752]],teal,.004,opacity=.82),
        _line([[.20,.768],[.78,.768]],ice,.002,opacity=.34),
    ]
    for i in range(7):
        x=.21+i*.082
        details.extend([
            _box(x,.736,x+.039,.752,"#3D8C94",.006,
                 "#93DFD5",.0015),
            _line([[x-.026,.778],[x+.011,.763],[x+.055,.782]],teal,
                  .0025,opacity=.44),
            _line([[x-.022,.792],[x+.011,.776],[x+.053,.795]],gold,
                  .0018,opacity=.28),
        ])
    # 5. Glancing reflections, sparking motion traces and spatial rain.
    particles = []
    for i in range(11):
        x=.033+((i*103+17)%940)/1000
        y=.37+((i*31+11)%310)/1000
        particles.append(
            _line([[x,y],[min(.999,x+.031+(i%3)*.011),y-.002]],
                  ice if i%4 else gold,.0022,
                  opacity=.21+.05*(i%3)))
    for i in range(8):
        x=.08+i*.110
        particles.append(
            _line([[x,.756],[min(.995,x+.052),.751]],teal,.002,
                  opacity=.22))
    return sky, ground, shell, details, particles


__all__ = ("maglev_scene", "VERSION")
