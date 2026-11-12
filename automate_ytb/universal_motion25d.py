"""Deterministic, original cinematic 2.5D motion grammar for ANY authored subject.

This renderer deliberately stays abstract where there is no approved image:
a text-only article about an animal cannot fabricate a species-accurate model.
It replaces static slide-like bars with depth, lighting, moving causal signals,
and scale-driven visual objects. Data, voice and Foley share the scene timeline.
No image models, outside assets or random runtime state are required.
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFont

VERSION = "generic-cinematic-kinetic-stage-v1"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], amount: float):
    t = _clamp(amount)
    return tuple(round(x * (1 - t) + y * t) for x, y in zip(a, b))


def _rgb(color, multiplier=1.0):
    return tuple(max(0, min(255, round(x * multiplier))) for x in color)


@lru_cache(maxsize=24)
def _font(size: int, bold: bool = False):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else
                              "DejaVuSans.ttf", max(10, size))


def _label(draw, label: str, x: float, y: float, width: int, size: int, color,
           *, bold: bool = True) -> None:
    """All labels stay inside their explicitly supplied region."""
    text = " ".join(label.split())
    size = max(11, int(size))
    font = _font(size, bold)
    while size > 11 and draw.textbbox((0, 0), text, font=font)[2] > width:
        size -= 1
        font = _font(size, bold)
    if draw.textbbox((0, 0), text, font=font)[2] > width:
        while text and draw.textbbox((0, 0), text + "…", font=font)[2] > width:
            text = text[:-1]
        text = text.rstrip() + "…"
    draw.text((round(x), round(y)), text, font=font, fill=color,
              stroke_width=1, stroke_fill=(9, 16, 28))


@lru_cache(maxsize=18)
def _background(width: int, height: int, dark: tuple, tint: tuple):
    """Cached multiscale world texture: no per-frame random particles."""
    surface = Image.new("RGB", (width, height), dark)
    d = ImageDraw.Draw(surface)
    for y in range(height):
        t = y / max(1, height - 1)
        color = _mix(dark, tint, 0.15 + 0.46 * t * t)
        d.line((0, y, width, y), fill=color)
    # Linear perspective converges on a stable horizon even when scenes cut.
    horizon = round(height * .76)
    vanishing = width // 2
    grid = _mix(tint, dark, .38)
    for i in range(-6, 7):
        x = vanishing + round(i * width * .14)
        d.line((vanishing, horizon - 30, x, height), fill=grid, width=1)
    for depth in (.79, .82, .86, .92):
        y = round(height * depth)
        d.line((0, y, width, y), fill=grid, width=1)
    # Unique seeded constellation in every scene, with zero frame flicker.
    for i in range(56):
        x = ((i * 9973 + 1531) % 997) * width // 997
        y = ((i * 4517 + 109) % 997) * horizon // 997
        r = 1 if i % 5 else 2
        dot = _mix(tint, (223, 236, 249), (.22 if i % 4 else .45))
        d.ellipse((x-r, y-r, x+r, y+r), fill=dot)
    return surface


def _halo(draw, x, y, radius, color, intensity=1.0):
    radius = max(3, int(radius))
    for layer, strength in ((2.8, .15), (2.1, .25), (1.55, .38)):
        rr = round(radius * layer)
        stroke = max(1, round(radius * .13))
        draw.ellipse((x-rr, y-rr, x+rr, y+rr),
                     outline=(*color, round(120 * strength * intensity)),
                     width=stroke)


def _beam(draw, a, b, color, thickness):
    thickness = max(1, round(thickness))
    for scale, alpha in ((5.0, 22), (2.8, 50), (1.0, 240)):
        draw.line((round(a[0]), round(a[1]), round(b[0]), round(b[1])),
                  fill=(*color, alpha), width=max(1, round(thickness * scale)))


def _shadow(draw, x, y, rx, color=(1, 5, 13)):
    for layer, alpha in ((2.5, 21), (1.8, 40), (1.25, 72)):
        spread = rx * layer
        draw.ellipse((round(x-spread), round(y-rx*.20),
                      round(x+spread), round(y+rx*.30)),
                     fill=(*color, alpha))


def _column(draw, x, base, width, height, color, *, brightness=1.0):
    """Shaded 2.5D extruded pillar with physically common ground baseline."""
    width = max(6, round(width))
    top = round(base - max(0.0, height))
    r = width // 2
    _shadow(draw, x, base+10, r, color=(1, 7, 17))
    if height < 2:
        return
    face = _rgb(color, .58 + .40 * brightness)
    shadow = _rgb(color, .30 + .17 * brightness)
    light = _mix(color, (245, 253, 255), .43)
    # Right side is recessed: independent side and top surfaces give volume.
    draw.polygon(((x+r, top+4), (x+r+width*.24, top-width*.10),
                  (x+r+width*.24, base-width*.13), (x+r, base)),
                 fill=(*shadow, 255))
    draw.rounded_rectangle((round(x-r), top, round(x+r), round(base)),
                           radius=max(3, width//6), fill=(*face, 245))
    # During the first few growth frames the pillar can be only 2–6 px
    # tall. Pillow rejects inverted highlight bounds at these dimensions.
    if base-top >= 7:
        draw.rectangle((round(x-r*.53), top+3, round(x-r*.15), round(base-3)),
                       fill=(*light, 198))
        draw.line((round(x+r*.55), top+4, round(x+r*.55), round(base-3)),
                  fill=(*_rgb(color, .42), 150), width=max(1, width//9))
    draw.ellipse((round(x-r), top-width*.13, round(x+r), top+width*.17),
                 fill=(*_mix(face, light, .42), 245),
                 outline=(*light, 190), width=max(1,width//14))
    _halo(draw, x, top, max(4,width//5), color, brightness)
    draw.ellipse((round(x-width*.10), top-width*.10,
                  round(x+width*.10), top+width*.10),
                 fill=(*light, 240))


def _ruler(draw, left, right, y, color, ratio, width):
    line = _mix(color, (199, 222, 229), .45)
    _beam(draw, (left,y),(right,y), line, max(1,width*.004))
    n = 10
    for j in range(n+1):
        x=left+(right-left)*j/n
        h=(width*.036 if j in (0,n) else width*.021)
        draw.line((round(x), round(y-h),round(x),round(y+h*.34)),
                  fill=(*line, 160), width=max(1,round(width*.003)))
    cursor=left+(right-left)*_clamp(ratio)
    _halo(draw, cursor, y, max(4,width*.012), color)
    draw.ellipse((round(cursor-width*.012),round(y-width*.012),
                  round(cursor+width*.012),round(y+width*.012)),
                 fill=(*color,255),outline=(242,250,255,255),
                 width=max(1,round(width*.003)))


def _decimal_label(value: Decimal) -> str:
    if value >= Decimal("1e9"):
        return f"{value:.3E}".replace("E+", "e")
    if value < Decimal("0.01") and value != 0:
        return f"{value:.2E}".replace("E+", "e")
    return format(value.quantize(Decimal("0.01")), ",f").rstrip("0").rstrip(".")


def _measure(draw, beat, ratio, width, height, accent, extra, dark):
    ratio = _clamp(ratio)
    ground=round(height*.79)
    cx=round(width*.61)
    col_w=round(width*.15)
    # Height, measurement, marker and glow derive from the SAME numeric state.
    h=(.11+.53*ratio)*height if ratio > 0 else 0
    camera_dolly=round(width*.022*(ratio-.5))
    cx+=camera_dolly
    _column(draw,cx,ground,col_w,h,accent)
    _ruler(draw,width*.10,width*.90,height*.89,extra,ratio,width)
    _label(draw,beat["label"],width*.07,height*.045,
           round(width*.86),round(width*.065),(236,245,250))
    value=Decimal(str(ratio))*beat["scaleMax"]
    _label(draw,_decimal_label(value)+" "+beat["unit"],width*.07,height*.18,
           round(width*.86),round(width*.11),extra)
    _label(draw,"0",width*.09,height*.92,round(width*.23),
           round(width*.035),(171,191,212))
    _label(draw,_decimal_label(beat["scaleMax"])+" "+beat["unit"],
           width*.60,height*.92,round(width*.32),
           round(width*.033),(171,191,212))
    # Subtle reflected signal physically anchored to rising column.
    for i in range(4):
        offset=round(width*(.03+i*.04))
        draw.arc((cx-offset,ground-offset*.25,
                  cx+offset,ground+offset*.25),
                 0,180,fill=(*accent, max(15,100-i*24)),
                 width=max(1,round(width*.003)))


def _compare(draw, beat, progress, width, height, accent, extra, dark):
    maximum=max(beat["leftValue"],beat["rightValue"])
    ground=round(height*.76)
    base=round(height*.48)
    _beam(draw,(width*.11,ground),(width*.90,ground),
          _mix(accent,extra,.4),max(1,width*.006))
    for i,(key,value,col) in enumerate((("left",beat["leftValue"],accent),
                                        ("right",beat["rightValue"],extra))):
        x=round(width*(.33 if i == 0 else .70))
        height_px=base*_clamp(float(value/maximum))*_clamp(progress)
        _column(draw,x,ground,width*.18,height_px,col)
        label=beat[key]
        _label(draw,label,width*(.10 if i == 0 else .53),
               height*.80,round(width*.38),round(width*.054),
               (238,247,250))
        current=Decimal(str(_clamp(progress)))*value
        _label(draw,_decimal_label(current)+" "+beat["unit"],
               width*(.10 if i == 0 else .53),height*.865,
               round(width*.40),round(width*.065),col)
    # Single shared baseline and shared maximum make the comparison honest.
    _label(draw,"0",width*.06,height*.715,round(width*.1),
           round(width*.03),(174,192,210))


def _sequence(draw, beat, progress, width, height, accent, extra, dark):
    items=beat["items"]
    n=len(items)
    x=round(width*.24)
    top=round(height*.16)
    bottom=round(height*.83)
    gap=(bottom-top)/max(1,n-1)
    _beam(draw,(x,top),(x,bottom),_mix(accent,extra,.45),
          max(1,width*.007))
    current=progress*(n-1)
    for i,text in enumerate(items):
        y=round(top+gap*i)
        state=_clamp(current-i+1)
        if i:
            prev=round(top+gap*(i-1))
            draw.line((x,prev,x,y),fill=(*extra,48),
                      width=max(1,round(width*.014)))
            filled=_clamp(current-(i-1))
            if filled>0:
                _beam(draw,(x,prev),(x,prev+(y-prev)*filled),extra,
                      max(1,width*.009))
        _shadow(draw,x,y+width*.03,width*.072)
        radius=max(7,round(width*.044))
        color=_mix(_mix(dark,extra,.24),extra,state)
        _halo(draw,x,y,radius*.60,color,state)
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),
                     fill=(*_rgb(color,.53),255),
                     outline=(*color,240),width=max(1,width//130))
        draw.ellipse((x-radius*.42,y-radius*.55,
                      x+radius*.18,y+radius*.08),
                     fill=(*_mix(color,(255,255,255),.60),200))
        _label(draw,text,width*.36,y-width*.044,round(width*.56),
               round(width*.055),(234,242,249) if state>.4 else
               _mix(dark,(234,242,249),.47))
    # The traveling signal has a causal destination instead of random motion.
    sy=top+(bottom-top)*_clamp(progress)
    _halo(draw,x,sy,width*.030,accent)
    draw.ellipse((round(x-width*.021),round(sy-width*.021),
                  round(x+width*.021),round(sy+width*.021)),
                 fill=(*accent,240))


def _concept(draw, beat, progress, width, height, accent, extra, dark):
    items=beat["items"]
    n=len(items)
    cx,cy=width*.50,height*.46
    radius=min(width*.31,height*.33)
    # The central object persists as a meaningful stable anchor within scene.
    _shadow(draw,cx,cy+radius*.65,radius*.36)
    _halo(draw,cx,cy,width*.09,extra)
    for rr in (.16,.115,.075):
        r=width*rr
        draw.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(*extra,100),
                     width=max(1,round(width*.006)))
    r=width*.067
    draw.ellipse((cx-r,cy-r,cx+r,cy+r),
                 fill=(*_mix(dark,accent,.56),255),
                 outline=(*extra,230),width=max(2,round(width*.005)))
    # Stable node coordinates; material signal travels along connections.
    coords=[]
    for i,item in enumerate(items):
        angle=2*math.pi*i/n-math.pi/2
        x=cx+math.cos(angle)*radius
        y=cy+math.sin(angle)*radius*.85
        coords.append((x,y))
    for i,(x,y) in enumerate(coords):
        activation=_clamp(progress*n-i)
        _beam(draw,(cx,cy),(x,y),
              _mix(_mix(dark,accent,.35),accent,activation),
              width*.005)
        if activation:
            # One directed packet propagates from hub to each active concept.
            segment=_clamp(progress*n-i)
            p=(cx+(x-cx)*segment,cy+(y-cy)*segment)
            _halo(draw,p[0],p[1],width*.014,extra)
            draw.ellipse((p[0]-width*.013,p[1]-width*.013,
                          p[0]+width*.013,p[1]+width*.013),
                         fill=(*extra,240))
        node_color=_mix(dark,accent,.30+.70*activation)
        rr=max(7,round(width*.044))
        _shadow(draw,x,y+rr,rr)
        _halo(draw,x,y,rr*.55,node_color,activation)
        draw.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(*_rgb(node_color,.55),255),
                     outline=(*node_color,250),width=max(1,width//140))
        draw.ellipse((x-rr*.48,y-rr*.60,x+rr*.16,y+rr*.04),
                     fill=(*_mix(node_color,(255,255,255),.56),220))
        # Labels are positioned in a clamped row, away from the center hub.
        label_width=round(width*.34)
        label_x=max(width*.04,min(width*.96-label_width,x-label_width/2))
        label_y=max(height*.05,min(height*.92,y+rr+width*.011))
        _label(draw,items[i],label_x,label_y,label_width,
               round(width*.035),(231,240,245))


def render_stage(*, beat: dict, frame: int, first: int, last: int,
                 width: int, height: int, palette: tuple,
                 value_ratio: float | None = None) -> Image.Image:
    """Render original RGB visual, with no resets or unsupported fake facts.

    Measure's input is the ACTUAL MasterTimeline quantity ratio. All other
    grammars use the true absolute scene boundaries. Same frame => same image.
    """
    if (type(frame) is not int or type(first) is not int or
            type(last) is not int or not first <= frame < last):
        raise ValueError("Invalid absolute frame bounds")
    if (type(width) is not int or type(height) is not int or
            not 150 <= width <= 1200 or not 160 <= height <= 1200):
        raise ValueError("Invalid bounded stage dimensions")
    if (type(beat) is not dict or beat.get("kind") not in
            ("measure","compare","sequence","concept")):
        raise ValueError("Unsupported visual grammar")
    if (type(palette) is not tuple or len(palette) != 4):
        raise ValueError("A real scene color palette is required")
    phase=(frame-first)/max(1,last-first)
    progress=phase*phase*(3-2*phase)
    dark,tint,accent,extra=palette
    image=_background(width,height,dark,tint).copy()
    draw=ImageDraw.Draw(image,"RGBA")
    # Fixed horizon and camera language across editorial cuts; no shudder.
    if beat["kind"]=="measure":
        if (type(value_ratio) not in (float,int) or
                not math.isfinite(value_ratio) or not 0 <= value_ratio <= 1):
            raise ValueError("Measure requires validated numeric world state")
        _measure(draw,beat,value_ratio,width,height,accent,extra,dark)
    elif beat["kind"]=="compare":
        _compare(draw,beat,progress,width,height,accent,extra,dark)
    elif beat["kind"]=="sequence":
        _sequence(draw,beat,progress,width,height,accent,extra,dark)
    else:
        _concept(draw,beat,progress,width,height,accent,extra,dark)
    return image
