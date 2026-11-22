"""Original score, synchronous drill foley and encoded-audio onset check."""
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

from timeline import CUES, FRAME_COUNT, RATE, SAMPLES

TAU=math.tau
N=FRAME_COUNT*SAMPLES

def seconds(n):
    return np.arange(round(RATE*n),dtype=np.float64)/RATE

def fade(t,a,r):
    return np.clip(t/a,0,1)*np.clip((t[-1]-t)/r,0,1)

def hz(note):
    return 440*2**((note-69)/12)

def lay(out,mono,sample,volume,pan=0.):
    end=min(N,sample+len(mono))
    if end<=sample:
        return
    ang=(pan+1)*math.pi/4
    out[sample:end]+=mono[:end-sample,None]*volume*np.array([math.cos(ang),math.sin(ang)])

def band_noise(rng,t,low,high):
    n=len(t)
    f=np.fft.rfftfreq(n,1/RATE)
    width=np.clip(f/(low+1),0,1)*np.exp(-(f/high)**2.6)
    v=np.fft.irfft(np.fft.rfft(rng.standard_normal(n))*width,n=n)
    return v/max(3*np.std(v),1e-8)

def drum(t):
    p=TAU*(49*t+77*(1-np.exp(-32*t))/32)
    return (np.sin(p)+.30*np.sin(2.018*p))*np.minimum(t*390,1)*np.exp(-10*t)

def note(midi,t):
    p=TAU*hz(midi)*t
    vib=.26*np.sin(p*2.011)*np.exp(-t*4)
    return (.71*np.sin(p+vib)+.19*np.sin(p*2.003+.55)+.10*np.sin(p*3.017))*fade(t,.008,.18)*np.exp(-t*3.05)

def signature(freq,index):
    t=seconds(.090)
    p=TAU*(freq*t+(1750+390*index)*t*t)
    env=fade(t,.0019,.05)*np.exp(-t*15.5)
    return (.68*np.sin(p)+.21*np.sin(p*1.873)+.11*np.sin(p*2.713))*env

def compose(path):
    mix=np.zeros((N,2),np.float64)
    rng=np.random.default_rng(2611)
    subdivisions=60/126/2
    score_stops=[0.,3.8,7.5,12.,16.72,18.70,22.46,26.77,32.]
    harmony=[(38,45,53,60),(34,41,53,57),(41,48,55,64),(36,43,52,55),
             (33,45,48,64),(26,38,45,53),(34,46,50,57),(38,45,53,64)]
    for i,(a,b) in enumerate(zip(score_stops,score_stops[1:])):
        t=seconds(b-a+.66)
        for k,midi in enumerate(harmony[i]):
            f=hz(midi)
            for pan in (-.53,.53):
                p=TAU*(f+.11*pan)*t+k*.37
                pad=.70*np.sin(p+.13*np.sin(t*.56+k))+.22*np.sin(p*2.007)+.08*np.sin(p*3.01)
                lay(mix,pad*fade(t,.79,.80),round(a*RATE),(.057,.036,.027,.019)[k],pan)
    for i in range(math.ceil(32/subdivisions)):
        now=i*subdivisions
        if 18.55<now<19.1 or 22.18<now<23.22 or 26.30<now<27.1:
            continue
        chord=harmony[max(j for j,a in enumerate(score_stops[:-1]) if now>=a)]
        pitch=chord[(0,2,1,3,2,1,3,2)[i%8]]+24
        pan=math.sin(i*.83)*.50
        t=seconds(.59)
        pluck=note(pitch,t)
        amp=(.055 if i%2 else .082)*(.73 if now<3.1 else 1.)
        lay(mix,pluck,round(now*RATE),amp,pan)
        lay(mix,pluck,round((now+.179)*RATE),amp*.22,-pan)
        if i%4==0 and 1.4<now<28.75:
            lay(mix,drum(seconds(.44)),round(now*RATE),.098 if now<20 else .123)
        if i%2==1 and 4.<now<26.2:
            t=seconds(.116)
            pulse=band_noise(rng,t,3800,9500)*fade(t,.004,.06)*np.exp(-t*11)
            lay(mix,pulse,round(now*RATE),.064,pan*.73)

    # Mechanical rasp starts at contact and stops as the drill locks at Kola.
    start,end=CUES[0].frame*SAMPLES,CUES[4].frame*SAMPLES
    t=seconds((end-start)/RATE)
    envelope=fade(t,.10,.10)*(.63+.37*np.sin(t*22+t*t*.12)**2)
    grit=band_noise(rng,t,180,1700)
    motor=np.sin(TAU*(67*t+1.09*t*t))+.30*np.sin(TAU*(138*t+2.4*t*t))
    lay(mix,(.48*grit+.20*motor)*envelope,start,.127,-.10)

    # Let the score recede around the drill stop and scale reveal so the
    # mechanical hit and the final chord each have room to land.
    clock=np.arange(N,dtype=np.float64)/RATE
    automation=np.interp(clock,
        [0,1.6,4.3,8.0,12.4,16.8,18.22,19.04,20.5,21.83,22.35,23.45,24.75,26.35,27.3,29.6,31.8],
        [.55,.69,.89,1.0,1.17,1.23,.78,.46,.71,.53,.17,.35,.87,.38,1.38,1.23,.74])
    mix*=automation[:,None]

    for i,c in enumerate(CUES):
        at=c.frame*SAMPLES
        transient=signature(c.frequency,i)
        pan=(0.,-.34,.32,-.28,.08,-.32,.24)[i]
        lay(mix,transient,at,(.27,.21,.22,.23,.34,.25,.30)[i],pan)
        lay(mix,transient,at+round(.115*RATE),.041,-pan)
        t=seconds((.53,.48,.72,.58,1.18,1.30,1.17)[i])
        grit=band_noise(rng,t,(760,1830,920,2100,720,430,780)[i],2900+i*330)
        burst=grit*fade(t,.014,.21)*np.exp(-t*(5 if i<5 else 1.9))
        lay(mix,burst,at,.17 if i in (0,4,5) else .11,pan)
        if i in (0,2,4,6):
            lay(mix,drum(t),at,.25 if i in (4,6) else .15)
        if i in (1,3,6):
            for j,n in enumerate((72+i,79+i,84+i) if i==6 else (70+i,77+i)):
                lay(mix,note(n,seconds(1.1)),at+round(.073*j*RATE),.122/(1+j*.32),-pan)
        if i==5:
            p=TAU*(650*t-178*t*t)
            lay(mix,np.sin(p)*fade(t,.11,.60),at,.094,-.49)

    for dt,level in ((.029,.057),(.112,.043),(.196,.022)):
        d=round(dt*RATE)
        mix[d:]+=mix[:-d,::-1].copy()*level
    t=np.arange(N)/RATE
    mix*=fade(t,.029,.67)[:,None]
    encoded=np.rint(np.clip(mix,-.95,.95)*32767).astype("<i2")
    with wave.open(str(path),"wb") as f:
        f.setparams((2,2,RATE,N,"NONE","not compressed"))
        f.writeframes(encoded.tobytes())

def verify_sync(video,receipt):
    raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(video),"-map","0:a:0",
        "-ar",str(RATE),"-ac","1","-f","f32le","pipe:1"])
    x=np.frombuffer(raw,dtype=np.float32)
    report=[]
    for i,c in enumerate(CUES):
        at=c.frame*SAMPLES
        base=at-round(.095*RATE)
        s=signature(c.frequency,i).astype(np.float32)[:1392]
        w=x[base:at+round(.095*RATE)+len(s)]
        # First derivative downweights bass and momentum of the musical bed.
        z=np.diff(w)
        p=np.diff(s)
        hit=int(np.argmax(np.correlate(z,p,mode="valid")))+base
        delay=hit-at
        if abs(delay)>SAMPLES:
            raise RuntimeError(f"{c.name} onset missed its locked video frame: {delay} samples")
        report.append({"cue":c.name,"videoFrame":c.frame,"expectedSample":at,"matchedSample":hit,
                       "offsetMs":round(1000*delay/RATE,3)})
    Path(receipt).write_text(json.dumps(report,indent=2)+"\n")
    print("Encoded soundtrack cues:",report,flush=True)
