"""Reusable subject-aware cinematic choreography for original 2.5D art.

All keyframe motion comes from a recognized script-grounded procedural subject
family and a continuous episode clock, not per-scene restart or frame RNG.
Trajectories are stylized, not a simulated biological or physical process.
Rendering, depth/parallax, authored actor interpolation, Kokoro and Foley
continue to use the same existing universal pipeline.
"""
from __future__ import annotations

import math

VERSION = "grounded-causal-subject-choreography-v1"

FAMILIES = frozenset((
    "botanical", "celestial", "rail", "weather", "ocean", "security"
))
ACTOR_DEPTHS = (25, 45, 65, 85)


def _ease(q: float) -> float:
    return q*q*(3-2*q)


def subject_pose(family: str, z: int, moment: float) -> dict:
    """An exact deterministic continuous pose on the entire episode 0..1.

    The four layer roles are environment, hero, attached-looking detail and
    foreground motifs. Every family has a distinctly different movement:
    botanical growth, orbital revolution, rail travel, wind/rainfall, wave
    breaking, or a floating secure-lock visual with travelling signals.
    Numeric coordinates are unit-stage deltas, not real-world measures.
    """
    if (type(family) is not str or family not in FAMILIES
            or type(z) is not int or z not in ACTOR_DEPTHS
            or type(moment) not in (int, float) or not math.isfinite(moment)
            or not 0 <= moment <= 1):
        raise ValueError("Unsafe subject-specific episode choreography")
    t=float(moment)
    growth=_ease(t)
    a=math.tau*t
    values: dict[int,tuple[float,float,float,float]]
    if family=="botanical":
        # Grow a planted trunk and a canopy at different rates; pollen
        # follows a drifting wind. The independent background stays stable.
        values={
            25:(.008*math.sin(a*.40), .004*math.sin(a*.70), 1., 0.),
            45:(.010*math.sin(a*.60), .115*(1-growth)-.014*growth,
                .66+.49*growth, -4.+9.*growth),
            65:(.015*math.sin(a*1.30), .053*(1-growth)-.019*growth,
                .48+.64*growth, -12.+14.*growth+4.*math.sin(a*1.5)),
            85:(.075*math.sin(a*.91), -.13*growth+.022*math.sin(a*2.),
                .87+.18*growth, 9.*math.sin(a*1.2)),
        }
    elif family=="celestial":
        # The ring and small orbiting body are in one original mid-layer.
        # Revolve that layer around its central pivot, while the large
        # planet rotates more slowly. Starfield moves at its own depth.
        values={
            25:(-.013*t, .003*math.sin(a*.6), 1., -.9*math.sin(a)),
            45:(.018*math.sin(a*.65), -.013*math.cos(a*.7), 1.02,
                -13.+26.*t),
            65:(.026*math.cos(a*1.2)-.026, .025*math.sin(a*1.2),
                .98, -52.+104.*t),
            85:(-.075*t, .018*math.sin(a*.56), 1.03, -8.+16.*t),
        }
    elif family=="rail":
        # Motor and windows travel together; vapor trails behind the body.
        # Wheels are still an illustrative static drawing, not falsely
        # labelled as rotating physics-accurate train hardware.
        travel=-.17+.34*growth
        suspension=.004*math.sin(a*4.5)
        values={
            25:(-.055*growth, 0., 1.0, 0.),
            45:(travel, suspension, 1.02, .35*math.sin(a*1.4)),
            65:(travel, suspension+.002*math.sin(a*5.), 1.02,
                .35*math.sin(a*1.4)),
            85:(travel-.025-.028*growth, -.095*growth,
                1.05+.09*growth, -6.+12.*t),
        }
    elif family=="weather":
        # The cloud drifts horizontally with the wind, drops descend
        # independently below it; high atmosphere passes slowly.
        wind=-.13+.26*growth
        values={
            25:(-.023*growth, .004*math.sin(a*.8), 1., 0.),
            45:(wind, .014*math.sin(a*.9), 1.04, 2.4*math.sin(a*.7)),
            65:(wind+.013*math.sin(a*2.6), .16*growth,
                .94+.10*growth, -5.+3.*math.sin(a*2.1)),
            85:(-.08*growth+.025*math.sin(a*1.8), -.03*growth,
                1.01, 5.*math.sin(a*1.2)),
        }
    elif family=="ocean":
        # A wave advances, lifts and breaks, with separate foam and spray.
        # Its angular oscillation and visible growth are not just sideways
        # parallax shared by every kind of illustration.
        swell=math.sin(math.pi*growth)
        crest=math.sin(a*1.45)
        values={
            25:(-.014*t, .007*math.sin(a*.45), 1., 0.),
            45:(.048*math.sin(a*.84), -.047*swell+.014*crest,
                .89+.21*swell, 10.5*crest),
            65:(.060*math.sin(a*.84+.20), -.052*swell+.012*crest,
                .89+.22*swell, 12.6*crest+3.*math.cos(a*2.0)),
            85:(.072*math.sin(a*1.25), -.123*swell,
                .84+.30*swell, -12.*math.sin(a*1.15)),
        }
    else:
        # A security padlock and separate status particles. This denotes
        # "security" visually, but DOES NOT assert a real login succeeded.
        pulse=(1-math.cos(a*2.0))*.5
        values={
            25:(-.007*math.sin(a*.8), 0., 1., 0.),
            45:(.008*math.sin(a*1.2), -.022*pulse,
                .94+.105*pulse, 2.*math.sin(a)),
            65:(.016*math.sin(a*.85), -.01*pulse,
                1.+.054*pulse, -3.0*math.sin(a*1.4)),
            85:(.084*math.sin(a*1.35), -.041*math.cos(a*1.1),
                .90+.13*pulse, 11.*math.sin(a)),
        }
    x,y,scale,angle=values[z]
    return {
        "x":round(x,7),"y":round(y,7),
        "scale":round(scale,7),"angle":round(angle,7),
    }


def subject_motion_tracks(family: str, index: int, total: int) -> list[dict]:
    """Use global story time so same actor frame on either side of a cut joins.

    Five keys per shot resolve the faster rain/wave/orbit cycles without
    allocating a custom renderer or synthesizing new images each frame.
    """
    if (type(family) is not str or family not in FAMILIES
            or type(index) is not int or type(total) is not int
            or not 2<=total<=12 or not 0<=index<total):
        raise ValueError("Invalid bounded subject motion storyboard")
    tracks=[]
    for z in ACTOR_DEPTHS:
        keys=[]
        for at in (0., .25, .5, .75, 1.):
            state=subject_pose(family,z,(index+at)/total)
            keys.append({"at":at, **state})
        tracks.append({"z":z,"keys":keys})
    return tracks
