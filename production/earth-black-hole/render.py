#!/usr/bin/env python3
"""SQUEEZE THE EARTH — original portrait 2.5-D, procedural artwork and beat-locked sound.
Physics: Earth-mass Schwarzschild radius ~8.87mm; thought experiment only.
Dependency: numpy, Pillow, OpenCV, scipy, ffmpeg. No source photographs/audio.
"""
import argparse, json, math, os, subprocess, wave, hashlib
from pathlib import Path
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from scipy.signal import butter, sosfilt

DIR=Path(os.environ.get('EARTH_BLACKHOLE_OUTPUT','/mnt/data/earth_bh_work'))
DIR.mkdir(parents=True,exist_ok=True)
W,H=720,1280
FPS=30; NFR=960; SR=48000; SPF=SR//FPS; NS=NFR*SPF
TAU=math.tau
RNG=np.random.default_rng(41528)
BIG='/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf'
BOLD='/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
REG='/usr/share/fonts/opentype/inter/Inter-Medium.otf'
MED='/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
WHITE=(243,247,250); MINT=(139,244,210); VIOLET=(183,147,255); YELLOW=(255,206,122)
PURPLE=(155,114,250); RED=(255,134,98)

# Shared event schedule (one beat=0.5s, one phrase=4s).
EVENTS=[
 {'frame':0,'label':'EARTH','radius':6371000.,'unit':'6,371 KM','detail':'A PLANET-SIZED WORLD','color':MINT,'note':46},
 {'frame':120,'label':'THE MOON','radius':1737000.,'unit':'1,737 KM','detail':'SHRUNK TO THE MOON’S RADIUS','color':(142,201,255),'note':49},
 {'frame':240,'label':'EVEREST','radius':8848.,'unit':'8.85 KM','detail':'AS HIGH AS EVEREST','color':(249,199,138),'note':51},
 {'frame':360,'label':'BURJ KHALIFA','radius':828.,'unit':'828 M','detail':'TALLER THAN A SKYSCRAPER','color':(255,163,133),'note':54},
 {'frame':480,'label':'A PERSON','radius':1.75,'unit':'1.75 M','detail':'JUST HUMAN-SIZED','color':(185,156,253),'note':56},
 {'frame':600,'label':'TENNIS BALL','radius':.0335,'unit':'3.35 CM','detail':'TENNIS BALL RADIUS','color':(239,216,140),'note':58},
 {'frame':720,'label':'COIN','radius':.010,'unit':'1.0 CM','detail':'SMALLER THAN A COIN','color':(255,178,110),'note':61},
 {'frame':840,'label':'EVENT HORIZON','radius':.00887,'unit':'8.9 MM','detail':'EARTH’S MASS. BLACK HOLE.','color':(255,193,133),'note':66},
]
assert all(e['frame']%120==0 for e in EVENTS)

def smooth(v):
    v=np.clip(v,0,1)
    return v*v*(3-2*v)

def ease_out(v):
    v=np.clip(v,0,1)
    return 1-(1-v)**3

def stage(frame):
    return min(7,frame//120)

def radius_real(f):
    i=stage(f)
    if i==7: return .00887
    a=EVENTS[i]['radius'];b=EVENTS[i+1]['radius']
    p=smooth((f-i*120)/120)
    return math.exp(math.log(a)*(1-p)+math.log(b)*p)

def format_size(r):
    if r>=1000:
        return (f'{r/1000:,.0f}' if r>=1e5 else f'{r/1000:,.1f}')+' km'
    if r>=1:
        return (f'{r:,.0f}' if r>10 else f'{r:.2f}')+' m'
    if r>=.1: return f'{r*100:.1f} cm'
    return f'{r*1000:.1f} mm'

# World textures, procedurally generated once.
def fbm(h,w,layers,seed=28):
    rg=np.random.default_rng(seed); v=np.zeros((h,w),np.float32)
    for j,(shape,amp) in enumerate(layers):
        y,x=shape
        coarse=rg.normal(0,1,(y,x)).astype(np.float32)
        v+=cv2.resize(coarse,(w,h),interpolation=cv2.INTER_CUBIC)*amp
    return v

TEXW,TEXH=1400,700
Y0,X0=np.mgrid[:TEXH,:TEXW].astype(np.float32)
GEO=fbm(TEXH,TEXW,[((4,7),.67),((10,18),.30),((27,54),.16),((76,135),.08)],9)
CLOUDS=fbm(TEXH,TEXW,[((8,12),.55),((22,33),.40),((57,90),.20),((132,180),.09)],14)
YLAT=np.abs((Y0/TEXH-.5)*2)
continents=np.clip((GEO+.13)*4.8,0,1)*np.clip((1-YLAT)*1.95,0,1)
continent_shelves=np.clip((GEO+.34)*2.8,0,1)
OCEAN=np.stack((12+27*continent_shelves,55+54*continent_shelves,104+43*continent_shelves),axis=-1)
LAND=np.stack((58+24*GEO,112+51*np.clip(GEO,0,1),82+13*GEO),axis=-1)
DRY=np.clip((np.abs(Y0/TEXH-.5)-.08)*3.0,0,1)
LAND=LAND*(1-DRY[:,:,None]*.43)+np.array([176,143,85])*DRY[:,:,None]*.43
COL=OCEAN*(1-continents[:,:,None])+LAND*continents[:,:,None]
ICE=np.clip((YLAT-.82)*10,0,1)
COL=COL*(1-ICE[:,:,None])+np.array([209,222,226])*ICE[:,:,None]
EARTH_TEX=np.uint8(np.clip(COL,0,255))
CLOUD_TEX=np.uint8(np.clip(CLOUDS*88+118,0,255))
MAPSIZE=520
xx,yy=np.meshgrid(np.linspace(-1.04,1.04,MAPSIZE,dtype=np.float32),np.linspace(-1.04,1.04,MAPSIZE,dtype=np.float32))
rr=xx**2+yy**2
pz=np.sqrt(np.maximum(1-rr,0))
lat=np.arcsin(np.clip(yy,-1,1))
lon=np.arctan2(xx,np.maximum(pz,.0001))
TEXTURE_X=(lon/TAU+.5)*TEXW
TEXTURE_Y=(lat/math.pi+.5)*TEXH
vis=(rr<=1).astype(np.float32)
light=np.clip(.81*pz+.47*(-xx)+.35*(-yy),0,1)
light=(.16+.94*light**.82)
fresnel=np.maximum(0,(1-pz))**3.4
view_theta=np.arctan2(yy,xx)

# Static star and haze layers.
stars=[]
for j in range(520):
    stars.append((RNG.uniform(0,W),RNG.uniform(0,H),RNG.uniform(.25,1),RNG.uniform(0,TAU),RNG.choice([1,1,1,2]),RNG.choice([0,1,2])))
star_arr=np.array(stars,dtype=np.float32)
# pre-rendered background with subtle cosmic light shafts and dense dark gradients
BXYx,BXYy=np.meshgrid(np.arange(W,dtype=np.float32),np.arange(H,dtype=np.float32))
def build_bg():
    y=BXYy/H;x=BXYx/W
    purple=np.exp(-((x-.27)**2/.17+(y-.63)**2/.22))
    blue=np.exp(-((x-.81)**2/.12+(y-.26)**2/.21))
    teal=np.exp(-((x-.58)**2/.12+(y-.88)**2/.21))
    v=fbm(H,W,[((6,4),.56),((18,12),.17),((55,30),.07)],42)
    return np.uint8(np.clip(np.stack((5+13*purple+7*blue+3*v,9+7*purple+12*blue+11*teal+4*v,24+27*purple+30*blue+19*teal+5*v),axis=-1),0,255))
BG=build_bg()

# Typography cached as RGBA glyphs with gentle drop shadows.
@lru_cache(maxsize=280)
def txtsprite(text,size,color,kind='bold',shadow=True):
    p={'hero':BIG,'bold':BOLD,'med':MED,'reg':REG}[kind]
    try: font=ImageFont.truetype(p,size)
    except: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',size)
    b=font.getbbox(text,stroke_width=0)
    tw=int(font.getlength(text)+1); th=max(18,b[3]-b[1])
    im=Image.new('RGBA',(tw+20,th+26))
    d=ImageDraw.Draw(im)
    y=9-b[1]
    if shadow:
        d.text((11,y+2),text,font=font,fill=(1,3,11,145))
    d.text((10,y),text,font=font,fill=(*color,255))
    return np.asarray(im)

def overlay(dst,rgba,x,y,alpha=1.0):
    if alpha<=0: return
    x=int(round(x));y=int(round(y));h,w=rgba.shape[:2]
    x0=max(0,x);x1=min(W,x+w);y0=max(0,y);y1=min(H,y+h)
    if x0>=x1 or y0>=y1:return
    data=rgba[y0-y:y1-y,x0-x:x1-x]
    a=(data[:,:,3:4].astype(np.float32)/255.)*alpha
    roi=dst[y0:y1,x0:x1]
    roi[:]=roi*(1-a)+data[:,:,:3]*a

def center_text(dst,string,size,color,cx,cy,kind='bold',alpha=1):
    if not string:return
    s=txtsprite(string,size,color,kind)
    overlay(dst,s,cx-s.shape[1]/2,cy-s.shape[0]/2,alpha)

def background(t,f):
    dst=BG.copy()
    # Warped parallax stars; show colored optical trails during compression beats.
    for j,(sx,sy,z,phase,r,typ) in enumerate(stars):
        dx=(sx-W*.5)*(1+.012*math.sin(t*.42))*1.07 + 15*math.sin(.18*t+phase)*z
        dy=(sy-H*.48)*(1+.016*math.sin(t*.39))+10*math.cos(t*.18+phase)*z
        px=int((dx+W*.5)%W); py=int((dy+H*.48)%H)
        tw=.53+.43*math.sin(t*(1.2+typ*.7)+phase)**2
        b=int((88+117*z)*tw)
        c=(b*.73,b*.88,b) if typ==0 else ((b*.78,b*.98,b*.89) if typ==1 else (b,b*.78,b*.89))
        col=tuple(int(v) for v in c)
        cv2.circle(dst,(px,py),int(r),col,-1,cv2.LINE_AA)
        if r>1.5 and tw>.8:
            cv2.line(dst,(px-3,py),(px+3,py),col,1,cv2.LINE_AA)
            cv2.line(dst,(px,py-3),(px,py+3),col,1,cv2.LINE_AA)
    # Perspective orbit grid arcs move smoothly; warm when at high compression.
    v=smooth((t-20)/8)
    rings=((126,27),(176,39),(240,56),(321,80),(439,110))
    for j,(rx,ry) in enumerate(rings):
        col=(int(28+34*v),int(49+16*v),int(81-22*v))
        cv2.ellipse(dst,(360,730), (rx,ry), -20, 0,360,col,1,cv2.LINE_AA)
    for j in range(10):
        c=150+j*50
        x1=int(360+(j-5)*90)
        cv2.line(dst,(x1,870),(360+(j-5)*12,770),(18,31,55),1,cv2.LINE_AA)
    return dst

def draw_earth_sprite(t,heat):
    shift= (t*6.8) % TEXW
    mapx=(TEXTURE_X+shift).astype(np.float32)
    color=cv2.remap(EARTH_TEX,mapx,TEXTURE_Y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
    clouds=cv2.remap(CLOUD_TEX,mapx+t*2.3,TEXTURE_Y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
    ca=np.clip((clouds.astype(np.float32)-140)/142,0,.8)
    color=color*(1-ca[:,:,None])+np.array([212,233,237])*ca[:,:,None]
    magma=np.stack((np.clip(111+84*color[:,:,0]/255+109*(1-pz),0,255),
                    np.clip(55+72*(1-pz),0,255),
                    np.clip(62+70*pz,0,255)),axis=-1)
    # Bright branching fractures appear as compression increases.
    fissures=1.0-np.abs(np.sin(14*view_theta+26*xx+8*np.sin(yy*9)))*np.abs(np.cos(8*yy-6*xx))
    veins=np.clip((fissures-.91)*11,0,1)*heat**1.3
    magma+=np.array([83,116,69])*veins[:,:,None]
    color=color*(1-heat)+magma*heat
    color=color*light[:,:,None]
    color+=np.array([34,84,142])*fresnel[:,:,None]*(1-heat)*1.35
    color+=np.array([59,22,13])*fresnel[:,:,None]*heat
    alpha=vis*(np.clip((1-rr)*180,0,1))
    return np.dstack((np.uint8(np.clip(color,0,255)),np.uint8(np.clip(alpha*255,0,255))))

# Custom geometric comparison visuals with genuine depth layering.
def comparison(dst,idx,t,color):
    if idx==0: return
    phase=min(1,(t-EVENTS[idx]['frame']/FPS)*3)
    if phase<0:return
    a=ease_out(phase)
    px=90-int((1-a)*160)
    py=905
    edge=tuple(int(c) for c in color)
    fill=(23,35,49)
    if idx==1:  # moon relief with craters
        cv2.circle(dst,(px+35,py-36),49,fill,-1,cv2.LINE_AA)
        cv2.circle(dst,(px+35,py-36),49,edge,2,cv2.LINE_AA)
        for x,y,r in [(24,-53,10),(54,-15,14),(45,-59,7),(7,-26,8)]:
            cv2.circle(dst,(px+x,py+y),r,(67,76,95),1,cv2.LINE_AA)
    elif idx==2: # jagged mountain ridges
        p=np.array([(px-20,py+29),(px+9,py-12),(px+30,py-51),(px+41,py-28),(px+60,py-89),(px+78,py-36),(px+109,py+28)],np.int32)
        cv2.fillPoly(dst,[p],fill,cv2.LINE_AA);cv2.polylines(dst,[p],False,edge,2,cv2.LINE_AA)
        cv2.line(dst,(px+49,py-63),(px+60,py-89),WHITE,2,cv2.LINE_AA)
    elif idx==3:  # glass skyscraper
        p=np.array([(px+13,py+26),(px+16,py-27),(px+29,py-28),(px+32,py-86),(px+38,py-112),(px+46,py-87),(px+52,py-28),(px+63,py-28),(px+70,py+26)],np.int32)
        cv2.fillPoly(dst,[p],fill,cv2.LINE_AA);cv2.polylines(dst,[p],True,edge,2,cv2.LINE_AA)
        for y in range(py-31,py+25,9):
            cv2.line(dst,(px+18,y),(px+64,y),(74,122,135),1,cv2.LINE_AA)
    elif idx==4: # person anatomical silhouette
        cv2.circle(dst,(px+37,py-74),14,fill,-1,cv2.LINE_AA)
        cv2.circle(dst,(px+37,py-74),14,edge,2,cv2.LINE_AA)
        cv2.line(dst,(px+37,py-60),(px+37,py-2),edge,8,cv2.LINE_AA)
        for q in [(-24,-44),(-26,-19),(26,-45),(27,-22),(-18,21),(18,21)]:
            pass
        cv2.line(dst,(px+35,py-40),(px+13,py-13),edge,5,cv2.LINE_AA)
        cv2.line(dst,(px+39,py-40),(px+61,py-13),edge,5,cv2.LINE_AA)
        cv2.line(dst,(px+37,py-2),(px+21,py+30),edge,6,cv2.LINE_AA)
        cv2.line(dst,(px+37,py-2),(px+55,py+30),edge,6,cv2.LINE_AA)
    elif idx==5:
        cv2.circle(dst,(px+38,py-27),47,fill,-1,cv2.LINE_AA)
        for y in range(py-74,py+21,8):
            xofs=int(math.sqrt(max(0,47**2-(y-(py-27))**2)))
            cv2.line(dst,(px+38-xofs,y),(px+38+xofs,y),(93,127,51),2,cv2.LINE_AA)
        cv2.circle(dst,(px+38,py-27),47,edge,2,cv2.LINE_AA)
    elif idx in (6,7):
        cv2.circle(dst,(px+39,py-25),45,(27,34,45),-1,cv2.LINE_AA)
        cv2.circle(dst,(px+39,py-25),45,edge,3,cv2.LINE_AA)
        if idx==6:
            cv2.circle(dst,(px+39,py-25),34,(110,120,129),2,cv2.LINE_AA)
            center_text(dst,'Ø',43,WHITE,px+39,py-27)
        else:
            cv2.circle(dst,(px+39,py-25),14,(2,1,9),-1,cv2.LINE_AA)
            cv2.ellipse(dst,(px+39,py-25),(34,14),-20,0,360,YELLOW,2,cv2.LINE_AA)
    center_text(dst,'REFERENCE SCALE',14,(130,151,169),123,972,kind='med',alpha=a)
    center_text(dst,EVENTS[idx]['label'],21,WHITE,127,1006,kind='bold',alpha=a)

def rings_and_glow(dst,t,cx,cy,r,heat,collapse):
    # Static lens flare in the upper left projects a sweeping reflection over the orb.
    sh,sw=H//4,W//4
    halo=np.zeros((sh,sw,3),np.uint8)
    halo_alpha=.35+.3*np.sin(t*.35)**2
    col=(50,137,211) if heat<.7 else (186,88,56)
    cv2.circle(halo,(cx//4,cy//4),int((r+32)/4),col,3,cv2.LINE_AA)
    halo=cv2.resize(cv2.GaussianBlur(halo,(0,0),7),(W,H),interpolation=cv2.INTER_LINEAR)
    dst[:]=cv2.addWeighted(dst,1,halo,halo_alpha,0)
    # Thin orbit paths wrap behind then in front of the sphere.
    for k in range(3):
        b=t*(17+12*k)+k*59
        cl=(52+22*k,91+16*k,138+17*k)
        cv2.ellipse(dst,(cx,cy),(int(r*1.65+k*19),int(r*.48+k*17)),-18+b*.025,0,360,cl,1,cv2.LINE_AA)
    if collapse>0:
        for k in range(3):
            theta=(t*10+k*TAU/3)
            rad=r+(24+30*k)*collapse
            p=(int(cx+rad*math.cos(theta)),int(cy+rad*.59*math.sin(theta)))
            cv2.circle(dst,p,3,tuple(int((1-collapse)*c+collapse*z) for c,z in zip(MINT,YELLOW)),-1,cv2.LINE_AA)

def blackhole(dst,t,cx,cy,progress):
    progress=smooth(progress)
    if progress<=0:return
    # Gravitational lens: thick warm displaced arcs, hot photon band and black event horizon.
    for k in range(19,-1,-1):
        rad=int(100+k*4+16*math.sin(t*.35+k*.12))
        thickness=1 if k>5 else 2
        fade=(19-k)/19
        c=(int((40+95*fade)*progress),int((48+101*fade)*progress),int((99+85*fade)*progress))
        ang=(t*11+k*13)%360
        cv2.ellipse(dst,(cx,cy),(rad,int(rad*.70)),(t*4)%360,ang,ang+230,c,thickness,cv2.LINE_AA)
    # Rotating accretion streaks (purely illustrative: surrounding matter not assumed).
    for j in range(84):
        ang=j*TAU/84+t*(.8+(.3*j%7)/8)
        rad=142+33*math.sin(j*4.72+t*.65)
        xx=int(cx+rad*math.cos(ang));yy=int(cy+rad*.55*math.sin(ang))
        light=.25+.75*math.sin(j*13.3+t*2)**2
        bright=int(progress*light*239)
        cv2.circle(dst,(xx,yy),1 if j%3 else 2,(bright,int(bright*.69),int(bright*.38)),-1,cv2.LINE_AA)
    halo=np.zeros((H//4,W//4,3),np.uint8)
    cv2.ellipse(halo,(cx//4,cy//4),(44,23),-22,0,360,(80,105,254),5,cv2.LINE_AA)
    cv2.ellipse(halo,(cx//4,cy//4),(43,23),-22,28,175,(235,170,69),5,cv2.LINE_AA)
    halo=cv2.resize(cv2.GaussianBlur(halo,(0,0),6),(W,H),interpolation=cv2.INTER_LINEAR)
    dst[:]=cv2.addWeighted(dst,1,halo,progress*.69,0)
    cv2.circle(dst,(cx,cy),round(128*progress),(0,1,5),-1,cv2.LINE_AA)
    cv2.circle(dst,(cx,cy),round(129*progress),(92,140,255),2,cv2.LINE_AA)
    cv2.ellipse(dst,(cx,cy),(175,90),-22,198,357,(255,180,91),7,cv2.LINE_AA)
    cv2.ellipse(dst,(cx,cy),(175,90),-22,5,154,(143,171,255),4,cv2.LINE_AA)
    # Crossing light grazing the horizon.
    cv2.line(dst,(cx-132,cy-10),(cx-65,cy-2),(114,179,247),2,cv2.LINE_AA)
    cv2.line(dst,(cx+65,cy+3),(cx+142,cy+15),(230,169,98),2,cv2.LINE_AA)

def event_particles(dst,t):
    # Every 4 seconds a radial compression impulse travels outward.
    idx=int(t/4);phase=t%4
    if phase>1.85: return
    radius=60+phase*380
    alpha=(1-phase/1.85)**1.5
    if idx==0: return
    c=EVENTS[idx]['color']
    for j in range(64):
        ang=j*TAU/64+idx*.17
        rr=radius*(.82+.3*math.sin(j*9.44+idx)**2)
        x=int(360+rr*math.cos(ang))
        y=int(675+rr*.84*math.sin(ang))
        if 0<=x<W and 0<=y<H:
            m=int(alpha*(180+75*math.sin(j*3)**2))
            cv2.circle(dst,(x,y),1+(j%9==0),tuple(int(v*m/255) for v in c),-1,cv2.LINE_AA)
    outline=tuple(int(cj*alpha*.50) for cj in c)
    cv2.ellipse(dst,(360,675),(int(radius),int(radius*.84)),0,0,360,outline,1,cv2.LINE_AA)

def draw_sphere(dst,t,heat,compression):
    cx=int(365+9*math.sin(t*.28));cy=int(676+15*math.sin(t*.34))
    cycle=t%4
    # Each four-second phrase visibly crushes the sphere, then the virtual camera
    # pulls closer before the next beat. Both halves join without a frame jump.
    compression_zoom=smooth(cycle/2.95)
    rebound=smooth((cycle-2.95)/1.05)
    r=round(256-86*compression_zoom+86*rebound + 4*math.sin(t*.75))
    rings_and_glow(dst,t,cx,cy,r,heat,compression)
    sprite=draw_earth_sprite(t,heat)
    sprite=cv2.resize(sprite,(2*r,2*r),interpolation=cv2.INTER_LINEAR)
    # Black hole is visually interpolated only in closing four seconds.
    p=smooth((t-26.5)/2.2)
    overlay(dst,sprite,cx-r,cy-r,1-p)
    if p>0:
        blackhole(dst,t,cx,cy,p)
        if t>29.25:
            # The Moon keeps orbiting a fixed Earth-mass gravitational source.
            a=(t-29.25)*.69+.15
            mx=int(cx+263*math.cos(a)); my=int(cy+124*math.sin(a))
            cv2.circle(dst,(mx,my),11,(107,130,154),-1,cv2.LINE_AA)
            cv2.circle(dst,(mx-4,my-5),4,(189,203,207),-1,cv2.LINE_AA)
            cv2.circle(dst,(mx,my),12,(190,210,229),1,cv2.LINE_AA)
    # Volumetric rim highlights and moving arc glints.
    if p<.87:
        c=(49,122,214) if heat<.48 else (233,97,71)
        cv2.ellipse(dst,(cx,cy),(r+5,r+5),t*1.9,206,321,tuple(int(z*(1-p)) for z in c),3,cv2.LINE_AA)
    return cx,cy,r

def draw_hud(dst,f,t):
    idx=stage(f);ev=EVENTS[idx]
    accent=ev['color']
    # Gradient banner via dark translucent rectangle.
    cv2.rectangle(dst,(0,0),(W,235),(5,9,22),-1)
    center_text(dst,'SQUEEZE THE EARTH',41,WHITE,360,66,'hero')
    center_text(dst,'INTO A BLACK HOLE?',35,MINT,360,120,'bold')
    center_text(dst,'ONE PLANET. THE SAME MASS.',17,(139,158,181),360,174,'med')
    x1,x2=65,W-65;yy=218
    cv2.line(dst,(x1,yy),(x2,yy),(59,76,100),3,cv2.LINE_AA)
    fraction=f/(NFR-1)
    right=round(x1+(x2-x1)*fraction)
    cv2.line(dst,(x1,yy),(right,yy),accent,4,cv2.LINE_AA)
    for j,e in enumerate(EVENTS):
        x=round(x1+(x2-x1)*e['frame']/NFR)
        cv2.circle(dst,(x,yy),2 if j>idx else 4,(115,128,146) if j>idx else accent,-1,cv2.LINE_AA)
    cv2.circle(dst,(right,yy),6,WHITE,-1,cv2.LINE_AA)
    # Dynamic radius and large stage counter.
    value=format_size(radius_real(f))
    center_text(dst,'RADIUS',21,(152,171,188),360,270,'med')
    center_text(dst,value,61,WHITE,360,340,'hero')
    pct=f*100/(NFR-1)
    if f>=EVENTS[-1]['frame']:
        center_text(dst,'EVENT HORIZON',21,YELLOW,360,389,'bold')
    else:
        center_text(dst,f'{pct:.0f}% COMPRESSED ON THIS JOURNEY',16,accent,360,394,'med')
    # Scene-bottom information panel.
    cv2.rectangle(dst,(0,1086),(W,H),(7,13,27),-1)
    cv2.line(dst,(66,1087),(W-66,1087),(38,62,83),1,cv2.LINE_AA)
    if idx!=7:
        center_text(dst,ev['label'],31,accent,360,1126,'hero')
        center_text(dst,ev['detail'],19,WHITE,360,1171,'med')
    else:
        center_text(dst,'EARTH-MASS BLACK HOLE',27,YELLOW,360,1125,'hero')
        center_text(dst,'GRAVITY FAR AWAY: UNCHANGED',19,WHITE,360,1169,'med')
    center_text(dst,'THOUGHT EXPERIMENT • ARTISTIC SCALE',12,(104,122,146),360,1233,'med')
    # Stage marker at left of scene.
    if idx>0:
        comparison(dst,idx,t,accent)

def draw(f):
    t=f/FPS
    idx=stage(f)
    heat=smooth((t-5.5)/13.0)
    stage_react=1-smooth((t%4)/.6)
    d=background(t,f)
    event_particles(d,t)
    # Movement speed and perspective make story one continuous animated scene.
    if t>25.9:
        heat=min(1,heat)
    draw_sphere(d,t,heat,smooth((t-25)/4))
    draw_hud(d,f,t)
    # Vertical thin lights across rotating scene.
    if f%120<8 and f>=120:
        flash=int(16*(1-(f%120)/8))
        d=np.minimum(d.astype(np.uint16)+flash,255).astype(np.uint8)
    return d

# Original cinematic score; sound onsets at exactly the video event frames.
def gen_kick():
    t=np.arange(int(SR*.42))/SR
    phase=TAU*(49*t+87*(1-np.exp(-42*t))/42)
    return (.87*np.sin(phase)+.13*np.sin(phase*2.02))*(1-np.exp(-t*900))*np.exp(-t*11)

def gen_snare(rng):
    t=np.arange(int(SR*.26))/SR
    n=rng.standard_normal(len(t))
    n=sosfilt(butter(2,550/(SR/2),btype='highpass',output='sos'),n)
    return (.65*n+.27*np.sin(TAU*184*t))*np.exp(-t*19)*(1-np.exp(-t*250))

def gen_hat(rng,openhat=False):
    t=np.arange(int(SR*(.24 if openhat else .085)))/SR
    n=sosfilt(butter(2,5200/(SR/2),btype='highpass',output='sos'),rng.standard_normal(len(t)))
    return n*np.exp(-t*(15 if openhat else 82))*(1-np.exp(-t*900))

def synth_note(midi,seconds,kind='pluck'):
    t=np.arange(round(SR*seconds))/SR
    hz=440*2**((midi-69)/12)
    phase=TAU*hz*t
    tri=2/np.pi*np.arcsin(np.sin(phase))
    if kind=='pluck':
        s=(.64*tri+.21*np.sin(2*phase+.19)+.09*np.sin(3.01*phase)+.06*np.sin(4.01*phase))
        env=(1-np.exp(-t*550))*np.exp(-t*6.7)
    elif kind=='bell':
        s=.54*np.sin(phase+ .7*np.exp(-3*t)*np.sin(phase*2.016))
        s+=.24*np.sin(2.007*phase+.13)*np.exp(-1.7*t)
        s+=.13*np.sin(3.012*phase)*np.exp(-7*t)
        s+=.09*np.sin(5.072*phase+1.8)*np.exp(-17*t)
        env=(1-np.exp(-t*300))*np.exp(-t*2.8)
    else:
        s=.61*np.sin(phase)+.25*tri+.14*np.sin(2.006*phase+.35)
        env=(1-np.exp(-t*18))*np.minimum(1,(seconds-t)/.65)
    return s*env

def lay(buffer,mono,at,gain=1,pan=0):
    start=round(at*SR)
    if start<0:
        mono=mono[-start:];start=0
    end=min(start+len(mono),len(buffer))
    if start>=end:return
    lr=math.pi*(pan+1)/4
    buffer[start:end,0]+=mono[:end-start]*gain*math.cos(lr)
    buffer[start:end,1]+=mono[:end-start]*gain*math.sin(lr)

def filtered_noise(rng,dur,lo=200,hi=9000):
    n=round(dur*SR)
    x=rng.standard_normal(n)
    sos=butter(3,[max(30,lo)/(SR/2),min(SR/2-500,hi)/(SR/2)],btype='bandpass',output='sos')
    v=sosfilt(sos,x)
    return v / max(np.std(v)*3,.1)

def event_hit(rng,idx):
    # Layered branded earcon (kick/thunder, stereo crack, pitched chime).
    duration=1.65
    t=np.arange(round(SR*duration))/SR
    d=np.zeros_like(t)
    f=(178+37*idx)
    ph=TAU*(f*t+ (320+44*idx)*t*t)
    d+=.28*np.sin(ph)*np.exp(-t*19)*(1-np.exp(-t*400))
    crack=filtered_noise(rng,.35,1700+idx*90,12500)
    d[:len(crack)]+=.72*crack*np.exp(-np.arange(len(crack))/SR*(22+idx))
    ring=np.sin(TAU*(42+idx*3)*t +1.8*np.exp(-t*3)*np.sin(TAU*380*t))
    d+=.56*ring*np.exp(-t*(5.2 if idx<7 else 2.4))
    if idx==7:
        t2=np.arange(round(SR*1.5))/SR
        d[:len(t2)]+=.29*np.sin(TAU*(96*t2-35*t2*t2))*np.exp(-t2*2.8)
    return d

def music():
    rng=np.random.default_rng(111425)
    mix=np.zeros((NS,2),np.float32)
    dt=60/120
    progress_chords=[(42,49,54,57),(38,45,50,54),(45,52,57,61),(40,47,52,56),
                     (42,49,54,57),(38,45,50,54),(33,40,45,52),(30,42,49,54)]
    # Breathing stereo atmospheric harmony, slightly detuned analog oscillators.
    for bar in range(16):
        at=bar*2
        i=min(7,bar//2)
        for k,note in enumerate(progress_chords[i]):
            t=np.arange(round(2.7*SR))/SR
            f=440*2**((note-69)/12)
            phase=TAU*f*t
            base=(.62*np.sin(phase+.09*np.sin(TAU*(.17+k*.07)*t))+.17*np.sin(phase*2.001)+.21*np.sin(phase*.499))
            env=np.minimum(1,t/.38)*np.minimum(1,(2.7-t)/.83)
            g=(.027,.021,.012,.008)[k]*(.75+min(bar,9)*.033)
            lay(mix,base*env,at,g,(-.58 if k%2 else .58))
    # Exact musical grid: sixteenths for high end, 4/4 percussion with stops and drops.
    kick=gen_kick();snare=gen_snare(rng);hat=gen_hat(rng);openh=gen_hat(rng,True)
    bass_cache={}
    for step in range(128):
        at=step*.25
        i=min(7,int(at/4)); sub=step%8
        # Drum rolls accelerate approaching final transformation.
        if (step%2==0 or (at>24 and step%2==1)) and not (27.45<at<28):
            h=hat if (step%2==0) else openh
            lay(mix,h,at,.019 if at<12 else .024,pan=.42 if step%4 else -.42)
        if step%4==0 and at<31.1 and not(27.35<at<28):
            lay(mix,kick,at,.23 if at<12 else (.28 if at<24 else .37),pan=0)
        if step%8==4 and at<31 and not (27.35<at<28):
            lay(mix,snare,at,.045 if at<12 else .056,pan=.03)
        if step%2==1 and 6<at<31.2:
            # stereo shuffled hi hats
            lay(mix,hat,at+.012,.014,pan=math.sin(step*.9)*.62)
        if step%2==0 and 4<=at<29.9:
            note=progress_chords[i][(0,2,1,3,2,1,3,1)[(step//2)%8]]+24
            sound=synth_note(note,.68,'pluck')
            lay(mix,sound,at,.049 if at<20 else .062,pan=math.sin(step*1.74)*.47)
            lay(mix,sound,at+.179,.014,pan=-math.sin(step*1.74)*.47)
        if step%4==0 and at<31:
            root=progress_chords[i][0]
            if root not in bass_cache:
                s=synth_note(root-12,.47,'soft')
                bass_cache[root]=s
            lay(mix,bass_cache[root],at,.079 if at<16 else .100)
    # Cinematic arrangement rather than a constant loop: evolving loudness and
    # a near-silent 600-ms vacuum immediately before the black-hole reveal.
    bed_clock=np.arange(NS,dtype=np.float32)/SR
    automation=np.interp(bed_clock,
        [0,1,3.7,4.15,5.5,7.8,8.35,11.7,12.5,15.8,16.35,
         19.8,20.45,23.7,24.35,26.9,27.22,27.5,27.90,
         28.05,28.7,29.5,31.0,31.95],
        [.55,.64,.79,.67,.83,.96,.85,1.11,1.14,.90,.58,
         .81,.94,.98,1.08,1.14,.67,.16,.07,
         .64,1.24,1.05,.91,.56]).astype(np.float32)
    mix*=automation[:,None]

    # Active rises into each scene change, with side-to-side motion.
    for i,e in enumerate(EVENTS):
        at=e['frame']/FPS
        if i:
            rise=.76 if i<7 else 1.26
            t=np.arange(round(rise*SR))/SR
            n=filtered_noise(rng,rise,600 if i<7 else 130,8000 if i<7 else 14000)
            env=((t/rise)**2.0)*np.minimum(1,(rise-t)/.085)
            sweep=.35*np.sin(TAU*(170*t+(i*46+330)*t*t))
            lay(mix,(n+.35*sweep)*env,at-rise,.10 if i<7 else .20,pan=(-1)**i*.53)
        ear=event_hit(rng,i)
        lay(mix,ear,at,.18 if i<6 else (.29 if i==6 else .46),pan=(-1)**i*.26)
        if i in (1,3,5,7):
            bell=synth_note(e['note']+24,1.8,'bell')
            lay(mix,bell,at,.093 if i<7 else .18,pan=.23)
            lay(mix,bell,at+.215,.032,pan=-.47)
        # Exact counter synchronization: short 50ms tick every major stage and an answer note.
        t=np.arange(round(SR*.09))/SR
        key=np.sin(TAU*(960+140*i)*t)*np.exp(-t*80)
        lay(mix,key,at,.19,pan=.14)
    # Final three seconds have an intense sub/air pulse and echo decay.
    t=np.arange(round(3.65*SR))/SR
    low=np.sin(TAU*(48*t+8*np.sin(t*4.2))) *np.exp(-t*.85)
    air=filtered_noise(rng,len(t)/SR,80,3300)
    lay(mix,low,28,.195)
    lay(mix,air*np.exp(-t*1.13)*.26,28,.11,pan=-.3)
    # Multi-tap diffused echoes with crossfeed; restrained wet balance.
    dry=mix.copy()
    for delay,gain in ((.041,.061),(.118,.044),(.229,.036),(.377,.025)):
        n=int(delay*SR)
        mix[n:]+=dry[:-n,::-1]*gain
    # Crest factor control with soft tape saturation and headroom.
    mix=np.tanh(mix*1.24)/1.24
    # Master dynamic automation: rhythmic duck around each 4-second cinematic hit.
    tt=np.arange(NS)/SR
    duck=np.ones(NS,np.float32)
    for e in EVENTS:
        at=e['frame']/FPS
        if at>0:
            v=tt-at
            duck-=.22*np.exp(-(v/.21)**2).astype(np.float32)
    mix*=duck[:,None]
    mix[:round(SR*.045)]*=np.linspace(0,1,round(SR*.045))[:,None]
    end=round(SR*.68)
    mix[-end:]*=np.linspace(1,0,end)[:,None]
    peak=np.max(np.abs(mix))
    mix=(mix/max(peak,1e-7)*.87).astype(np.float32)
    path=DIR/'original-score.wav'
    pcm=np.rint(np.clip(mix,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as f:
        f.setparams((2,2,SR,NS,'NONE','not compressed'))
        f.writeframes(pcm.tobytes())
    return path

def validate(path):
    meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-show_chapters','-of','json',str(path)]))
    v=next(s for s in meta['streams'] if s['codec_type']=='video')
    a=next(s for s in meta['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(1080,1920)
    assert v['avg_frame_rate']=='30/1'
    assert v['codec_name']=='h264' and a['codec_name']=='aac'
    assert int(v['nb_frames'])==NFR
    assert abs(float(meta['format']['duration'])-32)<.08
    assert not meta.get('chapters')
    assert set(meta['format'].get('tags',{})) <= {'major_brand','minor_version','compatible_brands','encoder'}
    for s in meta['streams']:
        assert set(s.get('tags',{})) <= {'language','handler_name','vendor_id','encoder'}
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
    # The one exact clock: every stage starts on frame 120*i and soundtrack sample 192000*i.
    assert SPF*120==4*SR
    report={'video':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'frames':NFR,'duration':32,'resolution':'1080x1920','fps':FPS,
            'sound':'stereo AAC 224k, original procedural 120 BPM score and synchronized design',
            'syncClocks':[{'stage':e['label'],'frame':e['frame'],'videoSeconds':e['frame']/FPS,'audioSample':e['frame']*SPF} for e in EVENTS],
            'qa':'passed, full video+audio decode, no optional metadata'}
    (DIR/'qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    return report

def make_contact():
    frames=[0,102,130,245,360,495,620,745,855,925]
    images=[]
    for f in frames:
        frame=draw(f)
        path=DIR/f'preview_{f:04d}.jpg'
        cv2.imwrite(str(path),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,92])
        images.append(cv2.resize(frame,(216,384)))
    contact=np.zeros((2*384,5*216,3),np.uint8)
    for i,img in enumerate(images):
        y=(i//5)*384;x=i%5*216
        contact[y:y+384,x:x+216]=img
    Image.fromarray(contact).save(DIR/'contact.jpg',quality=92)

def render():
    import time
    start_clock=time.perf_counter()
    wav=music()
    print('Audio generated in',round(time.perf_counter()-start_clock,2),'s',flush=True)
    result=DIR/'earth-into-black-hole.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
         '-r',str(FPS),'-i','pipe:0','-i',str(wav),'-map','0:v:0','-map','1:a:0',
         '-vf','scale=1080:1920:flags=bicubic',
         '-c:v','libx264','-preset','ultrafast','-crf','18','-threads','4',
         '-pix_fmt','yuv420p','-maxrate','14M','-bufsize','16M',
         '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
         '-c:a','aac','-b:a','224k','-ar',str(SR),
         '-af','loudnorm=I=-13.8:TP=-1.6:LRA=9,alimiter=limit=0.76:level=0',
         '-metadata','title=','-map_metadata','-1','-map_metadata:s','-1','-map_chapters','-1',
         '-movflags','+faststart',str(result)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE,bufsize=1<<23)
    try:
        for f in range(NFR):
            if f%120==0:print(f'frames {f}/{NFR}; wall {time.perf_counter()-start_clock:.1f}s',flush=True)
            process.stdin.write(draw(f).tobytes())
    except BrokenPipeError:
        raise RuntimeError('ffmpeg encoder crashed')
    finally:
        process.stdin.close()
        code=process.wait()
        if code:
            raise RuntimeError(f'ffmpeg return {code}')
    return validate(result)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true')
    a=ap.parse_args()
    make_contact()
    if not a.preview:
        print(render(),flush=True)