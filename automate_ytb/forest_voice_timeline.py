"""Measured Kokoro voice -> physical 2.5D forest beat alignment.

No estimated words-per-minute timestamps. Each visual shot follows the
duration of the *actual synthesized* 24 kHz PCM sentence.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .forest_story25d import STORY

ENGLISH_SCRIPT=(
    "Every step in the forest can lead to a little discovery.",
    "One gentle touch, and the flower comes alive.",
    "Look! A butterfly has come to say hello.",
    "And just like that, the meadow has another story to tell.",
)
FRENCH_SCRIPT=(
    "Dans la forêt, chaque pas réserve une petite découverte.",
    "Un léger contact, et la fleur prend vie.",
    "Regarde ! Un papillon vient lui rendre visite.",
    "Et voilà, la prairie a une nouvelle histoire à raconter.",
)


@dataclass(frozen=True)
class TimedBeat:
    name: str
    narration: str
    start: float
    end: float
    speech_start: float
    speech_end: float
    source_start: float
    source_end: float


@dataclass(frozen=True)
class NarratedTimeline:
    duration: float
    beats: tuple[TimedBeat,...]

    def at(self,t: float) -> tuple[float,TimedBeat]:
        if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=self.duration:
            raise ValueError("Invalid narrated video clock")
        beat=next((b for b in self.beats if t<b.end),self.beats[-1])
        q=max(0.,min(1.,(t-beat.start)/(beat.end-beat.start)))
        return beat.source_start+q*(beat.source_end-beat.source_start),beat


def measured_timeline(report: dict, *, language: str="en") -> NarratedTimeline:
    """Map four *measured* Kokoro sentence spans to the four physical shots."""
    if language not in ("en","fr"):
        raise ValueError("Narration language must be English or French")
    if not isinstance(report,dict) or report.get("engine")!="kokoro-natural":
        raise ValueError("Requires a genuine Kokoro voice report")
    if report.get("language")!=language:
        raise ValueError("Voice and video languages differ")
    spans=report.get("beats")
    if not isinstance(spans,list) or len(spans)!=len(STORY):
        raise ValueError("Four independently measured voice sentences required")
    texts=ENGLISH_SCRIPT if language=="en" else FRENCH_SCRIPT
    duration=report.get("durationSeconds")
    if type(duration) not in (float,int) or not math.isfinite(duration) or not 8<=duration<=90:
        raise ValueError("Voice duration outside 8-90s")
    last_end=0.
    result=[]
    for i,(span,story,text) in enumerate(zip(spans,STORY,texts)):
        if not isinstance(span,dict) or span.get("index")!=i+1 or span.get("text")!=text:
            raise ValueError("Narration script and measured report do not match")
        start_ms,end_ms=span.get("startMs"),span.get("endMs")
        if (type(start_ms) is not int or type(end_ms) is not int or
                start_ms<0 or end_ms<=start_ms or start_ms<last_end*1000-1):
            raise ValueError("Invalid or overlapping real PCM timestamps")
        start,end=start_ms/1000,end_ms/1000
        if end>duration+.002:
            raise ValueError("Voice timestamp exceeds PCM duration")
        name,src_start,src_end,*_=story
        # Each shot begins at the previous shot's end, with 0.14s breathing
        # room around speech. No words are cut by a camera transition.
        shot_start=result[-1].end if result else 0.
        shot_length=max(1.1,(end-start)+.32)
        shot_end=shot_start+shot_length
        result.append(TimedBeat(name,text,shot_start,shot_end,
                                shot_start+.12,shot_start+.12+(end-start),
                                src_start,src_end))
        last_end=end
    total=result[-1].end+.35
    if total>90:
        raise ValueError("Narrated film exceeds 90 seconds")
    return NarratedTimeline(round(total,4),tuple(result))
