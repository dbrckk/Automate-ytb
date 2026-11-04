"""Visual cue timing inferred from *actual synthesized phrase boundaries*.

This is phrase-level synchronization only. No word alignment or phoneme timing
is claimed, and there are no network calls or new inference dependencies.
"""
from __future__ import annotations
import math
import re

VERSION="science-phrase-event-timing-v2-ocean"
PATTERNS={
    "volcano":{
        "magma":r"\b(magma|melt(?:s|ed|ing)?|molten)\b",
        "pressure":r"\b(pressure|bubbles?|gas(?:es)?|trapped)\b",
        "ascent":r"\b(ris(?:es|ing)|upward|ascend(?:s|ing)?|cracks?|vent)\b",
        "eruption":r"\b(erupt(?:s|ion|ing)?|blast(?:s|ing)?|ash|ejecta|fragments?)\b",
        "lava":r"\b(lava|flows?|cool(?:s|ed|ing)?)\b",
    },
    "ocean":{
        "solar":r"\b(sun|sunlight|solar|heat(?:s|ing)?|soleil)\b",
        "wind":r"\b(winds?|push(?:es|ing)?|driv(?:e|es|ing)|vents?)\b",
        "coriolis":r"\b(coriolis|rotat(?:e|es|ion|ing)|bends?|gyres?)\b",
        "sinking":r"\b(sink(?:s|ing)?|cold|salty|dense|density|poles?)\b",
        "heat":r"\b(heat|warm(?:ing)?|climate|redistribut(?:e|es|ing)|transport)\b",
    },
    "aurora":{
        "solar_wind":r"\b(solar wind|sun|particles?|releases?|sends?)\b",
        "magnetic_field":r"\b(magnetic|field|magnetosphere|poles?)\b",
        "collisions":r"\b(collid(?:e|es|ing)|collisions?|strike(?:s)?|hits?)\b",
        "emission":r"\b(excit(?:ed|es|ation)|emit(?:s|ted|ting)?|light|glow(?:s|ing)?)\b",
        "curtains":r"\b(curtains?|ripple(?:s|ing)?|danc(?:e|es|ing)|auroras?)\b",
    },
}


def audio_event_fraction(domain:str, beat:str, segments:list[dict]|None,
                         scene_start_ms:int)->float|None:
    """Midpoint of the FIRST synthesized phrase describing a visible action.

    Returns None when no audio-derived action cue can be found; the cinematic
    director then uses its deterministic authored shot center instead.
    """
    if domain not in PATTERNS or beat not in PATTERNS[domain]:
        raise ValueError("Unsupported semantic scene action")
    if type(scene_start_ms) is not int or not 0<=scene_start_ms<=3_600_000:
        raise ValueError("Invalid audio scene start")
    if segments is None:
        return None
    if not isinstance(segments,list) or not 1<=len(segments)<=200:
        raise ValueError("Invalid synthesized phrase list")
    previous=scene_start_ms
    match=None
    for segment in segments:
        if not isinstance(segment,dict):
            raise ValueError("Invalid audio phrase record")
        start,end,text=segment.get("startMs"),segment.get("endMs"),segment.get("text")
        if (type(start) is not int or type(end) is not int
                or not isinstance(text,str) or not text.strip()
                or start!=previous or end<=start
                or end>3_600_000):
            raise ValueError("Invalid audio phrase boundaries")
        if match is None and re.search(PATTERNS[domain][beat],text,re.IGNORECASE):
            match=(start+end)/2
        previous=end
    duration=previous-scene_start_ms
    if duration<=0:
        raise ValueError("Invalid audio phrase duration")
    return (match-scene_start_ms)/duration if match is not None else None
