"""Continuous cinematic length-scale infographic, grounded in authored narration.

An original reusable motion-graphics renderer: one persistent measuring world,
source-only numerical landmarks and one uninterrupted interpolated progress
clock. Never extracts facts from a title or generates missing measurements.

This is a deliberately narrow quantitative grammar, not an arbitrary-topic
animation model. Unsupported or ambiguous narrations use the previous engine.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from functools import lru_cache
import math
import re

from PIL import Image, ImageDraw, ImageFont, ImageFilter

VERSION = "source-anchored-continuous-log-scale-cinematic-v1"
# Base units are metres. Exact SI definitions except the internationally
# conventional light year = Julian year (365.25 days) * 299792458 m/s.
_UNIT_FACTORS = {
    "mm": ("mm", "0.001"),
    "millimeter": ("mm", "0.001"),
    "millimeters": ("mm", "0.001"),
    "millimetre": ("mm", "0.001"),
    "millimetres": ("mm", "0.001"),
    "cm": ("cm", "0.01"),
    "centimeter": ("cm", "0.01"),
    "centimeters": ("cm", "0.01"),
    "centimetre": ("cm", "0.01"),
    "centimetres": ("cm", "0.01"),
    "m": ("m", "1"),
    "meter": ("m", "1"),
    "meters": ("m", "1"),
    "metre": ("m", "1"),
    "metres": ("m", "1"),
    "mètre": ("m", "1"),
    "mètres": ("m", "1"),
    "km": ("km", "1000"),
    "kilometer": ("km", "1000"),
    "kilometers": ("km", "1000"),
    "kilometre": ("km", "1000"),
    "kilometres": ("km", "1000"),
    "kilomètre": ("km", "1000"),
    "kilomètres": ("km", "1000"),
    "mile": ("mi", "1609.344"),
    "miles": ("mi", "1609.344"),
    "foot": ("ft", "0.3048"),
    "feet": ("ft", "0.3048"),
    "inch": ("in", "0.0254"),
    "inches": ("in", "0.0254"),
    "light-year": ("ly", "9460730472580800"),
    "light-years": ("ly", "9460730472580800"),
    "light year": ("ly", "9460730472580800"),
    "light years": ("ly", "9460730472580800"),
    "année-lumière": ("ly", "9460730472580800"),
    "années-lumière": ("ly", "9460730472580800"),
}
_UNITS = "|".join(re.escape(x) for x in
                 sorted(_UNIT_FACTORS, key=lambda x: (-len(x), x)))
_QUANTITY = re.compile(
    r"(?<![\w.])(?P<number>\d{1,12}(?:\.\d{1,5})?)"
    r"\s*(?P<unit>" + _UNITS + r")\b", re.IGNORECASE)


def derive_scale_journey(beats: list[dict]) -> dict | None:
    """Accept only 3-12 sequential strictly growing explicit length claims.

    Each source paragraph must contain exactly one unambiguous magnitude
    with an allowed length unit. Mixed SI units are converted exactly;
    no missing facts, extrapolation or guessed comparisons are generated.
    """
    if type(beats) is not list or not 3 <= len(beats) <= 12:
        return None
    points = []
    prior = Decimal("0")
    for beat in beats:
        if type(beat) is not dict or type(beat.get("narration")) is not str:
            return None
        matches = list(_QUANTITY.finditer(beat["narration"]))
        if len(matches) != 1:
            return None
        match = matches[0]
        try:
            value = Decimal(match.group("number"))
            unit, factor = _UNIT_FACTORS[match.group("unit").casefold()]
            metres = value * Decimal(factor)
        except (InvalidOperation, KeyError, ArithmeticError):
            return None
        if not Decimal("0.000000001") <= metres <= Decimal("1e34"):
            return None
        if metres <= prior:
            return None
        prior = metres
        label = beat.get("title")
        if type(label) is not str or not label.strip():
            label = match.group(0)
        points.append({
            "sourceSpan": match.group(0),
            "value": format(value, "f"),
            "unit": unit,
            "metres": format(metres, "f"),
            "label": " ".join(label.split()[:8])[:64],
            "illustration": _explicit_landmark(beat["narration"]),
        })
    # A tiny increase compared to previous stages is not a chart journey.
    if prior / Decimal(points[0]["metres"]) < Decimal("2"):
        return None
    return {"engine": VERSION, "metric": "length",
            "baseUnit": "m", "points": points}


def _explicit_landmark(text: str) -> str:
    """Only display an original icon when this beat actually names the object."""
    terms = (
        ("mountain", r"\b(?:mountains?|montagnes?|everest)\b"),
        ("earth", r"\b(?:earth|terre|planète|planet)\b"),
        ("moon", r"\b(?:moon|lune)\b"),
        ("tower", r"\b(?:towers?|skyscrapers?|buildings?|"
                  r"immeubles?|tours?|bâtiments?)\b"),
        ("tree", r"\b(?:trees?|forest|arbre|arbres|forêt)\b"),
        ("human", r"\b(?:person|people|human|humain|humains|personne)\b"),
    )
    for kind, pattern in terms:
        if re.search(pattern, text, re.IGNORECASE):
            return kind
    return "ruler"


def scale_coordinate(journey: dict, metres: Decimal) -> float:
    """Global base-10 logarithmic axis shared by every beat and every frame."""
    points = journey["points"]
    smallest = Decimal(points[0]["metres"])
    largest = Decimal(points[-1]["metres"])
    lower = math.log10(float(smallest)) - .45
    upper = math.log10(float(largest)) + .45
    position = (math.log10(float(metres)) - lower) / (upper-lower)
    return max(.0, min(1., position))


def eased_progress(journey: dict, index: int, local: float) -> float:
    """Continuous position at boundaries; no per-shot restart or jump."""
    if (type(index) is not int or not 0 <= index < len(journey["points"])
            or type(local) not in (int, float) or not math.isfinite(local)
            or not 0 <= local <= 1):
        raise ValueError("Invalid continuous scale animation clock")
    stops = journey["points"]
    high = Decimal(stops[index]["metres"])
    low = (Decimal(stops[index-1]["metres"]) if index else high / Decimal(2))
    ease = local*local*(3.-2.*local)
    return (1.-ease)*scale_coordinate(journey,low)+ease*scale_coordinate(journey,high)


@lru_cache(maxsize=12)
def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",size)


def _fitted(draw: ImageDraw.ImageDraw, text: str, max_width: int,
            start_size: int, *, bold: bool = False):
    text = " ".join(text.split())
    for size in range(start_size, max(10,start_size//2)-1,-1):
        font = _font(size,bold)
        if draw.textlength(text,font=font) <= max_width:
            return text,font
    # A visible but honestly abbreviated editorial heading is preferable
    # to a silent source claim being truncated; full source remains narrated.
    font = _font(max(10,start_size//2),bold)
    while text and draw.textlength(text+"…",font=font) > max_width:
        text=text[:-1]
    return text.rstrip()+"…",font


def _paint_landmark(draw: ImageDraw.ImageDraw, kind: str,
                    x: int, base: int, unit: int, stroke: tuple[int,int,int]):
    """Original bounded line-art context icons, not stolen visual assets."""
    w = max(12,unit)
    thick=max(2,w//36)
    if kind == "tree":
        draw.line([(x,base),(x,base-w*.76)],fill=stroke,width=thick*3)
        for dx,dy in ((-.36,-.44),(.4,-.58),(-.30,-.72),(.25,-.86)):
            draw.line([(x,base-w*.40),(x+w*dx,base+w*dy)],
                      fill=stroke,width=thick*2)
        for dx,dy in ((-.35,-.55),(.35,-.68),(-.15,-.90)):
            draw.ellipse((x+w*(dx-.23),base+w*(dy-.21),
                          x+w*(dx+.23),base+w*(dy+.21)),
                         outline=stroke,width=thick)
    elif kind == "tower":
        draw.polygon([(x-w*.38,base),(x-w*.36,base-w),
                      (x+w*.36,base-w),(x+w*.38,base)],
                     outline=stroke,width=thick)
        for row in range(5):
            for col in range(3):
                ox=x-w*.25+col*w*.23
                oy=base-w*.85+row*w*.15
                draw.rectangle((ox,oy,ox+w*.11,oy+w*.07),
                               outline=stroke,width=max(1,thick//2))
    elif kind == "mountain":
        draw.line([(x-w*.78,base),(x-w*.18,base-w*.88),
                   (x+w*.05,base-w*.58),(x+w*.33,base-w*1.13),
                   (x+w*.84,base)],fill=stroke,width=thick*2,joint="curve")
        draw.line([(x-w*.44,base-w*.36),(x-w*.18,base-w*.88),
                   (x-w*.02,base-w*.67)],fill=(239,214,175),width=thick)
    elif kind in ("earth","moon"):
        r=w*.49
        draw.ellipse((x-r,base-2*r,x+r,base),outline=stroke,width=thick*2)
        if kind=="earth":
            for dx,dy in ((-.24,-.72),(.19,-.52),(-.18,-.29)):
                draw.ellipse((x+dx*w-w*.13,base+dy*w-w*.09,
                              x+dx*w+w*.13,base+dy*w+w*.09),
                             fill=(36,109,124),outline=stroke,width=1)
        else:
            for dx,dy in ((-.18,-.6),(.18,-.47),(.0,-.22)):
                r2=w*.07
                draw.ellipse((x+dx*w-r2,base+dy*w-r2,
                              x+dx*w+r2,base+dy*w+r2),
                             outline=stroke,width=1)
    elif kind=="human":
        r=w*.15
        draw.ellipse((x-r,base-w*.95,x+r,base-w*.65),
                     outline=stroke,width=thick)
        draw.line([(x,base-w*.65),(x,base-w*.22)],fill=stroke,width=thick*2)
        draw.line([(x-w*.28,base-w*.51),(x,base-w*.42),
                   (x+w*.28,base-w*.51)],fill=stroke,width=thick)
        draw.line([(x,base-w*.22),(x-w*.24,base)],
                  fill=stroke,width=thick)
        draw.line([(x,base-w*.22),(x+w*.24,base)],
                  fill=stroke,width=thick)
    else:
        draw.rounded_rectangle((x-w*.32,base-w*.98,
                                x+w*.32,base),radius=thick*2,
                               outline=stroke,width=thick)
        for y in range(1,9):
            l=w*(.24 if y%2==0 else .11)
            yy=base-w*(y/10)
            draw.line([(x-w*.30,yy),(x-w*.30+l,yy)],
                      fill=stroke,width=max(1,thick//2))


def render_scale_frame(
    journey: dict, topic: str, frame: int,
    boundaries: list[int], position: int, width: int, height: int
) -> Image.Image:
    """Render a self-contained 9:16, stage-persistent animated comparison.

    Numerical labels are ALWAYS original quantities (not interpolated
    synthetic factual claims). Geometry smoothly interpolates between them
    on an absolute log axis to convey orders of magnitude.
    """
    if (type(frame) is not int or type(boundaries) is not list
            or type(position) is not int
            or not 0 <= position < len(journey["points"])
            or not boundaries[position] <= frame < boundaries[position+1]
            or width not in (360,720,1080) or height != width*16//9):
        raise ValueError("Invalid grounded scale video frame")
    first,last=boundaries[position:position+2]
    local=(frame-first)/max(1,last-first)
    scope=eased_progress(journey,position,local)
    w,h=width,height
    im=Image.new("RGB",(w,h),(7,12,29))
    d=ImageDraw.Draw(im)
    # Continuous original navy/violet luminous night, fixed in world space.
    for y in range(h):
        q=y/h
        d.line((0,y,w,y),fill=(
            round(7+11*q),round(12+8*q),
            round(29+13*math.sin(math.pi*q)**2)))
    for i in range(54):
        sx=((i*479+101)%991)/991*w
        sy=((i*311+59)%991)/991*h*.82
        rad=max(1,w//720)
        glow=36+(i%5)*9
        d.ellipse((sx-rad,sy-rad,sx+rad,sy+rad),
                  fill=(glow//2,glow//2,glow))
    # Unbroken upper typography system; current stage text can change but
    # overall layout, geometry, ruler and field never reset.
    title,tf=_fitted(d,topic,w*.85,max(15,round(w*.055)),bold=True)
    x=(w-d.textlength(title,font=tf))/2
    d.text((x,round(h*.053)),title,font=tf,fill=(239,245,255))
    unit_color=(106,241,208)
    ref=journey["points"][position]
    value_label=ref["sourceSpan"]
    value,vf=_fitted(d,value_label,w*.82,round(w*.065),bold=True)
    d.text(((w-d.textlength(value,font=vf))/2,round(h*.126)),
           value,font=vf,fill=unit_color)
    base_y=round(h*.198)
    left,right=round(w*.10),round(w*.90)
    d.line((left,base_y,right,base_y),fill=(64,84,108),
           width=max(2,w//270))
    for t in range(17):
        x=left+(right-left)*t/16
        d.line((x,base_y-round(w*.003),x,base_y+round(w*.003)),
               fill=(108,134,158),width=1)
    # Previous absolute landmarks remain fixed on the SAME measuring ruler.
    for point in journey["points"]:
        x=left+(right-left)*scale_coordinate(
            journey,Decimal(point["metres"]))
        d.ellipse((x-w*.004,base_y-w*.004,x+w*.004,base_y+w*.004),
                  fill=(91,136,144))
    knob=left+(right-left)*scope
    d.line((left,base_y,knob,base_y),fill=unit_color,
           width=max(2,w//135))
    r=max(3,w*.010)
    d.ellipse((knob-r,base_y-r,knob+r,base_y+r),
              fill=(240,251,255),outline=unit_color,width=max(1,w//400))
    # Stable bottom world stage with subtle perspective; the spire moves
    # continuously rather than recreating a slide for each numerical beat.
    ground=round(h*.783)
    for k in range(6):
        yy=ground+round(k*k*h*.0043)
        d.line((0,yy,w,yy),fill=(26+4*k,49+4*k,72+4*k),width=1)
    for k in range(-4,5):
        px=w*.57+(k/4)*w*1.2
        d.line((w*.57,ground,px,h),fill=(23,42,67),width=1)
    d.line((0,ground,w,ground),fill=(212,149,120),
           width=max(2,w//250))
    # Soft luminous tower is a persistent foreground world object.
    cx=round(w*.60)
    tower_min=h*.075
    tower_max=h*.47
    tower_height=tower_min+(tower_max-tower_min)*scope
    top=round(ground-tower_height)
    glow=Image.new("RGBA",im.size,(0,0,0,0))
    gd=ImageDraw.Draw(glow)
    for t in range(8,0,-1):
        radius=max(2,w*.003*t)
        opacity=round(16+(8-t)*2)
        gd.line((cx,top,cx,ground),
                fill=(255,170,92,opacity),
                width=round(radius*2))
    glow=glow.filter(ImageFilter.GaussianBlur(radius=max(2,round(w*.014))))
    im=Image.alpha_composite(im.convert("RGBA"),glow).convert("RGB")
    d=ImageDraw.Draw(im)
    d.line((cx,top,cx,ground),fill=(245,166,102),
           width=max(5,round(w*.012)))
    d.line((cx-round(w*.002),top,cx-round(w*.002),ground),
           fill=(255,247,211),width=max(2,round(w*.004)))
    spark=max(3,round(w*.010))
    d.ellipse((cx-spark,top-spark,cx+spark,top+spark),
              fill=(255,246,200),outline=(255,172,91),width=2)
    # Distinct object icons can appear ONLY from source-mentioned nouns.
    icon_x=round(w*.26)
    icon_base=ground
    icon_size=round(w*.205)
    _paint_landmark(d,ref["illustration"],icon_x,icon_base,icon_size,
                    (100,218,200))
    # One grounded source phrase, shown on the world rather than a slide card.
    landmark,lf=_fitted(d,ref["label"],round(w*.46),
                        max(12,round(w*.027)),bold=False)
    label_y=round(h*.805)
    d.text((round(w*.08),label_y),landmark,font=lf,
           fill=(188,218,226))
    # History markers are tied to past source values, never invented levels.
    # Fading record replaces repeated titles while keeping the same axis.
    for i in range(max(0,position-3),position):
        point=journey["points"][i]
        stage=eased_progress(journey,i,1.)
        py=round(ground-(tower_min+(tower_max-tower_min)*stage))
        delta=position-i
        text,font=_fitted(d,point["sourceSpan"],round(w*.20),
                          max(10,round(w*.019)),bold=False)
        xt=round(w*.69)
        d.line((cx+round(w*.016),py,xt-5,py),
               fill=(62,105,121),width=1)
        d.text((xt,py-font.size*.55),text,font=font,
               fill=(100+17*(3-delta),155,170))
    # Small moving glints signal current progress, independent of beat cuts.
    for i in range(11):
        phase=(frame*.013+i*.223)
        xx=cx+math.sin(phase*3.1+i)*w*(.022+(i%4)*.008)
        yy=ground-(tower_height*((i+1)/12)) + math.sin(phase*2)*w*.013
        rr=max(1,w//700)
        d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(246,188,138))
    return im
