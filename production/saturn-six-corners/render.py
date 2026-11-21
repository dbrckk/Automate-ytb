"""Reproducible portrait short about the north polar jet of Saturn."""
import math
import os
import subprocess
import time
import urllib.request
import wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from kokoro_onnx import Kokoro

OUT = Path("build/saturn-corners")
OUT.mkdir(parents=True, exist_ok=True)
ROOT = "https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/"
VOICE_ROOT = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
EARTH = "https://eol.jsc.nasa.gov/DatabaseImages/ESC/large/AS17/AS17-148-22727.JPG"
W, H, FPS, SR = 900, 1600, 30, 24000
cv2.setNumThreads(2)
RNG = np.random.default_rng(112126)

STORY = [
    ("hook", ("A hurricane inside a hexagon.", "That's real weather on Saturn.")),
    ("orbit", ("Above its north pole,", "a jet stream bends into six sides.")),
    ("scale", ("Nearly thirty thousand kilometers wide.", "You could fit two Earths across.")),
    ("cassini", ("Watch these clouds.", "They race around the edges", "like cars on a track.")),
    ("eye", ("And dead center, a hurricane.", "Its eye is about fifty times wider", "than a typical hurricane eye on Earth.")),
    ("archive", ("Voyager saw the hexagon in the eighties.", "Decades later, Cassini found it still there.")),
    ("wave", ("One idea: a wave in the jet holds the shape.", "The clouds keep moving through it.")),
]
PALETTE = [(255,208,147),(168,219,255),(160,231,245),(236,179,250),
           (255,175,149),(243,210,167),(255,211,151)]
HEX = np.array([(0.119,.51),(.301,.194),(.653,.156),(.868,.447),
                (.719,.785),(.372,.851)],dtype=np.float32)

def download(url, name):
    path = OUT/name
    if path.is_file():
        return path
    for attempt in range(3):
        try:
            req = urllib.request.Request(url,headers={"User-Agent":"Automate-ytb/2.0 video source"})
            with urllib.request.urlopen(req,timeout=70) as response, path.with_suffix(".tmp").open("wb") as handle:
                while block := response.read(1 << 20):
                    handle.write(block)
            path.with_suffix(".tmp").replace(path)
            return path
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 + attempt)
    raise RuntimeError(url)

def nasa(number, ext="jpg"):
    return download(f"{ROOT}pia{number[:2]}/pia{number}/PIA{number}.{ext}",f"{number}.{ext}")

def image(path):
    return np.asarray(Image.open(path).convert("RGB"))

def ease(p):
    p=max(0.,min(p,1.))
    return p*p*(3-2*p)

def narrate():
    import onnxruntime as ort
    os.environ.setdefault("OMP_NUM_THREADS","2")
    opts=ort.SessionOptions()
    opts.intra_op_num_threads=2
    opts.inter_op_num_threads=1
    graph=download(VOICE_ROOT+"kokoro-v1.0.fp16.onnx","kokoro.onnx")
    voices=download(VOICE_ROOT+"voices-v1.0.bin","voices.bin")
    sess=ort.InferenceSession(str(graph),sess_options=opts,providers=["CPUExecutionProvider"])
    model=Kokoro.from_session(sess,str(voices))
    style=.61*model.voices["am_onyx"]+.27*model.voices["am_michael"]+.12*model.voices["am_adam"]
    chunks=[]
    clock=0
    for idx,(key,lines) in enumerate(STORY):
        spoken=" ".join(lines)
        y,rate=model.create(spoken,voice=style,lang="en-us",
            speed=(1.03,1.02,1.01,1.07,.98,1.05,1.02)[idx],sentence_pause=.16,clause_pause=.075)
        assert rate == SR and y.ndim == 1
        env=np.sqrt(np.convolve(y*y,np.full(360,1/360),mode="same"))
        active=np.flatnonzero(env>.003)
        if not active.size:
            raise RuntimeError(f"Missing recording for {key}")
        start=max(0,active[0]-440)
        y=y[start:active[-1]+630]
        y=.58*np.tanh(2.04*y)
        lead=.13 if idx==0 else .09
        endpad=.37 if idx==6 else .21
        frames=math.ceil((lead+len(y)/SR+endpad)*FPS)
        weights=[len(model.tokenizer.phonemize(line,lang="en-us",norm=True))+2 for line in lines]
        marks=[lead]
        for count in np.cumsum(weights)[:-1]:
            ideal=len(y)*count/sum(weights)
            grid=np.arange(max(int(ideal-.24*SR),int((marks[-1]-lead+.40)*SR)),min(int(ideal+.24*SR),len(y)-9000),100)
            if grid.size:
                score=np.minimum(.94,env[start+grid]/.065)+np.abs(grid-ideal)/(.24*SR)
                ideal=grid[np.argmin(score)]
            marks.append(lead+ideal/SR)
        marks.append(lead+len(y)/SR+.09)
        if sorted(marks)!=marks:
            raise RuntimeError(f"Nonmonotonic captions for {key}")
        chunks.append((key,lines,clock,frames,marks,y))
        clock+=frames
        print("Narration",key,frames/FPS,flush=True)
    t=np.arange(clock*(SR//FPS),dtype=np.float32)/SR
    voice=np.zeros(len(t),dtype=np.float32)
    bed=np.zeros((len(t),2),dtype=np.float32)
    for i,(key,lines,f0,n,marks,y) in enumerate(chunks):
        a=f0/FPS
        b=a+n/FPS
        voice[round((a+marks[0])*SR):round((a+marks[0])*SR)+len(y)]=y
        root=(38.89,46.25,43.65,51.91,38.89,46.25,38.89)[i]
        rel=t-a
        window=np.clip((rel+.56)/.8,0,1)*np.clip((b-t+.83)/1.02,0,1)
        for c in (0,1):
            for j,(h,level) in enumerate(((1,.024),(2,.017),(3.002,.009),(6.001,.007),(8.041,.002))):
                phase=2*np.pi*(h*root+.11*c)*t+j*.72+c*.27
                bed[:,c]+=level*window*(.79+.21*np.sin(t*(.79+j*.31)+j))*np.sin(phase+.31*np.sin(t*.91+j))
        for j,d in enumerate((0.,.52,1.07,2.14,2.7,3.21)):
            if a+d > b-.35:
                continue
            keep=(rel>=d)&(rel<d+1.3)
            z=rel[keep]-d
            f=root*(4,6,8,9,6,12)[(j+i)%6]
            hit=.021*np.minimum(160*z,1)*(np.sin(2*np.pi*f*z)+.19*np.sin(2*np.pi*f*2.01*z))*np.exp(-4.5*z)
            bed[keep,j%2]+=hit
            bed[keep,1-j%2]+=.65*hit
        s=np.clip(rel,0,None)
        impact=(rel>=0)*np.minimum(180*s,1)*np.exp(-5.8*s)
        bend=2*np.pi*(37*s+34*(1-np.exp(-7*s))/7)
        bed+=((.14 if i in (0,4) else .071)*impact*np.sin(bend))[:,None]
        if i in (2,3,4,5):
            gap=marks[1]-.12
            keep=(rel>=gap)&(rel<gap+.58)
            q=rel[keep]-gap
            bed[keep]+=((.042*np.sin(2*np.pi*(630*q-142*q*q)))*
                         np.minimum(q*128,1)*np.exp(-11*q))[:,None]
    level=np.sqrt(np.convolve(voice*voice,np.full(501,1/501),mode="same"))
    bed*=(1-np.clip(level*4.4,0,.62))[:,None]
    bed*=(np.clip(t/.02,0,1)*np.clip((t[-1]-t)/.15,0,1))[:,None]
    pcm=np.clip((bed+voice[:,None])*32767,-32768,32767).astype("<i2")
    with wave.open(str(OUT/"mix.wav"),"wb") as out:
        out.setparams((2,2,SR,len(pcm),"NONE","not compressed"))
        out.writeframes(pcm.tobytes())
    return chunks

def mask_body(img):
    weight=np.max(img,axis=2)
    points=cv2.findNonZero((weight>22).astype(np.uint8))
    x,y,w,h=cv2.boundingRect(points)
    return img[y:y+h,x:x+w]

def label(text, size, color=(255,249,235), weight="bold", max_width=765):
    paths={
        "bold":"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "normal":"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "mono":"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    }
    font=ImageFont.truetype(paths[weight],size)
    while font.getlength(text)>max_width:
        size-=1
        font=ImageFont.truetype(paths[weight],size)
    width=math.ceil(font.getlength(text))+24
    im=Image.new("RGBA",(width,size+24))
    draw=ImageDraw.Draw(im)
    draw.text((width/2,(size+24)/2),text,font=font,anchor="mm",fill=color+(255,),
              stroke_width=2 if size<37 else 3,stroke_fill=(10,10,20,240))
    return np.array(im)

def write_label(frame,tex,x,y,alpha=1.):
    th,tw=tex.shape[:2]
    x=round(x-tw/2)
    y=round(y-th/2)
    if alpha<=0 or x<0 or y<0 or x+tw>W or y+th>H:
        return
    crop=frame[y:y+th,x:x+tw]
    a=tex[:,:,3:4].astype(np.float32)*(alpha/255)
    crop[:]=tex[:,:,:3]*a+crop*(1-a)

def paste(frame, img, x, y, width, alpha=1.):
    h,w=img.shape[:2]
    height=max(2,round(h*width/w))
    scaled=cv2.resize(img,(width,height),interpolation=cv2.INTER_LINEAR)
    x=round(x-width/2)
    y=round(y-height/2)
    x0,y0=max(0,x),max(0,y)
    x1,y1=min(W,x+width),min(H,y+height)
    if x1<=x0 or y1<=y0:
        return
    crop=frame[y0:y1,x0:x1]
    patch=scaled[y0-y:y1-y,x0-x:x1-x]
    # Photo pixels in space are black. Screen blend keeps the background behind the subject.
    matte=np.minimum(np.max(patch,axis=2,keepdims=True).astype(np.float32)/20,1)*alpha
    crop[:]=crop*(1-matte)+patch*matte

def warp(img, x, y, width, angle=0.):
    h,w=img.shape[:2]
    m=cv2.getRotationMatrix2D((w/2,h/2),angle,width/w)
    m[:,2] += [x-w/2,y-h/2]
    return cv2.warpAffine(img,m,(W,H),flags=cv2.INTER_LINEAR),m

def trace(frame, points, accent, t, progress=1.):
    path=np.vstack([points,points[0]])
    visible=[]
    for j in range(len(points)):
        u=np.clip(progress*len(points)-j,0,1)
        if u>0:
            visible.append((path[j],path[j]*(1-u)+path[j+1]*u))
    fx=np.zeros_like(frame)
    for a,b in visible:
        cv2.line(fx,tuple(np.int32(a)),tuple(np.int32(b)),accent,2,cv2.LINE_AA)
    glow=cv2.GaussianBlur(fx,(0,0),5)
    frame[:]=cv2.addWeighted(frame,1,glow,1.05,0)
    frame[:]=cv2.addWeighted(frame,1,fx,.64,0)
    if progress<.92:
        return
    for k in range(11):
        s=(k/11-t*.19)%1*len(points)
        j=int(s)
        u=s-j
        a,b=path[j],path[j+1]
        now=a+(b-a)*u
        prev=now+(b-a)*.10
        cv2.line(frame,tuple(np.int32(now)),tuple(np.int32(prev)),(250,234,214),1,cv2.LINE_AA)
        cv2.circle(frame,tuple(np.int32(now)),3,accent,-1,cv2.LINE_AA)

def optical(frames):
    gray=[cv2.cvtColor(a,cv2.COLOR_RGB2GRAY) for a in frames]
    return [cv2.calcOpticalFlowFarneback(a,b,None,.5,3,11,3,5,1.2,0)
            for a,b in zip(gray,gray[1:]+gray[:1])]

def interp(frames, flows, position):
    index=int(position)%len(frames)
    f=position%1
    flow=flows[index]
    h,w=flow.shape[:2]
    x,y=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    a=cv2.remap(frames[index],x-flow[:,:,0]*f,y-flow[:,:,1]*f,cv2.INTER_LINEAR)
    b=cv2.remap(frames[(index+1)%len(frames)],x+flow[:,:,0]*(1-f),y+flow[:,:,1]*(1-f),cv2.INTER_LINEAR)
    return cv2.addWeighted(a,1-f,b,f,0)

def main():
    base=image(nasa("17652"))
    color=image(nasa("14945"))
    rose=image(nasa("14944"))
    planet=mask_body(image(nasa("11141")))
    blue=mask_body(image(download(EARTH,"earth.jpg")))
    with Image.open(nasa("17652","gif")) as movie:
        observed=[np.asarray(im.convert("RGB")) for im in ImageSequence.Iterator(movie)]
    if len(observed)<5:
        raise RuntimeError("Cassini time series is missing frames")
    flows=optical(observed)
    voice=narrate()
    stars=RNG.uniform((0,0,.2),(W,H,1.),size=(172,3))
    gx,gy=np.meshgrid(np.linspace(-1,1,W,dtype=np.float32),np.linspace(-1,1,H,dtype=np.float32))
    q=np.exp(-((gx+.32)/1.45)**2-((gy+.13)/.9)**2)
    ambient=np.stack([4+q*14,5+q*10,12+q*25],axis=-1).astype(np.uint8)
    cap_shadow=np.exp(-((gy-.545)/.118)**2)*.54
    cap_shade=np.repeat((255*(1-cap_shadow)).astype(np.uint8)[:,:,None],3,axis=2)
    overlay={}
    for i,(key,lines) in enumerate(STORY):
        accent=PALETTE[i]
        overlay[key]={"captions":[label(line,46) for line in lines]}
        if key=="hook":
            overlay[key]["main"]=[label("SIX CORNERS.",88,accent),label("ONE HURRICANE.",59)]
        elif key=="orbit":
            overlay[key]["main"]=[label("SATURN'S NORTH POLE",37,accent,"mono")]
        elif key=="scale":
            overlay[key]["main"]=[label("30,000 km",96,accent),label("TWO EARTHS, TO SCALE",34,accent,"mono")]
        elif key=="cassini":
            overlay[key]["main"]=[label("CASSINI TIME-LAPSE",42,accent,"mono"),
                label("False color · NASA/JPL-Caltech/SSI/Hampton University",21,weight="normal")]
        elif key=="eye":
            overlay[key]["main"]=[label("50×",145,accent),label("THE DIAMETER OF A TYPICAL",32),
                                   label("EARTH HURRICANE EYE",35)]
        elif key=="archive":
            overlay[key]["main"]=[label("1980–81",108,accent),label("VOYAGER FLYBYS",38,accent,"mono"),
                                   label("2013",108,accent),label("CASSINI",38,accent,"mono")]
        else:
            overlay[key]["main"]=[label("ONE EXPLANATION",33,accent,"mono"),
                                   label("A WAVE IN THE JET",59,accent)]
    ffmpeg=["ffmpeg","-v","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate","30",
            "-i","pipe:0","-i",str(OUT/"mix.wav"),"-map","0:v:0","-map","1:a:0",
            "-map_metadata","-1","-map_metadata:s","-1","-map_chapters","-1",
            "-metadata:s:v:0","handler_name=","-metadata:s:a:0","handler_name=",
            "-metadata:s:v:0","encoder=","-metadata:s:a:0","encoder=","-fflags","+bitexact",
            "-flags:v","+bitexact","-flags:a","+bitexact","-write_tmcd","0",
            "-vf","scale=1080:1920:flags=lanczos:out_color_matrix=bt709",
            "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
            "-af","loudnorm=I=-14.5:TP=-1.5:LRA=8","-c:v","libx264","-preset","fast","-crf","18",
            "-threads","3","-maxrate","9M","-bufsize","15M","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
            "-ar","48000","-movflags","+faststart",str(OUT/"saturn-six-corners.mp4")]
    enc=subprocess.Popen(ffmpeg,stdin=subprocess.PIPE)
    try:
        for i,(key,lines,f0,n,marks,_) in enumerate(voice):
            accent=PALETTE[i]
            assets=overlay[key]
            main_label=assets["main"]
            print("Picture",key,n,flush=True)
            for j in range(n):
                t=j/FPS
                p=j/max(1,n-1)
                run_time=(f0+j)/FPS
                frame=ambient.copy()
                for st,(sx,sy,d) in enumerate(stars):
                    shift=(run_time*3.8+5*math.sin(run_time*.45))*(.5+d)
                    x=round((sx-shift)%W)
                    y=round((sy+shift*.21)%H)
                    v=round(23+d*105)
                    cv2.circle(frame,(x,y),1 if d<.83 else 2,(v,v,min(255,v+18)),-1,cv2.LINE_AA)
                if key in ("hook","scale","wave","cassini"):
                    src=base
                    angle=3*math.sin(t*.35)
                    width=970
                    cy=770
                    if key=="hook":
                        width=1088-126*ease(t/.67)+28*p
                        angle=-4+6*ease(t/.85)
                    elif key=="scale":
                        width=875
                        angle=-1.5
                    elif key=="cassini":
                        src=interp(observed,flows,p*(len(observed)-1))
                        width=1030+82*p
                        angle=0.
                    else:
                        src=interp(observed,flows,p*(len(observed)-1))
                        width=930+158*ease(p)
                        angle=1.8-5.8*ease(p)
                    pic,m=warp(src,435,cy,width,angle)
                    if key=="scale":
                        pic=cv2.convertScaleAbs(pic,alpha=.56)
                    frame=cv2.max(frame,pic)
                    points=cv2.transform((HEX*[src.shape[1],src.shape[0]]).astype(np.float32)[None,:,:],m)[0]
                    if key=="hook":
                        trace(frame,points,accent,t,ease((t-.045)/1.18))
                        popup=ease(t/.23)*(1-.52*ease((t-2.6)/1.2))
                        write_label(frame,main_label[0],435,217+17*(1-popup),popup)
                        write_label(frame,main_label[1],435,302+16*(1-popup),popup)
                    elif key=="scale":
                        trace(frame,points,accent,t,1.)
                        xlo,xhi=np.min(points[:,0]),np.max(points[:,0])
                        earth_w=round((xhi-xlo)*12742/30000)
                        y=790
                        a=ease((t-marks[1]+.17)/.34)
                        b=ease((t-marks[1]-.04)/.44)
                        paste(frame,blue,xlo+earth_w*.55-98*(1-a),y,earth_w,a)
                        paste(frame,blue,xhi-earth_w*.55+98*(1-b),y,earth_w,b)
                        yi=454
                        line=ease(t/.46)
                        center=(xlo+xhi)/2
                        left=round(center+(xlo-center)*line)
                        right=round(center+(xhi-center)*line)
                        cv2.line(frame,(left,yi),(right,yi),accent,2,cv2.LINE_AA)
                        for x in (left,right):
                            cv2.line(frame,(x,yi-12),(x,yi+12),accent,2,cv2.LINE_AA)
                        write_label(frame,main_label[0],435,342,line)
                        write_label(frame,main_label[1],435,1078,b)
                    elif key=="cassini":
                        trace(frame,points,accent,t,ease((t-.44)/.74))
                        write_label(frame,main_label[0],435,275,ease(t/.28))
                        write_label(frame,main_label[1],435,1145)
                    else:
                        trace(frame,points,accent,t,1.)
                        a=ease(t/.34)*(1-ease((p-.84)/.15))
                        write_label(frame,main_label[0],435,253,a)
                        write_label(frame,main_label[1],435,325,a)
                        if p>.86:
                            end,_=warp(base,435,770,1088,-4)
                            frame=cv2.addWeighted(frame,1-ease((p-.86)/.14),cv2.max(ambient,end),ease((p-.86)/.14),0)
                elif key=="orbit":
                    w=1010+127*ease(p)
                    planet_frame,_=warp(planet,460,790,w,-10+9*ease(p))
                    frame=cv2.max(frame,planet_frame)
                    d=ease((p-.53)/.28)
                    if d>0:
                        polar,_=warp(color,437,738,1000+130*p,1.5)
                        frame=cv2.addWeighted(frame,1-d,cv2.max(ambient,polar),d,0)
                    write_label(frame,main_label[0],435,240,ease(t/.3))
                elif key=="eye":
                    v=ease(t/.68)
                    eye,_=warp(rose,445,790,865+520*v+75*p,-5+7*p)
                    frame=cv2.max(frame,eye)
                    a=ease((t-marks[1]+.15)/.44)
                    write_label(frame,main_label[0],435,295+23*(1-a),a)
                    write_label(frame,main_label[1],435,411,a)
                    write_label(frame,main_label[2],435,457,a)
                elif key=="archive":
                    b=ease((t-marks[1]+.13)/.3)
                    old,_=warp(planet,455,783,1010+79*p,-12)
                    new,_=warp(color,442,755,1080,-1)
                    frame=cv2.max(frame,cv2.addWeighted(old,1-b,new,b,0))
                    write_label(frame,main_label[0],435,285,1-b)
                    write_label(frame,main_label[1],435,386,1-b)
                    write_label(frame,main_label[2],435,285,b)
                    write_label(frame,main_label[3],435,386,b)
                frame=cv2.multiply(frame,cap_shade,scale=1/255)
                for number,cap in enumerate(assets["captions"]):
                    cue=marks[number]-.033
                    if cue<=t<marks[number+1]-.033:
                        a=ease((t-cue+.02)/.067)
                        write_label(frame,cap,435,1241+7*(1-a),a)
                        break
                enc.stdin.write(frame.tobytes())
    finally:
        enc.stdin.close()
        code=enc.wait()
        if code:
            raise RuntimeError(f"FFmpeg exited with {code}")

if __name__=="__main__":
    main()
