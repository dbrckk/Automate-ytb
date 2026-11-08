"""Measured Kokoro captions: compact kinetic text, no opaque scene-covering cards.

Each beat is divided into short readable chunks. The chunk changes only while
real measured PCM is speaking, with small deterministic fades and safe lower
third placement. No invented word timestamps or giant dark boxes.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFont

from .forest_voice_timeline import NarratedTimeline

VERSION="forest-mobile-kinetic-compact-captions-p40-v1"
SIZE=(1080,1920)


@lru_cache(maxsize=1)
def _font():
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf",49)
    except OSError:
        return ImageFont.load_default()


def caption_chunks(text: str) -> tuple[str,...]:
    """Pixel-bounded phrases; speech timing is measured at beat level only."""
    if not isinstance(text,str) or not text.strip() or len(text)>300:
        raise ValueError("Invalid measured forest narration caption")
    font=_font()
    measure=ImageDraw.Draw(Image.new("L",(1,1)))
    words=text.split()
    chunks=[]
    line=[]
    for word in words:
        candidate=" ".join(line+[word])
        if line and (len(line)>=4 or
                     measure.textbbox((0,0),candidate,font=font)[2]>800):
            chunks.append(" ".join(line))
            line=[word]
        else:
            line.append(word)
    if line:
        chunks.append(" ".join(line))
    if any(measure.textbbox((0,0),chunk,font=font)[2]>860 for chunk in chunks):
        raise ValueError("Caption contains an unrenderably long word")
    return tuple(chunks)


def caption_plate(t:float,timeline:NarratedTimeline)->Image.Image:
    if not isinstance(timeline,NarratedTimeline):
        raise ValueError("Captions require a measured narration timeline")
    _,beat=timeline.at(t)
    canvas=Image.new("RGBA",SIZE)
    if t<beat.speech_start or t>=beat.speech_end:
        return canvas
    chunks=caption_chunks(beat.narration)
    span=beat.speech_end-beat.speech_start
    if span<=0:
        raise ValueError("Invalid measured PCM speech span")
    # These are proportional beat subdivisions, not claimed word alignments.
    progress=max(0.,min(1.-1e-9,(t-beat.speech_start)/span))
    position=progress*len(chunks)
    index=min(len(chunks)-1,int(position))
    local=position-index
    fade=min(1.,local/.12,(1.-local)/.12)
    alpha=max(0,min(255,round(255*fade)))
    if alpha==0:
        return canvas
    text=chunks[index]
    font=_font()
    draw=ImageDraw.Draw(canvas)
    bbox=draw.textbbox((0,0),text,font=font,stroke_width=3)
    width=bbox[2]-bbox[0]
    x=round((SIZE[0]-width)/2)
    y=1438
    # Light-weight outlined lettering: no solid rectangle masking the fox.
    draw.text((x,y),text,font=font,
              fill=(255,251,231,alpha),stroke_width=4,
              stroke_fill=(7,27,30,alpha))
    return canvas
