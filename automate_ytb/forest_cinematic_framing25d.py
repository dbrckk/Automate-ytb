"""Original shot-dependent optical framing for the 2.5D forest story.

The stage remains a true multilayer 1080x1920 world; an editorial crop
physically changes apparent shot scale and subject placement. Typography is
composited *after* framing so it remains sharp and mobile-safe.
"""
from __future__ import annotations

import math

from PIL import Image

from .forest_story25d import STORY
from .rig25d import GROUND

VERSION="forest-25d-mobile-hero-camera-p44-v1"
SIZE=(1080,1920)
# A measured phone-first framing pass: the head, shoulders, real feet and
# flower fill the portrait canvas while the narration stays below the action.
# A stronger contact close-up gives the impact a visible cinematic emphasis.
SHOTS={
    "discovery":(1.55,20.0),
    "contact":(1.72,100.0),
    "arrival":(1.55,80.0),
    "departure":(1.52,20.0),
}
DOLLY={"discovery":.055,"contact":.12,"arrival":-.08,"departure":-.05}
# Camera lead preserves the animal and creates screen space for the butterfly.
LEAD={"discovery":0.,"contact":12.,"arrival":62.,"departure":30.}
PAN={"discovery":-20.,"contact":20.,"arrival":20.,"departure":-10.}
MOBILE_GROUND_Y=1375.0

def shot_crop(t: float, *, beat: str, body_x: float) -> tuple[int,int,int,int]:
    if (type(t) not in (int,float) or not math.isfinite(t)
            or not 0<=t<=7.2 or beat not in SHOTS
            or type(body_x) not in (float,int) or not math.isfinite(body_x)
            or not 150<=body_x<=600):
        raise ValueError("Invalid physical 2.5D cinematic camera")
    scale,down=SHOTS[beat]
    start,end=next((a,b) for name,a,b,*_ in STORY if name==beat)
    progress=max(0.,min(1.,(t-start)/(end-start)))
    # At every cut boundary lens movement settles to zero velocity.
    envelope=math.sin(math.pi*progress)**2
    scale+=DOLLY[beat]*envelope
    w=round(SIZE[0]/scale)
    h=round(SIZE[1]/scale)
    # Follow the real torso rather than the center of the empty world.
    # The butterfly-reveal beat explicitly reserves right-side lead room.
    cx=body_x+175.+LEAD[beat]+PAN[beat]*envelope
    # Actual ground is world-space 1361px. Keep real planted paws near a
    # consistent output y=1375, safely ABOVE the subtitles at y>=1438.
    cy=GROUND-(MOBILE_GROUND_Y-SIZE[1]/2)/scale+.11*down*envelope
    left=max(0,min(SIZE[0]-w,round(cx-w/2)))
    top=max(0,min(SIZE[1]-h,round(cy-h/2)))
    return left,top,left+w,top+h


def cinematic_reframe(image: Image.Image, *, t: float,
                      beat: str, body_x: float) -> Image.Image:
    if not isinstance(image,Image.Image) or image.size!=SIZE or image.mode!="RGBA":
        raise ValueError("Cinematic framing requires full RGBA stage")
    region=shot_crop(t,beat=beat,body_x=body_x)
    return image.crop(region).resize(SIZE,Image.Resampling.BICUBIC)
