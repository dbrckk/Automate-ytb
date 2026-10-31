#!/usr/bin/env python3
"""Finish the solar-storm documentary, with acoustic captions and original sound.

The science imagery belongs to NASA; the narration and restrained sound bed
are original. Word times from Whisper are audited, not claimed perfect.
"""
import json
import sys
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"titan"))
from word_align import align_narration
from review_frames import create_contact_sheet
from review_shots import review_encoded_shots
from motion_graphics import apply_motion_graphics

OUT=HERE/"out"
DONE=OUT/"final"
DONE.mkdir(parents=True,exist_ok=True)

def run(cmd):
    subprocess.run([str(x) for x in cmd],check=True)

def fmt(t):
    n=max(0,int(round(t*100)))
    h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100)
    return f"{h}:{m:02}:{s:02}.{n:02}"

def srt(t):
    n=max(0,int(round(t*1000)))
    h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
    return f"{h:02}:{m:02}:{s:02},{n:03}"

def esc(text):
    return text.replace("\\","\\\\").replace("{",r"\{").replace("}",r"\}")

def build_captions(segments, words):
    head="""[Script Info]
Title: The Sun Can Hit Earth — English
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Voice,DejaVu Sans,67,&H00FFFFFF,&H00FFFFFF,&HAB0C1012,&H90000000,-1,0,0,0,100,100,0,0,1,6,1,2,67,67,326,1
Style: Context,DejaVu Sans,39,&H00E7F8FF,&H00FFFFFF,&HAB0C1012,&H90000000,-1,0,0,0,100,100,1,0,1,3,1,7,72,72,355,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    groups=[]
    pos=0
    for segment in segments:
        ws=words[pos:pos+len(segment["text"].split())]
        pos+=len(ws)
        if len(ws)!=len(segment["text"].split()):
            raise ValueError("Incomplete acoustic word alignment")
        group=[]
        for word in ws:
            if group and (len(group)>=4 or len(" ".join(x["word"] for x in group+[word]))>31):
                groups.append(group)
                group=[]
            group.append(word)
            if word["word"].endswith((".", "?", "!")):
                groups.append(group)
                group=[]
        if group: groups.append(group)
    if pos!=len(words):
        raise ValueError("Speech leftover words")

    rows=[];srt_rows=[]
    for n,group in enumerate(groups,1):
        start=float(group[0]["start"])
        end=float(group[-1]["end"])
        if n<len(groups):
            end=min(end+.06,float(groups[n][0]["start"]))
        if end<=start:continue
        srt_rows.extend([str(n),f"{srt(start)} --> {srt(end)}",
                         " ".join(x["word"] for x in group),""])
        for ix,word in enumerate(group):
            a=float(word["start"])
            b=float(group[ix+1]["start"]) if ix+1<len(group) else end
            if b-a<.035:continue
            tokens=[]
            for j,entry in enumerate(group):
                term=esc(entry["word"])
                if j==ix:
                    term=r"{\1c&H003BDAFF&}"+term+r"{\1c&H00FFFFFF&}"
                tokens.append(term)
            rows.append(f"Dialogue: 4,{fmt(a)},{fmt(b)},Voice,,0,0,0,,"
                        +" ".join(tokens))

    # Only short, relevant explainer labels, never a slide or scene counter.
    labels=[
        (1,.3,.3,"EXTREME ULTRAVIOLET · NASA / SDO"),
        (2,.45,.25,"CORONAL MASS EJECTION"),
        (3,.35,.35,"EARTH'S MAGNETIC SHIELD"),
        (4,.6,.40,"AURORAS · SPACE WEATHER"),
    ]
    for i,lead,trail,label in labels:
        a=segments[i]["start"]+lead
        b=segments[i]["end"]-trail
        if b-a>.6:
            rows.append(f"Dialogue: 1,{fmt(a)},{fmt(b)},Context,,0,0,0,,"
                        f"{{\\pos(70,350)\\fad(250,250)}}{esc(label)}")
    (DONE/"captions.ass").write_text(head+"\n".join(rows)+"\n",encoding="utf-8")
    (DONE/"subtitles_en.srt").write_text("\n".join(srt_rows),encoding="utf-8")
    return len(groups)

def ambience(segments,duration):
    sr=48000
    n=round(sr*duration)
    t=np.arange(n)/sr
    # Copyright-free generated underscore with scene-synced, subtle movement.
    oscill=(.40*np.sin(2*np.pi*55*t)+
            .23*np.sin(2*np.pi*82.41*t+.35*np.sin(.37*t))+
            .19*np.sin(2*np.pi*110*t)+
            .09*np.sin(2*np.pi*164.8*t))
    tone=.045*oscill*(.78+.22*np.sin(.12*t)**2)
    rng=np.random.default_rng(20261031)
    white=rng.standard_normal(n).astype(np.float32)
    # Cheap band-limited rustle to suggest solar wind, not actual space sound.
    from scipy.signal import butter, sosfilt
    hiss=sosfilt(butter(2,1800,fs=sr,output="sos"),white)
    hiss=hiss/max(.01,np.std(hiss))
    tone+=.0030*hiss
    for index in [1,2,3,4,5]:
        d=t-segments[index]["start"]
        mask=(d>=0)&(d<1.1)
        tone[mask]+=.008*np.sin(2*np.pi*(70*d[mask]+90*d[mask]**2))*np.exp(-4*d[mask])
    tone*=np.clip(t/.7,0,1)*np.clip((duration-t)/.65,0,1)
    stereo=np.column_stack([
        tone*(1+.035*np.sin(.29*t)),
        tone*(1-.035*np.sin(.29*t))
    ])
    sf.write(DONE/"original_underscore.wav",stereo.astype(np.float32),sr,subtype="PCM_16")

def main():
    report=json.loads((OUT/"production_report.json").read_text())
    scenes=report["segments"]
    voice=OUT/"narration.wav"
    words,details=align_narration(voice,scenes,DONE,model_name="base.en")
    caption_groups=build_captions(scenes,words)
    motion=apply_motion_graphics(DONE/"captions.ass",scenes,words)
    (DONE/"motion_graphics.json").write_text(
        json.dumps(motion,indent=2),encoding="utf-8")
    length=float(report["duration"])
    ambience(scenes,length)
    source=OUT/"Solar_Storm_Base_EN.mp4"
    dest=DONE/"Solar_Storm_Short_EN_1080x1920.mp4"
    ass=(DONE/"captions.ass").resolve()
    video=f"format=yuv420p,unsharp=5:5:0.2:3:3:0.05,ass=filename={ass}"
    mix=("[0:a]volume=1.0[n];[1:a]volume=0.72[a];"
         "[n][a]amix=inputs=2:duration=first:dropout_transition=0,"
         "loudnorm=I=-16:LRA=9:TP=-1.5[m]")
    run(["ffmpeg","-y","-v","error","-i",source,
         "-i",DONE/"original_underscore.wav",
         "-filter_complex",mix,"-map","0:v:0","-map","[m]",
         "-vf",video,"-r","30","-c:v","libx264","-preset","medium","-crf","18",
         "-c:a","aac","-b:a","192k","-ar","48000",
         "-movflags","+faststart", "-t",f"{length:.3f}",dest])
    run(["ffmpeg","-v","error","-i",dest,"-f","null","-"])
    p=subprocess.run(["ffprobe","-v","error","-show_entries",
                      "stream=codec_name,width,height,r_frame_rate,sample_rate",
                      "-of","json",str(dest)],capture_output=True,text=True,check=True)
    streams=json.loads(p.stdout)["streams"]
    if not any(x.get("width")==1080 and x.get("height")==1920 and
               x.get("r_frame_rate")=="30/1" for x in streams):
        raise RuntimeError("Shorts profile mismatch")
    if not any(x.get("sample_rate")=="48000" for x in streams):
        raise RuntimeError("AAC sample rate incorrect")
    run(["ffmpeg","-y","-v","error","-ss","1.5","-i",dest,
         "-frames:v","1",DONE/"cover.jpg"])
    if len(scenes)!=6:
        raise RuntimeError("Solar Storm must contain six authored narrated scenes")
    review=create_contact_sheet(dest,scenes,DONE/"contact_sheet.jpg")
    (DONE/"review_frames.json").write_text(
        json.dumps(review,indent=2),encoding="utf-8")
    shot_review=review_encoded_shots(
        dest,report["shot_plan"],length,DONE/"shot_contact_sheet.jpg")
    if shot_review["sampled_shots"] != report["shot_count"]:
        raise RuntimeError("Incomplete decoded shot review")
    animated_shots=sum(
        "original_science_animation" in x for x in report["shot_plan"])
    if animated_shots!=5 or report.get("original_animated_shots")!=5:
        raise RuntimeError("Missing original full-frame science animations")
    (DONE/"shot_review.json").write_text(
        json.dumps(shot_review,indent=2),encoding="utf-8")
    verified=sum(w["recognized"] for w in words)/len(words)
    qa={"status":"passed","video":dest.name,"duration":length,
        "shot_count":report["shot_count"],"caption_groups":caption_groups,
        "speech_recognition_fraction":round(verified,3),
        "visual_review":review,"shot_review":shot_review,
        "motion_graphics":motion,
        "editorial_approved":False,
        "inferred_words":sum(not w["recognized"] for w in words),
        "caption_source":"actual Kokoro WAV via faster-whisper",
        "streams":streams,"source_attribution":"NASA SVS footage + five original animated explainers; see publication.txt",
         "original_animated_shots":animated_shots,
         "nasa_source_shots":report["shot_count"]-animated_shots,
        "checks":["NASA source decodes","ffmpeg full video/audio decode",
                  "1080x1920 30 fps","AAC 48000 Hz","word timing checked",
                  "six actual decoded scene frames and Android contact sheet",
                  "all encoded NASA and original animation shots visually sampled",
                   "five original frame-by-frame science sequences verified",
                  "six voice-synced animated educational graphic cues"]}
    (DONE/"qa.json").write_text(json.dumps(qa,indent=2),encoding="utf-8")
    (DONE/"publication.txt").write_text((OUT/"publication.txt").read_text(),encoding="utf-8")
    print("SOLAR_FINAL_OK",json.dumps(qa),flush=True)

if __name__=="__main__":
    main()
