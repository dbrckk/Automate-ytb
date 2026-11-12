"""Original topic-agnostic kinetic Short engine.

Authored, source-reviewed facts become continuous motion; this never claims to
research, illustrate arbitrary real objects, or synthesize facts from a title.
Pillow + FFmpeg + existing SpeechEngine, MasterTimeline and Foley are reused.
"""
from __future__ import annotations

import argparse
from array import array
from decimal import Decimal, InvalidOperation
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont

from .foley_engine import create_causal_foley, mix_causal_foley
from .master_timeline import Beat, MasterTimeline, PropertyEvent, SoundCue, WorldObject
from .narration import SpeechEngine
from .shorts_delivery import validate_short

FPS = 30
KINDS = frozenset(("measure", "compare", "sequence", "concept"))
PALETTES = (
    ((10, 17, 38), (26, 49, 78), (245, 172, 115), (126, 222, 223)),
    ((12, 19, 32), (29, 50, 62), (234, 199, 114), (135, 206, 180)),
    ((20, 14, 44), (42, 30, 75), (241, 167, 190), (167, 196, 247)),
)
VERSION = "universal-kinetic-topic-driven-v1"


def _text(value, name, limit=120):
    if type(value) is not str or not 1 <= len(value.strip()) <= limit:
        raise ValueError(f"Invalid {name}")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValueError(f"Invalid control character in {name}")
    return value.strip()


def _number(value, name):
    if type(value) not in (str, int, float) or isinstance(value, bool):
        raise ValueError(f"Invalid {name}")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid {name}") from exc
    if not number.is_finite() or not Decimal(0) <= number <= Decimal("1e30"):
        raise ValueError(f"Out-of-range {name}")
    return number


def read_story(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > 120_000:
        raise ValueError("Missing or oversized JSON story")
    story = json.loads(path.read_text(encoding="utf-8"))
    if type(story) is not dict or story.get("schemaVersion") != 1:
        raise ValueError("Expected universal story schemaVersion 1")
    topic = _text(story.get("topic"), "topic", 150)
    language = story.get("language", "en")
    if language not in ("en", "fr"):
        raise ValueError("Language must be en or fr")
    scenes = story.get("beats")
    if type(scenes) is not list or not 2 <= len(scenes) <= 12:
        raise ValueError("Expected 2-12 original narrated beats")
    validated = []
    for index, beat in enumerate(scenes):
        if type(beat) is not dict or beat.get("kind") not in KINDS:
            raise ValueError(f"Invalid beat kind at {index}")
        kind = beat["kind"]
        current = {
            "kind": kind,
            "title": _text(beat.get("title"), "beat title", 90),
            "narration": _text(beat.get("narration"), "narration", 650),
        }
        if len(current["narration"].split()) < 3:
            raise ValueError("Narration must contain at least three words")
        if kind == "measure":
            current["label"] = _text(beat.get("label"), "quantity label", 60)
            current["value"] = _number(beat.get("value"), "quantity")
            current["scaleMax"] = _number(beat.get("scaleMax"), "scale maximum")
            current["unit"] = _text(beat.get("unit"), "unit", 20)
            if current["scaleMax"] <= 0 or current["value"] > current["scaleMax"]:
                raise ValueError("Quantity must fit its stated scale")
        elif kind == "compare":
            current["left"] = _text(beat.get("left"), "left label", 60)
            current["right"] = _text(beat.get("right"), "right label", 60)
            current["leftValue"] = _number(beat.get("leftValue"), "left value")
            current["rightValue"] = _number(beat.get("rightValue"), "right value")
            current["unit"] = _text(beat.get("unit"), "comparison unit", 20)
            if max(current["leftValue"], current["rightValue"]) <= 0:
                raise ValueError("Comparison needs a nonzero value")
        else:
            items = beat.get("steps" if kind == "sequence" else "nodes")
            if type(items) is not list or not 2 <= len(items) <= 5:
                raise ValueError(f"{kind} needs 2-5 authored labels")
            current["items"] = [_text(item, "visual label", 35) for item in items]
        sources = beat.get("sources", [])
        if type(sources) is not list or len(sources) > 6:
            raise ValueError("Invalid source list")
        for source in sources:
            if (type(source) is not str or not re.fullmatch(
                    r"https://[A-Za-z0-9.-]+(?:/[^\s]*)?", source)
                    or len(source) > 500):
                raise ValueError("Only explicit HTTPS fact sources accepted")
        current["sources"] = sources[:]
        validated.append(current)
    return {"topic": topic, "language": language, "beats": validated,
            "schemaVersion": 1}


def _font(size: int, bold=False):
    path = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def _fit(draw, text, width, font_size, *, bold=False, max_lines=3):
    tokens = text.split()
    font = _font(font_size, bold)
    lines, line = [], ""
    for token in tokens:
        candidate = (line + " " + token).strip()
        if line and draw.textbbox((0, 0), candidate, font=font)[2] > width:
            lines.append(line)
            line = token
        else:
            line = candidate
    if line:
        lines.append(line)
    if len(lines) > max_lines and font_size > 12:
        return _fit(draw, text, width, font_size-2, bold=bold, max_lines=max_lines)
    return lines[:max_lines], font


def _single_line(draw, text: str, max_width: int, size: int, *,
                 bold: bool = False) -> tuple[str, ImageFont.FreeTypeFont]:
    """Fit all authored strings into their actual mobile-safe pixel region."""
    font = _font(size, bold)
    while size > 12 and draw.textbbox((0, 0), text, font=font)[2] > max_width:
        size -= 2
        font = _font(size, bold)
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return text, font
    shortened = text
    while shortened and draw.textbbox((0, 0), shortened + "…", font=font)[2] > max_width:
        shortened = shortened[:-1]
    return (shortened.rstrip() + "…" if shortened else "…"), font


def _display(value: Decimal) -> str:
    if value == 0:
        return "0"
    if abs(value) >= Decimal("1e9"):
        return f"{value:.3E}".replace("E+", "e")
    return format(value.quantize(Decimal("0.01")), ",f").rstrip("0").rstrip(".")


def synthesize(story: dict, engine: str, output: Path, voice_name=None) -> list[int]:
    """Use actual PCM lengths for beat boundaries, not estimated speech speed."""
    speech = SpeechEngine(engine=engine, language=story["language"], voice=voice_name)
    rate, boundaries = None, [0]
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        for beat in story["beats"]:
            pcm, sample_rate = speech.audio(beat["narration"])
            if rate is None:
                rate = sample_rate
                wav.setframerate(rate)
            if sample_rate != rate or not pcm or len(pcm) % 2:
                raise RuntimeError("Inconsistent narration PCM")
            wav.writeframesraw(pcm)
            gap = round(rate * .17)
            wav.writeframesraw(b"\0\0" * gap)
            boundaries.append(boundaries[-1] + len(pcm)//2 + gap)
    if boundaries[-1] / rate > 179.0:
        raise ValueError("Narration exceeds 179 seconds")
    stamps = [round(n * FPS / rate) for n in boundaries]
    if stamps[0] != 0 or any(b-a < FPS for a, b in zip(stamps, stamps[1:])):
        raise ValueError("Each beat must have at least 1 second of real narration")
    return stamps


def timeline_for(story: dict, boundaries: list[int]) -> MasterTimeline:
    n = len(story["beats"])
    if (type(boundaries) is not list or len(boundaries) != n+1 or
            boundaries[0] != 0 or boundaries[-1] > FPS*180 or
            any(type(a) is not int or type(b) is not int or
                b-a < FPS for a, b in zip(boundaries, boundaries[1:]))):
        raise ValueError("Invalid PCM-derived scene boundaries")
    tracks, cues = [], []
    # A quantity is an enduring world object, not a scene-local counter.
    # Reappearance after unrelated beats resumes its last verified value.
    objects=[WorldObject("progress", {"value": 0.}, unit="fraction")]
    series_ids={}
    series_levels={}
    for i, beat in enumerate(story["beats"]):
        start, end = boundaries[i:i+2]
        event_id = f"story-progress-{i:02d}"
        tracks.append(PropertyEvent(event_id, "progress", "value",
                                    start, end, i/n, (i+1)/n))
        family = {"measure": "growth", "compare": "reveal",
                  "sequence": "count", "concept": "whoosh"}[beat["kind"]]
        cues.append(SoundCue(f"story-cue-{i:02d}", event_id, family,
                             offset_frames=0, gain_db=-24.))
        if beat["kind"] == "measure":
            key=(beat["label"].casefold(), beat["unit"], beat["scaleMax"])
            if key not in series_ids:
                object_id=f"quantity-{len(series_ids):02d}"
                series_ids[key]=object_id
                series_levels[key]=0.
                objects.append(WorldObject(object_id, {"value": 0.},
                                           unit="fraction"))
            target=float(beat["value"]/beat["scaleMax"])
            tracks.append(PropertyEvent(f"quantity-change-{i:02d}",
                                        series_ids[key], "value",start,end,
                                        series_levels[key],target))
            series_levels[key]=target
    return MasterTimeline(
        total_frames=boundaries[-1],
        objects=objects,
        beats=[Beat(f"beat-{i:02d}", boundaries[i], boundaries[i+1])
               for i in range(n)],
        events=tracks, cues=cues, fps=FPS)


def _series_id(story: dict, pos: int) -> str:
    """Stable ID by first authored occurrence of (label, unit, scale)."""
    beat=story["beats"][pos]
    key=(beat["label"].casefold(),beat["unit"],beat["scaleMax"])
    seen={}
    for old in story["beats"][:pos+1]:
        if old["kind"] != "measure":
            continue
        old_key=(old["label"].casefold(),old["unit"],old["scaleMax"])
        if old_key not in seen:
            seen[old_key]=f"quantity-{len(seen):02d}"
    return seen[key]


def _backdrop(width, height, palette):
    dark, tint, _, _ = palette
    img = Image.new("RGB", (width, height), dark)
    d = ImageDraw.Draw(img)
    for y in range(height):
        alpha = .30 * y / height
        d.line((0, y, width, y),
               fill=tuple(round(a*(1-alpha)+b*alpha) for a,b in zip(dark,tint)))
    for i in range(18):
        x = ((i*1193+293) % 997)/997 * width
        y = ((i*641+119) % 997)/997 * height
        r = max(1, width//420)
        d.ellipse((x-r,y-r,x+r,y+r), fill=tuple(min(255,c+20) for c in dark))
    return img


def _box(draw, xy, fill, radius=14, outline=None, width=1):
    draw.rounded_rectangle(tuple(map(int,xy)), radius=radius,
                           fill=fill, outline=outline, width=width)


def _bar(draw, x, y, w, h, fraction, color, palette):
    _box(draw, (x,y,x+w,y+h), palette[1], h//2)
    fill = int(w*max(0,min(1,float(fraction))))
    if fill:
        _box(draw, (x,y,x+max(h,fill),y+h), color, h//2)


def frame_image(story: dict, timeline: MasterTimeline, boundaries: list[int],
                frame: int, width: int, height: int, backdrop=None) -> Image.Image:
    if type(frame) is not int or not 0 <= frame < timeline.total_frames:
        raise ValueError("Invalid frame number")
    palette = PALETTES[sum(story["topic"].encode("utf-8")) % len(PALETTES)]
    dark, tint, accent, extra = palette
    base = backdrop.copy() if backdrop is not None else _backdrop(width,height,palette)
    d = ImageDraw.Draw(base)
    pos = next(i for i in range(len(boundaries)-1) if boundaries[i] <= frame < boundaries[i+1])
    beat = story["beats"][pos]
    start,end=boundaries[pos:pos+2]
    f = (frame-start)/max(1,end-start)
    ease = f*f*(3-2*f)
    pad=int(width*.09)
    stage_top=int(height*.34)
    stage_bottom=int(height*.74)
    # One persistent continuous editorial clock (same MasterTimeline as Foley).
    measured=timeline.state_at(frame)["objects"]["progress"]["value"]
    _bar(d,pad,int(height*.107),width-2*pad,max(3,width//140),measured,extra,palette)
    title_lines, font=_fit(d,story["topic"],width-2*pad,int(width*.055),bold=True,max_lines=2)
    for j,line in enumerate(title_lines):
        d.text((pad,int(height*.038)+j*font.size*1.18),line,font=font,fill=(241,245,252))
    header, hf=_fit(d,beat["title"],width-2*pad,int(width*.075),bold=True,max_lines=2)
    for j,line in enumerate(header):
        d.text((pad,int(height*.166)+j*hf.size*1.20),line,
               font=hf,fill=accent,stroke_width=1,stroke_fill=dark)
    # Scene-specific informational marks are animated, never slide images.
    if beat["kind"] == "measure":
        ratio=Decimal(str(timeline.state_at(frame)["objects"][
            _series_id(story,pos)]["value"]))
        amount=beat["scaleMax"]*ratio
        label, lf=_single_line(d,beat["label"],width-2*pad,int(width*.055),bold=True)
        d.text((pad,stage_top),label,font=lf,fill=(225,236,241))
        number, big=_single_line(d,_display(amount)+" "+beat["unit"],
                                width-2*pad,int(width*.095),bold=True)
        d.text((pad,stage_top+int(height*.09)),number,font=big,fill=extra)
        _bar(d,pad,stage_top+int(height*.22),width-2*pad,
             max(10,width//30),ratio,accent,palette)
        d.text((pad,stage_top+int(height*.275)),
               "0",font=_font(int(width*.037)),fill=(165,182,200))
        limit=_display(beat["scaleMax"])+" "+beat["unit"]
        bb=d.textbbox((0,0),limit,font=_font(int(width*.037)))
        d.text((width-pad-(bb[2]-bb[0]),stage_top+int(height*.275)),limit,
               font=_font(int(width*.037)),fill=(165,182,200))
    elif beat["kind"] == "compare":
        maximum=max(beat["leftValue"],beat["rightValue"])
        for i,(label,value,col) in enumerate((
                (beat["left"],beat["leftValue"],accent),
                (beat["right"],beat["rightValue"],extra))):
            y=stage_top+int(i*height*.18)
            label_text, label_font=_single_line(d,label,width-2*pad,
                                                 int(width*.057),bold=True)
            d.text((pad,y),label_text,font=label_font,fill=(237,242,247))
            _bar(d,pad,y+int(height*.075),width-2*pad,max(10,width//32),
                 (value/maximum)*Decimal(str(ease)),col,palette)
            v=_display(value*Decimal(str(ease)))+" "+beat["unit"]
            value_text, value_font=_single_line(d,v,width-2*pad,int(width*.045))
            d.text((pad,y+int(height*.115)),value_text,font=value_font,fill=col)
    elif beat["kind"] == "sequence":
        items=beat["items"]
        step=max(1,int((stage_bottom-stage_top)/(len(items))))
        for i,label in enumerate(items):
            cy=stage_top+step*i+step//2
            cx=pad+int(width*.07)
            if i:
                d.line((cx,cy-step,cx,cy),fill=tint,width=max(2,width//120))
            rr=int(width*.039)
            active=ease*len(items)>=i+.10
            d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),
                      fill=extra if active else tint,
                      outline=(234,245,249),width=max(1,width//240))
            stage_label, stage_font=_single_line(
                d,label,width-2*pad-int(width*.18),int(width*.052),bold=True)
            d.text((pad+int(width*.18),cy-int(width*.033)),stage_label,
                   font=stage_font,
                   fill=(235,240,249) if active else (120,148,162))
    else:
        items=beat["items"]
        cx,cy=width//2,(stage_top+stage_bottom)//2
        rr=int(width*.090)
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=tint,
                  outline=extra,width=max(2,width//155))
        d.text((cx-int(width*.023),cy-int(width*.027)),"+",font=_font(int(width*.05),True),
               fill=(245,245,255))
        for i,label in enumerate(items):
            theta=math.tau*i/len(items)-math.pi/2 + .07*math.sin(frame/25)
            orbit=int(width*.32)
            x=cx+math.cos(theta)*orbit
            y=cy+math.sin(theta)*orbit*.86
            d.line((cx,cy,x,y),fill=extra,width=max(2,width//200))
            rad=int(width*.026)
            d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=accent)
            txt,font=_fit(d,label,int(width*.26),int(width*.032),bold=True,max_lines=2)
            bx=d.textbbox((0,0),txt[0],font=font)
            d.text((max(pad,min(width-pad-(bx[2]-bx[0]),x-(bx[2]-bx[0])/2)),
                    y+rad+int(width*.015)),txt[0],font=font,fill=(234,240,249))
    # Audio-paced text window; segment times measured, word times NOT measured.
    words=beat["narration"].split()
    window=7
    offset=min(max(0,len(words)-window),int(f*len(words)))
    snippet=" ".join(words[offset:offset+window])
    lines,subfont=_fit(d,snippet,width-2*pad,int(width*.048),bold=True,max_lines=3)
    caption_y=int(height*.825)
    d.rounded_rectangle((pad-8,caption_y-15,width-pad+8,
                        caption_y+int(height*.12)),radius=14,fill=(10,20,36))
    for j,line in enumerate(lines):
        d.text((pad,caption_y+j*int(subfont.size*1.28)),line,
               font=subfont,fill=(247,249,253))
    return base


def _music(output:Path,total_frames:int):
    """Synthesize one original continuous quiet ambience, no 8-second scene loops."""
    rate=16000
    total=round(total_frames*rate/FPS)
    with wave.open(str(output),"wb") as dst:
        dst.setnchannels(1); dst.setsampwidth(2);dst.setframerate(rate)
        for start in range(0,total,4096):
            pcm=array("h")
            for index in range(start,min(total,start+4096)):
                t=index/rate
                env=min(1.,t/.55,max(0.,(total-index)/rate/.55))
                pad=sum(math.sin(math.tau*k*t) for k in (110.,164.81,220.))
                bloom=.24*math.sin(math.tau*55*t)
                v=int(max(-.9,min(.9,(pad*.036+bloom*.022)*env))*32767)
                pcm.append(v)
            if sys.byteorder!="little":pcm.byteswap()
            dst.writeframesraw(pcm.tobytes())


def produce(brief:Path,output:Path,*,voice="kokoro",voice_name=None,
            width=720) -> dict:
    if voice not in ("kokoro","espeak") or type(width) is not int or width not in (360,720,1080):
        raise ValueError("Voice kokoro/espeak and width 360/720/1080 required")
    story=read_story(brief)
    height=width*16//9
    output=output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="universal-original-") as temp:
        work=Path(temp)
        voice_file=work/"narration.wav"
        stamps=synthesize(story,voice,voice_file,voice_name=voice_name)
        timeline=timeline_for(story,stamps)
        sfx=work/"foley.wav"
        create_causal_foley(timeline=timeline,output=sfx,
                            duration_seconds=timeline.total_frames/FPS)
        background=_backdrop(width,height,PALETTES[sum(story["topic"].encode())%3])
        silent=work/"picture.mp4"
        cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-f","rawvideo","-pix_fmt","rgb24","-s",f"{width}x{height}",
             "-r",str(FPS),"-i","pipe:0","-an","-c:v","libx264",
             "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
             "-movflags","+faststart",str(silent)]
        encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE,
                                 stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            for frame in range(timeline.total_frames):
                encoder.stdin.write(frame_image(story,timeline,stamps,frame,
                                               width,height,background).tobytes())
            encoder.stdin.close()
            encoder.stdin=None
            _,err=encoder.communicate(timeout=600)
        except Exception:
            encoder.kill(); encoder.wait()
            raise
        if encoder.returncode or not silent.is_file():
            raise RuntimeError("FFmpeg video rendering failed: "+err.decode(errors="replace")[-1000:])
        ambient=work/"ambient.wav"
        _music(ambient,timeline.total_frames)
        mix=mix_causal_foley(silent_video=silent,foley=sfx,output=output,
              duration_seconds=timeline.total_frames/FPS,profile="high",
              voice=voice_file,music=ambient)
    delivery=validate_short(output,require_audio=True)
    manifest={
        "engine":VERSION,"topic":story["topic"],"language":story["language"],
        "durationSeconds":timeline.total_frames/FPS,"beats":len(story["beats"]),
        "visualKinds":sorted(set(b["kind"] for b in story["beats"])),
        "resolution":[width,height],"fps":FPS,"voiceEngine":voice,
        "narrationTiming":"actual-PCM-beat-boundaries",
        "subtitleTiming":"estimated-proportional-not-word-aligned",
        "music":"original-continuous-procedural-ambient",
        "sound":"original-event-locked-foley","mix":mix,
        "factsReviewed":False,"humanReviewed":False,"publicationApproved":False,
        "sourceURLs":sorted(set(s for b in story["beats"] for s in b["sources"])),
        "delivery":delivery,
    }
    output.with_suffix(".json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description="Original 9:16 kinetic Short from authored topic facts")
    input_group=p.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--brief",type=Path,
                             help="Explicit JSON story with original structured facts")
    input_group.add_argument("--script-file",type=Path,
                             help="Original EN/FR narration, paragraphs or sentences")
    p.add_argument("--topic",help="Required with --script-file")
    p.add_argument("--language",choices=("en","fr"),default="en")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--voice",choices=("kokoro","espeak"),default="kokoro")
    p.add_argument("--voice-name")
    p.add_argument("--width",type=int,choices=(360,720,1080),default=720)
    a=p.parse_args(argv)
    try:
        brief=a.brief
        if a.script_file is not None:
            from .universal_script import compile_original_script
            if not a.script_file.is_file() or a.script_file.stat().st_size > 8500:
                raise ValueError("Missing or oversized original script file")
            story=compile_original_script(
                topic=a.topic, script=a.script_file.read_text(encoding="utf8"),
                language=a.language)
            brief=a.output.with_suffix(".story.json")
            brief.parent.mkdir(parents=True,exist_ok=True)
            brief.write_text(json.dumps(story,ensure_ascii=False,indent=2)+"\n",
                             encoding="utf8")
        report=produce(brief,a.output,voice=a.voice,voice_name=a.voice_name,width=a.width)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0 if report["delivery"]["status"]=="passed" else 2
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
