#!/usr/bin/env python3
"""Create a short-form documentary from NASA SVS footage and Kokoro voice.
No synthetic placeholder scenery, no numbered scenes, no robot TTS.
Assets: NASA SVS 20403 (public domain video, source audio discarded).
"""
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import wave

import numpy as np
import requests
import soundfile as sf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
CACHE = ROOT / ".source_cache"
OUT.mkdir(exist_ok=True, parents=True)
CACHE.mkdir(exist_ok=True, parents=True)

NASA = "https://svs.gsfc.nasa.gov/vis/a020000/a020400/a020403/"
MEDIA = {
    "intro": "JWST_Titan_Intro_Final_V001.mp4",
    "lake": "Methane_1080_h264_V2.mp4",
    "rain": "Titan_Climate_1080_h264.mp4",
    "time": "Titan_Timelapse_1080_h264.mp4",
    "chemistry": "Webb_Titan_Shot3_h264_1080.mp4",
}
SCENES = [
    ("intro", "What if you stood beside an ocean on another world?", 23.0),
    ("intro", "This is Titan, Saturn's largest moon, beneath a thick orange sky.", 28.0),
    ("lake", "Its vast lakes are filled with liquid methane and ethane, not water.", 0.5),
    ("rain", "Methane evaporates, forms clouds, and sometimes falls back as rain.", 0.8),
    ("time", "At minus one hundred and seventy nine degrees Celsius, water is frozen solid.", 1.0),
    ("chemistry", "Here, even the weather runs on a completely different kind of chemistry.", 1.1),
]
VOICE = "af_heart"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def run(cmd):
    print("RUN", " ".join(map(str,cmd))[:280], flush=True)
    subprocess.run([str(x) for x in cmd], check=True)

def probe(file):
    p = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nokey=1:noprint_wrappers=1",str(file)], text=True,capture_output=True,check=True)
    return float(p.stdout.strip())

def retrieve(url, target):
    if target.exists() and target.stat().st_size > 100000:
        return
    tmp = target.with_suffix(".partial")
    for attempt in range(3):
        try:
            with requests.get(url, timeout=(20,150), stream=True,headers={"User-Agent":"Mozilla/5.0"}) as r:
                r.raise_for_status()
                with tmp.open("wb") as f:
                    for block in r.iter_content(1024*1024):
                        if block: f.write(block)
            if tmp.stat().st_size < 100000:
                raise RuntimeError("NASA media unexpectedly small")
            with tmp.open("rb") as f:
                if b"ftyp" not in f.read(32): raise RuntimeError("Not MP4 data")
            tmp.replace(target)
            print("NASA asset",target.name,target.stat().st_size,flush=True)
            return
        except Exception as exc:
            print("Download retry",url,type(exc).__name__,str(exc)[:180],flush=True)
            time.sleep(attempt+1)
    raise RuntimeError(f"Failed downloading authoritative footage: {url}")

def produce_narration():
    # Kokoro-82M (Apache-2.0), high-quality American English voice.
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a")
    sr = 24000
    all_samples = []
    segments = []
    cursor = 0
    for i, (_, text, _) in enumerate(SCENES):
        parts = []
        for _,_,audio in pipe(text, voice=VOICE, speed=0.99, split_pattern=r"\n+"):
            parts.append(np.asarray(audio,dtype=np.float32))
        if not parts:
            raise RuntimeError(f"No Kokoro audio for scene {i}")
        speech = np.concatenate(parts)
        # Keep narration continuous, but breathing space between thoughts.
        pause = np.zeros(int(sr*0.24),dtype=np.float32)
        speech_duration = len(speech)/sr
        segments.append({"text":text,"speech_duration":speech_duration,"start":cursor/sr,"end":(cursor+len(speech))/sr})
        all_samples.append(speech)
        all_samples.append(pause)
        cursor += len(speech)+len(pause)
    voice=np.concatenate(all_samples)
    sf.write(OUT/"narration.wav", voice, sr, subtype="PCM_16")
    return segments, len(voice)/sr

def srt_time(t):
    ms = int(round(t*1000))
    h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def caption_parts(text):
    # Short spoken phrases; no scene numbers or explanatory cards.
    words = text.split()
    if len(words) <= 9: return [text]
    pivot = len(words)//2
    # Prefer natural punctuation or a small clause boundary.
    for i in range(max(3,pivot-2),min(len(words)-2,pivot+3)):
        if words[i-1].endswith((",",".",";")):pivot=i;break
    return [" ".join(words[:pivot])," ".join(words[pivot:])]

def subtitle_file(segments):
    lines=[];events=[]
    for seg in segments:
        parts=caption_parts(seg["text"])
        step=(seg["end"]-seg["start"])/len(parts)
        for p,part in enumerate(parts):
            a=seg["start"]+p*step
            b=seg["start"]+(p+1)*step
            events.append({"start":a,"end":b,"caption":part})
            lines.extend([str(len(events)),f"{srt_time(a)} --> {srt_time(b)}",part,""])
    (OUT/"subtitles.srt").write_text("\n".join(lines),encoding="utf-8")
    return events

def make_clip(key, shotno, length, seek):
    source=CACHE/MEDIA[key]
    dur=probe(source)
    # Use original animation frames, never a zoom over a static picture.
    usable_start=min(max(0.,seek),max(0.,dur-length-0.1))
    clip=OUT/f"scene_{shotno:02d}.mp4"
    # 9:16 reframing; avoid distorted aspect ratio or letterboxing.
    vf=("scale=1080:1920:force_original_aspect_ratio=increase:"
        "flags=lanczos,crop=1080:1920,setsar=1,"
        "eq=contrast=1.035:saturation=1.04,format=yuv420p")
    run(["ffmpeg","-y","-hide_banner","-loglevel","error",
         "-stream_loop","-1","-ss",str(usable_start),"-i",source,
         "-t",f"{length:.3f}","-an","-vf",vf,
         "-r","30","-c:v","libx264","-preset","veryfast","-crf","19",
         "-pix_fmt","yuv420p", "-movflags","+faststart",clip])
    if abs(probe(clip)-length)>0.25:raise RuntimeError(f"Scene duration wrong: {clip}")
    return clip

def main():
    # Do not substitute procedural placeholder cards when a source fails.
    for key,filename in MEDIA.items():
        retrieve(NASA+filename,CACHE/filename)
        print("MEDIA",key,probe(CACHE/filename),flush=True)
    segs, duration=produce_narration()
    print("NARRATION",duration,flush=True)
    events=subtitle_file(segs)
    clips=[]
    for i, (key,_,seek) in enumerate(SCENES):
        segment_duration=segs[i]["speech_duration"]+0.24
        clips.append(make_clip(key,i,segment_duration,seek))
    concat=OUT/"list.txt"
    concat.write_text("".join(f"file '{str(p)}'\n" for p in clips))
    plain=OUT/"assembled.mp4"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat",
         "-safe","0","-i",concat,"-c","copy","-an",plain])
    output=OUT/"Titan_NASA_Kokoro_EN_1080x1920.mp4"
    # No slideshow or number overlays. Narration is foreground; keep sound free of
    # third-party music and preserve NASA video silence.
    run(["ffmpeg","-y","-hide_banner","-loglevel","error",
         "-i",plain,"-i",OUT/"narration.wav",
         "-map","0:v:0","-map","1:a:0",
         "-c:v","copy","-c:a","aac","-b:a","192k",
         "-af","highpass=f=65,lowpass=f=10000,loudnorm=I=-16:LRA=9:TP=-1.5",
         "-t",f"{duration:.3f}","-movflags","+faststart",output])
    # Explicit thumbnail extracted from actual moving source.
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss","3.0",
         "-i",output,"-frames:v","1",OUT/"cover.jpg"])
    info={"video":output.name,"duration":probe(output),
          "dimensions":"1080x1920","fps":30,"voice":"Kokoro-82M af_heart",
          "sources":[{"url":NASA+x,"credit":"NASA Goddard Space Flight Center / Conceptual Image Lab"} for x in MEDIA.values()],
          "segments":segs,"caption_events":len(events),
          "warnings":["Scientific visualizations show plausible Titan conditions, not footage captured at Titan's surface."]}
    (OUT/"production_report.json").write_text(json.dumps(info,indent=2))
    (OUT/"publication.txt").write_text(
        "Title: Titan Has Oceans — But They're Not Made of Water\n"
        "Description: The lakes on Saturn's largest moon contain liquid methane and ethane. "
        "A short science documentary using public-domain NASA visualizations. "
        "Visualization credit: NASA/GSFC Conceptual Image Lab.\n"
        "Hashtags: #Titan #Saturn #Space #ScienceShorts\n")
    assert output.stat().st_size>500000
    run(["ffmpeg","-v","error","-i",output,"-f","null","-"])
    print("FINAL_OK",str(output),output.stat().st_size,info["duration"],flush=True)

if __name__=="__main__":
    main()
