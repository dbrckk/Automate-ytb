#!/usr/bin/env python3
"""Tsunami: The Invisible Wave. Entirely original frame animation & sound, no asset sourcing.
Science explanation: NOAA JetStream tsunami propagation, illustrative heights/strata.
"""
import math, os, sys, json, subprocess, wave, hashlib
from pathlib import Path
from functools import lru_cache
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H,FPS,NFR=540,960,30,900
SR=48000; SPF=SR//FPS; DURATION=NFR/FPS
OUT=Path(os.environ.get('AUTOMATE_YTB_OUT','build/tsunami'))
OUT.mkdir(parents=True,exist_ok=True)
OUTMP4=OUT/'tsunami-the-invisible-wave.mp4'
PREVIEW=OUT/'tsunami_contact.png'
TAU=math.tau
CUES=[(0.52,'FAULT SHIFT',190), (3.08,'OCEAN DISPLACED',360), (7.00,'OPEN OCEAN',483),
      (12.60,'CONTINENTAL SHELF',255),(18.00,'SHOALING',716),(23.10,'NEAR SHORE',423),
      (25.67,'SURGE',309),(28.33,'ENERGY REVEAL',838)]
CUE_FR=[round(c[0]*FPS) for c in CUES]
RNG=np.random.default_rng(91926)
FONT='/usr/share/fonts/truetype/lato/Lato-Heavy.ttf'
FONT2='/usr/share/fonts/truetype/lato/Lato-Bold.ttf'
if not Path(FONT).exists(): FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def clamp(x,a=0.,b=1.): return max(a,min(b,x))
def ease(x): x=clamp(x);return x*x*(3-2*x)
def blend_color(a,b,f):return tuple(int(a[i]*(1-f)+b[i]*f) for i in range(3))
def create_sky():
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    radial=np.exp(-(((xx-430)/310)**2+((yy-265)/390)**2)*1.8)
    sky=np.zeros((H,W,3),np.float32)
    for k,(base,g) in enumerate([(9,13),(14,24),(32,30)]):
        sky[:,:,k]=base+g*(1-yy/H)+radial*([13,17,24][k])
    # Spectral noise and photographic atmospheric falloff
    n=np.random.default_rng(777).standard_normal((120,68)).astype(np.float32)
    n=cv2.resize(n,(W,H),interpolation=cv2.INTER_CUBIC)
    sky+=n[:,:,None]*.9
    return np.clip(sky,0,255).astype('uint8')
SKY=create_sky()
XS=np.arange(W,dtype=np.float32)
Y=np.arange(H,dtype=np.float32)[:,None]

# Static full-screen prepared textures, animated with scroll and parallax lighting.
rr=np.random.default_rng(616)
WNOISE=rr.standard_normal((H,W)).astype(np.float32)
WNOISE=cv2.GaussianBlur(WNOISE,(0,0),2.0)
WNOISE/=max(.01,WNOISE.std())
rock_noise=rr.standard_normal((H//6,W//6)).astype(np.float32)
rock_noise=cv2.resize(rock_noise,(W,H),interpolation=cv2.INTER_CUBIC)
rock_noise2=rr.standard_normal((H//2,W//4)).astype(np.float32)
rock_noise2=cv2.resize(rock_noise2,(W,H),interpolation=cv2.INTER_CUBIC)
rock_noise=rock_noise*.68+rock_noise2*.19
DEBRIS=rr.uniform([0,0,.25,0],[W,H,1,TAU],size=(152,4))
STARS=rr.uniform([0,0,.25],[W,440,1],size=(105,3))
FOAM=rr.uniform([0,0,.2,.5],[1,1,1,1],size=(68,4))

@lru_cache(maxsize=400)
def glyph(txt,size,color,width=520,tracking=0):
    font=ImageFont.truetype(FONT,int(size))
    while font.getlength(txt)>width and size>10:
        size-=1;font=ImageFont.truetype(FONT,int(size))
    ww=int(font.getlength(txt))+8
    im=Image.new('RGBA',(ww,int(size)*2+4),(0,0,0,0))
    dd=ImageDraw.Draw(im)
    dd.text((ww/2,(int(size)*2+4)/2-2),txt,anchor='mm',font=font,fill=tuple(color)+(255,),stroke_width=1,stroke_fill=(9,17,31,235))
    return np.array(im)

def overlay(dst,img,x,y,opacity=1):
    if opacity<.005:return
    h,w=img.shape[:2];x,y=round(x),round(y)
    x0=max(0,x);y0=max(0,y);x1=min(W,x+w);y1=min(H,y+h)
    if x1<=x0 or y1<=y0:return
    src=img[y0-y:y1-y,x0-x:x1-x]
    alpha=(src[:,:,3:4].astype(np.float32)*(opacity/255.))
    dest=dst[y0:y1,x0:x1]
    dest[:]=(dest*(1-alpha)+src[:,:,:3]*alpha).astype(np.uint8)

def txt(f,s,size,color,x,y,alpha=1,width=510):
    img=glyph(s,size,color,width)
    overlay(f,img,x-img.shape[1]/2,y-img.shape[0]/2,alpha)

def polygon(f,verts,color): cv2.fillPoly(f,[np.array(verts,np.int32)],color,cv2.LINE_AA)
def polyl(f,verts,color,w=2): cv2.polylines(f,[np.asarray(verts,np.int32)],False,color,w,cv2.LINE_AA)

def parse_phase(t):
    # Long camera trajectory followed by a punchy ending.
    return ease((t-3.12)/22.12)

def bathymetry(p):
    # Seafloor rises progressively on the approach to the coast.
    sweep=XS-(840-530*p)
    s=np.clip(sweep/270,0,1);s=s*s*(3-2*s)
    floor=817-268*s+9*np.sin(XS*.026-1.9*p)*s
    return floor.astype(np.int32)

def coast_x(p): return 760-395*p

def watery_surface(p,t):
    # Shoaling compresses wavelength, raises illustrative crest, changes camera proximity.
    origin=83+290*p
    sigma=211-145*p
    height=5+155*p**3.25
    body=np.exp(-((XS-origin)/sigma)**2)
    secondary= -.25*np.exp(-((XS-origin+sigma*1.5)/(sigma*.62))**2)
    ripple=1.1*np.sin(XS*.07+t*2.0)+.66*np.sin(XS*.147-t*3.7)
    ys=439+2.2*np.sin(t*.27)-height*(body+secondary)+ripple
    return ys.astype(np.int32)

def draw_clouds(f,t,p):
    # Multiplane wisps, no static stock imagery.
    for i in range(13):
        cx=int((84*i+55+17*math.sin(i*3.2)+t*(2+i*.14)*(1 if i%2 else -1))%(W+130)-65)
        cy=int(307-18*math.sin(i*.8)-i*14.0)
        r=(31+(i*9)%37,10+(i*3)%15)
        color=(15+i%4*2,30+i%4*3,44+i%5*3)
        cv2.ellipse(f,(cx,cy),r,5,0,360,color,-1,cv2.LINE_AA)
        cv2.ellipse(f,(cx-10,cy-5),(int(r[0]*.65),int(r[1]*.45)),5,0,360,(24,43,60),1,cv2.LINE_AA)
    # A distant sun halo and layered cloud rims give the sky cinematic depth.
    sunx=int(434+16*math.sin(t*.033));suny=262
    for radius,col in [(74,(16,40,57)),(56,(24,55,71)),(39,(35,71,88))]:
        cv2.circle(f,(sunx,suny),radius,col,-1,cv2.LINE_AA)
    cv2.circle(f,(sunx,suny),17,(91,155,158),-1,cv2.LINE_AA)
    cv2.circle(f,(sunx-5,suny-6),11,(139,181,169),-1,cv2.LINE_AA)
    # Distant silhouette mountains and coast form parallax and depth.
    mountain=[(0,420),(0,370),(43,375),(81,358),(124,381),(182,345),(218,379),(258,369),(306,388),(360,363),(423,390),(540,378),(540,445)]
    shift=int(t*.35+20*p)
    m=[(x-shift,y) for x,y in mountain]
    polygon(f,m,(21,45,63))
    polyl(f,m[1:-1],(41,75,91),1)
    for x,y,z in STARS:
        if y<310:
            gl=int(48+58*z+(math.sin(t*.7+x*.3)+1)*9)
            cv2.circle(f,(int(x),int(y)),1,(gl,gl,int(gl*1.14)), -1,cv2.LINE_AA)

def draw_plate(f,t,shift):
    if t>5.8:return
    w=ease((t-.5)/1.0)*(1-ease((t-4.9)/.9))
    # Two tectonic plates, epicenter and animated seismic wave arcs.
    q=int(5.7*math.sin(t*37)*math.exp(-max(t-.7,0)/1.3))
    fault_x=round(283-shift*.25)
    polyl(f,[(fault_x-38,832),(fault_x-8,884+q),(fault_x+17,897+q),(fault_x+52,951)],(254,132,66),3)
    for k in range(5):
        rr=60+((max(t-.52,0)*82+k*64)%370)
        a=max(0,1-rr/500)*w
        if a>.01:
            color=(int(55+120*a),int(73+76*a),int(80+55*a))
            cv2.ellipse(f,(fault_x,905),(int(rr),int(rr*.18)),0,180,355,color,2,cv2.LINE_AA)
    if .55<t<2.3:
        for i in range(28):
            rad=6+i*3.9+(t-.5)*24
            x=int(fault_x+math.cos(i*2.77+t*2)*rad)
            y=int(885+math.sin(i*2.77+t*2)*rad*.35)
            cv2.circle(f,(x,y),1+(i%5==0),(254,170+int(i%4*15),66),-1,cv2.LINE_AA)

def draw_ocean(f,t,p,floor,sy):
    # Polygons derive from live high-frequency surface and seafloor (not image panning).
    shore=coast_x(p)
    visible=(XS<shore+1).astype(np.bool_)
    above=np.maximum(0,430-Y)/530
    # draw rock base with procedural folded strata and inhomogeneous illumination
    rows=np.arange(H)[:,None]; floor_mask=rows>=floor[None,:]
    s=(rows + np.sin(XS[None,:]*.035+rock_noise*.07)*22).astype(np.float32)
    strata=.5+.5*np.cos(s*.063+rock_noise*.46)
    rock=np.zeros((H,W,3),np.float32)
    for k in range(3):
        rock[:,:,k]=[34,40,48][k]+strata*[18,22,20][k]+rock_noise*[6,7,8][k]
    # sediment bands and warm fracture glow below epicentre
    for y in range(675,H,35):
        draw_offset=math.sin(y*.025)*16
        line_y=(y+9*np.sin(XS*.033+draw_offset)).astype(np.int32)
        sel=(rows>=line_y[None,:]-1)&(rows<line_y[None,:]+1)&floor_mask
        rock[sel,:]=np.clip(rock[sel,:]+np.array([20,16,10]),0,255)
    f[floor_mask]=np.clip(rock[floor_mask],0,255).astype(np.uint8)
    draw_plate(f,t,20*p)
    # Water texture with bi-directional energy ribbons and caustic fold lighting.
    wmask=(rows>=sy[None,:])&(rows<floor[None,:])&(XS[None,:]<shore)
    ydist=(rows-sy[None,:]).astype(np.float32)
    z=np.clip(ydist/390,0,1)
    mod=.5+.5*np.sin(.013*rows+.021*XS[None,:]+t*1.8)
    caustics=np.cos(XS[None,:]*.048-ydist*.026+t*4.3+np.sin(ydist*.019+t*.7))
    faint=(caustics+.6*np.sin(XS[None,:]*.073+ydist*.018-t*2))*5.4*np.exp(-z*2.2)
    # Water follows a deep lighting gradient (warm shimmer at surface, cold abyss below).
    water=np.empty((H,W,3),np.uint8)
    base=(1-z)
    water[:,:,0]=np.clip(6+base*20+faint*.3+WNOISE*1.9,0,255)
    water[:,:,1]=np.clip(38+base*62+faint*.9+WNOISE*2.8,0,255)
    water[:,:,2]=np.clip(64+base*93+faint*1.3+WNOISE*2.6,0,255)
    f[wmask]=water[wmask]
    # Sub-surface angular streaks and light caustics animate with different depth rates.
    for i in range(17):
        gx=int((i*109+t*(9+i%3*4)-p*54)%(W+125)-50)
        gy=int(485+(i*83)%270+math.sin(t*.75+i)*11)
        if 0<gx<W and sy[gx]<gy<floor[gx]:
            length=(15+(i%4)*17)
            color=(29,105+(i%3)*8,146+(i%4)*9)
            cv2.line(f,(gx,gy),(min(W-1,gx+length),gy-6),color,1,cv2.LINE_AA)
    # Telltale sub-surface velocity streaks: 3 parallax depths.
    for plane in (0,1,2):
        phase=t*(1.6+plane*.9)+(p*14)
        for k in range(19):
            x0=int((k*91+plane*119-phase*28)%(W+260)-130)
            y0=int(465+plane*82+(k*11)%65+6*math.sin(t*.9+k))
            if x0<shore and 390<y0<900:
                color=(28+plane*6,78+plane*9,105+plane*14)
                cv2.line(f,(x0,y0),(x0+60+plane*14,y0-9),color,1,cv2.LINE_AA)
    # dynamic neon rim and spray computed from a complete wave field
    pts=np.column_stack((XS.astype(np.int32),sy))
    polyl(f,pts,(77,186,192),5)
    polyl(f,pts-[(0,2)],(174,248,227),2)
    polyl(f,pts+[(0,13)],(22,102,135),2)
    crest=int(np.argmin(sy));cy=int(sy[crest])
    halo=np.zeros((H,W,3),np.uint8)
    cv2.circle(halo,(crest,cy+5),round(24+40*p),(0,84,98),-1,cv2.LINE_AA)
    halo=cv2.GaussianBlur(halo,(0,0),16)
    f=cv2.addWeighted(f,1.0,halo,.46,0)
    # Crests burst upward at the near-shore phase and move on every frame.
    for k in range(66):
        phi=k*2.39996
        q=((t*.51+k*.173)%1)
        dx=(k%13-6)*3.2+math.sin(phi)*q*(13+86*p)
        dy=-q*(13+110*p**2)+q*q*40
        px=int(crest+dx);py=int(cy+dy)
        if p>.53 and 0<px<W and 0<py<H:
            col=(140+int(72*(1-q)),214+int(25*(1-q)),237)
            cv2.circle(f,(px,py),1+(k%17==0),col,-1,cv2.LINE_AA)
    for px,py,z,phase in DEBRIS:
        x=int((px+math.sin(phase+t*(.35+z))*32-t*(1+z)*9)%(W+80)-40)
        y=int((py+t*(8+z*13)+p*z*110)%H)
        if y>430 and x<shore-12 and y<floor[max(0,min(W-1,x))] and y>sy[max(0,min(W-1,x))]:
            alpha=int(62+int(80*z))
            cv2.circle(f,(x,y),1+(z>.86),(alpha//3,alpha,alpha+13),-1,cv2.LINE_AA)
    # Fish schools, weighted by camera depth, move independently from the ocean layers.
    visibility=(1-ease((t-13)/6))*ease((t-2)/2)
    for group in range(3):
        offset=group*32
        for k in range(16):
            dx=int(((group*205+k*39+t*(-13-3*group))%(W+110))-50)
            dy=int(565+group*64+22*math.sin(k*.5+t*.35+group))
            if dx<=0 or dx>=W-1 or not sy[dx]+16<dy<floor[dx]-15:continue
            body=(int(24+65*visibility),int(68+69*visibility),int(91+69*visibility))
            r=2+(k%5==0)
            polygon(f,[(dx-3*r,dy),(dx,dy-r),(dx+2*r,dy),(dx,dy+r)],body)
            polygon(f,[(dx-3*r,dy),(dx-5*r,dy-2*r),(dx-5*r,dy+2*r)],body)
    # Near-coast current spirals show the energy rushing into a shorter wavelength.
    if p>.55:
        crest=int(np.argmin(sy))
        for i in range(9):
            cy=int(sy[crest])+30+i*13
            rx=int((66-i*4)*p)
            pts=[(crest+int(rx*math.cos(a+t*.10+i*.16)),cy+int((11+i*2)*math.sin(a)))
                 for a in np.linspace(.15,math.pi*1.1,21)]
            polyl(f,pts,(42+i*3,143+i*5,156+i*4),1)
    return f

def draw_boat(f,t,p,sy):
    life=ease((t-5.4)/1.15)*(1-ease((t-15)/1.3))
    if life<=.01:return
    x=int(376-12*p-13*math.sin(t*.4));y=int(sy[min(W-1,x)]-7)
    # hull, deck, cabin, antenna and reflected navigation light
    h=np.array([(x-42,y-6),(x+41,y-6),(x+26,y+16),(x-31,y+15)],np.int32)
    polygon(f,h,(19,46,63));polyl(f,h,(155,210,210),2)
    polygon(f,[(x-23,y-22),(x+13,y-22),(x+21,y-6),(x-26,y-6)],(185,208,195))
    for xx in range(x-18,x+17,11): cv2.rectangle(f,(xx,y-17),(xx+7,y-10),(44,106,143),-1)
    cv2.line(f,(x+6,y-26),(x+6,y-47),(212,221,214),2,cv2.LINE_AA)
    cv2.line(f,(x+6,y-45),(x+21,y-39),(177,190,175),1,cv2.LINE_AA)
    cv2.circle(f,(x+21,y-39),2,(255,146,70),-1,cv2.LINE_AA)
    polyl(f,[(x-48,y+6),(x-66,y+11),(x-81,y+8)],(73,178,185),2)
    txt(f,'SHIP BARELY NOTICES',18,(213,246,231),W//2,662,life)

def draw_city(f,t,p,sy):
    shore=coast_x(p)
    alpha=ease((p-.64)/.24)
    if alpha<=.001:return
    skyline=int(shore)
    # Land comes into view as the follow-camera crosses the shelf.
    land=np.array([(skyline,428),(540,420),(540,960),(skyline-32,960),(skyline-4,694),(skyline+3,514)],np.int32)
    polygon(f,land,(80,84,76)); polyl(f,land[:3],(183,158,100),3)
    # long warm coastal boulevard and beach layers
    polygon(f,[(skyline,490),(540,446),(540,510),(skyline+12,559)],(134,120,86))
    cv2.line(f,(skyline+3,479),(W,434),(231,207,157),2,cv2.LINE_AA)
    # Silhouettes with real depth windows, roofs and lampposts.
    for j in range(4):
        bx=int(skyline+22+j*73)
        if bx>W+60:continue
        top=int(346-(j%2)*27+(j==2)*12)
        width=38+(j%2)*14
        polygon(f,[(bx,top+11),(bx+width//2,top-8),(bx+width,top+11),(bx+width,468)],(31+j*5,49+j*4,59+j*4))
        polyl(f,[(bx,top+11),(bx+width//2,top-8),(bx+width,top+11)],(126,151,150),2)
        for wy in range(top+36,450,17):
            for wx in range(bx+7,bx+width-4,14):
                color=(228,174,91) if (wx+wy)//7%4 else (78,142,158)
                cv2.rectangle(f,(wx,wy),(wx+6,wy+9),color,-1)
        cv2.line(f,(bx+width+4,439),(bx+width+4,410),(76,86,91),2,cv2.LINE_AA)
        cv2.circle(f,(bx+width+4,409),4,(251,194,125),-1,cv2.LINE_AA)
    # flood surge overlays city at the moment wave reaches the coast.
    surge=ease((t-24.1)/2.0)
    if surge>.01:
        xedge=int(skyline+65*surge)
        level=int(456-85*surge+12*math.sin(t*2.7))
        mask=np.zeros((H,W),np.uint8)
        cv2.fillPoly(mask,[np.array([(skyline-65,535),(xedge,level),(W,level+18),(W,960),(skyline-65,960)],np.int32)],255)
        wash=np.array((19+int(20*surge),124+int(13*surge),151+int(31*surge)),np.uint8)
        f[mask>0]=(f[mask>0].astype(np.float32)*.26+wash*.74).astype(np.uint8)
        # Moving contours and refractive-looking foam atop the flood, not flat fill.
        for yy in range(level+23,580,17):
            xx=np.arange(max(0,xedge-10),W,11)
            if len(xx):
                zz=yy+3*np.sin(xx*.052-t*4.1)+3*np.sin(xx*.097+t*3.1)
                pts=np.column_stack((xx,zz)).astype(np.int32)
                polyl(f,pts,(57,159+(yy%3)*8,178),1)
        cv2.line(f,(xedge,level),(W,level+18),(193,252,242),4,cv2.LINE_AA)
        for k in range(36):
            a=k*2.21
            r=18+int((t*37+k*17)%110)
            fx=int(xedge+math.cos(a)*r*.6)
            fy=int(level+math.sin(a)*r*.3-15*surge)
            if 0<=fx<W and 0<=fy<H:
                cv2.circle(f,(fx,fy),1+(k%7==0),(148,229,230),-1,cv2.LINE_AA)

def draw_logo(f,t,p):
    # Pinned editorial composition—does not obscure video motion.
    gradient=np.zeros_like(f)
    for y in range(176):
        opacity=(1-y/200)**2
        gradient[y,:]=(8,14,29)
    alpha=np.clip((1-np.arange(195)/195)**1.4,0,1)[:,None,None]*.92
    f[:195]=(gradient[:195]*alpha+f[:195]*(1-alpha)).astype(np.uint8)
    txt(f,'THE WAVE',39,(247,248,244),270,64)
    txt(f,"YOU CAN'T SEE",45,(241,244,234),270,111)
    cv2.line(f,(46,174),(494,174),(70,81,106),2,cv2.LINE_AA)
    cv2.line(f,(46,174),(int(46+448*p),174),(84,229,194),4,cv2.LINE_AA)
    cv2.circle(f,(int(46+448*p),174),4,(247,221,149),-1,cv2.LINE_AA)
    txt(f,'DEEP OCEAN',14,(181,202,209),96,203)
    txt(f,'COAST',14,(181,202,209),464,203)
    d=4000*(10/4000)**p
    sp=3.6*math.sqrt(9.81*d)
    txt(f,'WATER DEPTH',17,(140,185,192),140,250)
    txt(f,f'{d:,.0f} m',30,(251,219,145),143,290)
    txt(f,'WAVE SPEED',17,(140,185,192),394,250)
    txt(f,f'{sp:.0f} km/h',30,(118,249,214),398,290)
    label='EARTHQUAKE' if t<3.7 else ('ALMOST INVISIBLE' if t<12 else ('THE WAVE SLOWS' if t<18.7 else ('THE WATER RISES' if t<25.7 else 'THE COAST FLOODS')))
    txt(f,label,22,(251,241,218),270,764)
    txt(f,'As water gets shallower, the wave slows and grows.',16,(189,214,221),270,800,width=520)
    txt(f,'Illustrative animation · wave heights exaggerated',13,(139,162,168),270,918)
    if t>27:
        a=ease((t-27)/.65)
        txt(f,'NOT A NORMAL WAVE.',32,(248,223,163),270,847,a)


def draw_frame(frame):
    t=frame/FPS
    p=parse_phase(t)
    f=SKY.copy()
    draw_clouds(f,t,p)
    floor=bathymetry(p)
    sy=watery_surface(p,t)
    f=draw_ocean(f,t,p,floor,sy)
    if t<16:draw_boat(f,t,p,sy)
    draw_city(f,t,p,sy)
    # Cinematic wave crest / impact lens-shake in the water but stable UI.
    if any(abs(t-cue[0])<.18 for cue in CUES[1:]):
        impact=max(math.exp(-((t-c[0])/.085)**2) for c in CUES[1:])
        f=cv2.addWeighted(f,1-.13*impact,np.full_like(f,(62,110,119)),.13*impact,0)
    draw_logo(f,t,p)
    return f

def audio_envelope(t,attack=.005,release=.12):
    if not len(t):return t
    return np.clip(t/attack,0,1)*np.clip((t[-1]-t)/release,0,1)

def tone(n,sec):
    t=np.arange(round(sec*SR))/SR
    f=440*2**((n-69)/12)
    ang=TAU*f*t
    signal=.66*np.sin(ang+.21*np.sin(ang*2.012)*np.exp(-t*6))
    signal+=.21*np.sin(ang*2.003+.3)*np.exp(-t*4)
    signal+=.12*np.sin(ang*3.013+.3)*np.exp(-t*8)
    signal*=audio_envelope(t,.009,.10)*np.exp(-t*2.8)
    return signal

def noise(sec,low=500,high=9000):
    t=np.arange(round(sec*SR))/SR
    a=np.fft.rfft(RNG.standard_normal(len(t)))
    freq=np.fft.rfftfreq(len(t),1/SR)
    response=(1-np.exp(-(freq/(low+1))**2))*np.exp(-(freq/high)**4)
    s=np.fft.irfft(a*response,n=len(t))
    return s/max(3*s.std(),1e-6)

def percussion(sec=.5):
    t=np.arange(round(sec*SR))/SR
    phi=TAU*(48*t+90*(1-np.exp(-31*t))/31)
    return (np.sin(phi)+.2*np.sin(phi*2.034))*(1-np.exp(-240*t))*np.exp(-9*t)

def stereo_add(o,signal,when,gain=1.,pan=0):
    ix=round(when*SR);e=min(len(o),ix+len(signal))
    if ix<0 or ix>=e:return
    a=(pan+1)*math.pi/4
    o[ix:e,0]+=signal[:e-ix]*gain*math.cos(a)
    o[ix:e,1]+=signal[:e-ix]*gain*math.sin(a)

def accent(c,ix):
    t=np.arange(round(.115*SR))/SR
    pitch=c[2]
    phi=TAU*(pitch*t+(1650+ix*400)*t*t)
    return (.70*np.sin(phi)+.18*np.sin(phi*1.96)+.12*np.sin(phi*3.17))*audio_envelope(t,.0019,.035)*np.exp(-11*t)

def compose_sound():
    n=NFR*SPF
    mix=np.zeros((n,2),np.float64)
    bpm=122; step=60/bpm/2
    chordsets=[(38,45,53,57,62),(33,45,52,57,60),(41,48,53,57,64),(36,43,53,55,60),
               (34,41,50,53,60),(38,45,53,57,64)]
    starts=[0,3.07,7,12.6,18,23.1,30]
    # Layered drone swell and mid-range arpeggio track change in emotional intensity.
    for i,chord in enumerate(chordsets):
        st=starts[i];dt=starts[i+1]-st+.4
        tm=np.arange(round(dt*SR))/SR
        wd=audio_envelope(tm,.43,.5)
        for k,note in enumerate(chord):
            fo=440*2**((note-69)/12)
            for pan in (-.55,.55):
                phi=TAU*(fo+pan*.12)*tm
                sig=(np.sin(phi+.12*np.sin(tm*(.42+k*.04)))*.68+.21*np.sin(phi*2.006)+.09*np.sin(phi*3.007))
                stereo_add(mix,sig*wd,st,.050/(1+k*.24),pan)
    for i in range(math.ceil(DURATION/step)):
        st=i*step
        if st>DURATION-.1:continue
        ci=max(j for j in range(len(chordsets)) if st>=starts[j])
        notes=chordsets[ci]
        key=notes[(0,2,3,4,2,1,4,3)[i%8]]+24
        pan=math.sin(i*.89)*.45
        piano=tone(key,.66)
        scale=(.58 if st<5 else .9 if st<12 else 1.12 if st<23 else 1.39)
        if 25.55<st<26.35:scale*=.30
        stereo_add(mix,piano,st,.10*scale*(.7 if i%2 else 1),pan)
        stereo_add(mix,piano,st+.18,.024*scale,-pan)
        if i%4==0 and st>2.5:
            stereo_add(mix,percussion(.44),st,.12*(.85 if st<16 else 1.3))
        if i%2 and st>9.0:
            hats=noise(.12,2300,12000)
            tt=np.arange(len(hats))/SR
            stereo_add(mix,hats*np.exp(-18*tt)*audio_envelope(tt,.005,.07),st,.048*scale,pan*.75)
    # Continuous water movement spectral layer; rises towards the shore.
    tm=np.arange(n)/SR
    hush=noise(DURATION,55,2200)
    swell=.7+.3*np.sin(tm*1.42)**2
    gain=.016+(.075* np.clip((tm-11)/15,0,1)**2)
    stereo_add(mix,hush*swell*gain,0,1,-.32)
    # Underwater pulse sounds slow and sparse in deep ocean; later accelerating.
    for st in np.arange(4,27,.48):
        p=parse_phase(st);sig=noise(.17,400,5600)
        tt=np.arange(len(sig))/SR
        env=np.exp(-17*tt)*audio_envelope(tt,.008,.06)
        stereo_add(mix,sig*env,st,.038+.039*p,math.sin(st*1.6)*.54)
    # Each visual event has a unique exact-frame attack and different timbre.
    for i,c in enumerate(CUES):
        st=CUE_FR[i]/FPS
        mark=accent(c,i)
        pan=[.0,-.42,.35,-.35,.37,-.26,.12,0][i]
        stereo_add(mix,mark,st,[.37,.24,.20,.23,.27,.29,.43,.35][i],pan)
        stereo_add(mix,mark,st+.14,.055,-pan)
        if i in (0,1,4,6,7):stereo_add(mix,percussion(.8),st,.2 if i<5 else .34,pan*.5)
        dur=[1.1,1.1,.7,.75,.9,1.2,2.1,1.2][i]
        s=noise(dur, 150+70*i,4500+390*i)
        tt=np.arange(len(s))/SR
        ramp=audio_envelope(tt,.07,.4)*np.exp(-tt*(3.4 if i<6 else 1.8))
        stereo_add(mix,s*ramp,st,.16 if i<6 else .29,pan*.7)
        if i in (2,3,5,7):
            st2=st+.10
            stereo_add(mix,tone([64,71,76,81][(2,3,5,7).index(i)],1.12),st2,.18,pan)
    # Short quiet spot creates perceived loudness in the climactic surge.
    duck=np.interp(tm,[0,3.0,5.5,12,17.8,22.9,25.25,25.6,25.75,26.8,28.3,29.8],
                   [.77,.73,1,1.06,.94,1.16,1.09,.25,1.25,1.25,1.12,.64])
    mix*=duck[:,None]
    # Early echo and microstereo provide width; no copyrighted samples.
    for delta,g in ((.033,.051),(.097,.037),(.191,.024)):
        d=round(delta*SR)
        mix[d:]+=mix[:-d,::-1].copy()*g
    fadein=np.minimum(1,np.arange(n)/(SR*.018))
    fadeout=np.minimum(1,np.arange(n-1,-1,-1)/(SR*.57))
    mix*=(fadein*fadeout)[:,None]
    peak=np.max(np.abs(mix))
    if peak>.95:mix*=.95/peak
    audio=OUT/'tsunami-sound-original.wav'
    with wave.open(str(audio),'wb') as f:
        f.setparams((2,2,SR,len(mix),'NONE','not compressed'))
        f.writeframes(np.rint(mix*32767).astype('<i2').tobytes())
    return audio

def make_contact():
    times=[.7,4.3,7.9,12.9,18.7,24.1,26.2,29]
    rows=[]
    for t in times:
        f=draw_frame(round(t*FPS))
        im=Image.fromarray(f);im.thumbnail((216,384))
        rows.append((im,t))
    sheet=Image.new('RGB',(216*4,408*2),(10,14,22))
    dd=ImageDraw.Draw(sheet)
    for k,(im,t) in enumerate(rows):
        x=(k%4)*216;y=(k//4)*408
        sheet.paste(im,(x,y));dd.text((x+10,y+386),f'{t:.1f}s',fill=(220,233,241))
    sheet.save(PREVIEW)
    return PREVIEW

def make_video(wav):
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24',
             '-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(wav),'-map','0:v:0','-map','1:a:0',
             '-vf','scale=1080:1920:flags=lanczos','-r',str(FPS),'-c:v','libx264','-preset','fast','-crf','17',
             '-threads','4','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
             '-c:a','aac','-b:a','224k','-ar',str(SR),'-af','loudnorm=I=-14:TP=-1.5:LRA=10',
             '-map_metadata','-1','-map_metadata:s','-1','-map_chapters','-1','-movflags','+faststart',str(OUTMP4)]
    proc=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for fr in range(NFR):
            if fr%90==0:print('frame',fr,'/',NFR,flush=True)
            f=draw_frame(fr)
            proc.stdin.write(f.tobytes())
    except Exception:
        proc.stdin.close();proc.terminate();proc.wait();raise
    proc.stdin.close()
    code=proc.wait()
    if code:raise RuntimeError(f'FFmpeg failed: {code}')
    return OUTMP4

def verify():
    p=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-show_streams','-show_chapters','-of','json',str(OUTMP4)]))
    streams=p['streams'];vid=next(x for x in streams if x['codec_type']=='video');aud=next(x for x in streams if x['codec_type']=='audio')
    assert vid['width']==1080 and vid['height']==1920 and vid['avg_frame_rate']=='30/1'
    assert aud['codec_name']=='aac' and vid['codec_name']=='h264'
    assert abs(float(p['format']['duration'])-30)<.05
    assert p.get('chapters')==[]
    assert int(vid['nb_frames'])==NFR
    assert set(p['format'].get('tags',{})) <= {'major_brand','minor_version','compatible_brands','encoder'}
    assert set(vid.get('tags',{})) <= {'language','handler_name','vendor_id','encoder'}
    assert set(aud.get('tags',{})) <= {'language','handler_name','vendor_id','encoder'}
    subprocess.run(['ffmpeg','-v','error','-i',str(OUTMP4),'-f','null','-'],check=True)
    sha=hashlib.sha256(OUTMP4.read_bytes()).hexdigest()
    print('DONE',OUTMP4,OUTMP4.stat().st_size,'bytes',sha,flush=True)
    return sha

if __name__=='__main__':
    previewonly='--preview' in sys.argv
    print('Creating contact preview...',flush=True)
    make_contact()
    if not previewonly:
        wav=compose_sound()
        make_video(wav)
        verify()
        wav.unlink(missing_ok=True)