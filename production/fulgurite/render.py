#!/usr/bin/env python3
"""Fulgurite: Lightning made glass. Reproducible vertical original 2.5D film + locked soundtrack.

All visual layers, surface textures, stereo score and Foley are procedurally generated.
Science: https://home.nps.gov/articles/grsa-fulgurites.htm and https://www.canada.ca/en/environment-climate-change/services/lightning/learn-more/fulgurites.html
The geometry and timing are an artistic visualization, not a simulation.
"""
from __future__ import annotations
import os, math, json, hashlib, subprocess, wave, pathlib, argparse
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Video and audio clocks: every rendered frame contains exactly 1,600 audio samples.
FPS=30; SR=48000; SP=SR//FPS; DUR=33; FRAMES=DUR*FPS
W=720; H=1280; TAU=math.tau
ROOT=pathlib.Path(os.environ.get('FULGURITE_OUTPUT','build/fulgurite'))
ROOT.mkdir(parents=True, exist_ok=True)
FILE=ROOT/'lightning-made-glass.mp4'; SND=ROOT/'original-score.wav'
cv2.setNumThreads(2)
SEED=20261125
rng=np.random.default_rng(SEED)
X,Y=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
BLACK=(12,14,28); OFFWHITE=(250,248,242); BLUE=(119,222,252); AMBER=(252,185,98); WARM=(245,228,196)
CUES=[(0,'opening'),(60,'storm_bass'),(141,'charge'),(156,'lightning_hit'),(175,'thunder'),(211,'subsurface_dive'),(300,'molten_front'),(416,'enter_glass'),(550,'cooling'),(665,'specimen_reveal'),(820,'hero_title'),(938,'outro')]

# -- Deterministic noise materials ------------------------------------------------
def fractal(h,w,layers,seed):
    gen=np.random.default_rng(seed)
    out=np.zeros((h,w),np.float32)
    for hh,ww,amp in layers:
        a=gen.standard_normal((hh,ww)).astype(np.float32)
        out+=cv2.resize(a,(w,h),interpolation=cv2.INTER_CUBIC)*amp
    out-=np.mean(out); out/=max(1e-6,np.std(out))
    return out

cloud_n=fractal(1480,1024,[(6,7,.55),(18,17,.28),(43,32,.16),(120,96,.07)],20)
cloud_detail=fractal(1480,1024,[(18,31,.45),(65,73,.31),(180,200,.14)],21)
cy=np.linspace(0,1,1480,dtype=np.float32)[:,None]
light_break=np.clip((cloud_n*.36 + cloud_detail*.18+.60-cy*.70),-.7,1.0)
SKY=np.empty((1480,1024,3),np.uint8)
for k,(base,twilight,cloudweight) in enumerate([(16,56,25),(19,63,30),(40,88,52)]):
    o=base+twilight*np.clip((cy-.44),0,1)**2+cloudweight*np.clip(light_break,0,1)
    o+=9*np.sin(cy*10+2+k)*np.exp(-((cy-.55)/.28)**2)
    SKY[:,:,k]=np.clip(o,0,255).astype(np.uint8)

# Dense dune relief with grains and optical depth.
sand_n=fractal(1600,1030,[(9,9,.43),(35,37,.29),(150,155,.17),(380,440,.10)],88)
sand_grain=fractal(1600,1030,[(320,340,.56),(650,680,.38)],89)
ssy=np.linspace(0,1,1600,dtype=np.float32)[:,None]
SAND=np.zeros((1600,1030,3),np.uint8)
rough=.8 + .23*np.clip(sand_n,-2,2) + .08*sand_grain
for k,(p,q) in enumerate([(52,73),(44,66),(41,61)]):
    SAND[:,:,k]=np.clip((p+q*ssy**.54)*rough,0,255).astype(np.uint8)

# Cross-section: veins and laminae respond to depth, parallax and strike heat.
under_n=fractal(2400,1000,[(14,12,.45),(42,36,.33),(100,96,.16),(400,500,.06)],109)
under_crys=fractal(2400,1000,[(33,55,.45),(180,230,.29),(480,800,.13)],113)
uy=np.linspace(0,1,2400,dtype=np.float32)[:,None]
ux=np.linspace(0,1,1000,dtype=np.float32)[None,:]
lamina=np.sin(uy*111+np.sin(ux*23)*1.8+under_n*2.5)
clay=np.sin(uy*28+under_n*1.0+np.sin(ux*13)*2.4)
UNDER=np.zeros((2400,1000,3),np.uint8)
for k,(base,w1,w2,ns) in enumerate([(64,35,16,24),(53,26,23,18),(56,19,40,23)]):
    UNDER[:,:,k]=np.clip(base+w1*lamina+w2*clay+ns*under_n+under_crys*7,0,255).astype(np.uint8)

# Small collection of cinematic depth-oriented motes, repeated only through geometry.
MOTES=np.random.default_rng(430).uniform(size=(255,5)).astype(np.float32)
MOTES[:,0]*=W; MOTES[:,1]*=H
MOTES[:,2]=MOTES[:,2]**.7
MOTES[:,3]*=TAU
MOTES[:,4]=MOTES[:,4]**2

# -- Typography -----------------------------------------------------------------
BOLD='/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
MED='/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf'
if not os.path.exists(BOLD):
    BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    MED=BOLD

@lru_cache(240)
def label_rgba(s,pts=58,fill=OFFWHITE,bold=True,width=655):
    fontpath=BOLD if bold else MED
    while pts>13:
        font=ImageFont.truetype(fontpath,pts)
        if font.getlength(s)<width:break
        pts-=1
    im=Image.new('RGBA',(int(font.getlength(s))+20,pts+23),(0,0,0,0))
    d=ImageDraw.Draw(im)
    d.text((im.width/2,im.height/2-2),s,anchor='mm',font=font,fill=(*fill,255),stroke_width=0)
    return np.asarray(im)

def blend_rgba(bg,layer,x,y,opacity=1.):
    if opacity<=0:return
    x,y=round(x),round(y)
    hh,ww=layer.shape[:2]
    a,b=max(0,x),max(0,y); c,d=min(W,x+ww),min(H,y+hh)
    if c<=a or d<=b:return
    s=layer[b-y:d-y,a-x:c-x]
    alpha=s[:,:,3:4].astype(np.float32)*(opacity/255.)
    z=bg[b:d,a:c]
    z[:]=np.clip(z*(1-alpha)+s[:,:,:3]*alpha,0,255).astype(np.uint8)

def caption(bg,s,y,pts=60,fill=OFFWHITE,alpha=1.,offset=0,bold=True):
    im=label_rgba(s,pts,fill,bold)
    blend_rgba(bg,im,(W-im.shape[1])/2+offset,y-im.shape[0]/2,alpha)

def smooth(x):
    x=float(np.clip(x,0,1)); return x*x*(3-2*x)

def easeout(x):
    x=float(np.clip(x,0,1)); return 1-(1-x)**3

def screen_text(frame,t):
    # Cinematic text is intentionally sparse; the moving subject is the storyteller.
    # alpha and vertical parallax are tied to the same timeline as the sound cues.
    segments=[
        (0.0,4.55,('THE SKY CAN MAKE','GLASS.'),BLUE),
        (5.55,9.5,('ONE STRIKE.','MOLTEN SAND.'),AMBER),
        (9.5,14.4,('A FLASH OF HEAT','FUSES THE GRAINS'),AMBER),
        (14.45,19.5,('GLASS GROWS','UNDERGROUND.'),BLUE),
        (19.6,24.25,('THEN IT COOLS','INTO A HOLLOW TUBE.'),BLUE),
        (24.4,28.05,('A SCULPTURE','BURIED IN SAND.'),WARM),
        (28.1,33.1,('FULGURITE','PETRIFIED LIGHTNING'),AMBER),
    ]
    for i,(a,b,lines,color) in enumerate(segments):
        if not a-.25<=t<b+.15:continue
        fadein=smooth((t-a+.12)/.48)
        fadeout=smooth((b+.07-t)/.44)
        op=fadein*fadeout
        dy=round((1-fadein)*18)
        headline=lines[0]
        second=lines[1]
        if i<6:
            caption(frame,headline,119+dy,49,OFFWHITE,op)
            caption(frame,second,188+dy,65,color,op)
        else:
            caption(frame,headline,144+dy,94,OFFWHITE,op)
            caption(frame,second,224+dy,35,color,op,bold=False)
    # fine kinetic timeline progress bar with periodic event markers
    yt=300
    cv2.line(frame,(49,yt),(671,yt),(78,88,108),2,cv2.LINE_AA)
    for fr,label in CUES[1:-1]:
        pos=49+int(622*fr/FRAMES)
        cv2.line(frame,(pos,yt-4),(pos,yt+4),(125,143,147),1,cv2.LINE_AA)
    end=49+round(622*t/DUR)
    cv2.line(frame,(49,yt),(end,yt),BLUE if t<15 else AMBER,3,cv2.LINE_AA)
    cv2.circle(frame,(end,yt),4,OFFWHITE,-1,cv2.LINE_AA)
    caption(frame,'SCIENCE  /  CINEMATIC EXPLAINER',331,17,(145,159,173),.9,bold=False)
    # Safe area below subject.
    caption(frame,'LIGHTNING  +  SILICA  =  NATURAL GLASS',1169,22,(196,204,210),.80,bold=False)

# -- Visual primitives ----------------------------------------------------------
def vignette(frame,amount=.30):
    if not hasattr(vignette,'mask'):
        xx=(X/W-.5)*1.5; yy=(Y/H-.47)*1.1
        vignette.mask=np.clip((xx*xx+yy*yy)*.72,0,.84).astype(np.float32)
    m=1-amount*vignette.mask
    frame[:]=np.clip(frame.astype(np.float32)*m[:,:,None],0,255).astype(np.uint8)

def glows(img,layer,sigma=11,opacity=.85):
    g=cv2.GaussianBlur(layer,(0,0),sigma)
    cv2.addWeighted(img,1,g,opacity,0,dst=img)

def scatter(frame,t,strength=1,bright=True):
    for i, (px,py,z,p,tw) in enumerate(MOTES):
        x=int((px+(t*18*(.4+z)+23*math.sin(p+t*.43))*strength)%W)
        y=int((py-(t*24*(.5+z)) +10*math.cos(p+t*.67))%H)
        lum=30+min(170,int(z*190))
        color=(lum,round(lum*.75),round(lum*.48)) if bright else (lum//2,round(lum*.73),lum)
        cv2.circle(frame,(x,y),1 if z<.84 else 2,color,-1,cv2.LINE_AA)

def camera_texture(texture,t,dx,dy):
    a=int((110+dx+12*math.sin(t*.13)))
    b=int((0+dy))
    h,w=texture.shape[:2]
    # Reflect wrapping never introduces black seam.
    return cv2.remap(texture,X+a,Y+b,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)

def dunes(frame,t,foreground=True):
    """Moving volumetric sand layers with surface grain from the 2D material map."""
    shift=23*math.sin(t*.13)
    if foreground:
        pts=np.array([(x,int(904+50*math.sin((x+shift)/117)+24*math.sin((x+shift*1.8)/69))) for x in range(-5,W+12,9)],np.int32)
        pts2=np.array([(x,int(1055+34*math.sin((x+shift*.6)/93)+20*math.cos((x+shift)/43))) for x in range(-5,W+12,9)],np.int32)
        tex=camera_texture(SAND,t,3,int(t*9))
        shade=np.zeros_like(tex)
        for k,off in enumerate((21,18,16)):
            shade[:,:,k]=np.clip(tex[:,:,k].astype(np.float32)*.75+off,0,255)
        mask=np.zeros((H,W),np.uint8)
        cv2.fillPoly(mask,[np.vstack((pts,[[W,H],[0,H]]))],255)
        cv2.copyTo(shade,mask,frame)
        cv2.polylines(frame,[pts],False,(194,152,125),2,cv2.LINE_AA)
        # slightly nearer dune has lower light and more grain
        cv2.fillPoly(mask,[np.vstack((pts2,[[W,H],[0,H]]))],255)
        cv2.copyTo(cv2.addWeighted(shade,.62,np.full_like(shade,(36,31,43)),.38,0),mask,frame)
        cv2.polylines(frame,[pts2],False,(157,119,101),2,cv2.LINE_AA)
    else:
        pts=np.array([(x,int(758+30*math.sin((x+t*10)/77)+20*math.sin((x+t*6)/147))) for x in range(-5,W+12,9)],np.int32)
        mask=np.zeros((H,W),np.uint8)
        cv2.fillPoly(mask,[np.vstack((pts,[[W,900],[0,900]]))],255)
        tex=camera_texture(SAND,t,int(t*2),45)
        cv2.copyTo(cv2.addWeighted(tex,.68,np.full_like(tex,(51,43,62)),.32,0),mask,frame)
        cv2.polylines(frame,[pts],False,(151,120,116),2,cv2.LINE_AA)

# Precompute lightning main path, branches for all keyframes.
def generate_bolt(x0,y0,x1,y1,gen,segments=44,jitter=44):
    ans=[]
    for i in range(segments+1):
        s=i/segments
        bend=gen.standard_normal()*jitter*(.36+.44*math.sin(math.pi*s))
        xx=x0+(x1-x0)*s+bend
        yy=y0+(y1-y0)*s
        ans.append([int(xx),int(yy)])
    ans[0]=[int(x0),int(y0)];ans[-1]=[int(x1),int(y1)]
    return np.array(ans,np.int32)
BOLT=generate_bolt(397,-40,399,773,np.random.default_rng(30),47,25)
B_BRANCH=[]
for i in (7,15,21,29,35,40):
    pt=BOLT[i]
    shift=(-1)**i*(95+(i%3)*26)
    B_BRANCH.append(generate_bolt(pt[0],pt[1],pt[0]+shift,pt[1]+(95+i%3*31),np.random.default_rng(i),14,17))

def lightning_flash(f):
    p=f-156
    if p<0:return 0
    if p<=3:return (1.0,.47,.75,.23)[p]
    if p<13:return .22*math.exp(-(p-4)/2.8)
    if 16<p<20:return .24*math.exp(-(p-16)/2)
    return 0

def storm(f,t):
    strength=lightning_flash(f)
    frame=camera_texture(SKY,t,int(t*2),0)
    # Storm cloud depth: soft horizontal volumetric bands drift independently.
    cover=np.zeros((H,W,3),np.uint8)
    for i in range(8):
        xa=int(230+78*math.sin(i*1.22+t*.19)); ya=int(430+i*38+14*math.sin(t*.18+i))
        cv2.ellipse(cover,(xa,ya),(350-i*16,45+i*4),-8,0,360,(14+i*2,17+i*3,31+i*3),-1,cv2.LINE_AA)
    cover=cv2.GaussianBlur(cover,(0,0),25)
    cv2.addWeighted(frame,.80,cover,.38,0,dst=frame)
    # Sand is real multi-octave relief, not a flat filled polygon.
    ground=camera_texture(SAND,t,-9,int(t*3))
    edge=np.array([(x,int(793+19*math.sin((x+t*4)/64)+21*math.sin((x+t*5)/161))) for x in range(0,W+8,8)],np.int32)
    mask=np.zeros((H,W),np.uint8)
    cv2.fillPoly(mask,[np.vstack((edge,[[W,H],[0,H]]))],255)
    cv2.copyTo(ground,mask,frame)
    dunes(frame,t,False)
    dunes(frame,t,True)
    scatter(frame,t,.8,False)
    if strength>0:
        p=round(7*math.sin((f-156)*2.7)*strength)
        flash=np.full_like(frame,(235,223,225),dtype=np.uint8)
        cv2.addWeighted(frame,1-strength*.56,flash,strength*.56,0,dst=frame)
        glow=np.zeros_like(frame)
        cv2.polylines(glow,[BOLT+np.array([p,0])],False,(172,204,255),20,cv2.LINE_AA)
        for br in B_BRANCH:
            cv2.polylines(glow,[br+np.array([p,0])],False,(99,172,241),8,cv2.LINE_AA)
        cv2.polylines(frame,[BOLT+np.array([p,0])],False,(160,234,255),7,cv2.LINE_AA)
        cv2.polylines(frame,[BOLT+np.array([p,0])],False,(249,251,255),3,cv2.LINE_AA)
        for br in B_BRANCH:
            cv2.polylines(frame,[br+np.array([p,0])],False,(151,212,255),2,cv2.LINE_AA)
        glows(frame,glow,18,strength*.85)
    if f>=156:
        dt=(f-156)/FPS
        for i in range(140):
            a=i*2.39996; rr=(18+210*min(dt,1))*math.sqrt((i+.1)/140)
            px=int(402+rr*math.cos(a)+24*math.sin(t*.31+i))
            py=int(774+rr*.30*math.sin(a)-dt*dt*42+3*i%8)
            if 0<=px<W and 0<=py<H:
                q=max(0.,1-dt/3.9)*(0.37+.63*(i%9)/9)
                color=(round(254*q),round(180*q),round(102*q))
                cv2.circle(frame,(px,py),1+int(i%7==0),color,-1,cv2.LINE_AA)
        if dt<2.2:
            rr=int(15+260*easeout(dt/2.2))
            cv2.ellipse(frame,(401,785),(rr,max(4,rr//4)),0,0,360,(178,223,240),2,cv2.LINE_AA)
    if f>180:
        # Camera pushes beneath the sand before transitioning to a section.
        push=smooth((f-180)/40)
        overlay=np.zeros_like(frame)
        overlay[:]=(20,17,30)
        cv2.addWeighted(frame,1-push*.38,overlay,push*.38,0,dst=frame)
    return frame

# -- Underground tube network ---------------------------------------------------
MAIN_WORLD=np.linspace(0,2000,180)
def xmain(y):
    return 380+64*np.sin(y/241)+20*np.sin(y/57)
PATHS=[]
PATHS.append(np.column_stack((xmain(MAIN_WORLD),MAIN_WORLD)).astype(np.float32))
for y0,sgn,endlen in ((185,-1,460),(360,+1,600),(650,-1,430),(900,+1,510),(1210,-1,360),(1450,+1,470)):
    vv=np.linspace(0,1,58)
    yy=y0+endlen*vv
    xx=xmain(y0)+sgn*(275*vv**1.13)+15*np.sin(vv*11+sgn*2)*np.sin(vv*math.pi)
    PATHS.append(np.column_stack((xx,yy)).astype(np.float32))

def draw_tubes(frame,cam_y,t):
    # Render a branch structure with crust, fused glass, hollow channels and specular ridges.
    thermalfront=max(-200.,(t-7.3)*315)
    glow=np.zeros_like(frame)
    for k,path in enumerate(PATHS):
        pts=path.copy()
        pts[:,0]+=6*math.sin(t*.62+k)+5*(k%3-1)
        pts[:,1]=pts[:,1]-cam_y+455
        visible=(pts[:,1]>180)&(pts[:,1]<H+40)
        ptsi=pts.astype(np.int32)
        if not np.any(visible):continue
        # Jagged dark insulating charred sand around the exterior.
        cv2.polylines(frame,[ptsi],False,(26,29,38),39 if k==0 else 27,cv2.LINE_AA)
        cv2.polylines(frame,[ptsi],False,(85,75,82),33 if k==0 else 21,cv2.LINE_AA)
        cv2.polylines(frame,[ptsi],False,(154,102,85),25 if k==0 else 15,cv2.LINE_AA)
        # Hollow center, edged by translucent, irregular quartz glass.
        cv2.polylines(frame,[ptsi],False,(40,27,33),15 if k==0 else 8,cv2.LINE_AA)
        for j in range(1,len(pts)):
            w_y=(path[j,1]+path[j-1,1])*.5
            if pts[j,1]<165 and pts[j-1,1]<165: continue
            if pts[j,1]>H+30 and pts[j-1,1]>H+30:continue
            diff=t-(7.3+w_y/315)
            h=smooth((diff+.4)/.29)*(1-smooth((diff-1.25)/1.85))
            if h>0:
                pa=tuple(int(v) for v in pts[j-1]); pb=tuple(int(v) for v in pts[j])
                col=(int(85+152*h),int(70+165*h),int(65+175*h))
                cv2.line(glow,pa,pb,col,17 if k==0 else 10,cv2.LINE_AA)
                cv2.line(frame,pa,pb,(round(110+110*h),round(120+90*h),round(160+92*h)),7 if k==0 else 4,cv2.LINE_AA)
        # A brighter, offset glancing reflection gives tubular shape.
        p2=ptsi+np.array([7 if k==0 else 3,-2],dtype=np.int32)
        cv2.polylines(frame,[p2],False,(177,147,130),2,cv2.LINE_AA)
    glows(frame,glow,12,.48)

def underground(f,t):
    u=smooth((t-6.8)/7.1)
    cam_y=1600*u
    # Asymmetrical strata move at a different speed from the glowing glass channels.
    frame=camera_texture(UNDER,t,170,int(cam_y*.70))
    fog=np.zeros_like(frame)
    cv2.rectangle(fog,(0,0),(W,H),(33,20,41),-1)
    cv2.addWeighted(frame,.84,fog,.16,0,dst=frame)
    # foreground deep-sand flakes and crystals
    for i,(mx,my,z,p,tw) in enumerate(MOTES):
        ax=int((mx+math.sin(p+t*.2)*21*z)%W)
        ay=int((my-cam_y*z*.32)%H)
        cv2.line(frame,(ax,ay),(ax+3,ay+1),(77+int(z*69),72+int(z*42),66+int(z*20)),1,cv2.LINE_AA)
    draw_tubes(frame,cam_y,t)
    if f>=416:
        w=smooth((f-416)/36)
        frame=cv2.addWeighted(frame,1-w, np.full_like(frame,(15,19,32)),w,0)
    return frame

# -- Inside a glass tube: moving perspective geometry --------------------------
# Polyhedral crystal rings create 2.5D parallax while camera traverses the bore.
def tunnel(f,t):
    """Ray-marched-looking 2.5D glass-tube interior with animated refraction.

    Wall material is a continuous procedural surface in elliptical cylindrical
    coordinates, not a sequence of wireframe rings.
    """
    cam=t-14.0
    cx=360+47*math.sin(t*.24)
    cy=683+33*math.cos(t*.21)
    xx=(X-cx)/370
    yy=(Y-cy)/530
    rr=np.sqrt(xx*xx+yy*yy)+1e-3
    angle=np.arctan2(yy,xx)
    d=1.0/(rr+.16)
    axial=(cam*.69+d*1.47)
    facets=np.sin(angle*10.0 + 1.1*np.sin(axial*1.4))
    refraction=.5+.5*np.sin(angle*13.0-axial*5.7+np.sin(axial*3.2))
    fine=.5+.5*np.sin(angle*44+axial*16+np.sin(angle*17)*2)
    bands=np.exp(-(np.sin(axial*2.9+angle*.31)/.24)**2)
    bright=np.clip(.16+.25*refraction+.15*fine+.13*facets+.23*bands,0,1)
    wave=np.exp(-(np.sin(angle*7+axial*8.0)/.22)**2)
    # Metallic glass: deep purple shadows, warm amber interior and cold specular streaks.
    gloss=.52+.48*(np.sin(angle*3-axial*2.9)**2)
    r=(37+154*bright +66*bands +19*wave)*gloss
    g=(31+107*bright +31*bands +51*wave)*gloss
    b=(55+95*bright +93*wave +27*bands)*gloss
    tunnelmask=np.clip((rr-.105)/.20,0,1)
    tunnelmask=tunnelmask*tunnelmask*(3-2*tunnelmask)
    frame=np.stack((r,g,b),axis=-1).astype(np.float32)
    frame*=tunnelmask[:,:,None]
    # A framed exit hole with physically meaningful depth cues.
    centerR=np.sqrt((X-cx)**2+(Y-cy)**2)
    ring=np.exp(-((centerR-72)/11)**2)
    frame+=ring[:,:,None]*np.array([74.,117.,156.],np.float32)[None,None,:]
    # Broad specular rim aimed toward rotating studio lights.
    spec=np.exp(-(np.sin(angle*2.5 + axial*1.7)/.093)**2)*np.clip(rr-.2,0,1)
    frame+=spec[:,:,None]*np.array([40.,74.,105.],np.float32)
    frame=np.clip(frame,0,255).astype(np.uint8)
    # Fast moving luminous dust strongly emphasizes camera travel and perspective.
    for i,(px,py,z,phase,tw) in enumerate(MOTES):
        a=phase+t*(.22+.12*z)
        depth=(z+cam*(.21+.13*tw))%1
        distance=48+810*(1-depth)**1.7
        px=int(cx+distance*math.cos(a))
        py=int(cy+distance*1.31*math.sin(a))
        if 0<px<W and 335<py<H-70:
            lum=int(95+(1-depth)*120)
            cv2.line(frame,(px,py),(px+int(4*math.cos(a)),py+int(6*math.sin(a))),(lum,round(lum*.93),min(255,lum+29)),1,cv2.LINE_AA)
    if f>=550:
        u=smooth((f-550)/65)
        frame=cv2.addWeighted(frame,1-u*.22,np.full_like(frame,(46,36,54)),u*.22,0)
    return frame

# -- A rotating branching real-world-inspired fulgurite --------------------------------
# 3D centerlines used with a camera orbit: parallax, occlusion, glancing reflections.
HERO_BRANCHES=[]
main=np.linspace(-1,1,93)
HERO_BRANCHES.append((np.column_stack((.11*np.sin(main*7)+.07*np.sin(main*19),main*1.7,.13*np.cos(main*8)+.05*np.sin(main*21))),.085))
for idx,(level,sgn,tilt,length) in enumerate(((-.65,-1,.1,.78),(-.4,1,.36,.95),(.03,-1,.7,1.18),(.21,1,.8,.85),(.55,-1,1.1,.72),(.84,1,1.8,.65))):
    q=np.linspace(0,1,55)
    center=np.array([.11*math.sin(level/1.7*7)+.07*math.sin(level/1.7*19),level,.13*math.cos(level/1.7*8)])
    xx=center[0]+sgn*(length*q**1.12)+.07*np.sin(q*13+idx)*q
    yy=center[1]+(.33+.46*tilt)*q-.09*np.sin(q*4)
    zz=center[2]+(.21*np.cos(q*6+idx)+sgn*.26*q)
    HERO_BRANCHES.append((np.column_stack((xx,yy,zz)),.062))

def hero_project(points,t,zoom=1):
    yaw=-.34+(t-22.0)*.152
    pitch=.10+.13*math.sin(t*.23)
    sy=math.sin(yaw);cy=math.cos(yaw);sp=math.sin(pitch);cp=math.cos(pitch)
    a=points[:,0]*cy-points[:,2]*sy
    z=points[:,0]*sy+points[:,2]*cy
    b=points[:,1]*cp-z*sp
    depth=points[:,1]*sp+z*cp
    s=(200*zoom/(1+.12*depth))
    cx=W/2+18*math.sin(t*.31)
    return np.column_stack((cx+a*s,700+b*s,depth)),s

def hero(f,t):
    # Cinematic defocused foreground / backlight, not one flat background.
    bg=camera_texture(SAND,t,int(t*3),round(t*4))
    frame=cv2.addWeighted(bg,.45,np.full_like(bg,(15,16,32)),.55,0)
    # Stage lights are a radial warm-white source with cool top rim.
    light=np.exp(-((X-525)**2/(2*220**2)+(Y-600)**2/(2*315**2))).astype(np.float32)
    for k,a in enumerate((56,58,96)):
        frame[:,:,k]=np.clip(frame[:,:,k].astype(np.float32)+a*light,0,255).astype(np.uint8)
    for i,(x,y,z,p,tw) in enumerate(MOTES[:80]):
        xx=int((x+(t-22)*11*(.3+z))%W)
        yy=int((y-(t-22)*8*(1+z))%H)
        radius=2+int(z>0.8)*2
        cv2.circle(frame,(xx,yy),radius,(38+round(z*117),45+round(z*90),62+round(z*104)),-1,cv2.LINE_AA)
    # A glassy fulgurite is coated with sand and branched, hollow inside.
    scale=.84+.11*easeout((t-22)/7.8)
    layers=[]
    for i,(path,r) in enumerate(HERO_BRANCHES):
        proj,s=hero_project(path,t,scale)
        depth=float(np.mean(proj[:,2]))
        layers.append((depth,i,proj,r))
    layers.sort(key=lambda x:x[0],reverse=True)
    for depth,i,pts,r in layers:
        center=pts[:,:2].astype(np.int32)
        width=max(8,int(r*220*scale))
        shadow=center+np.array([8,9],np.int32)
        cv2.polylines(frame,[shadow],False,(14,14,20),width*4,cv2.LINE_AA)
        # An uneven sand-encrusted outer rock shell and glass veins beneath.
        cv2.polylines(frame,[center],False,(62,52,56),width*4,cv2.LINE_AA)
        cv2.polylines(frame,[center],False,(120,87,70),width*3,cv2.LINE_AA)
        cv2.polylines(frame,[center],False,(185,128,84),width+9,cv2.LINE_AA)
        cv2.polylines(frame,[center],False,(45,37,47),max(4,width//2),cv2.LINE_AA)
        high=center+np.array([-max(2,width//2),-5],np.int32)
        cv2.polylines(frame,[high],False,(234,213,167),max(2,width//4),cv2.LINE_AA)
        side=center+np.array([max(2,width//2),2],np.int32)
        cv2.polylines(frame,[side],False,(110,165,193),max(1,width//5),cv2.LINE_AA)
        # Deterministic microroughness, mineral grain clusters, and discontinuous gloss.
        for q in range(1,len(pts)-1,2):
            xx,yy=center[q]
            if 280<yy<1110 and 10<xx<W-10:
                phase=math.sin(q*13.37+i*17.1)
                off=round((width+4)*phase*1.03)
                v=round((.5+.5*math.sin(q*7.9+i*4.7))*60)
                cv2.circle(frame,(xx+off,yy+int(3*math.cos(q*6.5))),1 if q%4 else 2,
                           (111+v,115+v//2,119+v//3),-1,cv2.LINE_AA)
                if q%9==0:
                    cv2.line(frame,(xx-width,yy-3),(xx-width//2,yy-8),(173,190,188),1,cv2.LINE_AA)
    # Warm glass specular glints are timed with final sound accents.
    for i in range(13):
        ang=i*2.39996 + t*.14
        q=140+14*(i%4)
        xx=int(W/2+math.cos(ang)*q); yy=int(715+math.sin(ang)*q*1.65)
        rad=2+(i%3)
        cv2.circle(frame,(xx,yy),rad,(203,221,246),-1,cv2.LINE_AA)
    if f>=820:
        p=smooth((f-820)/24)
        # Gentle iris and final highlight, keeping the sculpture visible.
        flash=np.zeros_like(frame);cv2.circle(flash,(W//2,710),int(160+p*190),(26,83,117),4,cv2.LINE_AA)
        glows(frame,flash,17,.42)
    return frame

def render_frame(f):
    t=f/FPS
    if t<7.8:
        frame=storm(f,t)
    elif t<14.3:
        frame=underground(f,t)
        if t<8.35:
            a=smooth((t-7.8)/.55)
            frame=cv2.addWeighted(storm(int(7.8*FPS),7.8),1-a,frame,a,0)
    elif t<22.5:
        frame=tunnel(f,t)
        if t<14.85:
            a=smooth((t-14.3)/.55)
            frame=cv2.addWeighted(underground(int(14.3*FPS),14.3),1-a,frame,a,0)
    else:
        frame=hero(f,t)
        if t<23.25:
            a=smooth((t-22.5)/.75)
            frame=cv2.addWeighted(tunnel(int(22.5*FPS),22.5),1-a,frame,a,0)
    # Consistent premium text/safe areas & near-black cinematic gradient.
    sh=np.clip((Y-230)/245,0,1).astype(np.float32)
    top=frame[:,:].astype(np.float32)
    top[:]=(16,19,31)
    top*=.96
    frame[:]=np.clip(frame*sh[:,:,None]+top*(1-sh[:,:,None]),0,255).astype(np.uint8)
    # footer lift means typography stays legible across solid sand and animated cloud.
    screen_text(frame,t)
    vignette(frame,.62)
    return frame

# -- Original music and richly spatialized synchronous sound ------------------
def ntime(n):return np.arange(int(SR*n),dtype=np.float64)/SR

def stereo_add(mix,src,at,gain=.1,pan=0):
    ix=int(round(at*SR)); n=min(len(src),len(mix)-ix)
    if n<=0 or ix<0:return
    theta=(float(np.clip(pan,-.98,.98))+1)*np.pi/4
    mix[ix:ix+n,0]+=src[:n]*gain*math.cos(theta)
    mix[ix:ix+n,1]+=src[:n]*gain*math.sin(theta)

def env(t,attack=.006,release=.14):
    return np.minimum(1,t/attack)*np.minimum(1,(t[-1]-t)/release)

def bandnoise(gen,seconds,lo=120,hi=8000):
    n=round(SR*seconds); x=gen.standard_normal(n).astype(np.float32)
    F=np.fft.rfftfreq(n,1/SR)
    hp=np.minimum(1,F/(lo+1)); lp=np.exp(-(F/hi)**3.0)
    arr=np.fft.irfft(np.fft.rfft(x)*hp*lp,n=n)
    return arr/max(float(np.std(arr)*3.3),1e-6)

def bass_drum(t):
    phase=TAU*(40*t+97*(1-np.exp(-36*t))/36)
    return (np.sin(phase)+.19*np.sin(phase*2))*np.minimum(1,SR*.001*t)*np.exp(-t*9)

def glass_note(midi,t):
    hz=440*2**((midi-69)/12)
    p=TAU*hz*t
    color=.48*np.sin(p)+.23*np.sin(2.01*p+.21)+.17*np.sin(3.91*p)+.12*np.sin(5.48*p+.75)
    return color*np.minimum(1,250*t)*np.exp(-3.15*t)

def gust(gen,duration,center=500,shape=0):
    t=ntime(duration)
    hiss=bandnoise(gen,duration,center,2500+center)
    w=.6+.4*np.sin(TAU*(2.3*t+shape*t*t))**2
    return hiss*env(t,.06,.21)*w

def compose_audio(path):
    gen=np.random.default_rng(9102026)
    mix=np.zeros((DUR*SR,2),np.float64)
    # Harmonic structure changes with subject: cloudy intro -> charged strike -> molten heat -> glass -> reveal.
    sections=[(0,(38,45,53,57),.7),(5.2,(34,46,53,58),1.15),(9.8,(36,43,52,57),1.),
              (14.3,(41,48,55,60),.82),(19.8,(38,45,53,60),1.14),(23.0,(33,45,52,57),1.25),
              (28.2,(38,45,53,62),1.47)]
    for i,(st,ch,amp) in enumerate(sections):
        ed=(sections[i+1][0] if i<len(sections)-1 else DUR)+.6
        ed=min(DUR,ed)
        t=ntime(ed-st)
        pad_env=env(t,.38,.60)
        for k,note in enumerate(ch):
            freq=440*2**((note-69)/12)
            for side in (-1,1):
                p=TAU*(freq+side*.10)*t
                pad=(.69*np.sin(p+.22*np.sin(t*.58+k))+.20*np.sin(p*2.001+side*.8)+.11*np.sin(p*3.005+.15))
                stereo_add(mix,pad*pad_env,st,.027*amp/(1+k*.36),side*.55)
    beat=60/128
    for i in range(int(DUR/(beat/2))+1):
        at=i*beat/2
        # Intro hides percussion; the post-flash pulse locks to the visual drive.
        power=.37 if at<5.0 else (1.13 if at<14.3 else .92 if at<22.5 else 1.24)
        if 4.98<at<5.50 or 27.8<at<28.44:power*=.16
        if i%2==0:
            t=ntime(.41)
            stereo_add(mix,bass_drum(t),at,.083*power)
            if i%4==0 and at>5.8:
                stereo_add(mix,bass_drum(t),at,.056*power,pan=-.06)
        if i%2:
            dur=.146;t=ntime(dur)
            tick=bandnoise(gen,dur,4100,11100)*env(t,.003,.032)*np.exp(-12*t)
            stereo_add(mix,tick,at,.045*power,pan=.18*math.sin(i*.65))
        if i%4==2:
            dur=.25;t=ntime(dur)
            clap=bandnoise(gen,dur,1550,6200)*env(t,.005,.11)*np.exp(-12*t)
            stereo_add(mix,clap,at,.047*power,pan=-.25)
        chord=sections[max(k for k,s in enumerate(sections) if at>=s[0])][1]
        arp=chord[(0,2,1,3,2,1,3,0)[i%8]]+(24 if i%4==3 else 12)
        if at>5.75:
            tt=ntime(.58)
            stereo_add(mix,glass_note(arp,tt),at,.083*power,pan=.58*math.sin(i*.52))
            stereo_add(mix,glass_note(arp,tt),at+.167,.018*power,pan=-.58*math.sin(i*.52))
    # Running environmental beds, highly dynamic from wind into heated sand into crystalline ambience.
    bed=bandnoise(gen,DUR,70,850).astype(np.float64)
    tim=np.arange(DUR*SR,dtype=np.float64)/SR
    wind=.039+ .048*np.exp(-((tim-4.6)/2.5)**2)+.018*np.exp(-((tim-15.8)/4)**2)
    for side in (-1,1):
        stereo_add(mix,bed*wind,0.,.63,pan=side*.7)
    # Music 'ducks' instantly before strike and major reveals, then recovers smoothly.
    curve=np.interp(tim,
        [0,1.5,4.2,4.96,5.16,5.56,7.1,9.8,12.1,14.2,17.9,21.8,22.65,23.6,27.55,28.18,29.0,31.5,33.],
        [.68,.74,.97,.23,.10,.86,1.0,.92,1.13,.70,1.08,.75,.20,1.27,.72,.24,1.30,1.15,.0])
    # We need the sidechain on the score; with this post-sum pass effects stay sharp since
    # their gain is compensated with event-local peaks above.
    mix*=curve[:,None]
    # Distant sky rumbles from a synthesised descending oscillator and filtered noise.
    for at,gain in ((1.7,.11),(5.35,.33),(6.25,.17)):
        sec=2.40;t=ntime(sec)
        trem=np.sin(TAU*(52*t+25*(1-np.exp(-4*t))/4))
        wobble=np.sin(TAU*(70*t+12*t*t))*np.exp(-t*3)
        roar=bandnoise(gen,sec,90,630)
        stereo_add(mix,(trem*.58+roar*.56+wobble*.17)*np.exp(-t*1.16)*env(t,.09,.31),at,gain,pan=-.2 if at<5 else .22)
    # Ultra-fast stepped leader & white-hot contact at exact frame 156; heavily synchronized.
    t=ntime(.85)
    leader=bandnoise(gen,.85,1250,15500)
    charge=leader*env(t,.009,.11)*(1+.3*np.sin(91*t))
    stereo_add(mix,charge,141/FPS,.12,pan=-.41)
    click_t=ntime(.09)
    crack=(.45*np.sin(TAU*(190+3600*click_t)*click_t)+.55*bandnoise(gen,.09,1650,15000))*env(click_t,.0015,.028)*np.exp(-click_t*13)
    stereo_add(mix,crack,156/FPS,.35,pan=.28)
    stereo_add(mix,bass_drum(ntime(.7)),156/FPS,.45)
    for j in range(11):
        d=.075+.07*j
        tt=ntime(.13)
        spark=bandnoise(gen,.13,2400,11000)*env(tt,.002,.053)*np.exp(-12*tt)
        stereo_add(mix,spark,156/FPS+d,.065*(1-j/14),pan=math.sin(j*.82)*.78)
    # Rocks, brittle grains and liquid glass fizz, with moving source and panning.
    for i in range(140):
        at=7.9+i*.092
        if at>22.0:break
        tt=ntime(.065)
        noise=bandnoise(gen,.065,950+int((i*37)%3200),8000)
        envgrain=env(tt,.002,.024)*np.exp(-22*tt)
        period=(.04+.04*np.sin(i*1.81)**2)
        stereo_add(mix,noise*envgrain,at,period* (1.45 if 11.2<at<14.9 else .62),pan=math.sin(i*1.43)*.86)
    for f,name in CUES[5:]:
        at=f/FPS
        t=ntime(.64)
        rise=(.38+.62*np.sin(t*9)**2)*env(t,.03,.22)
        texture=bandnoise(gen,.64,1800,9200)
        impact=texture*rise*np.exp(-t*4)
        p=(math.sin(f)*.62)
        stereo_add(mix,impact,at,.085 if name not in ('specimen_reveal','hero_title') else .15,p)
        if name in ('molten_front','specimen_reveal','hero_title','outro'):
            stereo_add(mix,bass_drum(ntime(.58)),at,.24 if name!='hero_title' else .34)
        if name in ('enter_glass','cooling','specimen_reveal','hero_title'):
            for j,n in enumerate((74,81,86,90)):
                stereo_add(mix,glass_note(n,ntime(1.1)),at+j*.073,.093 if j<2 else .067,(-1)**j*.49)
    # Stereo room reflections, organic depth without artificial preset music.
    wet=np.zeros_like(mix)
    for delay,gain in ((.035,.071),(.084,.052),(.153,.039),(.247,.020)):
        n=int(delay*SR)
        wet[n:]+=mix[:-n,::-1]*gain
    mix+=wet
    # Conservative pre-encoding peak, final loudness validated via FFmpeg EBU measurement.
    peak=float(np.max(abs(mix)))
    mix*=.89/max(peak, .89)
    fade=np.minimum(1,tim/.040)*np.minimum(1,(DUR-tim)/.73)
    mix*=fade[:,None]
    out=np.rint(np.clip(mix,-.97,.97)*32767).astype('<i2')
    with wave.open(str(path),'wb') as wf:
        wf.setparams((2,2,SR,len(out),'NONE','not compressed'))
        wf.writeframes(out.tobytes())
    return {'peak':peak,'cues':[{'frame':f,'audioSample':f*SP,'name':name,'seconds':round(f/FPS,5)} for f,name in CUES]}

def subprocess_run(args,**kwargs):
    subprocess.run([str(a) for a in args],check=True,**kwargs)

def render_movie():
    # Original frames encoded via a pipe, no bitmap slide show or held frames.
    args=['ffmpeg','-hide_banner','-loglevel','error','-y',
          '-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0',
          '-i',SND,'-map','0:v:0','-map','1:a:0','-vf','scale=1080:1920:flags=lanczos',
          '-c:v','libx264','-pix_fmt','yuv420p','-preset','faster','-crf','19','-threads','4',
          '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
          '-c:a','aac','-b:a','224k','-ar',str(SR),
          '-af','loudnorm=I=-14.4:TP=-1.4:LRA=9,alimiter=limit=0.82',
          '-map_metadata','-1','-map_metadata:s','-1','-map_chapters','-1',
          '-movflags','+faststart',FILE]
    pipe=subprocess.Popen([str(v) for v in args],stdin=subprocess.PIPE)
    try:
        for f in range(FRAMES):
            frame=render_frame(f)
            if f%120==0:
                print('frame',f,'/',FRAMES,flush=True)
            pipe.stdin.write(frame.tobytes())
    finally:
        pipe.stdin.close()
        if pipe.wait()!=0:raise RuntimeError('ffmpeg encoder failed')


def qa_video(cue_data):
    subprocess_run(['ffmpeg','-v','error','-xerror','-i',FILE,'-f','null','-'])
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',FILE]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (video['width'],video['height'])==(1080,1920)
    assert video['avg_frame_rate']=='30/1' and video['codec_name']=='h264'
    assert int(video['nb_frames'])==FRAMES and audio['codec_name']=='aac'
    assert abs(float(probe['format']['duration'])-DUR)<.07
    assert set(probe['format'].get('tags',{}))<={'major_brand','minor_version','compatible_brands','encoder'}
    assert not probe.get('chapters')
    assert all(x['audioSample']==x['frame']*SP for x in cue_data['cues'])
    sha=hashlib.sha256(FILE.read_bytes()).hexdigest()
    info={'sha256':sha,'size':FILE.stat().st_size,'duration':DUR,'fps':FPS,'frames':FRAMES,
          'resolution':[1080,1920],'audioSampleRate':SR,'music':'original, stereo',
          'originalAssets':True,'cues':cue_data['cues'],'science':'Natural fulgurites: lightning fuses silicate sand into hollow glass tubes','probe':probe}
    (ROOT/'qa.json').write_text(json.dumps(info,indent=2)+'\n')
    print('PASS',sha,FILE.stat().st_size,flush=True)
    return info

def contact():
    points=[0,105,156,188,256,337,414,475,592,672,797,880]
    cards=[]
    for f in points:
        frame=render_frame(f)
        fr=cv2.resize(frame,(180,320),interpolation=cv2.INTER_AREA)
        cards.append(fr)
    contact=np.vstack([np.hstack(cards[i:i+4]) for i in range(0,len(cards),4)])
    Image.fromarray(contact).save(ROOT/'contact.jpg',quality=92)
    print('Contact',ROOT/'contact.jpg',flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--preview',action='store_true')
    args=p.parse_args()
    contact()
    if args.preview:return
    cue_data=compose_audio(SND)
    render_movie()
    qa_video(cue_data)
    SND.unlink(missing_ok=True)

if __name__=='__main__':main()