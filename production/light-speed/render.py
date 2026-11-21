"""A source-checked, uninterrupted portrait journey along a light pulse."""
from bisect import bisect_right
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
import argparse
import math
import subprocess
import wave

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from automate_ytb.universal_scale_journey import derive_scale_journey, eased_progress, scale_coordinate

W,H,FPS,SAMPLE_RATE=810,1440,30,48000
C=299792458
OUT=Path("build/light-speed")
OUT.mkdir(parents=True,exist_ok=True)
cv2.setNumThreads(2)
WHITE=(247,248,240)
CYAN=(132,240,223)
MUTED=(129,153,180)
WARM=(255,206,123)
PURPLE=(177,154,224)
TAU=math.tau

# Screen time, measured distance, waypoint description, sprite, scale label.
# Neptune is an approximation to its orbital distance, not a live ephemeris.
STOPS=[
    (0.,3.2,"EARTH DIAMETER","12742 km","earth","12,742 km"),
    (3.2,7.65,"THE MOON","384400 km","moon","384,400 km"),
    (7.65,12.38,"THE SUN","149597871 km","sun","149.6 million km"),
    (12.38,17.28,"NEPTUNE'S DISTANCE","4495000000 km","neptune","≈ 4.5 billion km"),
    (17.28,21.87,"ONE LIGHT-DAY","25902068371 km","day","25.9 billion km"),
    (21.87,30.8,"PROXIMA CENTAURI","4.24 light-years","proxima","≈ 40 trillion km"),
]
JOURNEY=derive_scale_journey([{"title":s[2],"narration":s[3]} for s in STOPS])
if JOURNEY is None:
    raise ValueError("All six reference distances must be strictly increasing.")
DIST=[float(p["metres"]) for p in JOURNEY["points"]]
COORD=[scale_coordinate(JOURNEY,Decimal(p["metres"])) for p in JOURNEY["points"]]
LOW=math.log10(DIST[0])-.45
HIGH=math.log10(DIST[-1])+.45
SPEED=[.60,.65,.69,.67,.63,.62]
TARGET_TIMES=[s[0]+(s[1]-s[0])*u for s,u in zip(STOPS,SPEED)]
PRNG=np.random.default_rng(110621)
star_layers=[
  PRNG.uniform((0,-450,.22),(W,H+450,1.),size=(count,3)) for count in (136,81,37)
]
Y,X=np.mgrid[0:H,0:W].astype(np.float32)
night=np.exp(-((X-W*.52)/(W*.73))**2-((Y-H*.60)/(H*.53))**2)
stars_bg=np.stack([7+night*6,11+night*14,23+night*23],axis=-1).astype(np.uint8)
LAND_MAP=[
 [(25,20),(38,15),(48,23),(47,34),(39,42),(43,45),(38,50),(31,43),(24,37),(17,26)],
 [(41,49),(54,45),(64,54),(61,64),(51,82),(46,85),(43,71),(45,60)],
 [(53,22),(62,14),(76,17),(85,27),(80,35),(69,33),(63,44),(57,38)],
 [(66,39),(75,36),(84,47),(78,65),(70,73),(67,64),(70,53),(62,48)],
 [(82,66),(94,64),(96,77),(86,79),(80,72)]
]
CRATERS=[(-.46,-.24,.15),(.40,-.50,.118),(.25,.40,.205),(-.34,.41,.085),
         (.48,.25,.082),(.07,-.15,.08),(-.66,.17,.062),(-.07,.57,.057),(.62,-.10,.075)]

def smooth(x):
    u=max(0.,min(1.,x))
    return u*u*(3-2*u)

def gain(x):
    return max(0.,min(1.,x))

@lru_cache(maxsize=86)
def text_sprite(text,size,col,bold=True,mwidth=670,align="center"):
    family="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    f=ImageFont.truetype(family,size)
    while max(f.getlength(line) for line in text.splitlines())>mwidth:
        size-=1
        f=ImageFont.truetype(family,size)
    width=math.ceil(max(f.getlength(s) for s in text.splitlines()))+14
    height=round(size*1.30*len(text.splitlines()))+13
    im=Image.new("RGBA",(width,height))
    draw=ImageDraw.Draw(im)
    for n,line in enumerate(text.splitlines()):
        x=7 if align=="left" else width-7 if align=="right" else width/2
        anchor="lm" if align=="left" else "rm" if align=="right" else "mm"
        draw.text((x,7+size*(.64+n*1.30)),line,font=f,fill=col+(255,),anchor=anchor)
    return np.asarray(im)

def composite(dst,src,x,y,opacity=1.):
    if opacity<=0:
        return
    h,w=src.shape[:2]
    x,y=round(x),round(y)
    x0,y0=max(x,0),max(y,0)
    x1,y1=min(x+w,W),min(y+h,H)
    if x1<=x0 or y1<=y0:
        return
    patch=src[y0-y:y1-y,x0-x:x1-x]
    roi=dst[y0:y1,x0:x1]
    alpha=patch[:,:,3,None].astype(np.float32)*(opacity/255)
    roi[:]=roi*(1-alpha)+patch[:,:,:3]*alpha

def text(dst,msg,size,col,x,y,alpha=1.,anchor="center",bold=True,mwidth=670):
    src=text_sprite(msg,size,col,bold,mwidth,anchor)
    offset=src.shape[1]/2 if anchor=="center" else 0 if anchor=="left" else src.shape[1]
    composite(dst,src,x-offset,y-src.shape[0]/2,alpha)

def body(kind, size, phase):
    # Texture is evaluated in spherical screen coordinates on each frame.
    gx,gy=np.meshgrid(np.linspace(-1,1,size,dtype=np.float32),np.linspace(-1,1,size,dtype=np.float32))
    r2=gx*gx+gy*gy
    z=np.sqrt(np.clip(1-r2,0,1))
    lon=np.arctan2(gx,z+.001)
    wave=np.sin(23*gx+phase*.9)*np.sin(18*gy-phase*.6)
    wave+=.52*np.sin(48*gx+29*gy-phase)*np.cos(23*gy+phase*.7)
    wave+=.26*np.cos(100*gy+31*gx+phase*1.6)
    if kind=="earth":
        base=[47,121,184]
    elif kind=="moon":
        base=[154,170,194]
    elif kind=="neptune":
        base=[55,133,207]
        wave+=1.22*np.sin(22*gy+1.3*np.sin(lon*1.6+phase))
    else:
        base=[248,150,56] if kind=="sun" else [242,97,69]
        wave+=.55*np.sin(42*r2+lon*5-phase)
    rgb=np.zeros((size,size,3),dtype=np.float32)+np.array(base,dtype=np.float32)
    rgb+=wave[:,:,None]*np.array([15,12,8])
    if kind in ("earth","moon"):
        surface=Image.new("L",(size,size))
        d=ImageDraw.Draw(surface)
        if kind=="earth":
            for poly in LAND_MAP:
                d.polygon([(round(a*size/100+size*.11*math.sin(phase*.44)),round(b*size/100)) for a,b in poly],fill=255)
            mix=np.asarray(surface).astype(np.float32)/255
            rgb=rgb*(1-mix[:,:,None])+np.array([86,173,131])*mix[:,:,None]
            cloud=np.clip((wave-.60)*.55,0,.55)*(.65+.35*np.sin(17*gy+12*gx+.73*phase))
            rgb=rgb*(1-cloud[:,:,None])+np.array([203,233,240])*cloud[:,:,None]
        else:
            for cx,cy,r in CRATERS:
                x=(cx+.020*math.sin(phase))*size/2+size/2
                y=cy*size/2+size/2
                z0=r*size/2
                d.ellipse((x-z0,y-z0,x+z0,y+z0),fill=164)
                d.arc((x-z0,y-z0,x+z0,y+z0),194,350,fill=59,width=max(1,size//85))
            rgb-=np.asarray(surface).astype(np.float32)[:,:,None]*.255
    lighting=np.clip(-.51*gx-.41*gy+.80*z,0,1)
    if kind in ("sun","proxima"):
        rgb*= (.65+.34*lighting)[:,:,None]
    else:
        rgb*= (.38+.72*lighting**.55)[:,:,None]
    rim=np.exp(-((z-.14)/.18)**2)*np.clip((.70-gx)/1.15,.16,.95)
    rgb+=rim[:,:,None]*np.array([71,84,87])
    coverage=np.clip((1-r2)*size*.36,0,1)
    return np.dstack((np.clip(rgb,0,255),coverage*255)).astype(np.uint8)

def add_ambient(frame,t,q):
    for i,stars in enumerate(star_layers):
        drift=(46*q+t*2.1)*(i+1)**1.42
        for x,y,depth in stars:
            xx=round((x+drift*.17+math.sin(t*.34+y)*4*(i+1))%W)
            yy=round((y+drift)%(H+115))
            if yy<265 or yy>H-100:
                continue
            lum=round(depth*(36+i*26)*(.79+.21*math.sin(t*2.1+x)))
            color=(lum,lum+6,lum+17)
            cv2.circle(frame,(xx,yy),1+int(i==2 and depth>.86),color,-1,cv2.LINE_AA)
    for j in range(12):
        plane=.76+j*.029
        yy=round(H*(plane+.014*math.sin(q*5+j*.21)))
        width=round(W*(.20+j*.054))
        cv2.line(frame,(W//2-width,yy),(W//2+width,yy),(15+j,32+j,45+j),1,cv2.LINE_AA)

def travel_time(seconds):
    if seconds<1:
        return f"{round(seconds*1000)} ms"
    if seconds<10:
        return f"{seconds:.2f} s"
    if seconds<60:
        return f"{round(seconds)} s"
    if seconds<3600:
        minutes,sec=divmod(round(seconds),60)
        return f"{minutes}m {sec:02d}s"
    if abs(seconds-86400) <= 35:
        return "1 light-day"
    if seconds<86400:
        hours,minutes=divmod(round(seconds/60),60)
        return f"{hours}h {minutes:02d}m"
    if seconds<31557600:
        return f"{seconds/86400:.1f} days"
    return f"{seconds/31557600:.2f} years"

def draw_progress(frame,q,index,arrival):
    left=105
    right=705
    y=301
    cv2.line(frame,(left,y),(right,y),(51,75,95),2,cv2.LINE_AA)
    current=round(left+(right-left)*(q-COORD[0])/(COORD[-1]-COORD[0]))
    current=max(left-8,min(current,right))
    cv2.line(frame,(left,y),(current,y),CYAN,3,cv2.LINE_AA)
    for i,p in enumerate(COORD):
        x=round(left+(right-left)*(p-COORD[0])/(COORD[-1]-COORD[0]))
        cv2.line(frame,(x,y-9),(x,y+9),CYAN if i<=index else (84,112,133),2,cv2.LINE_AA)
    cv2.circle(frame,(current,y),5,WARM,-1,cv2.LINE_AA)
    text(frame,"EARTH",17,MUTED,left,326)
    text(frame,"NEXT STAR",17,MUTED,right,326)
    if arrival>.03:
        cv2.circle(frame,(current,y),round(5+17*(1-arrival)),WARM,1,cv2.LINE_AA)

def draw_marker(frame,glow,t,q,p,xy,index,intensity):
    x,y=xy
    s=STOPS[index]
    kind=s[4]
    approach=smooth((q-(p-.095))/.045)
    past=1-smooth((q-p-.034)/.104)
    opacity=approach*past*intensity
    if opacity<=.007 or y<360 or y>1025:
        return
    # Markers are drawn in different depth planes, on both sides of the path.
    side=1 if index in (1,3,5) else -1
    separation=(132,124,132,124,130,135)[index]
    cx=x+side*(separation+round(22*(1-approach)))
    cy=y+round((index%2-.5)*10+7*math.sin(t*.9+index))
    apparent=(128,101,166,129,142,151)[index]
    size=round(apparent*(.89+.18*approach-.22*(1-past)))
    hue=(CYAN,(181,196,219),WARM,(143,178,244),PURPLE,(255,170,110))[index]
    if kind=="day":
        for n in range(4):
            radius=round(size*(.20+.133*n))
            cv2.ellipse(glow,(cx,cy),(radius,round(radius*.64)),-28,
                        (t*41+67*n)%360,(t*41+67*n)%360+280,
                        tuple(round(g*opacity*.4) for g in hue),2,cv2.LINE_AA)
        cv2.circle(frame,(cx,cy),8,tuple(round(g*opacity) for g in hue),-1,cv2.LINE_AA)
    else:
        if kind in ("sun","proxima"):
            for j in range(13):
                a=j*TAU/13+t*.31
                r=size*(.58+.07*math.sin(j*1.8+t*2.6))
                start=(round(cx+size*.39*math.cos(a)),round(cy+size*.39*math.sin(a)))
                end=(round(cx+r*math.cos(a)),round(cy+r*math.sin(a)))
                cv2.line(glow,start,end,tuple(round(g*.52*opacity) for g in hue),2,cv2.LINE_AA)
        cv2.circle(glow,(cx,cy),round(size*.48),tuple(round(g*opacity*.53) for g in hue),4,cv2.LINE_AA)
        composite(frame,body(kind,size,t*.83),cx-size/2,cy-size/2,opacity)
    linecolor=tuple(int(channel*opacity*.75) for channel in hue)
    cv2.line(frame,(x,y),(round(cx-side*size*.42),cy),linecolor,1,cv2.LINE_AA)
    cv2.circle(frame,(x,y),5,linecolor,1,cv2.LINE_AA)
    label_y=cy+round(size*.51)+23
    text(frame,s[2],25,WHITE,cx,label_y,opacity,mwidth=231)
    text(frame,s[5],23,hue,cx,label_y+31,opacity,bold=False,mwidth=220)

@lru_cache(maxsize=1)
def origin_earth():
    return body("earth",400,1.24)

def ship_out(frame,glow,x,y,t):
    # The interstellar leg is much longer than the planetary legs. Moving
    # trails make the last camera pullback visible even between landmarks.
    weight=smooth((t-22.28)/.77)*(1-smooth((t-27.24)/.82))
    if weight<.01:
        return
    for i in range(78):
        a=i*2.399963
        phase=(i*.618034+(t-22.0)*.52)%1
        dist=49+phase**1.92*652
        span=(6+phase*phase*125)*weight
        cs,sn=math.cos(a),math.sin(a)
        p=(round(x+cs*dist),round(y+sn*dist))
        q=(round(x+cs*(dist+span)),round(y+sn*(dist+span)))
        level=round(weight*(18+phase*55)*(.47+.53*math.sin(math.pi*phase)**2))
        color=(level,round(level*.95),round(level*1.54))
        if p[1]>358 and q[1]>330:
            cv2.line(frame,p,q,color,1+int(phase>.89),cv2.LINE_AA)
            if i%7==0:
                cv2.line(glow,p,q,color,3,cv2.LINE_AA)

def paint(t):
    index=min(len(STOPS)-1,bisect_right([s[0] for s in STOPS],t)-1)
    start,end,*_=STOPS[index]
    p=gain((t-start)/(end-start))
    flight=gain(p/SPEED[index])
    q=eased_progress(JOURNEY,index,flight)
    arrive=1-smooth((t-TARGET_TIMES[index])/.68) if t>=TARGET_TIMES[index] else 0.
    sec=10**(LOW+(HIGH-LOW)*q)/C
    frame=stars_bg.copy()
    add_ambient(frame,t,q)
    # The moving camera and fixed world markers use the same logarithmic axis.
    camera=q + .49*(1-smooth(t/2.10)) - .155*math.sin(math.pi*flight)**2 - .026*math.sin(q*6.2)
    fx=W/2+16*math.sin(q*4.8)
    base=1094
    edge=479
    view=563+151*q
    marker_y=lambda a:round(edge+(camera-a)*view)
    glow=np.zeros_like(frame)
    core=np.zeros_like(frame)
    tip=(round(fx),marker_y(q))
    foot=(round(fx-38*q),base)
    ship_out(frame,glow,*tip,t)
    radius=round(17+405*(1-smooth(t/7.7)))
    origin=cv2.resize(origin_earth(),(2*radius,2*radius),interpolation=cv2.INTER_LINEAR)
    composite(frame,origin,foot[0]-radius,base-7, .84)
    cv2.ellipse(glow,(foot[0],base+radius-7),(radius,radius),0,211,329,(60,110,145),2,cv2.LINE_AA)
    cv2.line(glow,tip,foot,(121,77,31),17,cv2.LINE_AA)
    cv2.line(core,tip,foot,(252,187,101),7,cv2.LINE_AA)
    cv2.line(core,tip,foot,(255,247,204),2,cv2.LINE_AA)
    for j in range(25):
        k=(j/25-t*.89)%1
        x=round(tip[0]+(foot[0]-tip[0])*k + 22*math.sin(j*12+t*3)*k)
        y=round(tip[1]+(foot[1]-tip[1])*k)
        power=round(31+147*(1-k))
        cv2.circle(core,(x,y),1+int(j%9==0),(power,int(power*.78),int(power*.41)),-1,cv2.LINE_AA)
    for i,coord in enumerate(COORD):
        y=marker_y(coord)
        x=round(tip[0]+(foot[0]-tip[0])*gain((y-tip[1])/(base-tip[1])))
        draw_marker(frame,glow,t,q,coord,(x,y),i,1. if i==index else .79)
    cv2.circle(glow,tip,16+(round(35*(1-arrive)) if arrive else 0),(189,109,43),4,cv2.LINE_AA)
    cv2.circle(core,tip,5,(255,248,222),-1,cv2.LINE_AA)
    for i in range(1,5):
        y=tip[1]-(12+8*i)
        cv2.line(core,(tip[0]-10//i,y),(tip[0]+10//i,y),(201//i,143//i,82//i),1,cv2.LINE_AA)
    frame=cv2.add(frame,cv2.GaussianBlur(glow,(0,0),10))
    frame=cv2.add(frame,core)
    cv2.ellipse(frame,foot,(58,10),0,0,360,(74,91,105),1,cv2.LINE_AA)
    cv2.ellipse(frame,foot,(21,5),0,0,360,WARM,1,cv2.LINE_AA)
    text(frame,"FROM EARTH",19,(175,206,223),foot[0],1140)
    text(frame,"HOW FAR CAN",55,WHITE,W/2,132)
    text(frame,"LIGHT GO?",61,WHITE,W/2,198)
    text(frame,travel_time(sec),38,CYAN,W/2,259)
    draw_progress(frame,q,index,arrive)
    if t<3.08:
        text(frame,"One pulse. Watch the clock.",26,WHITE,W/2,1188,1-smooth((t-2.46)/.56))
    final=smooth((t-27.15)/.46)
    if final:
        text(frame,"4.24 years to the next star.",28,WHITE,W/2,1190,final)
    return frame

def music():
    n=round(STOPS[-1][1]*SAMPLE_RATE)
    t=np.arange(n,dtype=np.float64)/SAMPLE_RATE
    out=np.zeros((n,2),np.float64)
    notes=(55,61.735,65.406,73.416,82.407,98)
    for i,(start,end,*_) in enumerate(STOPS):
        sel=(t>=max(0,start-.30))&(t<=min(t[-1],end+.28))
        local=t[sel]-start
        ramp=np.clip((local+.30)/.57,0,1)*np.clip((end-t[sel]+.28)/.57,0,1)
        for ch in (0,1):
            f=notes[i]+.09*ch
            x=TAU*f*t[sel]
            bed=.085*np.sin(x+.40*np.sin(local*1.7))+.043*np.sin(x*2.003+ch*.4)
            bed+=.034*np.sin(x*3.005+local*.97)+.019*np.sin(x*5.002+.66*math.sin(i))
            out[sel,ch]+=bed*ramp
        beat=.46-.018*i
        for j in range(math.ceil((end-start)/beat)):
            event=start+.02+j*beat
            sel=(t>=event)&(t<event+.59)
            z=t[sel]-event
            pitch=notes[i]*(4,6,8,5)[j%4]
            tone=np.sin(TAU*pitch*z+.49*np.sin(TAU*2.004*pitch*z)*np.exp(-13*z))
            pulse=tone*np.minimum(z*190,1)*np.exp(-(9+j%2)*z)
            out[sel,j%2]+=.087*pulse
            out[sel,1-j%2]+=.052*pulse
    for i,when in enumerate([0.0]+TARGET_TIMES):
        sel=(t>=when)&(t<when+.93)
        z=t[sel]-when
        hit=(np.sin(TAU*(43*z+36*(1-np.exp(-8*z))/8))*.20+
            np.sin(TAU*(492+46*i)*z)*.087)*np.exp(-6.1*z)*np.minimum(z*220,1)
        out[sel,0]+=hit
        out[sel,1]+=.88*hit
    out*=np.minimum(t/.048,1)[:,None]*np.minimum((t[-1]-t)/.44,1)[:,None]
    pcm=(np.clip(out,-.99,.99)*32767).astype("<i2")
    with wave.open(str(OUT/"score.wav"),"wb") as wav:
        wav.setparams((2,2,SAMPLE_RATE,len(pcm),"NONE","not compressed"))
        wav.writeframes(pcm.tobytes())

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    opts=parser.parse_args()
    if opts.preview:
        for i,t in enumerate((1.85,3.05,6.95,11.6,16.4,20.9,25.2,29.1)):
            Image.fromarray(paint(t)).save(OUT/f"preview-{i}.jpg",quality=91)
        return
    music()
    raw=OUT/"encoded.mp4"
    target=OUT/"how-far-can-light-go.mp4"
    cmd=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","30","-i","pipe:0",
         "-i",str(OUT/"score.wav"),"-map","0:v:0","-map","1:a:0",
         "-vf","scale=1080:1920:flags=lanczos:out_color_matrix=bt709","-pix_fmt","yuv420p",
         "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
         "-c:v","libx264","-preset","fast","-crf","18","-maxrate","9M","-bufsize","13M","-threads","4",
         "-af","loudnorm=I=-14.4:TP=-1.4:LRA=8","-c:a","aac","-b:a","192k","-ar","48000",str(raw)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(round(STOPS[-1][1]*FPS)):
            if n%(FPS*5)==0:
                print("Rendering",n/FPS,flush=True)
            proc.stdin.write(paint(n/FPS).tobytes())
    finally:
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError("Failed to encode portrait short")
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(raw),"-map","0:v","-map","0:a","-c","copy",
                    "-map_metadata","-1","-map_metadata:s","-1","-map_chapters","-1","-fflags","+bitexact",
                    "-movflags","+faststart",str(target)],check=True)
    raw.unlink()

if __name__=="__main__":
    main()
