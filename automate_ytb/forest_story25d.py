"""Deterministic event-directed four-shot storyboard for the forest pilot.

Timing follows the actual grounded contact and subsequent butterfly flight.
This is a visual editorial preview, not a claim of neural narration.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image, ImageDraw, ImageFont

from .forest_contact25d import IMPACT_TIME

VERSION="forest-event-directed-four-beat-story-v1"
SIZE=(1080,1920)
STORY=(
    ("discovery",0.,IMPACT_TIME,"A LITTLE DISCOVERY","Every step holds a surprise."),
    ("contact",IMPACT_TIME,IMPACT_TIME+.65,"ONE GENTLE TOUCH","A flower answers."),
    ("arrival",IMPACT_TIME+.65,IMPACT_TIME+2.55,"SOMETHING STIRS","A visitor appears."),
    ("departure",IMPACT_TIME+2.55,7.2,"AND LIFE MOVES ON","The meadow comes alive."),
)


@dataclass(frozen=True)
class StoryShot:
    beat: str
    title: str
    subtitle: str
    progress: float
    camera_x: float
    camera_y: float


def story_shot(t: float) -> StoryShot:
    if type(t) not in (float,int) or not math.isfinite(t) or not 0<=t<=7.2:
        raise ValueError("Invalid bounded forest story clock")
    for name,start,end,title,subtitle in STORY:
        if t<end or name=="departure":
            q=max(0.,min(1.,(t-start)/(end-start)))
            eased=q*q*(3-2*q)
            # Return to neutral at shot cuts: no sudden jump at a cut.
            move=math.sin(math.pi*q)
            if name=="discovery":
                x,y=22*move,-7*move
            elif name=="contact":
                x,y=-28*move,11*move
            elif name=="arrival":
                x,y=34*move,-12*move
            else:
                x,y=-20*move,7*move
            return StoryShot(name,title,subtitle,eased,x,y)
    raise AssertionError("Unreachable storyboard beat")


def story_overlay(t: float) -> Image.Image:
    shot=story_shot(t)
    image=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype("DejaVuSans-Bold.ttf",45)
        small=ImageFont.truetype("DejaVuSans.ttf",29)
    except OSError:
        font=ImageFont.load_default()
        small=font
    # Gentle per-shot title fades, no static slideshow or giant opaque cards.
    q=shot.progress
    alpha=round(255*min(1.,q/.14,(1-q)/.12))
    alpha=max(0,alpha)
    if not alpha:
        return image
    d.rounded_rectangle((55,105,1025,253),radius=24,
                        fill=(9,27,37,round(alpha*.68)))
    d.text((90,122),shot.title,font=font,fill=(244,251,238,alpha))
    d.text((91,193),shot.subtitle,font=small,fill=(191,236,215,alpha))
    return image
