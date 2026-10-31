#!/usr/bin/env python3
"""Finish Titan short: burned English captions, factual motion graphics, audio bed.

Only improves existing NASA footage and Kokoro narration. No slide generator,
credit-based API, extra stock assets, or automatically fabricated facts.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

SAMPLE_RATE = 48000

def run(*args):
    subprocess.run([str(x) for x in args], check=True)

def duration(file):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(file)],
        check=True,capture_output=True,text=True)
    return float(r.stdout.strip())

def stamp(t):
    n=max(0,int(round(t*100)))
    h,n=divmod(n,360000); m,n=divmod(n,6000); s,n=divmod(n,100)
    return f"{h}:{m:02}:{s:02}.{n:02}"

def stamp_srt(t):
    n=max(0,int(round(t*1000)))
    h,n=divmod(n,3600000); m,n=divmod(n,60000); s,n=divmod(n,1000)
    return f"{h:02}:{m:02}:{s:02},{n:03}"

def chunks(text):
    words=text.split()
    groups=[]; current=[]
    for word in words:
        if current and (len(" ".join(current+[word]))>29 or len(current)>=5):
            groups.append(" ".join(current));current=[]
        current.append(word)
        if word.endswith((",", ";", ":")) and len(current)>=3:
            groups.append(" ".join(current));current=[]
    if current: groups.append(" ".join(current))
    if len(groups)>1 and len(groups[-1].split())==1:
        groups[-2]+=" "+groups.pop()
    return groups

def captions(segments):
    events=[]
    for seg in segments:
        phrases=chunks(seg["text"])
        weights=[sum(max(1.0,len(w.strip(",.;"))**.55) for w in p.split())
                 for p in phrases]
        cur=seg["start"]
        for i,(phrase,weight) in enumerate(zip(phrases,weights)):
            end=seg["end"] if i==len(phrases)-1 else cur+(seg["end"]-seg["start"])*weight/sum(weights)
            if end-cur>=.36:
                events.append((cur,end,phrase))
            cur=end
    return events

def escape(text):
    return text.replace("\\","\\\\").replace("{",r"\{").replace("}",r"\}")

def write_subtitles(segments, words, folder):
    """Burn short English groups with word-level highlighting from the spoken WAV."""
    head="""[Script Info]
Title: Titan — English narration, acoustically aligned
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narration,DejaVu Sans,68,&H00FFFFFF,&H00FFFFFF,&HAC10171B,&H99000000,-1,0,0,0,100,100,0,0,1,6,2,2,64,64,325,1
Style: Key,DejaVu Sans,41,&H00F4EFE4,&H00FFFFFF,&HA8111820,&H99000000,-1,0,0,0,100,100,1,0,1,3,0,7,65,65,380,1
Style: Value,DejaVu Sans,83,&H00FFFFFF,&H00FFFFFF,&HA8111820,&H99000000,-1,0,0,0,100,100,-1,0,1,3,1,7,65,65,425,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Keep contextual groups legible even on 5-inch phones; never a slide/card.
    groups=[]
    offset=0
    for segment in segments:
        # Each caption group must stay inside its narrated sentence. Never
        # leak upcoming text into the previous scene or across a picture cut.
        count=len(segment["text"].split())
        sentence_words=words[offset:offset+count]
        if len(sentence_words)!=count:
            raise ValueError("Missing aligned words for scene")
        offset+=count
        current=[]
        for word in sentence_words:
            line=" ".join(x["word"] for x in current+[word])
            if current and (len(current)>=4 or len(line)>30):
                groups.append(current)
                current=[]
            current.append(word)
            if word["word"].endswith((".", "?", "!")):
                groups.append(current)
                current=[]
        if current:
            groups.append(current)
    if offset!=len(words):
        raise ValueError("Subtitle timeline has unassigned words")

    ass_rows=[]
    srt=[]
    for n,group in enumerate(groups,1):
        first=float(group[0]["start"])
        last=float(group[-1]["end"])
        if n<len(groups):
            last=min(last + .07, float(groups[n][0]["start"]))
        srt.extend([str(n),f"{stamp_srt(first)} --> {stamp_srt(last)}",
                    " ".join(x["word"] for x in group),""])
        for i,active in enumerate(group):
            a=float(active["start"])
            b=float(group[i+1]["start"]) if i+1<len(group) else last
            if b <= a + .02:
                b=min(last,a+.07)
            if b <= a:
                continue
            tokens=[]
            for j,w in enumerate(group):
                token=escape(w["word"])
                if i==j:
                    tokens.append(r"{\1c&H0085DEFF&}"+token+r"{\1c&H00FFFFFF&}")
                else:
                    tokens.append(token)
            ass_rows.append(
                f"Dialogue: 5,{stamp(a)},{stamp(b)},Narration,,0,0,0,,"
                + " ".join(tokens)
            )

    (folder/"subtitles_final.srt").write_text("\n".join(srt),encoding="utf-8")
    overlays=[
        (1,.15,.45,"Key","SATURN  /  HOME TO TITAN",375),
        (2,.45,.38,"Key","LAKES OF METHANE + ETHANE",365),
        (3,.55,.55,"Key","EVAPORATION → CLOUDS → RAIN",380),
        (4,.42,.45,"Value","−179°C",385),
    ]
    for i,enter,leave,style,content,y in overlays:
        start=segments[i]["start"]+enter
        end=segments[i]["end"]-leave
        if end>start+.35:
            ass_rows.append(
                f"Dialogue: 1,{stamp(start)},{stamp(end)},{style},,0,0,0,,"
                f"{{\\an7\\pos(74,{y})\\fad(240,250)}}{escape(content)}"
            )
    (folder/"captions.ass").write_text(head+"\n".join(ass_rows)+"\n",encoding="utf-8")
    return len(groups)

def soundbed(segments,total,path):
    rate=SAMPLE_RATE
    n=int(total*rate);t=np.arange(n,dtype=np.float64)/rate
    pad=(.28*np.sin(2*np.pi*55*t+.36*np.sin(2*np.pi*.068*t))+
         .22*np.sin(2*np.pi*82.4*t+.21*np.sin(2*np.pi*.053*t))+
         .18*np.sin(2*np.pi*130.81*t)+.09*np.sin(2*np.pi*196*t))
    pad*=.075*(.82+.18*np.sin(2*np.pi*.11*t)**2)
    rng=np.random.default_rng(20403)
    noise=rng.standard_normal(n).astype(np.float32)
    try:
        from scipy.signal import butter,sosfilt
        low=sosfilt(butter(2,400,fs=rate,output="sos"),noise)
        rain=sosfilt(butter(2,2400,fs=rate,output="sos"),noise)
    except ImportError:
        low=np.convolve(noise,np.full(80,1/80),mode="same")
        rain=np.convolve(noise,np.full(8,1/8),mode="same")
    low/=max(np.std(low),.01)
    rain/=max(np.std(rain),.01)
    seg=segments[3]
    ramp=np.clip((t-seg["start"])/.55,0,1)*np.clip((seg["end"]-t)/.55,0,1)
    audio=pad+.0034*low+.0105*rain*ramp
    for seg in segments[1:]:
        d=t-seg["start"]
        mask=(d>=0)&(d<.9)
        audio[mask]+=.012*np.sin(2*np.pi*(95*d[mask]+50*d[mask]**2))*np.exp(-6*d[mask])
    audio*=np.minimum(1,t/.6)*np.minimum(1,(total-t)/.7)
    stereo=np.column_stack([audio*(1+.025*np.sin(2*np.pi*.06*t)),
                            audio*(1-.025*np.sin(2*np.pi*.06*t))]).astype(np.float32)
    sf.write(path,np.clip(stereo,-.3,.3),rate,subtype="PCM_16")

def render(source, report, voice, folder):
    folder.mkdir(parents=True,exist_ok=True)
    segs=json.loads(report.read_text(encoding="utf-8"))["segments"]
    length=duration(source)
    if len(segs)!=6 or abs(length-segs[-1]["end"])>1.3:
        raise ValueError("Rendered video and Kokoro segment timing mismatch")
    from word_align import align_narration
    words, scene_coverage = align_narration(voice, segs, folder, model_name="base.en")
    count=write_subtitles(segs,words,folder)
    soundbed(segs,length,folder/"ambience.wav")
    output=folder/"Titan_Documentary_Enhanced_EN.mp4"
    af="[0:a]volume=1.0[n];[1:a]volume=0.75[b];[n][b]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=9[a]"
    vf=f"format=yuv420p,unsharp=5:5:0.35:3:3:0.08,ass=filename={str((folder/'captions.ass').resolve())}"
    run("ffmpeg","-y","-hide_banner","-loglevel","error",
        "-i",source,"-i",folder/"ambience.wav",
        "-filter_complex",af,"-map","0:v:0","-map","[a]",
        "-vf",vf,"-r","30","-c:v","libx264","-crf","18","-preset","medium",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000",
        "-movflags","+faststart","-t",f"{length:.4f}",output)
    run("ffmpeg","-v","error","-i",output,"-f","null","-")
    probe = subprocess.run(["ffprobe","-v","error","-select_streams","a:0",
        "-show_entries","stream=sample_rate","-of","default=noprint_wrappers=1:nokey=1",
        str(output)],capture_output=True,text=True,check=True)
    if probe.stdout.strip() != "48000":
        raise RuntimeError(f"Unsupported output audio sample rate: {probe.stdout.strip()}")
    run("ffmpeg","-y","-v","error","-ss","1.4","-i",output,
        "-frames:v","1",folder/"cover_enhanced.jpg")
    qa={"file":output.name,"duration":duration(output),"subtitles_burned":True,
        "caption_groups":count,"narration":"Kokoro af_heart","image_source":"NASA 4K",
        "animated_callouts":["Titan","methane lakes","rain cycle","temperature"],
        "verified":"full ffmpeg decode + narration word timing", "alignment_scenes":scene_coverage,
        "verified_word_fraction":round(sum(w["recognized"] for w in words)/len(words),3),
        "caveat":"illustrative animations, not actual Titan footage"}
    (folder/"qa_enhanced.json").write_text(json.dumps(qa,indent=2))
    print("ENHANCED_OK",json.dumps(qa),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--report",required=True,type=Path)
    parser.add_argument("--voice",required=True,type=Path)
    parser.add_argument("--outdir",required=True,type=Path)
    args=parser.parse_args()
    render(args.input,args.report,args.voice,args.outdir)
