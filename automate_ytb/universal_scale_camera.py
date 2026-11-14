"""Original continuous-world camera choreography for grounded numeric Shorts.

The camera, source points, glow and hand-drawn illustrative landmarks share
ONE global logarithmic coordinate system, not one camera per narration beat.
No image downloads, physics claims, AI-generated quantities, or new assets.
A v21 saved story without this version marker keeps its original renderer.
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFilter

from .universal_scale_journey import (
    _fitted, _font, eased_progress, scale_coordinate)

VERSION = "source-scale-continuous-world-camera-landmarks-v22"
_ART_STYLE = "original-illustrative-not-physical-scale"
_CANVAS_START = .246
_CANVAS_END = .822


def camera_pose(journey: dict, index: int, phase: float) -> dict:
    """Absolute perspective clock: no jump when a beat number changes."""
    q=eased_progress(journey,index,phase)
    return {
        "progress": q,
        "center": .13+.50*q+.009*math.sin(math.pi*q),
        "zoom": .98+.16*q,
        "pan": .019*math.sin(3.5*q),
    }


def world_y(pose: dict, world_position: float) -> float:
    """Project a source waypoint into screen height (normalized)."""
    if (type(world_position) not in (int,float)
            or not math.isfinite(world_position)
            or not 0 <= world_position <= 1):
        raise ValueError("Waypoint must lie within one grounded world")
    return .72-(world_position-pose["center"])*.80*pose["zoom"]


@lru_cache(maxsize=5)
def _backdrop(width: int, height: int) -> Image.Image:
    frame=Image.new("RGB",(width,height))
    d=ImageDraw.Draw(frame)
    for y in range(height):
        depth=y/height
        d.line((0,y,width,y),fill=(
            round(8+11*depth),round(14+9*depth),
            round(31+10*math.sin(math.pi*depth)**2+8*depth)))
    # Original angular silhouettes near the bottom of the phone, not a card.
    floor=round(height*.82)
    for step in range(6):
        yy=floor+round(step*step*height*.0031)
        d.line((0,yy,width,yy),
               fill=(17+2*step,32+2*step,52+2*step),width=1)
    return frame


@lru_cache(maxsize=35)
def _landmark_icon(kind: str, size: int) -> Image.Image:
    """Original detailed multi-plane line-art. NOT a calibrated physical size."""
    side=size
    icon=Image.new("RGBA",(side,side),(0,0,0,0))
    d=ImageDraw.Draw(icon)
    w=side/100.
    p=lambda x,y:(round(x*w),round(y*w))
    line=max(1,round(side*.014))
    mint=(122,231,209,255)
    teal=(51,149,160,230)
    blue=(40,93,134,240)
    gold=(236,181,115,255)
    if kind=="ruler":
        d.polygon([p(20,83),p(59,11),p(79,19),p(40,90)],
                  fill=(32,71,90,240))
        d.polygon([p(24,83),p(59,15),p(70,19),p(36,87)],
                  fill=(63,122,138,255),outline=mint)
        d.line([p(60,16),p(75,21),p(42,90),p(36,87)],
               fill=teal,width=line)
        for i in range(9):
            u=i/9.
            px=24+36*u
            py=81-65*u
            d.line([p(px,py),p(px+9 if i%3==0 else px+5,py+1)],
                   fill=gold if i%3==0 else mint,width=line)
    elif kind=="human":
        d.ellipse((*p(42,12),*p(58,28)),fill=(45,111,131,255),
                  outline=mint,width=line*2)
        d.polygon([p(44,30),p(56,30),p(62,54),p(38,54)],
                  fill=blue,outline=mint)
        d.line([p(44,34),p(26,49),p(23,63)],fill=mint,width=line*3)
        d.line([p(56,34),p(73,49),p(78,58)],fill=mint,width=line*3)
        d.line([p(43,54),p(37,79),p(30,92)],fill=mint,width=line*3)
        d.line([p(57,54),p(61,79),p(69,92)],fill=mint,width=line*3)
        d.line([p(35,92),p(22,92)],fill=gold,width=line*2)
        d.line([p(64,92),p(77,92)],fill=gold,width=line*2)
        for x,y in ((44,42),(53,42),(47,49)):
            d.ellipse((*p(x-1.2,y-1.2),*p(x+1.2,y+1.2)),fill=gold)
    elif kind=="tree":
        d.polygon([p(43,87),p(44,48),p(55,42),p(58,87)],
                  fill=(91,89,76,255),outline=gold)
        for a,b in [((48,56),(23,37)),((52,56),(78,31)),
                    ((49,46),(33,19)),((52,44),(61,11))]:
            d.line([p(*a),p(*b)],fill=gold,width=line*3)
        for x,y,r in ((35,32,18),(62,28,20),(44,19,17),
                      (20,49,13),(75,49,14),(51,46,22)):
            d.ellipse((*p(x-r,y-r),*p(x+r,y+r)),
                      fill=(20,93+((x+y)%3)*9,88,255),
                      outline=mint,width=line)
        for i in range(27):
            x=19+(i*37)%62
            y=13+(i*19)%43
            d.ellipse((*p(x,y),*p(x+2,y+3)),
                      fill=gold if i%5==0 else mint)
    elif kind=="tower":
        d.polygon([p(25,87),p(26,18),p(64,12),p(64,88)],
                  fill=(33,75,104,255),outline=mint)
        d.polygon([p(64,12),p(77,27),p(77,89),p(64,88)],
                  fill=(18,49,76,255),outline=teal)
        d.line([p(25,87),p(77,89)],fill=gold,width=line*2)
        for row in range(9):
            yy=23+row*6.8
            for col in range(4):
                xx=31+col*7.6
                tint=gold if (row*4+col)%7==0 else mint
                d.rectangle((*p(xx,yy),*p(xx+4,yy+3.5)),
                            fill=tint if col==1 and row%3==0 else (25,56,81,255),
                            outline=tint,width=line)
        d.line([p(46,14),p(46,3)],fill=mint,width=line)
        d.ellipse((*p(44,1),*p(48,5)),fill=gold)
    elif kind=="mountain":
        d.polygon([p(3,86),p(31,40),p(45,56),p(66,12),p(97,87)],
                  fill=(31,76,104,255),outline=mint)
        d.polygon([p(28,86),p(66,12),p(97,87)],
                  fill=(19,50,82,255))
        d.polygon([p(49,39),p(66,12),p(78,40),p(69,35),p(62,43)],
                  fill=(215,225,219,255))
        d.line([p(15,81),p(32,53),p(41,68),p(59,49)],
               fill=gold,width=line)
        d.line([p(70,47),p(78,61),p(88,76)],
               fill=teal,width=line)
        for k in range(7):
            x=15+k*10
            d.line([p(x,91),p(x+7,91)],fill=mint,width=line)
    elif kind in ("earth","moon"):
        d.ellipse((*p(12,12),*p(88,88)),
                  fill=(18,54,93,255) if kind=="earth"
                  else (72,84,105,255),outline=mint,width=line*2)
        if kind=="earth":
            for pts in (
                [(26,30),(39,22),(48,28),(44,43),(31,49),(22,40)],
                [(61,49),(79,43),(84,61),(73,77),(60,69)],
                [(39,62),(52,56),(62,68),(53,78),(41,74)],
            ):
                d.polygon([p(*v) for v in pts],fill=(34,139,133,255),
                          outline=gold,width=1)
            for dy in (35,51,67):
                d.arc((*p(17,dy-16),*p(83,dy+16)),0,180,
                      fill=(104,201,208,160),width=line)
        else:
            for x,y,r in ((31,32,8),(60,25,5),(51,63,11),
                          (72,58,6),(34,74,5)):
                d.ellipse((*p(x-r,y-r),*p(x+r,y+r)),
                          fill=(55,66,88,255),outline=gold,width=line)
        d.arc((*p(12,12),*p(88,88)),200,310,fill=gold,width=line*3)
    else:
        # Strict fallback for unrecognized context: still original vector art.
        d.rectangle((*p(23,12),*p(69,89)),
                    fill=(30,75,92,255),outline=mint,width=line*2)
        for tick in range(12):
            y=17+tick*5.7
            d.line([p(25,y),p(43 if tick%2 else 56,y)],
                   fill=gold if tick%3==0 else mint,width=line)
    return icon


def _label(draw: ImageDraw.ImageDraw, phrase: str,
           width: int, start: int, bold: bool):
    return _fitted(draw,phrase,width,start,bold=bold)


def _paint_ruler(canvas: Image.Image, journey: dict,
                  pose: dict, width: int, height: int) -> None:
    d=ImageDraw.Draw(canvas)
    left,right=round(width*.09),round(width*.91)
    y=round(height*.213)
    bar=max(2,width//200)
    d.line((left,y,right,y),fill=(43,82,107),width=bar)
    # All markers use the same quantitative global logarithmic coordinates.
    for i,point in enumerate(journey["points"]):
        coord=scale_coordinate(journey,Decimal(point["metres"]))
        x=round(left+(right-left)*coord)
        reached=coord<=pose["progress"]+.00001
        d.line((x,y-round(width*.012),x,y+round(width*.012)),
               fill=(112,216,199) if reached else (67,106,125),
               width=max(2,width//350))
        if reached:
            d.ellipse((x-3,y-3,x+3,y+3),fill=(193,240,222))
    current=round(left+(right-left)*pose["progress"])
    d.line((left,y,current,y),fill=(104,241,210),width=bar+1)
    r=max(4,width//85)
    d.ellipse((current-r,y-r,current+r,y+r),
              fill=(246,251,241),outline=(104,241,210),width=bar)
    caption,font=_label(d,"LOGARITHMIC DISTANCE",round(width*.75),
                        max(9,round(width*.019)),False)
    d.text((left,round(height*.230)),caption,
           fill=(104,147,160),font=font)


def _beam_glow(width: int, length: int, start: int, end: int):
    """Blur only the illuminated beam interval, never the entire picture."""
    strip=max(40,round(width*.16))
    gl=Image.new("RGBA",(strip,length))
    gd=ImageDraw.Draw(gl)
    center=strip//2
    gd.line((center,start,center,end),
            fill=(249,159,86,160),width=max(4,round(width*.026)))
    return gl.filter(ImageFilter.GaussianBlur(radius=max(3,round(width*.024))))


def render_cinematic_scale_frame(
    journey: dict, topic: str, frame: int,
    boundaries: list[int], position: int, width: int, height: int
) -> Image.Image:
    """One optical world and continuous camera, with source-only numbers."""
    if (type(frame) is not int or type(boundaries) is not list
            or type(position) is not int or type(journey) is not dict
            or not 0 <= position < len(journey.get("points",[]))
            or len(boundaries)!=len(journey["points"])+1
            or not boundaries[position] <= frame < boundaries[position+1]
            or width not in (360,720,1080) or height != width*16//9):
        raise ValueError("Invalid original world-camera frame")
    first,last=boundaries[position:position+2]
    phase=(frame-first)/max(1,last-first)
    pose=camera_pose(journey,position,phase)
    q=pose["progress"]
    base=_backdrop(width,height).copy()
    lo,hi=round(height*_CANVAS_START),round(height*_CANVAS_END)
    stage=Image.new("RGBA",(width,hi-lo),(0,0,0,0))
    d=ImageDraw.Draw(stage)
    cx=round(width*(.53+pose["pan"]))
    # Camera moves the three star planes by different fractions of world q.
    # Everything depends on global progress, not local beat/frame index.
    for plane in (0,1,2):
        for k in range(29):
            x=round(width*(((k*367+plane*181+53)%997)/997)
                    +width*.016*math.sin(q*2.7+plane*3+k))
            y=round(((((k*191+plane*257+73)%941)/941)
                      *height*.59+q*height*(.024+.022*plane))
                    % (hi-lo))
            radius=max(1,round(width*(.0011+.00055*plane)))
            d.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(70+plane*18,115+plane*13,160+plane*11,
                            115+plane*30))
    # Stable ground and world horizon translate with the virtual camera.
    ground=round(height*world_y(pose,0))-lo
    if ground < hi-lo+width*.12:
        d.line((0,ground,width,ground),
               fill=(176,140,101,210),width=max(2,width//250))
        for i in range(13):
            depth=i/13
            line_y=ground+round(width*depth*depth*.65)
            if line_y < hi-lo:
                d.line((0,line_y,width,line_y),
                       fill=(50,76,97,90),width=max(1,width//700))
    # Continuous luminous spire; world origin can move offscreen.
    top=round(height*world_y(pose,q))-lo
    beam_top=max(-width,top)
    beam_bottom=min(hi-lo+width,max(ground,top))
    if beam_bottom > beam_top:
        visible_start=max(0,beam_top)
        visible_end=min(hi-lo,beam_bottom)
        if visible_end>visible_start:
            gl=_beam_glow(width,hi-lo,visible_start,visible_end)
            stage.alpha_composite(gl,(cx-gl.width//2,0))
            d=ImageDraw.Draw(stage)
            d.line((cx,visible_start,cx,visible_end),
                   fill=(245,156,83,245),
                   width=max(4,round(width*.009)))
            d.line((cx-1,visible_start,cx-1,visible_end),
                   fill=(255,241,194,255),
                   width=max(1,round(width*.0025)))
    # A tip stays connected to the same worldline, not a new slide per beat.
    spark=max(4,round(width*.011))
    if -spark<=top<=hi-lo+spark:
        d.ellipse((cx-spark,top-spark,cx+spark,top+spark),
                  fill=(255,245,189,255),outline=(255,177,99,255),
                  width=max(2,width//400))
    # All previously reached source-anchored reference icons live in world
    # space. They shift automatically under the moving camera.
    for i,point in enumerate(journey["points"]):
        coord=scale_coordinate(journey,Decimal(point["metres"]))
        activation=(q-coord+.017)/.047
        if activation<=0:
            continue
        alpha=round(255*max(0.,min(1.,activation)))
        y=round(height*world_y(pose,coord))-lo
        if not -width*.3<=y<=hi-lo+width*.3:
            continue
        side=-1 if i%2==0 else 1
        x=round(width*(.23 if side<0 else .80)
                +width*pose["pan"]*(1.6 if side<0 else .8))
        scale=round(width*(.16+.014*(1-abs(q-coord))))
        sprite=_landmark_icon(point["illustration"],scale).copy()
        sprite.putalpha(sprite.getchannel("A").point(
            lambda a:round(a*alpha/255)))
        stage.alpha_composite(sprite,(x-scale//2,y-scale))
        d=ImageDraw.Draw(stage)
        text,ft=_label(d,point["sourceSpan"],
                       round(width*.235),max(10,round(width*.023)),True)
        tx=round(x-d.textlength(text,font=ft)/2)
        d.text((tx,y+round(width*.008)),text,font=ft,
               fill=(197,239,223,alpha))
        # World-ruler leader persists at each numerically sourced position.
        d.line((cx,y,x,y),fill=(77,142,150,min(alpha,140)),
               width=max(1,width//570))
    # Tiny source-tied particles, advancing with the beam on a world clock.
    for i in range(12):
        age=(q*5+i*.347)
        frac=age%1
        x=cx+math.sin(age*6.1+i)*width*(.024+(i%4)*.007)
        y=top+frac*height*.12
        if 0<=y<hi-lo:
            radius=max(1,round(width*.0017))
            d.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(255,177,116,175))
    # Hard crop prevents world elements overlapping the stable title/captions.
    base.paste(stage,(0,lo),stage)
    d=ImageDraw.Draw(base)
    topic_text,tf=_label(d,topic,round(width*.86),
                         max(15,round(width*.053)),True)
    d.text(((width-d.textlength(topic_text,font=tf))/2,
            round(height*.049)),topic_text,font=tf,fill=(235,247,250))
    point=journey["points"][position]
    value,vf=_label(d,point["sourceSpan"],round(width*.72),
                    max(20,round(width*.081)),True)
    # Crossfade only between two actually authored adjacent measurements.
    # The transition does NOT display an invented intermediate measurement.
    alpha=min(1.,phase/.13) if position else 1.
    cy=round(height*.126)
    if alpha<1. and position:
        past=journey["points"][position-1]["sourceSpan"]
        text,old_font=_label(d,past,round(width*.72),
                             max(20,round(width*.081)),True)
        pad=round(width*.10)
        overlay=Image.new("RGBA",(width,round(height*.11)))
        od=ImageDraw.Draw(overlay)
        od.text(((width-od.textlength(text,font=old_font))/2,0),text,
                font=old_font,
                fill=(124,214,196,round(255*(1-alpha))))
        od.text(((width-od.textlength(value,font=vf))/2,0),value,
                font=vf,fill=(116,242,216,round(255*alpha)))
        base.paste(overlay,(0,cy),overlay)
    else:
        d.text(((width-d.textlength(value,font=vf))/2,cy),
               value,font=vf,fill=(116,242,216))
    _paint_ruler(base,journey,pose,width,height)
    tag,tag_font=_label(d,"ILLUSTRATIVE • ICONS NOT TO SCALE",
                        round(width*.78),max(8,round(width*.018)),False)
    d.text((round(width*.075),round(height*.837)),tag,
           font=tag_font,fill=(93,129,143))
    return base
