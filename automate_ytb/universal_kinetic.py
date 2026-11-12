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
VERSION = "universal-kinetic-cinematic-stage-v8-inline-bezier-scenes"


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
        from .universal_art25d import validate_layers
        from .universal_vector25d import validate_vector_layers
        current["visualLayers"] = validate_layers(beat.get("visualLayers"))
        current["visualVectors"] = validate_vector_layers(beat.get("visualVectors"))
        depths=[item["z"] for item in current["visualLayers"]+current["visualVectors"]]
        if len(depths)!=len(set(depths)) or len(depths)>12:
            raise ValueError("Original art and vector layers need distinct Z positions")
        current["visualQuery"] = (
            _text(beat["visualQuery"], "visual query", 120)
            if beat.get("visualQuery") is not None else None)
        if (current["visualQuery"] is not None
                and not current["visualQuery"].isprintable()):
            raise ValueError("Artwork query must be one printable line")
        if (current["visualLayers"] or current["visualVectors"]) and kind in ("measure", "compare"):
            raise ValueError("Numeric beats need visible grounded data; use graphical measure/compare")
        from .universal_actor_rig import validate_actor_rig
        current["actorTracks"],current["actorLinks"]=validate_actor_rig(
            beat.get("actorTracks"),beat.get("actorLinks"),
            current["visualLayers"]+current["visualVectors"])
        validated.append(current)
    # Foley validates at most 64 real cues. Every beat contributes its own
    # entry cue; a designed actor link contributes one contact cue.
    if len(validated)+sum(len(b["actorLinks"]) for b in validated)>64:
        raise ValueError("Too many event-locked audio cues for one Short")
    from .universal_actor_rig import validate_cut_continuity
    validate_cut_continuity({"beats":validated})
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


def synthesize(story: dict, engine: str, output: Path, voice_name=None,
               caption_cues: list[dict] | None = None) -> list[int]:
    """Generate real PCM per caption phrase; no estimated word alignment."""
    from .captions import caption_phrases
    speech = SpeechEngine(engine=engine, language=story["language"], voice=voice_name)
    rate = None
    cursor, boundaries, cues = 0, [0], []
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        for beat_index, beat in enumerate(story["beats"]):
            for phrase in caption_phrases(beat["narration"]):
                pcm, sample_rate = speech.audio(phrase)
                if rate is None:
                    rate = sample_rate
                    wav.setframerate(rate)
                if sample_rate != rate or not isinstance(pcm, bytes) or not pcm or len(pcm) % 2:
                    raise RuntimeError("Inconsistent narration PCM")
                start_sample = cursor
                wav.writeframesraw(pcm)
                cursor += len(pcm) // 2
                pause = .095 if phrase.rstrip().endswith((".", "!", "?", "…")) else .045
                pad = round(rate * pause)
                wav.writeframesraw(b"\0\0" * pad)
                cursor += pad
                cues.append((beat_index, phrase, start_sample, cursor))
            tail = round(rate * .12)
            wav.writeframesraw(b"\0\0" * tail)
            cursor += tail
            boundaries.append(cursor)
    if cursor / rate > 179.0:
        raise ValueError("Narration exceeds 179 seconds")
    stamps = [round(n * FPS / rate) for n in boundaries]
    if any(b-a < FPS for a, b in zip(stamps, stamps[1:])):
        raise ValueError("Each beat needs at least one second of narration")
    if caption_cues is not None:
        if type(caption_cues) is not list:
            raise ValueError("Invalid output caption list")
        for index, phrase, start, stop in cues:
            first, last = round(start*FPS/rate), round(stop*FPS/rate)
            if last <= first:
                raise ValueError("Synthesis produced too short a caption phrase")
            caption_cues.append({
                "beatIndex": index, "text": phrase,
                "startFrame": first, "endFrame": last,
                "startMs": round(start*1000/rate),
                "endMs": round(stop*1000/rate)})
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
        # A visual link has its own exact absolute source event. The shared
        # beat-progress cue only starts at beat boundaries and cannot carry
        # late cues (SoundCue offsets are limited to 300 frames).
        for j, link in enumerate(beat.get("actorLinks", [])):
            ident=f"link-{i:02d}-{j:02d}"
            at=start+round((end-start-1)*link["at"])
            at=min(end-2,max(start,at))
            objects.append(WorldObject(ident, {"opacity": 0.}))
            tracks.append(PropertyEvent(
                f"event-{ident}",ident,"opacity",at,at+2,0.,1.))
            cues.append(SoundCue(
                f"contact-{ident}",f"event-{ident}",
                "contact",offset_frames=0,gain_db=-21.))
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
                frame: int, width: int, height: int, backdrop=None,
                art_scenes=None, caption_cues=None,
                commons_scenes=None) -> Image.Image:
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
    # Licensed original illustration can replace a conceptual schematic.
    # The same authored shot clock drives independent depth-layer movement.
    art=art_scenes.get(pos) if art_scenes is not None else None
    if art is not None:
        from .universal_art25d import render_art_stage
        artwork=render_art_stage(art,frame,start,end)
        # Give the real illustrated world over half the portrait frame.
        # Two-line headers remain above it; PCM captions remain below.
        art_top=round(height*.27)
        base.paste(artwork,(pad,art_top),artwork)
    elif commons_scenes is not None and pos in commons_scenes:
        # Optional CC0 media can illustrate arbitrary authored concepts.
        # It is a moving crop of a real photo, NOT invented scene geometry.
        world_pad=round(width*.045)
        world_top=round(height*.274)
        artwork=commons_scenes[pos].render(frame,start,end)
        base.paste(artwork,(world_pad,world_top))
    # Fully authored art takes precedence. Otherwise use the shared
    # cinematic 2.5D grammar: real world-state values, extruded objects,
    # causal light signals, calibrated rulers and camera-stable depth.
    else:
        from .universal_motion25d import render_stage
        quantity_ratio=(timeline.state_at(frame)["objects"][
            _series_id(story,pos)]["value"]
            if beat["kind"]=="measure" else None)
        # A visual world should occupy the phone frame, not a small
        # diagram card. Keep the authored-art stage dimensions unchanged.
        world_pad=round(width*.045)
        world_top=round(height*.274)
        stage=render_stage(
            beat=beat,frame=frame,first=start,last=end,
            width=width-2*world_pad,height=round(height*.495),
            palette=palette,value_ratio=quantity_ratio)
        base.paste(stage,(world_pad,world_top))
    # Speech-synthesized phrase boundaries are measured from actual PCM,
    # never guessed word onsets or sliding seven-word subtitles.
    if caption_cues is not None:
        snippet=next((c["text"] for c in caption_cues
                      if c["startFrame"] <= frame < c["endFrame"]), "")
    else:
        words=beat["narration"].split()
        offset=min(max(0,len(words)-7),int(f*len(words)))
        snippet=" ".join(words[offset:offset+7])
    if snippet:
        lines,subfont=_fit(d,snippet,width-2*pad,int(width*.047),
                           bold=True,max_lines=2)
        for j,line in enumerate(lines):
            d.text((pad,int(height*.798)+j*int(subfont.size*1.32)),line,
                   font=subfont,fill=(248,251,254),
                   stroke_width=max(2,round(width*.004)),
                   stroke_fill=(3,7,17))
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
            width=720,commons_art=False,segment_art=False) -> dict:
    if (voice not in ("kokoro","espeak") or type(width) is not int
            or width not in (360,720,1080) or type(commons_art) is not bool
            or type(segment_art) is not bool or (segment_art and not commons_art)):
        raise ValueError("Voice kokoro/espeak and width 360/720/1080 required")
    story=read_story(brief)
    height=width*16//9
    output=output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="universal-original-") as temp:
        work=Path(temp)
        voice_file=work/"narration.wav"
        captions=[]
        stamps=synthesize(story,voice,voice_file,voice_name=voice_name,
                          caption_cues=captions)
        timeline=timeline_for(story,stamps)
        sfx=work/"foley.wav"
        create_causal_foley(timeline=timeline,output=sfx,
                            duration_seconds=timeline.total_frames/FPS)
        background=_backdrop(width,height,PALETTES[sum(story["topic"].encode())%3])
        from .universal_art25d import (
            bind_actor_camera_world, load_art_scenes)
        art_scenes,art_provenance=load_art_scenes(story,brief,width,height)
        camera_groups=bind_actor_camera_world(story,art_scenes,stamps)
        commons_scenes,commons_provenance={},[]
        if commons_art:
            from .universal_commons import build_commons_scenes
            commons_scenes,commons_provenance=build_commons_scenes(
                story,width-2*round(width*.045),round(height*.495),
                segment_art=segment_art)
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
                                               width,height,background,
                                               art_scenes,captions,
                                               commons_scenes).tobytes())
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
    from .captions import srt_time
    subtitle_path=output.with_suffix(".srt")
    subtitle_path.write_text("".join(
        f"{i}\n{srt_time(c['startMs'])} --> {srt_time(c['endMs'])}\n"
        f"{c['text']}\n\n" for i,c in enumerate(captions,1)),encoding="utf8")
    delivery=validate_short(output,require_audio=True)
    manifest={
        "engine":VERSION,"topic":story["topic"],"language":story["language"],
        "durationSeconds":timeline.total_frames/FPS,"beats":len(story["beats"]),
        "visualKinds":sorted(set(b["kind"] for b in story["beats"])),
        "resolution":[width,height],"fps":FPS,"voiceEngine":voice,
        "visualFallbackEngine":"generic-cinematic-kinetic-stage-v1",
        "commonsArtRequested":commons_art,
        "subjectSegmentationRequested":segment_art,
        "subjectSegmentationApplied":sum(
            1 for c in commons_provenance if c["segmentationApplied"]),
        "commonsScenes":len(commons_scenes),
        "commonsSources":commons_provenance,
        "narrationTiming":"actual-PCM-beat-boundaries",
        "subtitleTiming":"audio-derived-synthesized-phrases",
        "subtitleCues":len(captions),"subtitleFile":subtitle_path.name,
        "wordLevelAligned":False,
        "music":"original-continuous-procedural-ambient",
        "sound":"original-event-locked-foley","mix":mix,
        "authoredContactCues":sum(len(b["actorLinks"]) for b in story["beats"]),
        "artwork":{
            "engine":"scene25d-multilayer-owned-art",
            "scenesWithRealAuthoredArtwork":len(art_scenes),
            "approvedLayerProvenance":art_provenance,
            "authoredActionActors":sum(len(b["actorTracks"]) for b in story["beats"]),
            "authoredActorLinks":sum(len(b["actorLinks"]) for b in story["beats"]),
            "actionEngine":"universal-authored-actor-rig-continuous-world-v3",
            "continuousCameraGroups":camera_groups},
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
    p.add_argument("--commons-art",action="store_true",
                   help="Opt in to online CC0 1.0 Wikimedia visuals, subject to review")
    p.add_argument("--segment-art",action="store_true",
                   help="Use free local U2NetP foreground 2.5D matting; requires --commons-art")
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
        report=produce(brief,a.output,voice=a.voice,voice_name=a.voice_name,
                       width=a.width,commons_art=a.commons_art,
                       segment_art=a.segment_art)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0 if report["delivery"]["status"]=="passed" else 2
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
