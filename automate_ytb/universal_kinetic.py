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
import shutil
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
VERSION = "universal-kinetic-cinematic-stage-v16-causal-semantic-actions"


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
        from .universal_vector_art import validate_vector_layers
        current["visualLayers"] = validate_layers(beat.get("visualLayers"))
        current["visualVectors"] = validate_vector_layers(
            beat.get("visualVectors"),current["visualLayers"])
        current["visualQuery"] = (
            _text(beat["visualQuery"], "visual query", 120)
            if beat.get("visualQuery") is not None else None)
        if (current["visualQuery"] is not None
                and not current["visualQuery"].isprintable()):
            raise ValueError("Artwork query must be one printable line")
        if (current["visualLayers"] or current["visualVectors"]) and kind in ("measure", "compare"):
            raise ValueError("Numeric beats require grounded data diagrams rather than decoration")
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
    # Generated-art provenance is not a user-supplied label. When present,
    # its original object family, exact geometry and keyframes must agree
    # with the actual source-anchored deterministic template library.
    source_journey=story.get("proceduralScaleJourney")
    has_scale=("proceduralScaleJourney" in story
               or "proceduralScaleJourneyEngine" in story)
    has_camera="proceduralScaleCameraEngine" in story
    has_speech="proceduralScaleSpeechEngine" in story
    if has_speech:
        from .universal_scale_speech import VERSION as speech_version
        if (not has_camera
                or story["proceduralScaleSpeechEngine"]!=speech_version):
            raise ValueError("Untrusted source-PCM phrase choreography provenance")
    if has_camera:
        from .universal_scale_camera import VERSION as camera_version
        if (not has_scale
                or story["proceduralScaleCameraEngine"]!=camera_version):
            raise ValueError("Untrusted original world-camera provenance")
    if has_scale:
        from .universal_scale_journey import (
            VERSION as scale_version, derive_scale_journey)
        expected_journey=derive_scale_journey(validated)
        if (story.get("originalTextOnly") is not True
                or story.get("proceduralScaleJourneyEngine")!=scale_version
                or expected_journey is None
                or source_journey!=expected_journey
                or any(b["visualVectors"] or b["visualLayers"]
                       or b["actorTracks"] or b["actorLinks"]
                       for b in validated)):
            raise ValueError("Untrusted source-grounded scale animation provenance")
    subject_family=story.get("proceduralVisualFamily")
    motion_engine=story.get("proceduralMotionEngine")
    chapter_engine=story.get("proceduralVisualChapterEngine")
    compound_engine=story.get("proceduralVisualCompositionEngine")
    causal_engine=story.get("proceduralVisualInteractionEngine")
    has_contact=(causal_engine is not None
                 or "proceduralVisualInteractions" in story)
    has_compound=(compound_engine is not None
                  or "proceduralVisualCompositionFamilies" in story)
    has_chapters=(chapter_engine is not None
                  or "proceduralVisualFamilies" in story)
    if has_scale and (has_compound or has_chapters or subject_family is not None
                      or motion_engine is not None
                      or story.get("proceduralVisualEngine") is not None):
        raise ValueError("A scale journey cannot claim another artwork provenance")
    if has_contact and not has_compound:
        raise ValueError("Causal contact needs authenticated two-subject artwork")
    if has_compound:
        from .universal_subject_composition import (
            composition_families, composition_layers, composition_tracks,
            VERSION as composition_version)
        from .universal_subject_illustrations import VERSION as template_version
        from .universal_subject_motion import VERSION as motion_version
        selected=story.get("proceduralVisualCompositionFamilies")
        expected_compound=composition_families(validated)
        if (type(selected) is not list or expected_compound is None
                or selected!=expected_compound
                or compound_engine!=composition_version
                or has_chapters or subject_family is not None
                or story.get("proceduralVisualEngine")!=template_version
                or motion_engine!=motion_version):
            raise ValueError("Untrusted dual-subject provenance")
        if has_contact:
            from .universal_subject_interaction import (
                VERSION as contact_version, detect_contacts, contact_layers,
                contact_tracks_and_links)
            expected_contacts=detect_contacts(validated,expected_compound)
            if (causal_engine!=contact_version
                    or type(story.get("proceduralVisualInteractions")) is not list
                    or expected_contacts is None
                    or story["proceduralVisualInteractions"]!=expected_contacts):
                raise ValueError("Untrusted source-verb contact provenance")
        for i,(beat,families) in enumerate(zip(validated,expected_compound)):
            if has_contact:
                layers=(validate_vector_layers(contact_layers(families))
                        if families else [])
                native_tracks,native_links=(
                    contact_tracks_and_links(
                        families,i,len(validated),expected_contacts)
                    if families else ([],[]))
            else:
                layers=(validate_vector_layers(composition_layers(families))
                        if families else [])
                native_tracks=(composition_tracks(
                    families,i,len(validated)) if families else [])
                native_links=[]
            tracks,links=validate_actor_rig(native_tracks,native_links,layers)
            if (beat["visualVectors"]!=layers or beat["actorTracks"]!=tracks
                    or beat["actorLinks"]!=links or beat["visualLayers"]):
                raise ValueError("Dual-subject generated artwork was altered")
    elif has_chapters:
        from .universal_subject_illustrations import (
            subject_chapter_families, subject_layers, subject_tracks,
            CHAPTER_VERSION, VERSION as template_version)
        from .universal_subject_motion import VERSION as motion_version
        sequence=story.get("proceduralVisualFamilies")
        expected_sequence=subject_chapter_families(validated)
        if (type(sequence) is not list or expected_sequence is None
                or sequence != expected_sequence
                or chapter_engine != CHAPTER_VERSION
                or subject_family is not None
                or story.get("proceduralVisualEngine") != template_version
                or motion_engine != motion_version):
            raise ValueError("Untrusted per-beat subject provenance")
        for i,(beat,family) in enumerate(zip(validated,expected_sequence)):
            layers=(validate_vector_layers(subject_layers(family))
                    if family is not None else [])
            tracks=(validate_actor_rig(
                subject_tracks(i,len(validated),family=family,
                               engine=motion_version),[],layers)[0]
                    if family is not None else [])
            if (beat["visualVectors"]!=layers or beat["actorTracks"]!=tracks
                    or beat["actorLinks"] or beat["visualLayers"]):
                raise ValueError("Per-beat subject illustration was altered")
    elif motion_engine is not None and subject_family is None:
        raise ValueError("Subject motion must have grounded original artwork")
    if subject_family is not None and not has_chapters and not has_compound:
        from .universal_subject_illustrations import (
            select_subject, subject_layers, subject_tracks,
            VERSION as template_version)
        if (type(subject_family) is not str
                or story.get("proceduralVisualEngine")!=template_version
                or subject_family!=select_subject(
                    topic," ".join(b["narration"] for b in validated))):
            raise ValueError("Untrusted procedural subject provenance")
        from .universal_subject_motion import (
            VERSION as motion_version, LEGACY_VERSION as old_motion_version)
        if (motion_engine is not None
                and motion_engine not in (old_motion_version,motion_version)):
            raise ValueError("Untrusted procedural motion provenance")
        expected_layers=validate_vector_layers(subject_layers(subject_family))
        for i,beat in enumerate(validated):
            authored_tracks,_=validate_actor_rig(
                subject_tracks(i,len(validated),
                               family=(subject_family if motion_engine else None),
                               engine=motion_engine),
                [],expected_layers)
            if (beat["visualVectors"]!=expected_layers
                    or beat["actorTracks"]!=authored_tracks
                    or beat["actorLinks"] or beat["visualLayers"]):
                raise ValueError("Procedural subject illustration was altered")
    # A compiled source-only story must never be relabelled as manually
    # rights-confirmed art simply by deleting all of its provenance markers.
    # Editorial JSON briefs without originalTextOnly remain explicitly authored.
    if (story.get("originalTextOnly") is True and
            not (has_compound or has_chapters or subject_family is not None)
            and any(b["visualVectors"] or b["actorTracks"] for b in validated)):
        raise ValueError("Untrusted original-only storyboard provenance")
    result={"topic": topic, "language": language, "beats": validated,
            "schemaVersion": 1, "proceduralVisualFamily":subject_family,
            "proceduralMotionEngine":motion_engine}
    if has_chapters:
        result["proceduralVisualChapterEngine"]=chapter_engine
        result["proceduralVisualFamilies"]=expected_sequence
    if has_compound:
        result["proceduralVisualCompositionEngine"]=compound_engine
        result["proceduralVisualCompositionFamilies"]=expected_compound
    if has_contact:
        result["proceduralVisualInteractionEngine"]=causal_engine
        result["proceduralVisualInteractions"]=expected_contacts
    if has_scale:
        result["proceduralScaleJourneyEngine"]=scale_version
        result["proceduralScaleJourney"]=expected_journey
    if has_camera:
        result["proceduralScaleCameraEngine"]=camera_version
    if has_speech:
        result["proceduralScaleSpeechEngine"]=speech_version
    return result


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


def timeline_for(story: dict, boundaries: list[int],
                 scale_speech_timing: dict | None = None) -> MasterTimeline:
    n = len(story["beats"])
    if (type(boundaries) is not list or len(boundaries) != n+1 or
            boundaries[0] != 0 or boundaries[-1] > FPS*180 or
            any(type(a) is not int or type(b) is not int or
                b-a < FPS for a, b in zip(boundaries, boundaries[1:]))):
        raise ValueError("Invalid PCM-derived scene boundaries")
    if scale_speech_timing is not None:
        from .universal_scale_speech import scale_speech_event
        if story.get("proceduralScaleSpeechEngine") is None:
            raise ValueError("PCM phrase timing requires a sourced numeric journey")
        for i in range(n):
            scale_speech_event(scale_speech_timing,i,boundaries)
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
        if scale_speech_timing is None:
            cues.append(SoundCue(f"story-cue-{i:02d}", event_id, family,
                                 offset_frames=0, gain_db=-24.))
        else:
            from .universal_scale_speech import scale_speech_event
            trigger=scale_speech_event(scale_speech_timing,i,boundaries)
            at=trigger["valueStartFrame"]
            actor_id=f"source-scale-{i:02d}"
            visual_event_id=f"source-scale-reveal-{i:02d}"
            objects.append(WorldObject(actor_id, {"opacity":0.}))
            tracks.append(PropertyEvent(
                visual_event_id,actor_id,"opacity",at,at+2,0.,1.))
            cues.append(SoundCue(f"source-scale-tone-{i:02d}",
                                 visual_event_id,"scale-transition",
                                 offset_frames=0,gain_db=-28.))
            # A separate, quieter illustration chime is only justified
            # when narration mentions the object in a different PCM phrase.
            icon_at=trigger["landmarkStartFrame"]
            if (trigger["landmark"]!="ruler"
                    and icon_at>=at+5 and icon_at+2<=end):
                icon_id=f"source-landmark-{i:02d}"
                event=f"source-landmark-reveal-{i:02d}"
                objects.append(WorldObject(icon_id, {"opacity":0.}))
                tracks.append(PropertyEvent(
                    event,icon_id,"opacity",icon_at,icon_at+2,0.,1.))
                cues.append(SoundCue(f"source-landmark-tone-{i:02d}",
                                     event,"reveal",
                                     offset_frames=0,gain_db=-33.))
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
                commons_scenes=None,
                scale_speech_timing=None) -> Image.Image:
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
    # Author-supplied real world art receives a cinematic treatment; numeric
    # and conceptual diagrams retain their explicit reviewable data layout.
    art=art_scenes.get(pos) if art_scenes is not None else None
    journey=story.get("proceduralScaleJourney")
    if journey is not None:
        if story.get("proceduralScaleCameraEngine"):
            from .universal_scale_camera import render_cinematic_scale_frame
            base=render_cinematic_scale_frame(journey,story["topic"],frame,
                                               boundaries,pos,width,height,
                                               speech_timing=(scale_speech_timing if
                                                   story.get("proceduralScaleSpeechEngine")
                                                   else None))
        else:
            # Preserve pixel-level compatibility with old saved v21 stories.
            from .universal_scale_journey import render_scale_frame
            base=render_scale_frame(journey,story["topic"],frame,
                                    boundaries,pos,width,height)
        d=ImageDraw.Draw(base)
    elif art is None:
        measured=timeline.state_at(frame)["objects"]["progress"]["value"]
        _bar(d,pad,int(height*.107),width-2*pad,max(3,width//140),
             measured,extra,palette)
        title_lines,font=_fit(d,story["topic"],width-2*pad,
                              int(width*.055),bold=True,max_lines=2)
        for j,line in enumerate(title_lines):
            d.text((pad,int(height*.038)+j*font.size*1.18),
                   line,font=font,fill=(241,245,252))
        header,hf=_fit(d,beat["title"],width-2*pad,
                       int(width*.075),bold=True,max_lines=2)
        for j,line in enumerate(header):
            d.text((pad,int(height*.166)+j*hf.size*1.20),
                   line,font=hf,fill=accent,stroke_width=1,stroke_fill=dark)
    if journey is not None:
        pass  # The scale world has already occupied the full video frame.
    elif art is not None:
        from .universal_art25d import render_art_stage
        from .universal_cinematic_portrait import (
            composite_authored_world,shot_title_alpha)
        artwork=render_art_stage(art,frame,start,end)
        base=composite_authored_world(base,artwork)
        d=ImageDraw.Draw(base)
        # Small stable context label; the large narration heading is a brief
        # introductory overlay rather than a permanent PowerPoint title.
        title_lines,font=_fit(d,story["topic"],width-2*pad,
                              int(width*.040),bold=True,max_lines=2)
        for j,line in enumerate(title_lines):
            d.text((pad,int(height*.038)+j*font.size*1.18),
                   line,font=font,fill=(242,246,250))
        opacity=shot_title_alpha(frame,start,end)
        if opacity:
            overlay=Image.new("RGBA",base.size)
            od=ImageDraw.Draw(overlay)
            header,hf=_fit(od,beat["title"],width-2*pad,
                           int(width*.066),bold=True,max_lines=2)
            for j,line in enumerate(header):
                od.text((pad,int(height*.163)+j*hf.size*1.20),
                        line,font=hf,fill=(*accent,opacity),
                        stroke_width=max(2,round(width*.003)),
                        stroke_fill=(4,8,18,opacity))
            base=Image.alpha_composite(base.convert("RGBA"),overlay).convert("RGB")
            d=ImageDraw.Draw(base)
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
    # Canonical phonetic captions are phrase-timed from synthesized PCM.
    # No word timing is guessed. Without PCM cues, an in-memory preview
    # uses a static excerpt and makes no audio-alignment claim.
    from .universal_caption_overlay import paint_phrase_caption
    if caption_cues is not None:
        active=next((c for c in caption_cues
                     if c["startFrame"] <= frame < c["endFrame"]),None)
        if active is not None:
            paint_phrase_caption(
                base,active["text"],frame=frame,
                start=active["startFrame"],end=active["endFrame"],
                layout=active.get("layout"))
    else:
        words=beat["narration"].split()
        offset=min(max(0,len(words)-7),int(f*len(words)))
        snippet=" ".join(words[offset:offset+7])
        if snippet:
            paint_phrase_caption(base,snippet,frame=frame,start=start,end=end)
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
            width=720,commons_art=False,segment_art=False,
            export_narration=False) -> dict:
    if (voice not in ("kokoro","espeak") or type(width) is not int
            or width not in (360,720,1080) or type(commons_art) is not bool
            or type(segment_art) is not bool or (segment_art and not commons_art)
            or type(export_narration) is not bool):
        raise ValueError("Voice kokoro/espeak and width 360/720/1080 required")
    story=read_story(brief)
    height=width*16//9
    # Reject unrenderable spoken phrases *before* expensive Kokoro inference.
    # Every delivered subtitle must show every authored word in a bounded
    # mobile-safe line arrangement instead of silently truncating.
    from .captions import caption_phrases
    from .universal_caption_overlay import caption_layout
    for beat in story["beats"]:
        for phrase in caption_phrases(beat["narration"]):
            caption_layout(phrase,width=width,height=height)
    output=output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="universal-original-") as temp:
        work=Path(temp)
        voice_file=work/"narration.wav"
        captions=[]
        stamps=synthesize(story,voice,voice_file,voice_name=voice_name,
                          caption_cues=captions)
        from .universal_voice_evidence import inspect_narration
        voice_proof=inspect_narration(voice_file,engine=voice)
        if abs(voice_proof["durationMs"]-
               round(stamps[-1]*1000/FPS))>35:
            raise RuntimeError("Real synthesized PCM disagrees with video frame clock")
        for cue in captions:
            cue["layout"]=caption_layout(cue["text"],width=width,height=height)
        scale_speech_timing=None
        if story.get("proceduralScaleSpeechEngine"):
            from .universal_scale_speech import build_pcm_scale_timing
            scale_speech_timing=build_pcm_scale_timing(story,captions,stamps)
        timeline=timeline_for(story,stamps,scale_speech_timing)
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
                                               commons_scenes,
                                               scale_speech_timing).tobytes())
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
        # Validate real encoded media BEFORE preserving raw source narration.
        # A temporary failure cannot leave an exported WAV falsely presented
        # as the voice track of a successful published Short.
        delivery=validate_short(output,require_audio=True)
        if export_narration and delivery["status"] != "passed":
            raise RuntimeError(
                "Cannot preserve a narration proof for a failed final MP4: "
                + "; ".join(delivery.get("errors", [])))
        narration_export=None
        if export_narration:
            narration_export=output.with_suffix(".narration.wav")
            if narration_export.is_symlink():
                raise ValueError("Narration evidence destination cannot be a symlink")
            shutil.copyfile(voice_file,narration_export)
            copied=inspect_narration(narration_export,engine=voice)
            if copied["sha256"]!=voice_proof["sha256"]:
                narration_export.unlink(missing_ok=True)
                raise RuntimeError("Exported voice PCM differs from synthesized speech")
    from .captions import srt_time
    subtitle_path=output.with_suffix(".srt")
    subtitle_path.write_text("".join(
        f"{i}\n{srt_time(c['startMs'])} --> {srt_time(c['endMs'])}\n"
        f"{c['text']}\n\n" for i,c in enumerate(captions,1)),encoding="utf8")
    manifest={
        "engine":VERSION,"topic":story["topic"],"language":story["language"],
        "proceduralVisualFamily":story.get("proceduralVisualFamily"),
        "proceduralVisualFamilies":story.get("proceduralVisualFamilies"),
        "proceduralVisualChapterEngine":story.get("proceduralVisualChapterEngine"),
        "proceduralVisualCompositionEngine":story.get("proceduralVisualCompositionEngine"),
        "proceduralVisualCompositionFamilies":story.get("proceduralVisualCompositionFamilies"),
        "proceduralVisualInteractionEngine":story.get("proceduralVisualInteractionEngine"),
        "proceduralVisualInteractions":story.get("proceduralVisualInteractions"),
        "proceduralScaleJourneyEngine":story.get("proceduralScaleJourneyEngine"),
        "proceduralScaleCameraEngine":story.get("proceduralScaleCameraEngine"),
        "proceduralScaleSpeechEngine":story.get("proceduralScaleSpeechEngine"),
        "proceduralScaleSpeechTiming":scale_speech_timing,
        "proceduralScaleSpeechEventCount":(
            len(scale_speech_timing["events"]) if scale_speech_timing else 0),
        "proceduralScaleSpeechWordAligned":False,
        "proceduralScaleSpeechFoleyCueCount":sum(
            c["id"].startswith("source-scale-tone-")
            or c["id"].startswith("source-landmark-tone-")
            for c in timeline.audio_events()),
        "proceduralScaleLandmarkArtStyle":(
            "original-illustrative-not-physical-scale"
            if story.get("proceduralScaleCameraEngine") else None),
        "proceduralScaleLandmarkCount":len(
            (story.get("proceduralScaleJourney") or {}).get("points",[])),
        "proceduralScaleNumbersSourceVerified":bool(
            story.get("proceduralScaleJourney")),
        "proceduralCausalContactCount":sum(
            e is not None for e in (story.get("proceduralVisualInteractions") or [])),
        "proceduralMotionEngine":story.get("proceduralMotionEngine"),
        "proceduralVisualSceneCount":(
            sum(bool(f) for f in story["proceduralVisualCompositionFamilies"])
            if story.get("proceduralVisualCompositionFamilies") is not None
            else sum(f is not None for f in story["proceduralVisualFamilies"])
            if story.get("proceduralVisualFamilies") is not None
            else len(story["beats"]) if story.get("proceduralVisualFamily") else 0),
        "proceduralVisualEngine":(
            "original-source-anchored-procedural-subjects-v1"
            if (story.get("proceduralVisualFamily")
                or story.get("proceduralVisualFamilies")
                or story.get("proceduralVisualCompositionFamilies")) else None),
        "durationSeconds":timeline.total_frames/FPS,"beats":len(story["beats"]),
        "visualKinds":sorted(set(b["kind"] for b in story["beats"])),
        "resolution":[width,height],"fps":FPS,"voiceEngine":voice,
        "voiceName":(voice_name or ("ff_siwis" if story["language"]=="fr"
                                      else "af_heart")) if voice=="kokoro" else None,
        "voiceEvidence":voice_proof,
        "narrationWavFile":(narration_export.name if narration_export else None),
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
        "captionOverlayEngine":"pcm-phrase-cinematic-safe-caption-v1",
        "captionWordsOmitted":0,"captionLayoutPreflight":"passed",
        "wordLevelAligned":False,
        "music":"original-continuous-procedural-ambient",
        "sound":"original-event-locked-foley","mix":mix,
        "authoredContactCues":sum(len(b["actorLinks"]) for b in story["beats"]),
        "artwork":{
            "engine":"scene25d-original-vector-and-raster-illustrations",
            "vectorArtEngine":"original-bounded-multistop-surface-shading-v3",
            "originalVectorLayers":sum(len(b["visualVectors"]) for b in story["beats"]),
            "originalVectorShapes":sum(sum(len(l["shapes"]) for l in b["visualVectors"])
                                        for b in story["beats"]),
            "scenesWithRealAuthoredArtwork":len(art_scenes),
            "approvedLayerProvenance":art_provenance,
            "authoredActionActors":sum(len(b["actorTracks"]) for b in story["beats"]),
            "authoredActorLinks":sum(len(b["actorLinks"]) for b in story["beats"]),
            "flexibleActorParts":sum(
                sum("deform" in t for t in b["actorTracks"])
                for b in story["beats"]),
            "attachedActorParts":sum(
                sum("parentZ" in t for t in b["actorTracks"])
                for b in story["beats"]),
            "actionEngine":"universal-authored-actor-rig-hinge-flex-and-overscan-v7",
            "deformationEngine":"bounded-hinge-anchored-rgba-sway-v1",
            "contactVisualEngine":"localized-causal-glints-without-connector-beams-v1",
            "portraitCompositionEngine":"edge-matted-full-width-authored-world-v1",
            "jointTreeEngine":"authored-2d-joint-tree-v1",
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
    p.add_argument("--export-narration-wav",action="store_true",
                   help="Preserve verified source PCM as a separately inspectable WAV")
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
            # Generated declarative vector scenes are already schema-bounded.
            # Pretty-printed deep geometry can exceed the fixed JSON byte
            # ceiling for valid 5-12 beat original Shorts. Keep the exact
            # same authenticated data but serialize it compactly.
            brief.write_text(json.dumps(story,ensure_ascii=False,
                                        separators=(",",":"))+"\n",
                             encoding="utf8")
        report=produce(brief,a.output,voice=a.voice,voice_name=a.voice_name,
                       width=a.width,commons_art=a.commons_art,
                       segment_art=a.segment_art,
                       export_narration=a.export_narration_wav)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0 if report["delivery"]["status"]=="passed" else 2
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
