"""Original speech-safe forest score synchronized to the *physical* 2.5D film.

P4.7 closes an important production gap: the narrated MP4 previously
contained only the Kokoro voice. All sound is generated locally from
deterministic synthesis, no copyrighted recordings and no remote services.

Landing times originate from the rig's real stance schedule, the flower
chime occurs at the exact shared IK contact and butterfly rustle is only
present while that causal animation is visible. The measured Kokoro
timeline maps world actions into the final, voice-paced edit.
"""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import sys
import wave

from .forest_contact25d import IMPACT_TIME
from .forest_voice_timeline import NarratedTimeline
from .rig25d import PERIOD

VERSION = "forest-original-voice-ducked-causal-soundscape-p47-v1"
RATE = 24000
MAX_DURATION = 90.0


def source_to_video(source_t: float, timeline: NarratedTimeline) -> float:
    """Invert measured source-to-video beat timing, including exact cut edges."""
    if (type(source_t) not in (int,float) or not math.isfinite(source_t)
            or not 0 <= source_t <= 7.2
            or not isinstance(timeline,NarratedTimeline)
            or not timeline.beats):
        raise ValueError("Invalid physical sound event or Kokoro timeline")
    for beat in reversed(timeline.beats):
        if beat.source_start <= source_t <= beat.source_end:
            duration=beat.source_end-beat.source_start
            if duration <= 0 or beat.end<=beat.start:
                raise ValueError("Invalid measured source beat")
            return beat.start+(source_t-beat.source_start)*(beat.end-beat.start)/duration
    raise ValueError("Physical sound event lies outside narrated film")


def sound_events(timeline: NarratedTimeline) -> dict:
    """Proof-carrying, rig-derived audio cues in final edited time."""
    footsteps=[]
    for side,phase in (("left",0.0),("right",PERIOD*.5)):
        k=0
        while True:
            source_t=phase+k*PERIOD
            if source_t>=7.2:
                break
            if source_t>0:
                footsteps.append((side,round(source_to_video(source_t,timeline),6),
                                  round(source_t,6)))
            k+=1
    footsteps.sort(key=lambda item:item[1])
    return {
        "footsteps":tuple(footsteps),
        "flower":source_to_video(IMPACT_TIME,timeline),
        "butterfly":source_to_video(IMPACT_TIME+.12,timeline),
    }


def _ducker(t: float, timeline: NarratedTimeline) -> float:
    """Continuously duck the score beneath real, measured narration windows."""
    distance=min(max(beat.speech_start-t,0.,t-beat.speech_end)
                 for beat in timeline.beats)
    return .48+.52*min(1.,distance/.18)


def _flower_chime(dt: float) -> float:
    if dt<0. or dt>.58:
        return 0.
    env=math.exp(-7.8*dt)*(1-math.exp(-110*dt))
    return .081*env*(
        math.sin(2*math.pi*659.25*dt)
        + .32*math.sin(2*math.pi*988.88*dt)
        + .17*math.sin(2*math.pi*1318.5*dt))


def _footstep(dt: float) -> float:
    if dt<0. or dt>.16:
        return 0.
    envelope=math.exp(-29*dt)*(1-math.exp(-260*dt))
    return .055*envelope*(math.sin(2*math.pi*73*dt)
                          +.31*math.sin(2*math.pi*141*dt))


def _bird(t: float, start: float) -> float:
    dt=t-start
    if not 0<=dt<=.22:
        return 0.
    env=math.sin(math.pi*dt/.22)**2
    return .017*env*(math.sin(2*math.pi*(875*dt+240*dt*dt))
                     +.25*math.sin(2*math.pi*(1312*dt+360*dt*dt)))


def _pcm_to_array(pcm: bytes) -> array:
    if not isinstance(pcm,bytes) or len(pcm)%2:
        raise ValueError("Narration must be complete 16-bit mono PCM")
    result=array("h")
    result.frombytes(pcm)
    if sys.byteorder!="little":
        result.byteswap()
    return result


def mix_soundscape(voice_pcm: bytes, timeline: NarratedTimeline) -> tuple[bytes,dict]:
    """Mix narration with original environmental audio, without clipping.

    The output is 24kHz mono signed little-endian PCM. No invented speech:
    every voice sample is retained, without transcoding or time stretching.
    """
    if (not isinstance(timeline,NarratedTimeline)
            or type(timeline.duration) not in (int,float)
            or not math.isfinite(timeline.duration)
            or not 8<=timeline.duration<=MAX_DURATION
            or len(timeline.beats)!=4):
        raise ValueError("Four measured narration beats are required")
    voice=_pcm_to_array(voice_pcm)
    count=round(timeline.duration*RATE)
    if len(voice)!=count:
        raise ValueError("Kokoro PCM length differs from measured film")
    events=sound_events(timeline)
    peak=max((abs(sample) for sample in voice),default=0)/32768.
    # A measured, fixed headroom budget preserves even a loudly mastered
    # narrator while reserving space for foliage and small physical effects.
    voice_gain=min(1., .80/max(peak,.0001))
    samples=array("h")
    seed=0x59AD2E13
    low_pass=0.0
    beat_idx=0
    clip_count=0
    for i,sample in enumerate(voice):
        t=i/RATE
        while beat_idx < len(timeline.beats)-1 and t>=timeline.beats[beat_idx].end:
            beat_idx+=1
        beat=timeline.beats[beat_idx]
        fraction=max(0.,min(1.,(t-beat.start)/(beat.end-beat.start)))
        source_t=beat.source_start+fraction*(beat.source_end-beat.source_start)
        # Stationary pseudo-random ambience, repeatable and independent of
        # frame rate. The filtered layer creates gentle wind in the foliage.
        seed=(1664525*seed+1013904223)&0xffffffff
        white=seed/2147483648.-1.
        low_pass=.985*low_pass+.015*white
        wind_envelope=.58+.22*math.sin(.63*t+.4)+.12*math.sin(1.37*t)
        ambience=(
            .020*wind_envelope*(.23*white+.77*low_pass)
            +.0075*math.sin(2*math.pi*196*t+.08*math.sin(.4*t))
            +.004*math.sin(2*math.pi*294*t)
            +_bird(t,2.15)+_bird(t,8.85)+_bird(t,12.60)
        )
        footsteps=sum(_footstep(t-landing)
                      for _side,landing,_world in events["footsteps"])
        contact=_flower_chime(t-events["flower"])
        # The butterfly flutter is tied to the source animation itself:
        # a faster voice never changes the wing-relative choreography.
        since=source_t-IMPACT_TIME
        flutter=0.
        if .12 < since < 4.2:
            fade=min(1.,(since-.12)/.3,(4.2-since)/.55)
            wing_pulse=(.5+.5*math.sin(2*math.pi*9*since))**2
            flutter=.010*fade*wing_pulse*(white-low_pass)
        score=_ducker(t,timeline)*(ambience+flutter) + footsteps + contact
        mixed=sample/32768.*voice_gain+score
        if mixed>1. or mixed< -1.:
            clip_count+=1
        samples.append(max(-32768,min(32767,round(mixed*32768))))
    if sys.byteorder!="little":
        samples.byteswap()
    return samples.tobytes(), {
        "version":VERSION,
        "sampleRate":RATE,
        "channels":1,
        "voiceGain":round(voice_gain,5),
        "footstepCount":len(events["footsteps"]),
        "firstFootstepVideoSeconds":round(events["footsteps"][0][1],5),
        "contactSourceSeconds":round(IMPACT_TIME,5),
        "contactVideoSeconds":round(events["flower"],5),
        "butterflyVideoSeconds":round(events["butterfly"],5),
        "originalLocallySynthesized":True,
        "speechDucking":True,
        "causalIKEvents":True,
        "clippedSamples":clip_count,
    }


def render_soundscape(path: Path, voice_pcm: bytes,
                      timeline: NarratedTimeline) -> dict:
    """Write playable PCM WAV for FFmpeg; do not ship an unverified mix."""
    if not isinstance(path,Path) or path.suffix.lower()!=".wav":
        raise ValueError("Original soundscape destination must be WAV")
    payload,report=mix_soundscape(voice_pcm,timeline)
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(payload)
    if report["clippedSamples"]:
        raise RuntimeError("Original score has clipped PCM; refusing export")
    return report
