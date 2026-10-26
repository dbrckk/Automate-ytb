"""Small original airborne-impact/footstep puffs for cartoon animal animation.

Offline Pillow plate; timing is from vetted action enums, not untrusted text.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

IMPACT_VERSION = "original-contact-puffs-v1"
_ACTION_TIMING = {
    "jump": "lt(mod(t,1.75),0.20)+between(mod(t,1.75),1.42,1.70)",
    "walk": "lt(mod(t,1.23),0.13)",
    "run": "lt(mod(t,0.62),0.11)",
}


def draw_impact_plate(path: Path, *, weather: str) -> None:
    if weather not in ("day","night","wind","cloudy","rain","storm"):
        raise ValueError("Invalid authored weather")
    im=Image.new("RGBA",(188,88),(0,0,0,0))
    d=ImageDraw.Draw(im)
    shade=(171,190,193,82) if weather=="night" else (183,168,138,93)
    for x,y,r in ((30,55,17),(67,34,22),(106,46,16),(150,61,12)):
        d.ellipse((x-r,y-r,x+r,y+r),fill=shade)
    im=im.filter(ImageFilter.GaussianBlur(7))
    path.parent.mkdir(parents=True,exist_ok=True)
    im.save(path,format="PNG")


def overlay_impact(*,graph: str,label: str,names: list[str],
                   action: str,body_x: str) -> tuple[str,str,list[str]]:
    """Overlay subtle contact puffs near the feet for selected actions only."""
    if action not in ("idle","walk","run","jump","fly","talk","surprise","rest"):
        raise ValueError("Invalid character action")
    if action not in _ACTION_TIMING:
        return graph,label,names
    if not isinstance(body_x,str) or len(body_x)>25000 or any(c in body_x for c in ";[]'\":"):
        raise ValueError("Unsafe original pose")
    if "impact" in names:
        raise ValueError("Impact overlay already applied")
    idx=len(names)
    enable=_ACTION_TIMING[action]
    graph+=(f";[{label}][{idx}:v]overlay=x='({body_x})+99':y=570:"
            f"enable='{enable}':eval=frame:format=auto[impactdone]")
    return graph,"impactdone",names+["impact"]
