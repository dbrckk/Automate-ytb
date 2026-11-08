"""Original physically anchored plush-character art pass for forest 2.5D.

P3.7 enhances the existing identity-preserving sprites rather than replacing
their actual silhouette or re-solving IK: original procedural fur marks, soft
per-part wrapped light, jointed tapered limbs, textured toes, articulated
scarf tip, and contact-driven facial acting. Static art is cached by forest25d.
No model API, imported image, stochastic per-frame noise or fake 3D claim.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .rig25d import LegPose
from .forest_contact25d import IMPACT_TIME
from .animated_forest import COLORS

VERSION = "original-p37-plush-character-physical-acting-v1"
KINDS = ("fox", "rabbit", "cat")
PART_SIZES = {"body":(350,440),"ear":(150,240),"tail":(230,240)}
WARM = {"fox":(255,220,159),"rabbit":(255,252,242),"cat":(188,239,249)}
COOL = {"fox":(93,67,104),"rabbit":(101,97,145),"cat":(34,75,104)}


def finish_sprite(sprite: Image.Image, *, kind: str, part: str) -> Image.Image:
    """Add original masked fur and diffuse light WITHOUT changing any alpha."""
    if kind not in KINDS or part not in PART_SIZES:
        raise ValueError("Unsupported original P3.7 species or material")
    if not isinstance(sprite,Image.Image) or sprite.mode!="RGBA" or sprite.size!=PART_SIZES[part]:
        raise ValueError("Expected exact RGBA original animal sprite")
    source_alpha=sprite.getchannel("A")
    canvas=sprite.copy()
    if source_alpha.getbbox() is None:
        return canvas
    w,h=canvas.size
    # Large smooth shafts of warm key light and blue-violet bounced shadow.
    # Pixel strengths are clipped against the *existing* painted silhouette.
    key=Image.new("L",canvas.size)
    d=ImageDraw.Draw(key)
    d.ellipse((round(-.27*w),round(-.23*h),round(.87*w),round(.73*h)),
              fill=102 if part=="body" else 86)
    key=key.filter(ImageFilter.GaussianBlur(round(min(w,h)*.16)))
    key=ImageChops.multiply(key,source_alpha)
    lamp=Image.new("RGBA",canvas.size,WARM[kind]+(0,))
    lamp.putalpha(key)
    canvas.alpha_composite(lamp)
    shade=Image.new("L",canvas.size)
    sd=ImageDraw.Draw(shade)
    sd.ellipse((round(.40*w),round(.42*h),round(1.26*w),round(1.30*h)),
               fill=89 if part=="body" else 77)
    shade=shade.filter(ImageFilter.GaussianBlur(round(min(w,h)*.15)))
    shade=ImageChops.multiply(shade,source_alpha)
    bounce=Image.new("RGBA",canvas.size,COOL[kind]+(0,))
    bounce.putalpha(shade)
    canvas.alpha_composite(bounce)

    # Original, sparse directional tufts on flank, cheeks and tail. Texture
    # stays inside the source alpha and avoids the eyes/nose/face on purpose.
    details=Image.new("RGBA",canvas.size)
    brush=ImageDraw.Draw(details)
    seed={"fox":1729,"rabbit":2631,"cat":3497}[kind]
    rng=random.Random(seed+{"body":100,"ear":200,"tail":300}[part])
    if part=="body":
        for i in range(128):
            x=rng.randrange(71,280)
            y=rng.randrange(287,370)
            length=rng.randrange(4,12)
            rgb=WARM[kind] if i%4 else COOL[kind]
            brush.arc((x-4,y,x+length,y+length//2+5),166,295,
                      fill=rgb+(65 if i%4 else 54,),width=1)
        for side in (-1,1):
            for j in range(18):
                x=(73 if side<0 else 276)+side*rng.randrange(0,17)
                y=181+j*6
                dx=side*rng.randrange(3,11)
                brush.line((x,y,x+dx,y+3),
                           fill=WARM[kind]+(52,),width=1)
    elif part=="ear":
        for i in range(44):
            x=rng.randrange(39,111)
            y=rng.randrange(96,174)
            brush.line((x,y,x+rng.randrange(-4,5),y+rng.randrange(6,16)),
                       fill=WARM[kind]+(55,),width=1)
    else:
        for i in range(140):
            x=rng.randrange(23,207)
            y=rng.randrange(28,218)
            dx=rng.randrange(-5,10)
            brush.line((x,y,x+dx,y+rng.randrange(3,10)),
                       fill=WARM[kind]+(58 if i%3 else 33,),width=1)
    details.putalpha(ImageChops.multiply(details.getchannel("A"),source_alpha))
    canvas.alpha_composite(details)
    canvas.putalpha(source_alpha)
    return canvas


def facial_pose(t: float, *, interaction: bool) -> str:
    """Facial phases are driven by the rig's real paw-flower impact timestamp."""
    if (type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=7.2
            or type(interaction) is not bool):
        raise ValueError("Invalid grounded emotional-acting clock")
    if interaction and IMPACT_TIME-.43<=t<IMPACT_TIME+.10:
        return "look-down"
    if interaction and IMPACT_TIME+.10<=t<IMPACT_TIME+.53:
        return "surprise"
    if interaction and IMPACT_TIME+.53<=t<IMPACT_TIME+2.70:
        return "follow"
    if (t%3.1)<.105:
        return "blink"
    return "body"


def _segment(draw: ImageDraw.ImageDraw,
             a:tuple[float,float],b:tuple[float,float],
             radius_a:float,radius_b:float,
             *,fur:tuple[int,...],dark:tuple[int,...],
             light:tuple[int,...]) -> None:
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    if length<1:
        raise ValueError("Degenerate original two-bone limb")
    nx,ny=-dy/length,dx/length
    def strip(ra,rb):
        return ((a[0]+nx*ra,a[1]+ny*ra),
                (a[0]-nx*ra,a[1]-ny*ra),
                (b[0]-nx*rb,b[1]-ny*rb),
                (b[0]+nx*rb,b[1]+ny*rb))
    draw.polygon(strip(radius_a+3,radius_b+3),fill=dark)
    draw.polygon(strip(radius_a,radius_b),fill=fur)
    draw.line(((a[0]-nx*radius_a*.48,a[1]-ny*radius_a*.48),
               (b[0]-nx*radius_b*.54,b[1]-ny*radius_b*.54)),
              fill=light,width=4)
    draw.line(((a[0]+nx*radius_a*.69,a[1]+ny*radius_a*.69),
               (b[0]+nx*radius_b*.70,b[1]+ny*radius_b*.70)),
              fill=dark,width=3)


def draw_plush_leg(draw: ImageDraw.ImageDraw, *, pose: LegPose,
                   kind: str, side: str) -> None:
    """Volume-shaped two-bone leg; exact IK target is never moved."""
    if kind not in KINDS or side not in ("left","right") or not isinstance(pose,LegPose):
        raise ValueError("Invalid plush leg or original species")
    fur=COLORS[kind]["fur"]
    dark=COLORS[kind]["dark"]
    glow=WARM[kind]+(255,)
    cool=COOL[kind]+(255,)
    _segment(draw,pose.hip,pose.knee,23,19,fur=fur,dark=dark,light=glow)
    knee_x,knee_y=pose.knee
    draw.ellipse((knee_x-22,knee_y-22,knee_x+22,knee_y+22),fill=dark)
    draw.ellipse((knee_x-18,knee_y-18,knee_x+18,knee_y+18),fill=fur)
    draw.arc((knee_x-14,knee_y-17,knee_x+12,knee_y+14),
             164,258,fill=glow,width=3)
    _segment(draw,pose.knee,pose.foot,18,15,
             fur=fur,dark=dark,light=glow)
    fx,fy=pose.foot
    # Shadow side, lifted plush dome, toe separation and rim keep paw
    # readable from medium shots. The ground anchor remains (fx,fy).
    draw.ellipse((fx-37,fy-12,fx+36,fy+12),fill=dark)
    draw.ellipse((fx-32,fy-13,fx+31,fy+7),fill=fur)
    draw.arc((fx-28,fy-11,fx+20,fy+7),185,327,fill=glow,width=3)
    for offset in (-17,-2,13):
        xx=fx+offset
        draw.arc((xx-5,fy,xx+9,fy+12),175,289,fill=cool,width=2)


def scarf_tip(t: float, *, x: float, y: float,
              kind: str, contact: bool) -> Image.Image:
    """Small cloth articulation, attached to existing scarf, world moving."""
    if (type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=7.2
            or kind not in KINDS or type(contact) is not bool
            or type(x) not in (float,int) or type(y) not in (float,int)
            or not all(math.isfinite(v) for v in (x,y))):
        raise ValueError("Invalid original articulated scarf")
    image=Image.new("RGBA",(350,440))
    d=ImageDraw.Draw(image)
    gust=9*math.sin(4.1*t+.2)+5*math.sin(7.4*t)
    if contact:
        gust+=19*math.exp(-((t-IMPACT_TIME-.25)/.4)**2)
    end_x=275+gust
    end_y=415+3*math.sin(3.8*t)
    d.polygon(((248,333),(265,329),(end_x+8,end_y-10),
               (end_x-6,end_y+3),(253,365)),fill=(204,134,56,255))
    d.polygon(((250,337),(261,334),(end_x+2,end_y-15),
               (end_x-3,end_y-1),(255,361)),fill=(246,189,82,255))
    d.line(((253,343),(end_x-3,end_y-16)),
           fill=(255,229,151,205),width=3)
    return image
