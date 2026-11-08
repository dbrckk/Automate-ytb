"""Readable speech-timed lower-third captions for original forest Shorts.

Captions appear only while actual measured Kokoro PCM is speaking, with
a subtle animated reveal; no text inferred from approximate speech rate.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFont

from .forest_voice_timeline import NarratedTimeline


@lru_cache(maxsize=2)
def _fonts():
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf",40),ImageFont.truetype("DejaVuSans.ttf",31)
    except OSError:
        return ImageFont.load_default(),ImageFont.load_default()


def caption_plate(t: float, timeline: NarratedTimeline) -> Image.Image:
    if not isinstance(timeline,NarratedTimeline):
        raise ValueError("Captions require a measured narration timeline")
    _,beat=timeline.at(t)
    canvas=Image.new("RGBA",(1080,1920))
    if t<beat.speech_start or t>=beat.speech_end:
        return canvas
    q=(t-beat.speech_start)/(beat.speech_end-beat.speech_start)
    alpha=round(255*min(1.,(t-beat.speech_start)/.12,
                         (beat.speech_end-t)/.16))
    alpha=max(0,min(255,alpha))
    if alpha==0:
        return canvas
    # Wrap by actual font pixel widths, keeping TikTok's bottom controls clear.
    bold,_=_fonts()
    d=ImageDraw.Draw(canvas)
    words=beat.narration.split()
    lines=[]
    current=""
    for word in words:
        candidate=f"{current} {word}".strip()
        if d.textbbox((0,0),candidate,font=bold)[2]>890 and current:
            lines.append(current)
            current=word
        else:
            current=candidate
    if current:
        lines.append(current)
    if len(lines)>3:
        raise ValueError("Narration caption exceeds safe three-line mobile area")
    h=66*len(lines)+52
    top=1475-h
    d.rounded_rectangle((70,top,1010,top+h),radius=25,
                        fill=(7,24,31,round(alpha*.79)))
    for i,line in enumerate(lines):
        bbox=d.textbbox((0,0),line,font=bold)
        x=(1080-(bbox[2]-bbox[0]))/2
        d.text((x,top+23+66*i),line,font=bold,
               fill=(246,252,246,alpha),stroke_width=1,
               stroke_fill=(4,22,24,alpha))
    return canvas
