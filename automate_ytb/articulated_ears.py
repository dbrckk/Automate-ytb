"""Original separately articulated ears and owl feather tufts.

The source geometry matches the prior fused character drawings exactly at rest.
Each RGBA ear is positioned behind the head, independently of the torso, so
motion leaves no doubled ear silhouette or visible attachment seam.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

ARTICULATION_VERSION = "original-articulated-ears-v1"

ACTORS = ("fox", "rabbit", "cat", "owl")
SIDES = ("left", "right")
INK = (32, 38, 66, 255)


def draw_ear(path: Path, *, actor: str, side: str, palette: dict | None = None) -> None:
    """Draw an individual detachable ear sprite matching the original actor."""
    if actor not in ACTORS or side not in SIDES:
        raise ValueError("Unsupported ear actor/side")
    if actor != "owl":
        if not isinstance(palette, dict) or not {"fur","dark","ear"} <= palette.keys():
            raise ValueError("Missing original forest character colors")
        for channel in ("fur","dark","ear"):
            val = palette[channel]
            if (not isinstance(val, tuple) or len(val)!=4 or
                    any(not isinstance(c,int) or not 0<=c<=255 for c in val)):
                raise ValueError("Invalid RGBA palette")
    is_left = side == "left"
    size = (322,430) if actor == "owl" else (350,440)
    im = Image.new("RGBA",size,(0,0,0,0))
    d=ImageDraw.Draw(im)
    if actor == "owl":
        # Original pair of feather tufts, drawn behind the face plate.
        purple = (98,60,161,255)
        d.polygon([(51,143),(26,15),(132,84)] if is_left
                  else [(186,83),(289,14),(274,140)],fill=purple)
    elif actor == "rabbit":
        x,bend = (105,-24) if is_left else (225,26)
        d.ellipse((x-31+bend,6,x+24+bend,225),
                  fill=palette["fur"],outline=INK,width=6)
        d.ellipse((x-16+bend,24,x+11+bend,188),fill=palette["ear"])
    else:
        x = 77 if is_left else 273
        if actor == "fox":
            points=[(x-62,177),(x-8,8),(x+61,149)]
        else:
            points=[(x-51,174),(x-5,44),(x+53,159)]
        d.polygon(points,fill=palette["dark"])
        d.polygon([(x-37,151),(x-8,58),(x+35,144)],
                  fill=palette["ear"])
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,format="PNG")


def ear_position(action: str, *, actor: str, side: str,
                 body_x: int, body_y: int) -> tuple[str,str]:
    """Trusted FFmpeg overlay expressions for independently bouncing ears.

    Base translation exactly follows the original actor. Action-specific,
    opposing movements are small enough that the ear root stays behind the
    face. No raw narration text reaches the filter graph.
    """
    from .choreography import PROFILES, body_position
    if actor not in ACTORS or side not in SIDES or action not in PROFILES:
        raise ValueError("Unknown authored ear or action")
    px,py=body_position(action,x=body_x,y=body_y)
    amp={"idle":2,"walk":4,"run":7,"jump":9,"fly":6,
         "talk":3,"surprise":11,"rest":1}[action]
    freq={"idle":2.1,"walk":4.1,"run":7.9,"jump":5.0,
          "fly":5.5,"talk":2.7,"surprise":8.5,"rest":0.8}[action]
    scale=1.20 if actor=="rabbit" else (0.70 if actor=="owl" else 1.0)
    amount=round(amp*scale,2)
    phase="0" if side=="left" else "1.8"
    sign="+" if side=="left" else "-"
    # Head covers lower ear geometry, hiding the tiny base translation.
    x=f"({px}){sign}{amount}*sin(t*{freq}+{phase})"
    y=f"({py})+1.4*sin(t*{freq*0.63:.3f}+{phase})"
    return x,y
