"""Compose a new synchronized soundtrack and copy the source video stream."""
import argparse
import hashlib
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

from render import STOPS, TARGET_TIMES

RATE=48000
DURATION=STOPS[-1][1]
TAU=math.tau
SEED=20261121
ORIGINAL_SHA256="ef3a081e6d2327fc46e212141173077df558859ee8f99d8bcdefba6e5f081266"

def hz(note):
    return 440*2**((note-69)/12)

def time_grid(seconds):
    return np.arange(round(seconds*RATE),dtype=np.float64)/RATE

def taper(x,attack,release):
    return np.clip(x/attack,0,1)*np.clip((x[-1]-x)/release,0,1)

def noise_texture(rng,sec,center,width):
    n=round(sec*RATE)
    frequencies=np.fft.rfftfreq(n,1/RATE)
    raw=np.fft.rfft(rng.standard_normal(n))
    response=np.exp(-.5*(np.log2(np.maximum(frequencies,1)/center)/width)**2)
    band=np.fft.irfft(raw*response,n=n)
    return band/max(np.std(band)*3,1e-9)

def route(buffer,signal,when,gain,pan=0.):
    if not len(signal):
        return
    first=round(when*RATE)
    last=min(first+len(signal),len(buffer))
    if first>=last:
        return
    a=(pan+1)*math.pi/4
    buffer[first:last,0]+=gain*math.cos(a)*signal[:last-first]
    buffer[first:last,1]+=gain*math.sin(a)*signal[:last-first]

def echoed(buffer,signal,when,gain,pan=0.,delay=.177):
    route(buffer,signal,when,gain,pan)
    for j in range(1,5):
        route(buffer,signal,when+delay*j,gain*(.27**j),pan*(-1)**j)

def mallet(note,sec,soft=False):
    t=time_grid(sec)
    f=hz(note)
    attack=1-np.exp(-(125 if soft else 230)*t)
    phase=TAU*f*t
    color=.61*np.sin(phase+.27*np.exp(-5.4*t)*np.sin(phase*2.004))
    color+=.21*np.sin(phase*2.001+.4)*np.exp(-2.3*t)
    color+=.13*np.sin(phase*3.008+1)*np.exp(-7.4*t)
    color+=.055*np.sin(phase*5.032+.3)*np.exp(-15*t)
    return color*attack*np.exp(-(2.5 if soft else 4.1)*t)*taper(t,.004,.11)

def kick(sec=.42):
    t=time_grid(sec)
    angle=TAU*(43*t+74*(1-np.exp(-36*t))/36)
    return (.79*np.sin(angle)+.17*np.sin(angle*2.036))*np.minimum(1,185*t)*np.exp(-10.5*t)

def music():
    rng=np.random.default_rng(SEED)
    output=np.zeros((round(RATE*DURATION),2),dtype=np.float64)
    chords=[
        (0.0,(38,45,53,57,64)),(4.45,(34,41,53,57,60)),
        (8.14,(41,48,55,57,64)),(12.06,(36,43,52,57,62)),
        (16.58,(34,41,53,57,60)),(20.7,(33,45,52,57,64)),
        (TARGET_TIMES[-1],(38,45,53,60,64)),
    ]
    for i,(start,chord) in enumerate(chords):
        end=chords[i+1][0] if i+1<len(chords) else DURATION
        head=max(0.,start-.29)
        t=time_grid(min(DURATION,end+.56)-head)
        blend=taper(t,.91 if i else .44,.81)
        for j,note in enumerate(chord):
            f=hz(note)
            for side in (-1,1):
                phi=TAU*(f+side*.11)*t+j*.71
                voice=.64*np.sin(phi + .16*np.sin(TAU*(.23+j*.075)*t))
                voice+=.24*np.sin(phi*2.005+.3*side)*(.61+.39*np.sin(t*1.04+j)**2)
                voice+=.095*np.sin(phi*3.002+t*.32)
                intensity=(.053,.027,.024,.020,.015)[j]
                route(output,voice*blend,head,intensity,.55*side)

    tempo=60/116
    for n in range(math.ceil(DURATION/(tempo/2))):
        t=n*tempo/2
        chord=next(c for start,c in reversed(chords) if start<=t)
        ride=(0,2,1,3,2,4,1,3)[n%8]
        pitch=chord[ride]+(24 if ride<2 else 12)
        weight=(.52 if t<3.1 else .82)*(1 if n%2==0 else .66)
        weight*=1-.65*max(0.,1-abs(t-TARGET_TIMES[-1])/.9)
        pan=math.sin(n*.85)*.37
        echoed(output,mallet(pitch,.89,soft=True),t,.065*weight,pan)
        if n%4==0 and 3.10<t<26.7:
            route(output,kick(),t,.084 if t>12 else .060)
        if n%2==1 and 7.70<t<26.9:
            x=time_grid(.155)
            hiss=noise_texture(rng,.155,5900,1.0)
            route(output,hiss*taper(x,.009,.065)*np.exp(-13*x),t,.036,pan)

    opening=time_grid(.88)
    launch=np.sin(TAU*(315*opening+610*opening*opening))*.19
    launch+=noise_texture(rng,.88,1900,1.35)*.28
    route(output,launch*taper(opening,.14,.27)*np.exp(-.90*opening),.04,.125,-.12)
    route(output,kick(),0.,.20)

    pitches=(67,74,76,81,79,86)
    pans=(0.,.38,-.38,.39,-.35,.23)
    for j,when in enumerate(TARGET_TIMES):
        pan=pans[j]
        length=(.53,.67,.88,.64,.83,1.18)[j]
        lead=min(length*.65,when)
        x=time_grid(length)
        approach=(x/length)**1.62*np.clip((length-x)/.16,0,1)
        shift=TAU*((214+64*j)*x+(372+j*80)*x*x)
        texture=noise_texture(rng,length,760+320*j,.95)
        sweep=(.29*np.sin(shift)+.78*texture)*approach
        route(output,sweep,when-lead,.105 if j<4 else .135,pan*.82)
        echoed(output,mallet(pitches[j],1.18 if j!=5 else 1.86),when,
               (.102,.146,.144,.128,.147,.198)[j],pan)
        if j in (2,3,5):
            echoed(output,mallet(pitches[j]+7,.85),when+.074,.074,pan*-.55)
        if j in (0,2,4,5):
            route(output,kick(.58),when,.13 if j!=5 else .25)

    # A moving spatial bed supports the long camera pull into interstellar space.
    start=22.12
    t=time_grid(TARGET_TIMES[-1]-start+.78)
    swell=taper(t,1.3,.96)*(1+.16*np.sin(t*8.6))
    wash=noise_texture(rng,t[-1]+1/RATE,1370,1.50)[:len(t)]
    for side in (-1,1):
        carrier=.28*np.sin(TAU*(112*t+10*t*t+side*.24*t))
        route(output,(wash+carrier)*swell,start,.082,.72*side)
    for x,pitch in enumerate((74,81,86,88)):
        echoed(output,mallet(pitch,1.22),TARGET_TIMES[-1]+.115*x,.079,.46*(-1)**x)

    # Crossfeed delays put transients behind the dry score while retaining mono compatibility.
    wet=np.zeros_like(output)
    for seconds,gain in ((.029,.075),(.071,.056),(.112,.037),(.183,.023)):
        d=round(seconds*RATE)
        wet[d:]+=output[:-d,::-1]*gain
    output+=wet
    fade_in=np.minimum(np.arange(len(output))/(RATE*.045),1.)
    fade_out=np.minimum(np.arange(len(output)-1,-1,-1)/(RATE*.60),1.)
    output*= (fade_in*fade_out)[:,None]
    return np.rint(np.clip(output,-.98,.98)*32767).astype("<i2")

def run(*args):
    subprocess.run([str(a) for a in args],check=True)

def streamhash(path,index):
    return subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-map",index,
        "-c","copy","-f","streamhash","-hash","sha256","-"],text=True).strip()

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("input",type=Path)
    cli.add_argument("output",type=Path)
    args=cli.parse_args()
    sha=hashlib.sha256(args.input.read_bytes()).hexdigest()
    if sha!=ORIGINAL_SHA256:
        raise ValueError("Input does not match the previously published picture lock")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    score=args.output.with_suffix(".score.wav")
    pcm=music()
    with wave.open(str(score),"wb") as wav:
        wav.setparams((2,2,RATE,len(pcm),"NONE","not compressed"))
        wav.writeframes(pcm.tobytes())
    try:
        run("ffmpeg","-v","error","-y","-i",args.input,"-i",score,"-map","0:v:0","-map","1:a:0",
            "-c:v","copy","-c:a","aac","-b:a","224k","-ar",RATE,
            "-af","loudnorm=I=-14.4:TP=-1.4:LRA=9","-map_metadata","-1","-map_metadata:s","-1",
            "-map_chapters","-1","-fflags","+bitexact","-flags:a","+bitexact","-movflags","+faststart",args.output)
    finally:
        score.unlink(missing_ok=True)
    source_video=streamhash(args.input,"0:v:0")
    if source_video!=streamhash(args.output,"0:v:0"):
        raise RuntimeError("Video packets changed")
    if streamhash(args.input,"0:a:0")==streamhash(args.output,"0:a:0"):
        raise RuntimeError("The audio stream was not replaced")
    print("Encoded H.264 stream is identical to the original:",source_video,flush=True)

if __name__=="__main__":
    main()
