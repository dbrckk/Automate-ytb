"""Draw a continuous drill descent and a planetary-scale reveal."""
import argparse
from functools import lru_cache
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from sound import compose, verify_sync
from timeline import CUES, FRAME_COUNT, FPS, KOLA, RADIUS, depth, ease, shot

W,H=720,1280
OUT=Path("build/deepest-hole")
OUT.mkdir(parents=True,exist_ok=True)
cv2.setNumThreads(2)
rng=np.random.default_rng(4541)
X,Y=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
WHITE=(251,244,224)
GOLD=(255,201,123)
TEAL=(143,238,206)
BLUE=(159,192,228)
INK=(13,21,30)
PALETTE=np.array([(37,51,50),(65,57,43),(117,69,43),(132,79,55),
                  (62,60,85),(55,65,88),(87,53,79),(122,50,65)],np.float32)
SIZE=(960,2420)
tx,ty=np.meshgrid(np.linspace(0,1,SIZE[0],dtype=np.float32),
                    np.linspace(0,1,SIZE[1],dtype=np.float32))

def noise(size,levels):
    h,w=size
    n=np.zeros((h,w),np.float32)
    for rows,cols,weight in levels:
        coarse=rng.normal(0,1,(rows,cols)).astype(np.float32)
        n+=cv2.resize(coarse,(w,h),interpolation=cv2.INTER_CUBIC)*weight
    return n

def rock_texture():
    shape=ty.shape
    n=noise(shape,[(12,9,.51),(32,27,.28),(92,65,.13),(240,177,.08)])
    fine=noise(shape,[(89,15,.52),(241,55,.35),(880,320,.14)])
    bend=ty+.018*np.sin(tx*9.3)+.006*np.sin(tx*38)+n*.009
    layers=.41+.24*np.cos(bend*141+fine*.84)+.10*np.sin(bend*510+fine*.55)
    layers+=np.exp(-((bend*35%1-.65)/.09)**2)*.19
    c=np.stack([np.interp(bend,np.linspace(-.01,1.02,len(PALETTE)),PALETTE[:,i])
                for i in range(3)],axis=-1)
    c*= (.69+layers*.49+n*.17)[:,:,None]
    veins=np.clip((n-.6)*1.7,0,.43)*np.exp(-((bend*23%1-.34)/.11)**2)
    c+=veins[:,:,None]*[81,93,109]
    return np.clip(c,0,255).astype(np.uint8)

ROCK=rock_texture()
XMAP=X+111
NIGHT=np.stack([9+Y*.006,13+Y*.011,23+Y*.015],axis=-1).astype(np.uint8)
GHOSTS=rng.uniform((0,0,.13),(W,H,1),size=(151,3))
SPARKS=rng.uniform((0.,.51,.20,.025),(math.tau,1.39,1.25,.87),size=(67,4))
WALL_SHADE=(np.clip(.82+.15*np.sin((X/W)*math.pi),0,1)*255).astype(np.uint8)
SHADE=cv2.merge([WALL_SHADE]*3)

@lru_cache(maxsize=115)
def glyph(s,size,c,max_width=640):
    f=ImageFont.truetype("DejaVuSans-Bold.ttf",size)
    while f.getlength(s)>max_width:
        size-=1
        f=ImageFont.truetype("DejaVuSans-Bold.ttf",size)
    w=math.ceil(f.getlength(s))+10
    im=Image.new("RGBA",(w,size+15))
    d=ImageDraw.Draw(im)
    d.text((w/2,(size+15)/2),s,font=f,fill=c+(255,),anchor="mm",stroke_width=1,stroke_fill=(12,15,24,224))
    return np.asarray(im)

def overlay(dst,img,x,y,opacity=1.):
    h,w=img.shape[:2]
    x,y=round(x),round(y)
    x0,y0=max(0,x),max(0,y)
    x1,y1=min(W,x+w),min(H,y+h)
    if opacity<=0. or x1<=x0 or y1<=y0:
        return
    src=img[y0-y:y1-y,x0-x:x1-x]
    roi=dst[y0:y1,x0:x1]
    a=src[:,:,3,None]*(opacity/255.)
    roi[:]=src[:,:,:3]*a+roi*(1-a)

def text(frame,s,size,color,x,y,opacity=1.,max_width=640):
    g=glyph(s,size,color,max_width)
    overlay(frame,g,x-g.shape[1]/2,y-g.shape[0]/2,opacity)

def scene_landmarks():
    icons=[]
    for i in range(4):
        im=Image.new("RGBA",(230,166))
        d=ImageDraw.Draw(im)
        if i==0:
            layers=[[(40,145),(53,103),(72,85),(80,111),(101,77),(131,52),(154,25),
                      (185,65),(210,86),(221,145)],
                    [(18,146),(48,114),(84,128),(109,102),(126,119),(156,87),(177,120),(212,123),(227,146)]]
            d.polygon(layers[0],fill=(33,79,83,255))
            d.line(layers[0],fill=(94,155,151,255),width=2)
            d.polygon(layers[1],fill=(39,118,100,255))
        elif i==1:
            d.line((117,11,117,145),fill=(255,232,195,255),width=3)
            for j in range(10):
                y=20+j*12
                w=5+j*3
                d.polygon([(115-w,y+1),(117+w,y-7),(116+w,y+13),(115-w,y+18)],
                          fill=(77+j*5,131+j*4,162+j*4,255))
                d.line((116-w,y+1,118+w,y-7),fill=(197,224,230,255),width=2)
                d.line((113,y+1,113,y+13),fill=(224,226,181,255),width=1)
                d.line((120,y+1,121,y+13),fill=(38,84,102,255),width=2)
        elif i==2:
            path=[(15,71),(61,73),(77,84),(103,121),(115,134),(141,133),(162,108),
                  (177,66),(216,67)]
            for j in range(5):
                pts=[(x,min(156,y+j*7)) for x,y in path]
                d.polygon(pts+[(216,157),(15,157)],fill=(151+14*j,74+j*13,49+j*5,255))
                d.line(pts,fill=(223,151+j*8,105,255),width=2)
            d.line((102,137,118,145,144,141,157,147),fill=(102,195,208,255),width=4)
        else:
            d.rounded_rectangle((34,53,195,147),radius=30,fill=(31,42,54,255),outline=(104,180,179,255),width=4)
            for x in (62,100,139,173):
                d.line((x,137,x,87,x+10,69),fill=(99,129,138,255),width=3)
            d.line((42,131,193,131),fill=(122,170,167,255),width=2)
            d.line((46,140,188,140),fill=(96,139,144,255),width=2)
            d.polygon([(81,101),(129,101),(123,127),(88,127)],fill=(197,132,61,255),outline=(242,190,119,255),width=2)
            for x in (94,117):
                d.ellipse((x-5,124,x+5,134),fill=(51,55,62,255),outline=(165,175,174,255))
            for x,y in ((94,95),(106,93),(113,97),(121,92),(86,97)):
                d.polygon([(x-5,y),(x,y-6),(x+6,y)],fill=(253,215,115,255))
        icons.append(np.asarray(im))
    return icons

ICONS=scene_landmarks()

def drill(frame,x,y,t,stopped):
    gear=(x,y-37)
    cv2.rectangle(frame,(x-11,0),(x+11,y-34),(26,36,41),-1)
    cv2.line(frame,(x-6,0),(x-6,y-36),(93,118,118),2,cv2.LINE_AA)
    cv2.line(frame,(x+7,0),(x+7,y-36),(206,140,83),2,cv2.LINE_AA)
    for a in range(10,y-35,27):
        cv2.line(frame,(x-11,a),(x+11,a),(132,150,138),1,cv2.LINE_AA)
    silhouette=np.array([(x-30,y-64),(x+30,y-64),(x+29,y-20),(x+15,y+4),
                         (x,y+13),(x-16,y+4),(x-30,y-20)],np.int32)
    cv2.fillConvexPoly(frame,silhouette,(33,59,69),cv2.LINE_AA)
    cv2.polylines(frame,[silhouette],True,(146,195,189),2,cv2.LINE_AA)
    cs=math.sin((min(t,18.7) if stopped else t)*17)
    cv2.line(frame,(x-24,y-12),(x+20,y-35),(255,183,85),5,cv2.LINE_AA)
    for i in range(3):
        q=round((i-1)*13+6*cs)
        cv2.line(frame,(x+q,y-58),(x+q-4,y-22),(124,174,168),2,cv2.LINE_AA)
    cv2.circle(frame,gear,6,(229,221,165),-1,cv2.LINE_AA)
    cv2.circle(frame,(x,y+11),4,GOLD,-1,cv2.LINE_AA)

def launch_sparks(frame,glow,x,y,f):
    for i,c in enumerate(CUES[:5]):
        dt=(f-c.frame)/FPS
        if not 0 <= dt < .64:
            continue
        for a,s,fade,offset in SPARKS:
            life=dt-offset*.18
            if life<0:
                continue
            pulse=(1-dt/.64)**1.4
            d=life*s*(133+19*i)
            ax=round(x+math.cos(a)*d)
            ay=round(y-6+math.sin(a)*d*.54+74*life*life)
            lum=min(255,round(pulse*fade*239))
            cv2.circle(frame,(ax,ay),2 if fade>.9 else 1,(lum,round(lum*.71),round(lum*.39)),-1,cv2.LINE_AA)
            if fade>1.08:
                cv2.circle(glow,(ax,ay),3,(lum,round(lum*.56),round(lum*.24)),-1,cv2.LINE_AA)
    if CUES[0].frame<f<CUES[4].frame:
        t=f/FPS
        for i in range(24):
            phase=(i*.173+t*(2.0+i*.011))%1
            side=(-1)**i
            dx=round(6+side*(14+phase*58))
            dy=round(-4+14*math.sin(i)-83*phase+58*phase**2)
            g=round((1-phase)*(61+(i*31)%165))
            cv2.line(frame,(x+dx,y+dy),(x+dx+side*3,y+dy+3),(g,g//2,g//5),1,cv2.LINE_AA)

def underground(f):
    t=f/FPS
    dp=depth(f)
    u=math.log1p(dp/415)/math.log1p(KOLA/415)
    a=shot(f)
    cue=CUES[a]
    age=(f-cue.frame)/FPS
    shake=round(2.6*math.sin(26*t)*math.exp(-max(0.,age)*8.7)) if 0<=age<.4 else 0
    x=round(352+11*math.sin(u*4.5)+shake)
    py=round(533+u*193+14*math.sin(u*9.25)+shake)
    ground=round(535-u*974)+shake
    surface=np.maximum(Y-ground,0.)
    ymap=(surface*(1.22-.18*u)+u*354).astype(np.float32)
    rock=cv2.remap(ROCK,XMAP,ymap,cv2.INTER_LINEAR)
    frame=np.where((Y>=ground)[:,:,None],rock,NIGHT).astype(np.uint8)
    frame=cv2.multiply(frame,SHADE,scale=1/255)
    if ground>0:
        for h,w,color,light in ((-45,495,(21,45,52),(32,72,72)),(-30,127,(36,89,77),(55,112,95))):
            pts=np.array([(i,round(ground+h-19*math.sin(i/61)-32*math.cos(i/(w*.32)+h)))
                          for i in range(0,W+14,12)],np.int32)
            cv2.fillPoly(frame,[np.vstack((pts,(W,ground),(0,ground)))],color,cv2.LINE_AA)
            cv2.polylines(frame,[pts],False,light,1,cv2.LINE_AA)
        cv2.line(frame,(0,ground),(W,ground),(129,161,112),3,cv2.LINE_AA)
    anchor=py-95
    cv2.line(frame,(x-26,max(329,ground)),(x-23,anchor+71),(21,28,36),6,cv2.LINE_AA)
    cv2.line(frame,(x+26,max(329,ground)),(x+23,anchor+71),(25,35,43),8,cv2.LINE_AA)
    # Near and far dust drift at different speeds as the camera tracks the bore.
    for i,(gx,gy,z) in enumerate(GHOSTS):
        ay=round((gy-u*(.5+z*1.4)*628+t*(7+4*z))%H)
        ax=round((gx+6*math.sin(t*.51+i)-u*z*18)%W)
        if ay<max(336,ground) or abs(ax-x)<24:
            continue
        v=round(16+z*57)
        cv2.circle(frame,(ax,ay),1+int(z>.84),(v,v-1,v-5),-1,cv2.LINE_AA)
    drill(frame,x,py,t,f>=CUES[4].frame)
    glow=np.zeros_like(frame)
    launch_sparks(frame,glow,x,py,f)
    if 0<=age<.64:
        v=round(135*(1-age/.64))
        cv2.ellipse(glow,(x,py+7),(31+round(age*50),21+round(age*30)),0,0,360,(v,v//2,v//5),5,cv2.LINE_AA)
    if a<4 and age>-.2:
        side=-1 if a%2 else 1
        ix=x+side*167
        cy=py+66
        vis=ease((age+.2)/.62)
        overlay(frame,ICONS[a],ix-115,cy-83,vis*.92)
        if a:
            text(frame,cue.label,20,TEAL,ix,cy+99,vis,max_width=227)
            value=("","828 m","1.6 km","3.74 km")[a]
            text(frame,value,25,WHITE,ix,cy+131,vis)
    if a>=4:
        q=ease((f-CUES[4].frame)/23)
        sx=x-74
        cv2.line(frame,(sx,py+65),(W-sx,py+65),TEAL,2,cv2.LINE_AA)
        text(frame,"KOLA SUPERDEEP BOREHOLE",27,WHITE,360,py+102,q)
        text(frame,"DEEPEST VERTICAL BOREHOLE",18,TEAL,360,py+145,q)
    frame=cv2.add(frame,cv2.GaussianBlur(glow,(0,0),10))
    return frame,dp

@lru_cache(maxsize=1)
def planet_map():
    s=512
    g=np.linspace(-1.018,1.018,s,dtype=np.float32)
    x,y=np.meshgrid(g,g)
    r=np.hypot(x,y)
    z=np.sqrt(np.clip(1-r*r,0,1))
    rough=noise((s,s),[(6,7,.60),(18,19,.29),(53,56,.21),(119,115,.10)])
    outer=np.zeros((s,s,3),np.float32)+[17,65,123]
    outer+=rough[:,:,None]*[16,28,36]
    land=np.clip((rough-.16)*4,0,1)
    outer=outer*(1-land[:,:,None])+np.array([62,129,93])*land[:,:,None]
    clouds=(np.sin(y*23+rough*6)+.42*np.sin(19*x-21*y))*rough
    white=np.clip((clouds-.60)*.4,0,.50)
    outer=outer*(1-white[:,:,None])+np.array([201,230,222])*white[:,:,None]
    l=np.clip(-.5*x-.5*y+.79*z,0,1)
    outer*= (.31+.70*l**.6)[:,:,None]
    outer+=np.exp(-((z-.095)/.157)**2)[:,:,None]*np.array([25,78,91])
    mantle=(np.clip(r,.54,1)-.54)/.46
    core=np.clip((r-.191)/.355,0,1)
    hot=np.stack([254-84*mantle,181-100*mantle,84-32*mantle],axis=-1)
    liquid=np.stack([253-8*core,213-62*core,109-62*core],axis=-1)
    bands=np.where((r>.546)[:,:,None],hot,liquid)
    bands=np.where((r<.19)[:,:,None],np.array([255,241,166]),bands)
    contour=np.cos(r*139+rough*2.8)*.035+rough*.11
    bands*= (1+contour)[:,:,None]
    a=np.arctan2(y,x)
    wedge=((a>-.66)&(a<.65))
    out=np.where(wedge[:,:,None],bands,outer)
    out+=np.exp(-((r-.992)/.009)**2)[:,:,None]*np.array([23,50,54])
    alpha=np.clip((1-r)*s*.23,0,1)
    return np.dstack((np.clip(out,0,255),alpha*255)).astype(np.uint8)

def planetary(f):
    t=f/FPS
    u=ease((f-CUES[5].frame)/100)
    frame=NIGHT.copy()
    for gx,gy,z in GHOSTS:
        x=round((gx+t*z*2.8)%W)
        y=round((gy+u*z*24)%H)
        v=int(z*75)
        cv2.circle(frame,(x,y),1 if z<.9 else 2,(v,v+6,v+15),-1,cv2.LINE_AA)
    radius=round(196+214*(1-u))
    cx,cy=round(347-15*u),round(604+32*u)
    disc=cv2.resize(planet_map(),(2*radius,2*radius),interpolation=cv2.INTER_LINEAR)
    overlay(frame,disc,cx-radius,cy-radius)
    a=ease((f-CUES[6].frame)/17)
    tip=(cx+radius,cy)
    day=round(244*a)
    cv2.line(frame,(cx,cy),(tip[0],cy),(day,day,round(day*.62)),2,cv2.LINE_AA)
    cv2.circle(frame,tip,round(4+6*a),(int(255*a),int(195*a),int(95*a)),1,cv2.LINE_AA)
    if a>0:
        py=cy+radius+66
        text(frame,"12.26 km drilled",28,GOLD,360,py,a)
        text(frame,"6,371 km to Earth's center",26,BLUE,360,py+47,a)
    return frame

def paint(f):
    a=shot(f)
    if a<5:
        frame,d=underground(f)
    else:
        d=KOLA
        frame=planetary(f)
        transition=ease((f-CUES[5].frame)/30)
        if transition<1:
            old,_=underground(CUES[5].frame-1)
            frame=cv2.addWeighted(old,1-transition,frame,transition,0)
            life=(f-CUES[5].frame)/30
            brightness=round(84*(1-life)**2)
            radius=58+round(470*life)
            cv2.circle(frame,(343,703),radius,(brightness//2,brightness,brightness),2,cv2.LINE_AA)
    # Stable header remains readable across the changing strata.
    mask=(np.clip((Y-282)/160,0,1)*.92+.08).astype(np.float32)
    frame=(frame*mask[:,:,None]+NIGHT*(1-mask[:,:,None])).astype(np.uint8)
    text(frame,"HOW DEEP DID",51,WHITE,360,130)
    text(frame,"WE DRILL?",58,WHITE,360,199)
    if a<6:
        value=f"{d/1000:.2f} km" if d>=1000 else f"{round(d):,} m"
        text(frame,value,46,GOLD,360,272)
        lo,hi=113,607
        y=319
        cv2.line(frame,(lo,y),(hi,y),(79,85,98),2,cv2.LINE_AA)
        level=math.log1p(d/415)/math.log1p(KOLA/415)
        pointer=round(lo+(hi-lo)*level)
        cv2.line(frame,(lo,y),(pointer,y),TEAL,3,cv2.LINE_AA)
        for c in CUES[1:5]:
            x=round(lo+(hi-lo)*math.log1p(c.depth/415)/math.log1p(KOLA/415))
            cv2.line(frame,(x,y-6),(x,y+6),GOLD if d>=c.depth else BLUE,1,cv2.LINE_AA)
        cv2.circle(frame,(pointer,y),5,GOLD,-1,cv2.LINE_AA)
    else:
        v=.14+.86*ease((f-CUES[6].frame)/15)
        text(frame,f"{100*KOLA/RADIUS:.2f}% OF EARTH'S RADIUS",37,TEAL,360,273,v)
    return frame

def run(*args):
    subprocess.run([str(a) for a in args],check=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    if args.preview:
        for f in (5,48,146,250,388,593,701,866):
            Image.fromarray(paint(f)).save(OUT/f"preview-{f:04}.jpg",quality=93)
        return
    mix=OUT/"mix.wav"
    raw=OUT/"encoded.mp4"
    target=OUT/"how-deep-did-we-drill.mp4"
    compose(mix)
    cmd=["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
         "-r",str(FPS),"-i","pipe:0","-i",str(mix),"-map","0:v:0","-map","1:a:0",
         "-vf","scale=1080:1920:flags=lanczos:out_color_matrix=bt709",
         "-c:v","libx264","-pix_fmt","yuv420p","-preset","fast","-crf","18","-threads","4",
         "-maxrate","9M","-bufsize","14M","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
         "-af","loudnorm=I=-14.4:TP=-1.5:LRA=10","-c:a","aac","-b:a","224k","-ar","48000",str(raw)]
    writer=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for f in range(FRAME_COUNT):
            if f%150==0:
                print("Rendering",f/FPS,flush=True)
            writer.stdin.write(paint(f).tobytes())
    finally:
        writer.stdin.close()
        if writer.wait():
            raise RuntimeError("FFmpeg interrupted the portrait render")
    run("ffmpeg","-v","error","-y","-i",raw,"-map","0:v:0","-map","0:a:0","-c","copy",
        "-map_metadata","-1","-map_metadata:s","-1","-map_chapters","-1","-fflags","+bitexact",
        "-movflags","+faststart",target)
    raw.unlink()
    verify_sync(target,OUT/"audio-sync.json")

if __name__=="__main__":
    main()
