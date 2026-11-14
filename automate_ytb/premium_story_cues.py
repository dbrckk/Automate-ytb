"""Source-grounded visual actions for original premium science shorts.

The scene pack defines the actual object artwork. This module supplies
*actions* and scene-specific disclosures; it never fabricates numerical
claims or interprets words beyond the explicitly finite source vocabulary.

The compositing hooks are reusable for future subject action families.
All animations derive solely from absolute frame, clip boundaries and the
literal validated narration, so seeking and re-rendering are reproducible.
"""
from __future__ import annotations

import math
import re

from PIL import Image, ImageDraw, ImageFilter

VERSION = "original-narration-cued-2p5d-actions-v1"

# Specific phrases before generic matches; a hook that mentions 'wheels'
# must not eclipse a later technical sentence explicitly about motors.
_CUES = (
    ("airflow", re.compile(r"\b(?:air resistance|air drag|aerodynamic drag|wind resistance|résistance de l.air|traînée aérodynamique)\b", re.I)),
    ("propulsion", re.compile(r"\b(?:propulsion|propel\w*|poles?\b|motor\b|motors\b|pulled forward|pushed from behind|moteur|propulsion)\b", re.I)),
    ("wheels", re.compile(r"\b(?:rubber wheels|wheel\w*|retract\w*|roues?|rétract\w*)\b", re.I)),
    ("levitation", re.compile(r"\b(?:levitat\w*|lift\w*\b|magnet\w*\b|centered|centré\w*|lévitat\w*|aimant\w*)\b", re.I)),
    ("glide", re.compile(r"\b(?:maglev|train|guideway|track|rail|glid\w*|gliss\w*)\b", re.I)),
)

# Distinguishes when the narration explicitly denies wheel contact.
_NO_CONTACT = re.compile(r"\b(?:no wheels touching|without wheel contact|no wheel contact|aucun contact des roues)\b", re.I)


def cue_for_narration(narration: str) -> str | None:
    if type(narration) is not str or not 3 <= len(narration) <= 650:
        raise ValueError("Expected original bounded narration")
    # Air drag is the distinct terminal mechanism even when the
    # sentence also recalls an earlier contact-free stage.
    for label, pattern in _CUES[:2]:
        if pattern.search(narration):
            return label
    if _NO_CONTACT.search(narration):
        return "gap"
    for label, pattern in _CUES[2:]:
        if pattern.search(narration):
            return label
    return None


def action_sequence(beats: list[dict]) -> list[str | None]:
    if type(beats) is not list or not 2 <= len(beats) <= 12:
        raise ValueError("Expected a bounded narration sequence")
    return [cue_for_narration(beat["narration"]) for beat in beats]


def _ease(t: float) -> float:
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)


def _stroke_path(draw: ImageDraw.ImageDraw, points, color, thickness: int):
    draw.line([(round(x),round(y)) for x,y in points],
              fill=color,width=thickness,joint="curve")


def _draw_arc(draw, cx: float, baseline: float, radius: float, strength: float,
              hue: tuple[int,int,int], w: int):
    # A stylized field-loop ribbon around a guideway contact; not a
    # quantified electromagnetic field simulation.
    points=[]
    for index in range(19):
        u=index/18
        x=cx+(u-.5)*radius*2
        y=baseline-math.sin(math.pi*u)*radius*.43
        points.append((x,y))
    _stroke_path(draw,points,(*hue,round(145*strength)),max(2,round(w*.007)))


def render_maglev_action(artwork: Image.Image, narration: str, *,
                         frame: int, first: int, last: int) -> Image.Image:
    """Overlay grounded mechanism-specific actions on a real 2.5D stage.

    A shot with a source wheel explanation draws wheels; a source motor
    explanation lights the guideway sequentially; the two scenes do not
    become static copies. Only overlays on owned procedural maglev artwork.
    """
    if (not isinstance(artwork,Image.Image) or artwork.mode!="RGBA"
            or min(artwork.size)<64 or max(artwork.size)>1500
            or type(frame) is not int or type(first) is not int
            or type(last) is not int or not 0 <= first <= frame < last):
        raise ValueError("Invalid source-art action stage or frame")
    cue=cue_for_narration(narration)
    if cue is None:
        return artwork
    w,h=artwork.size
    u=(frame-first)/max(1,last-first)
    reveal=_ease(min(1.,u*3.))
    pulse=.5+.5*math.sin(2*math.pi*(frame/30.)*1.05)
    # Integrate within the real vehicle/guideway stage, never over captions.
    left,right=int(w*.13),int(w*.95)
    ground=int(h*.752)
    layer=Image.new("RGBA",artwork.size)
    d=ImageDraw.Draw(layer)
    mint=(84,244,221)
    gold=(250,182,109)
    white=(237,252,246)
    line_w=max(2,round(w*.007))

    if cue=="wheels":
        # Actual wheel-support concept appears only for a source mentioning
        # wheels. Slow translucent retraction indicates a change of support.
        retract=_ease(max(0.,(u-.33)/.50)) if re.search(r"retract",narration,re.I) else 0.
        for x in (int(w*.34),int(w*.68)):
            cy=ground-round(h*.029)-round(retract*h*.043)
            radius=max(4,round(w*.031))
            opacity=round(245*(1-retract*.88))
            d.line((x,cy-radius*2,x,cy), fill=(*white,round(opacity*.8)),
                   width=max(2,line_w))
            d.ellipse((x-radius,cy-radius,x+radius,cy+radius),
                      fill=(19,41,60,opacity),outline=(*white,opacity),
                      width=line_w)
            r2=radius*.44
            d.ellipse((x-r2,cy-r2,x+r2,cy+r2),
                      fill=(*gold,round(opacity*.7)))
        d.line((int(w*.23),ground,int(w*.80),ground),
               fill=(*gold,round(180*reveal)),width=line_w)
    elif cue in ("levitation","gap"):
        # Glowing separation strip makes the contact-free distance visible.
        for i in range(8):
            x=left+round((right-left)*(i+.5)/8)
            phase=math.sin(2*math.pi*((frame/30.)*.85+i/8))
            radius=round(w*(.067+.014*phase))
            _draw_arc(d,x,ground+round(h*.025),radius,
                      reveal*(.58+.42*pulse),mint,w)
        d.line((left,ground+round(h*.006),right,ground+round(h*.006)),
               fill=(*mint,round(110*reveal)),width=line_w)
        # An animated height bracket, not an invented numeric distance.
        x=int(w*.91)
        a=round(h*.704)
        b=round(h*.75)
        d.line((x,a,x,b),fill=(*white,round(220*reveal)),width=line_w)
        for y in (a,b):
            d.line((x-round(w*.014),y,x+round(w*.014),y),
                   fill=(*white,round(220*reveal)),width=line_w)
    elif cue=="propulsion":
        # Phase-aligned moving coils convey sequence and directional travel.
        y=ground+round(h*.038)
        spacing=(right-left)/7.
        for i in range(7):
            x=left+(i+.5)*spacing
            phase=(i/7.-frame/105.)%1.
            power=(1-phase)**2
            radius=max(4,round(w*.018))
            alpha=round(reveal*(80+170*power))
            d.rounded_rectangle((x-radius,y-radius,x+radius,y+radius),
                                radius=max(2,radius//3),
                                fill=(*mint,round(alpha*.38)),
                                outline=(*white,alpha),width=line_w)
        # Directional motion packets are tied to the track, not arbitrary
        # rings around an unrelated static icon.
        for i in range(3):
            frac=(frame/53.+i/3.)%1.
            x=left+(right-left)*frac
            y=ground-round(h*(.015+.012*i))
            d.line((x-round(w*.055),y,x,y),
                   fill=(*mint,round(150*reveal)),width=line_w)
            d.line((x-round(w*.015),y-round(w*.015),x,y,
                    x-round(w*.015),y+round(w*.015)),
                   fill=(*white,round(200*reveal)),width=line_w)
    elif cue=="airflow":
        # Incoming atmospheric streaks at the train nose, revealing drag.
        cx=int(w*.89)
        for i in range(10):
            phase=(frame/71.+i*.137)%1.
            x=cx+round((.12-phase*.48)*w)
            y=round(h*(.49+(i%5)*.038)+math.sin(phase*math.tau)*h*.006)
            if 0<x<w:
                length=round(w*(.065+.025*(i%3)))
                d.line((x,y,x-length,y),
                       fill=(*white,round(reveal*(63+24*(i%4)))),
                       width=max(1,line_w-1))
        for q in range(4):
            x=cx-round(q*w*.05)
            y=int(h*(.57+.015*q))
            d.arc((x-round(w*.044),y-round(w*.03),
                   x+round(w*.044),y+round(w*.03)),
                  190,335,fill=(*gold,round(reveal*(75+30*pulse))),
                  width=line_w)
    else:  # glide: source-mentioned vehicle travel, not invented hardware.
        for i in range(8):
            phase=(frame/90.+i*.163)%1.
            x=right-round((right-left)*phase)
            y=round(h*(.64+.02*(i%3)))
            d.line((x-round(w*.072),y,x,y),
                   fill=(*mint,round(35+95*reveal)),
                   width=max(1,line_w-1))

    # Soft-light layer is local to the illuminated action, with no diffusion
    # model download or time-dependent random number generation.
    tile=(max(0,left-round(w*.09)),round(h*.43),w,
          min(h,ground+round(h*.12)))
    clipped=layer.crop(tile)
    blur=clipped.resize((max(24,clipped.width//3),
                         max(24,clipped.height//3)),Image.Resampling.BILINEAR)
    blur=blur.filter(ImageFilter.GaussianBlur(max(1.5,w*.009)))
    blur=blur.resize(clipped.size,Image.Resampling.BILINEAR)
    blur.putalpha(blur.getchannel("A").point(lambda a:round(a*.32)))
    image=artwork.copy()
    image.alpha_composite(blur,(tile[0],tile[1]))
    image.alpha_composite(layer)
    return image
