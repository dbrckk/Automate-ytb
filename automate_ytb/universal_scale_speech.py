"""Speech-grounded visual anchors from measured synthesized PCM phrases.

These are exact *phrase* onset times, not detected onsets of individual words.
Every visual event is tied to a transcript phrase actually synthesized into
the final WAV. This module does not estimate duration from string length,
invent a word timestamp, or alter the synthesized speech.
"""
from __future__ import annotations

import re

from .captions import caption_phrases
from .universal_scale_journey import _explicit_landmark

VERSION = "source-scale-real-pcm-phrase-choreography-v23"
METHOD = "measured-synthesized-pcm-phrase-onsets-not-word-aligned"


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _has_exact_source_span(phrase: str, span: str) -> bool:
    """Match numbers as lexical source text, not as invented converted data."""
    return re.search(r"(?<!\w)" + re.escape(_normalized(span))
                     + r"(?!\w)", _normalized(phrase)) is not None


def _validated_cues(story: dict, captions: list[dict],
                    boundaries: list[int]) -> list[list[dict]]:
    beats=story["beats"]
    if (type(captions) is not list or type(boundaries) is not list
            or len(boundaries)!=len(beats)+1 or boundaries[0]!=0
            or any(type(n) is not int or type(m) is not int or n>=m
                   for n,m in zip(boundaries,boundaries[1:]))):
        raise ValueError("Invalid measured narration frame boundaries")
    groups=[[] for _ in beats]
    for cue in captions:
        if type(cue) is not dict:
            raise ValueError("Invalid measured speech caption")
        i=cue.get("beatIndex")
        a,b=cue.get("startFrame"),cue.get("endFrame")
        if (type(i) is not int or not 0<=i<len(beats)
                or type(a) is not int or type(b) is not int
                or not boundaries[i]<=a<b<=boundaries[i+1]
                or type(cue.get("text")) is not str
                or not cue["text"].strip()):
            raise ValueError("Untrusted speech caption time or original text")
        if groups[i] and a<groups[i][-1]["endFrame"]:
            raise ValueError("Overlapping measured speech phrases")
        groups[i].append(cue)
    for i,beat in enumerate(beats):
        expected=caption_phrases(beat["narration"])
        if [item["text"] for item in groups[i]]!=expected:
            raise ValueError("Synthesized captions do not match narrated source phrases")
    return groups


def build_pcm_scale_timing(story: dict, captions: list[dict],
                           boundaries: list[int]) -> dict:
    """Compile source-matched exact PCM phrase-start events for each beat.

    If a numeric source span is split or missing, fail closed rather than
    claiming reliable word alignment. Landmark cues use the first phrase
    where its actual source noun family is audible; otherwise reuse the
    number's measured phrase onset for an unlabeled ruler illustration.
    """
    if (type(story) is not dict
            or story.get("proceduralScaleSpeechEngine")!=VERSION
            or type(story.get("proceduralScaleJourney")) is not dict
            or len(story["beats"])!=len(story["proceduralScaleJourney"]["points"])):
        raise ValueError("Cannot anchor a story without v23 source provenance")
    grouped=_validated_cues(story,captions,boundaries)
    events=[]
    for i,(point,phrases) in enumerate(zip(
            story["proceduralScaleJourney"]["points"],grouped)):
        span=point["sourceSpan"]
        matched=[cue for cue in phrases
                 if _has_exact_source_span(cue["text"],span)]
        if len(matched)!=1:
            raise ValueError("Source measurement must occur in exactly one PCM phrase")
        value=matched[0]
        landmark=point["illustration"]
        identified=[cue for cue in phrases
                    if _explicit_landmark(cue["text"])==landmark]
        selected=(identified[0] if identified else value)
        start,end=boundaries[i:i+2]
        value_frame=min(end-2,max(start,value["startFrame"]))
        landmark_frame=min(end-2,max(start,selected["startFrame"]))
        events.append({
            "beatIndex":i,
            "sourceSpan":span,
            "valueStartFrame":value_frame,
            "valuePhrase":value["text"],
            "landmark":landmark,
            "landmarkStartFrame":landmark_frame,
            "landmarkPhrase":selected["text"],
        })
    return {"engine":VERSION,"method":METHOD,"wordLevelAligned":False,
            "events":events}


def scale_speech_event(timing: dict, index: int,
                       boundaries: list[int]) -> dict:
    """Validate a frozen-in-memory runtime event before rendering or mixing."""
    if (type(timing) is not dict or timing.get("engine")!=VERSION
            or timing.get("method")!=METHOD
            or timing.get("wordLevelAligned") is not False
            or type(timing.get("events")) is not list
            or type(index) is not int
            or not 0<=index<len(timing["events"])
            or type(boundaries) is not list
            or len(boundaries)!=len(timing["events"])+1):
        raise ValueError("Invalid source-PCM scale timing metadata")
    e=timing["events"][index]
    if (type(e) is not dict or e.get("beatIndex")!=index
            or type(e.get("sourceSpan")) is not str
            or type(e.get("valuePhrase")) is not str
            or type(e.get("landmark")) is not str
            or type(e.get("landmarkPhrase")) is not str
            or not _has_exact_source_span(e["valuePhrase"],e["sourceSpan"])):
        raise ValueError("Untrusted source-matched phrase event")
    start,end=boundaries[index:index+2]
    for key in ("valueStartFrame","landmarkStartFrame"):
        at=e.get(key)
        if type(at) is not int or not start<=at<=end-2:
            raise ValueError("Phrase event lies outside its source beat")
    return e


def measured_phase(frame: int, last: int, onset: int) -> float:
    """Continuous [0,1] clip phase; may begin after a narrated preamble."""
    if (type(frame) is not int or type(last) is not int
            or type(onset) is not int or not 0<=frame<last
            or not 0<=onset<last):
        raise ValueError("Invalid PCM-anchored animation interval")
    if frame<=onset:
        return 0.
    return min(1.,(frame-onset)/max(1,last-onset))


def measured_reveal(frame: int, last: int, onset: int) -> float:
    """Visual illustration appears shortly AFTER its exact phrase begins."""
    phase=measured_phase(frame,last,onset)
    duration=max(4,min(12,round((last-onset)*.22)))
    q=min(1.,max(0.,(frame-onset)/duration))
    return q*q*(3.-2.*q)
