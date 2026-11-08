"""Original shot-dependent optical framing for the 2.5D forest story.

The stage remains a true multilayer 1080x1920 world; an editorial crop
physically changes apparent shot scale and subject placement. Typography is
composited *after* framing so it remains sharp and mobile-safe.
"""
from __future__ import annotations

import math

from PIL import Image

VERSION="forest-25d-physical-shot-scale-p36-v1"
SIZE=(1080,1920)
SHOTS={
    "discovery":(1.15,20.0),
    "contact":(1.33,100.0),
    "arrival":(1.25,80.0),
    "departure":(1.18,20.0),
}


def shot_crop(t: float, *, beat: str, body_x: float) -> tuple[int,int,int,int]:
    if (type(t) not in (int,float) or not math.isfinite(t)
            or not 0<=t<=7.2 or beat not in SHOTS
            or type(body_x) not in (float,int) or not math.isfinite(body_x)
            or not 150<=body_x<=600):
        raise ValueError("Invalid physical 2.5D cinematic camera")
    scale,down=SHOTS[beat]
    w=round(SIZE[0]/scale)
    h=round(SIZE[1]/scale)
    # Keep the animal around the center-third while still framing the contact
    # and the butterfly. Shift follows the actual analytic world-space torso.
    cx=SIZE[0]/2+max(-65.,min(65.,(body_x+175-540)*.28))
    cy=970.+down
    left=max(0,min(SIZE[0]-w,round(cx-w/2)))
    top=max(0,min(SIZE[1]-h,round(cy-h/2)))
    return left,top,left+w,top+h


def cinematic_reframe(image: Image.Image, *, t: float,
                      beat: str, body_x: float) -> Image.Image:
    if not isinstance(image,Image.Image) or image.size!=SIZE or image.mode!="RGBA":
        raise ValueError("Cinematic framing requires full RGBA stage")
    region=shot_crop(t,beat=beat,body_x=body_x)
    return image.crop(region).resize(SIZE,Image.Resampling.BICUBIC)
