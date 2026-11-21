"""Compose Saturn entirely from animated procedural 2D layers.

The polar views project two independently advected cloud decks onto a tilted
atmospheric plane. The orbit views use an illuminated globe and two ring
layers, with the near ring occluding the globe. No image or footage inputs.
"""
import argparse
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

import render as previous

W, H, FPS = 720, 1280, 30
previous.W, previous.H = W, H
OUT = Path("build/saturn-25d")
OUT.mkdir(parents=True, exist_ok=True)
previous.OUT = OUT
cv2.setNumThreads(2)
TAU = math.tau
rng = np.random.default_rng(71)
pixels_x, pixels_y = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
screen_x = (pixels_x-W/2)/(W/2)
screen_y = (pixels_y-H/2)/(W/2)

def step(value):
    value = np.clip(value, 0, 1)
    return value * value * (3 - 2 * value)

def lerp(a, b, v):
    return a + (b-a)*v

def field(seed, shape=768):
    random = np.random.default_rng(seed)
    out = np.zeros((shape, shape), dtype=np.float32)
    axis = np.arange(shape,dtype=np.float32)/shape
    for size, scale in [(5,.43),(11,.23),(24,.14),(51,.09),(110,.06),(213,.033),(357,.025)]:
        cells = np.pad(random.normal(0,1,(size,size)).astype(np.float32),2,mode="wrap")
        x,y = np.meshgrid(2+axis*size,2+axis*size)
        layer = cv2.remap(cells,x,y,cv2.INTER_CUBIC)
        out += layer*scale
    return out

LOW = field(16)
HIGH = field(27)
WEATHER = field(32)
MICRO = field(151)
STARS = rng.uniform((0,0,.12),(W,H,1),size=(270,3))
COAL = [(7,16,24),(20,50,63),(51,111,119),(121,180,172),(215,225,187),(255,244,204)]
GOLD = [(29,21,29),(70,39,39),(131,72,53),(190,119,74),(228,173,112),(252,221,165)]
FIRE = [(11,9,25),(44,17,45),(102,32,60),(172,51,69),(229,106,77),(255,204,137)]
GAS = [(35,21,28),(86,49,43),(132,81,60),(188,135,90),(221,181,118),(253,223,168)]
OCEAN = [(5,19,45),(11,40,79),(21,74,120),(56,122,157),(94,155,180),(157,210,215)]
LAND = [(25,37,31),(40,69,55),(86,108,74),(134,133,79),(173,153,106),(224,196,143)]

def palette(colors):
    return np.stack([np.interp(np.arange(256),np.linspace(0,255,len(colors)),np.array(colors)[:,c])
                     for c in range(3)],axis=1).astype(np.float32)

LUT = [palette(points) for points in (COAL,GOLD,FIRE,GAS,OCEAN,LAND)]

def color(tone, lut):
    return LUT[lut][np.clip(tone*255,0,255).astype(np.uint8)]

def fetch(tex,x,y):
    return cv2.remap(tex,x.astype(np.float32),y.astype(np.float32),cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_WRAP)

def stars(t, dr=0):
    mist = np.exp(-((screen_x+.50+.15*math.sin(t*.2))/1.5)**2
                  -((screen_y+.5)/1.7)**2)
    bg = np.stack([5+mist*13,7+mist*12,16+mist*24],axis=-1).astype(np.uint8)
    for sx,sy,d in STARS:
        x = round((sx-t*(4+11*d)-dr*d)%W)
        y = round((sy+t*(2+4*d)+dr*.25*d)%H)
        lum = int((27+123*d*d) * (.70+.30*math.sin(t*(.7+d)+sx)))
        r = 1 if d<.94 else 2
        cv2.circle(bg,(x,y),r,(max(2,lum-13),lum,min(255,lum+21)),-1,cv2.LINE_AA)
    return bg

def hex_radius(a):
    # Slightly rounded corners are the result of wind, not a drawn polygon.
    sector = (a+math.pi*.5)%(math.pi/3)-math.pi/6
    return .94*math.cos(math.pi/6)/np.cos(sector) + .012*np.sin(12*a+.3)

def polar(t, z, squash=1., roll=0., cx=0., cy=-.03, ember=0.):
    x = (screen_x-cx)/(z*1.01)
    y = (screen_y-cy)/(z*squash)
    cs, sn = math.cos(roll), math.sin(roll)
    x,y = cs*x-sn*y, sn*x+cs*y
    a = np.arctan2(y,x)
    r = np.sqrt(x*x+y*y)
    belt = r-hex_radius(a)
    base = fetch(LOW,370+x*299+t*13,390+y*301-t*16)
    frost = fetch(MICRO,360+x*548-t*11,372+y*548+t*8)

    # Each layer flows at a different angular speed. Embedded vortices deflect
    # the upper cloud deck independently of the large-scale banding.
    spin = a + t*(.080 + .37*np.exp(-r*r/0.29))
    spin += .12*np.sin(7*r-3*a+.41*t) + .10*base
    swirl_r = r+.027*np.sin(a*4+r*17-1.45*t)+.062*base
    u, v = swirl_r*np.cos(spin), swirl_r*np.sin(spin)
    for azimuth, radius, curl in ((-.8,.53,1.0),(1.21,.59,-.76),(2.67,.41,1.1)):
        phase = azimuth+t*.17
        pu,pv = radius*math.cos(phase),radius*math.sin(phase)
        dx,dy = u-pu,v-pv
        strength=curl*np.exp(-(dx*dx+dy*dy)/.025)
        u,v = u-dy*strength,v+dx*strength
    cloud = fetch(HIGH,389+272*u,390+273*v)
    high_spin = a+.25*t+.16*np.sin(12*r+5*a)+.12*cloud
    wisps = fetch(WEATHER,365+481*r*np.cos(high_spin),355+489*r*np.sin(high_spin))
    center = .34 + .29*cloud + .12*wisps + .06*frost
    center += .065*np.sin(52*r-8*spin+7.0*cloud)
    center += .025*np.sin(101*r-13*spin+6.8*wisps)
    outer = .51+.38*base+.11*frost + .09*np.sin(29*r+3.8*base+.21*t)
    outer += .06*np.sin(76*r+7*cloud-a*2)
    tint = color(center,0)
    if ember:
        tint = lerp(tint,color(center+.085,2),ember)
    atmosphere = lerp(tint,color(outer,1),step((belt+.09)/.20)[:,:,None])
    stripe = np.exp(-((belt+.035*base)/.051)**2)
    inner = np.exp(-((belt+.11+.01*cloud)/.027)**2)
    filaments = (.57+.43*np.sin(14*a+t*7+19*wisps)) * (.72+.28*np.sin(63*a-t*5))
    glow = (.43*stripe*(.61+filaments*.39)+.12*inner)
    atmosphere += glow[:,:,None]*np.array([125,100,70])
    shade = np.clip(1.08+.17*(-x-y*.38)-.14*r+.13*wisps,.34,1.26)
    atmosphere *= shade[:,:,None]
    eye = np.exp(-((r/.105)**2.8))
    atmosphere *= 1-(.85*eye)[:,:,None]
    glimmer = np.exp(-((r+.008*cloud-.15)/.055)**2) * (.52+.48*np.sin(a*4+3.4*t+6*wisps))
    atmosphere += glimmer[:,:,None]*np.array([49,91,104])*(1-ember*.48)
    return np.clip(atmosphere,0,255).astype(np.uint8)

def draw_jet(frame,t,z,squash,roll,cx,cy,amount):
    if amount<=0:
        return frame
    glow = np.zeros_like(frame)
    for idx in range(70):
        a = idx*TAU/70-t*(.64 + .08*(idx%5))
        a += .015*math.sin(t*1.2+idx)
        d = .018*math.sin(3*a+idx)+.012*math.cos(idx*2)
        span = .018+.033*(idx%4)/3
        coords = []
        for q in (a,a-span*.48,a-span):
            r = float(hex_radius(q)) + d
            u,v = r*math.cos(q),r*math.sin(q)
            x,y = math.cos(roll)*u+math.sin(roll)*v, -math.sin(roll)*u+math.cos(roll)*v
            coords.append((round(W/2+(x*z*1.01+cx)*W/2),round(H/2+(y*z*squash+cy)*W/2)))
        light = int(amount*(36+112*(.5+.5*math.sin(idx*8.33+t*4))))
        cv2.polylines(glow,[np.array(coords,np.int32)],False,(light,int(light*.78),int(light*.40)),1,cv2.LINE_AA)
    bloom=cv2.GaussianBlur(glow,(0,0),3)
    return cv2.add(cv2.add(frame,glow),bloom)

def orbit(t,cx,cy,radius,tilt,cant,spread=0.):
    bg=stars(t,spread)
    x=(screen_x-cx)/radius
    y=(screen_y-cy)/radius
    s,c=math.sin(cant),math.cos(cant)
    rx,ry=x*c+y*s,-x*s+y*c
    front = ry>=0
    plane = ry/tilt
    rr=np.sqrt(rx*rx+plane*plane)
    grain=fetch(HIGH,370+rx*240+t*6,372+plane*240)
    ring = step((rr-1.20)/.044)*step((2.18-rr)/.061)
    ring *= (1-.90*np.exp(-((rr-1.825)/.038)**2))*(1-.57*np.exp(-((rr-1.97)/.014)**2))
    fine=.67+.14*np.sin(rr*146)+.064*np.sin(rr*372)+.079*np.sin(rr*61)+.036*grain
    fine*=np.clip(.92-.13*rx+ .07*np.sin(rr*17),.35,1)
    ringcolor = color(np.clip(fine,0,1),1)
    ringlight = np.clip(.88-.18*rx+.05*(plane<0),.22,1.)
    ringcolor *=ringlight[:,:,None]
    nearshadow = step((.67-np.abs(rx+.45))/.54)*step((plane-.34)/.53)
    ringcolor *= (1-.65*nearshadow)[:,:,None]
    backmix=(ring*(.42+.42*fine)*(~front))[:,:,None]
    bg=lerp(bg,ringcolor,backmix)

    u2=rx*rx+(ry*1.10)**2
    z=np.sqrt(np.clip(1-u2,0,1))
    lat=np.arcsin(np.clip((ry*1.097+.25*z)/1.032,-1,1))
    lon=np.arctan2(rx,z+.006)
    humid=fetch(LOW,390+lon*140+t*22,393+lat*203)
    fine_cloud=fetch(HIGH,390+lon*415+t*50,393+lat*630)
    details=fetch(MICRO,390+lon*780+t*41,393+lat*1200)
    lat+=.018*humid+.005*fine_cloud
    bands=.61+.11*np.cos(23*lat+.55*humid)+.062*np.sin(58*lat+1.77*humid)
    bands+=.033*np.sin(123*lat+2.8*fine_cloud)+.032*fine_cloud+.014*details
    glow=np.clip(-.57*rx-.28*ry+.78*z,0,1)
    planet=color(bands,3)
    planet*=((.20+.83*glow**.61) * (1-.22*np.clip(-ry+.18*rx,0,1)))[:,:,None]
    rim=np.exp(-((z-.075)/.17)**2)*step((.55-rx)/.55)
    planet+=rim[:,:,None]*np.array([38,36,25])
    planet_shadow = .24*np.exp(-((ry-.026+.08*rx)/.048)**2)
    planet*=(1-planet_shadow)[:,:,None]
    solid=step((1.004-u2)/.018)[:,:,None]
    bg=lerp(bg,planet,solid)
    frontmix=(ring*(.46+.48*fine)*front)[:,:,None]
    bg=lerp(bg,ringcolor,frontmix)
    return np.clip(bg,0,255).astype(np.uint8)

# Original geographic silhouette for a globe shown briefly in a scale overlay.
# Coordinates describe a simplified Atlantic-facing map in longitude/latitude.
CONTINENTS = [
    [(-170,63),(-141,68),(-121,55),(-118,33),(-96,16),(-90,21),(-83,9),(-77,11),(-83,25),
     (-72,40),(-54,49),(-60,57),(-82,64),(-95,69),(-130,73),(-157,70)],
    [(-81,12),(-67,11),(-61,7),(-42,-4),(-35,-10),(-47,-26),(-55,-33),(-66,-55),(-74,-47),(-72,-24),(-80,-7)],
    [(-54,59),(-43,59),(-19,72),(-20,82),(-58,83),(-70,76)],
    [(-10,35),(5,37),(17,32),(30,32),(43,12),(51,11),(48,2),(40,-12),(34,-22),(26,-34),
     (17,-35),(11,-24),(13,-13),(8,5),(-10,7),(-17,17),(-16,28)],
    [(-11,36),(-9,43), (4,47),(11,55),(7,58),(22,71),(46,69),(67,73),(88,71),
     (124,66),(154,62),(170,64),(155,51),(141,46),(126,36),(119,25),(110,8),(102,4),(95,19),
     (79,7),(70,24),(58,28),(52,14),(43,13),(36,29),(29,42),(19,38),(12,45),(4,43)],
    [(113,-22),(129,-14),(149,-14),(153,-28),(144,-39),(128,-35),(114,-29)],
    [(-180,-68),(-130,-73),(-85,-72),(-41,-65),(5,-71),(57,-68),(100,-72),(145,-69),(180,-68),(180,-90),(-180,-90)],
]
WORLD=np.zeros((360,720),np.uint8)
for poly in CONTINENTS:
    coords=np.array([((a+180)*2,(90-b)*2) for a,b in poly],np.int32)
    cv2.fillPoly(WORLD,[coords],255,cv2.LINE_AA)

def globe(t,diameter,west):
    d=max(5,diameter)
    xx,yy=np.meshgrid(np.linspace(-1.03,1.03,d,dtype=np.float32),np.linspace(-1.03,1.03,d,dtype=np.float32))
    rr=xx*xx+yy*yy
    zz=np.sqrt(np.clip(1-rr,0,1))
    lat=np.arcsin(np.clip(-yy*.978+.20*zz,-1,1))
    lon=np.arctan2(xx,zz*.978+yy*.20)
    sx=(lon/(2*np.pi)+.5+west+t*.045)*720
    sy=(.5-lat/np.pi)*360
    detail = fetch(LOW,sx*1.76,sy*2.92)
    mask=fetch(WORLD,sx+2.2*detail,sy+2*detail).astype(np.float32)/255
    ocean=color(.36+.19*detail+.15*np.abs(lat),4)
    land=color(.60+.32*detail-.19*np.abs(lat),5)
    ground=lerp(ocean,land,mask[:,:,None])
    clouds=fetch(WEATHER,sx*2.02+t*13,sy*2.21)+.27*fetch(HIGH,sx*4.9,sy*4.4)
    cover=step((clouds-.19)/.84)
    ground=lerp(ground,np.array([219,231,239]),(cover*.73)[:,:,None])
    light=np.clip(-.57*xx+.61*zz-.43*yy,0,1)
    ground *= (.27+.78*light**.55)[:,:,None]
    ground+=np.exp(-((zz-.13)/.164)**2)[:,:,None]*np.array([20,52,81])
    return np.clip(ground,0,255).astype(np.uint8),step((1.014-rr)/.054)

def paint_globe(frame,t,cx,cy,diameter,west,reveal):
    if reveal<=0:
        return
    img,alpha=globe(t,diameter,west)
    x,y=round(cx-diameter/2),round(cy-diameter/2)
    xx,yy=max(0,x),max(0,y)
    w,h=min(W,x+diameter)-xx,min(H,y+diameter)-yy
    if w>0 and h>0:
        slic=(slice(yy-y,yy-y+h),slice(xx-x,xx-x+w))
        mask=alpha[slic][:,:,None]*reveal
        old=frame[yy:yy+h,xx:xx+w]
        old[:]=lerp(old,img[slic],mask)

def satellite(t):
    layer=np.zeros((220,290,3),np.uint8)
    pivot=(127,119)
    cv2.line(layer,(129,136),(279,123),(184,144,102),3,cv2.LINE_AA)
    cv2.line(layer,(129,135),(279,122),(238,200,141),1,cv2.LINE_AA)
    cv2.circle(layer,(279,122),3,(197,214,229),-1,cv2.LINE_AA)
    for x,y in ((98,146),(151,152),(153,139)):
        cv2.line(layer,(129,125),(x,y),(181,133,85),3,cv2.LINE_AA)
        cv2.ellipse(layer,(x,y),(19,7),69,0,360,(112,123,134),-1,cv2.LINE_AA)
        for k in range(6):
            cv2.line(layer,(x-6+k*2,y-12),(x+2+k*2,y+13),(210-k*8,183-k*8,144-k*4),1,cv2.LINE_AA)
    cv2.rectangle(layer,(105,111),(154,163),(141,84,51),-1,cv2.LINE_AA)
    cv2.rectangle(layer,(108,112),(142,154),(220,144,69),-1,cv2.LINE_AA)
    for i in range(9):
        cv2.line(layer,(109,113+i*4),(139,112+i*4),(250-i*8,190-i*7,109-i*6),1,cv2.LINE_AA)
    cv2.line(layer,pivot,(183,193),(216,180,122),2,cv2.LINE_AA)
    cv2.line(layer,(127,135),(87,180),(142,152,166),2,cv2.LINE_AA)
    cv2.ellipse(layer,(136,103),(57,27),-19,0,360,(101,119,147),-1,cv2.LINE_AA)
    cv2.ellipse(layer,(133,96),(54,24),-19,0,360,(190,198,211),-1,cv2.LINE_AA)
    cv2.ellipse(layer,(134,94),(46,18),-19,0,360,(225,221,205),-1,cv2.LINE_AA)
    cv2.ellipse(layer,(135,96),(39,13),-19,0,240,(246,232,192),2,cv2.LINE_AA)
    cv2.line(layer,(133,95),(113,64),(120,135,153),3,cv2.LINE_AA)
    cv2.circle(layer,(113,64),4,(245,221,163),-1,cv2.LINE_AA)
    cv2.circle(layer,(138,143),3,(244,int(130+60*math.sin(t*8)**2),93),-1,cv2.LINE_AA)
    return layer

def overlay_text(text,size,col=(252,247,234),font="bold"):
    return previous.label(text,size,col,font,max_width=640)

def place(frame,img,x,y,alpha=1.):
    previous.write_label(frame,img,x,y,float(alpha))

TEXT = {
    "hook":[overlay_text("SIX CORNERS.",70,(255,202,125)),overlay_text("ONE HURRICANE.",45)],
    "orbit":[overlay_text("SATURN'S NORTH POLE",26,(190,220,236),"mono")],
    "scale":[overlay_text("30,000 km",75,(167,233,226)),overlay_text("TWO EARTHS, TO SCALE",26,(193,222,230),"mono")],
    "cassini":[overlay_text("CLOUDS IN THE JET",32,(255,222,166),"mono"),overlay_text("Atmospheric illustration",19,(209,224,226),"normal")],
    "eye":[overlay_text("50×",103,(255,204,147)),overlay_text("A TYPICAL EARTH HURRICANE EYE",22)],
    "archive":[overlay_text("1980–81",71,(255,204,147)),overlay_text("VOYAGER",30,(240,216,182),"mono"),
               overlay_text("2013",71,(159,218,229)),overlay_text("CASSINI",30,(209,227,229),"mono")],
    "wave":[overlay_text("ONE EXPLANATION",25,(255,223,171),"mono"),overlay_text("A WAVE IN THE JET",45)],
}
caption_shade = np.exp(-((pixels_y-989)/108)**2)*.55
shade=cv2.merge([np.round(255*(1-caption_shade)).astype(np.uint8)]*3)

def frame_at(key,lines,t,p,marks):
    titles=TEXT[key]
    if key=="hook":
        progress=step(t/.94)
        params=(lerp(1.40,1.01,progress),lerp(.80,.97,progress),lerp(-.25,-.12,progress),0.,-.14)
        frame=draw_jet(polar(t,*params),t,*params,.76)
        fr=step((t-.06)/.30)
        place(frame,titles[0],352,173+18*(1-fr),fr)
        place(frame,titles[1],352,241+16*(1-fr),fr)
    elif key=="orbit":
        frame=orbit(t,-.04,.12,lerp(.68,.83,step(p)),.35+.05*math.sin(t*.8),-.22+.09*p,t*9)
        q=step((p-.63)/.105)
        if q>0:
            cloud=polar(t,1.3-.28*q,.48+.48*q,-.16,0.,-.14)
            frame=cv2.addWeighted(frame,1-q,cloud,q,0)
        place(frame,titles[0],352,167,step(t/.29))
    elif key=="scale":
        params=(.97,.92,-.14,0.,-.07)
        frame=draw_jet(polar(t,*params),t,*params,.45)
        frame=cv2.convertScaleAbs(frame,alpha=.66)
        f=step((t-marks[1]+.14)/.45)
        g=step((t-marks[1]-.13)/.48)
        y=593
        left,right=52,668
        width=round((right-left)*12742/30000)
        paint_globe(frame,t,199-91*(1-f),y,width,-.03,f)
        paint_globe(frame,t,518+91*(1-g),y,width,.05,g)
        alpha=step(t/.24)
        loc=242
        ends=[round(lerp(360,pos,alpha)) for pos in (left,right)]
        cv2.line(frame,(ends[0],loc),(ends[1],loc),(150,227,217),2,cv2.LINE_AA)
        for v in ends:
            cv2.line(frame,(v,loc-7),(v,loc+7),(150,227,217),2,cv2.LINE_AA)
        place(frame,titles[0],352,170,alpha)
        place(frame,titles[1],352,831,g)
    elif key=="cassini":
        params=(1.03+.34*step(p),.83-.13*step(p),-.3+.24*p,.06-.12*p,-.18)
        frame=draw_jet(polar(t+9,*params),t+9,*params,.94)
        place(frame,titles[0],352,166,step(t/.28))
        place(frame,titles[1],352,231,step(t/.28))
    elif key=="eye":
        q=step(t/.84)
        z=lerp(1.09,2.66,q)+p*.37
        params=(z,.82+.11*p,-.32+.27*p,.06*math.sin(t*.7),-.13+.09*math.sin(t*.78))
        frame=polar(t+12,*params,ember=.76+.20*q)
        f=step((t-marks[1]+.13)/.38)
        place(frame,titles[0],352,191+17*(1-f),f)
        place(frame,titles[1],352,276,f)
    elif key=="archive":
        f=step((t-marks[1]+.1)/.34)
        frame=orbit(t+7,.28,.42,.61+.12*p,.32,-.45+.14*p,t*16)
        layer=satellite(t)
        foreground,_=previous.warp(layer,lerp(136,511,step(p)),lerp(752,536,step(p)),301+75*p,-15+17*p)
        frame=cv2.addWeighted(frame,1-f,cv2.max(frame,foreground),f,0)
        for j, y in enumerate((213,282)):
            place(frame,titles[j],352,y,1-f)
            place(frame,titles[j+2],352,y,f)
    else:
        f=step((p-.69)/.31)
        params=(lerp(1.07,1.40,f),lerp(.96,.80,f),lerp(-.12,-.25,f),0.,-.14)
        cloud=polar(lerp(20+t,0.,f),*params)
        frame=draw_jet(cloud,lerp(20+t,0.,f),*params,.76)
        alpha=step(t/.34)*(1-step((p-.72)/.23))
        place(frame,titles[0],352,176,alpha)
        place(frame,titles[1],352,231,alpha)
    # Darken the bottom band independently of the image content for phone legibility.
    frame=cv2.multiply(frame,shade,scale=1/255)
    for n,cap in enumerate(lines):
        start=marks[n]-.04
        if start<=t<marks[n+1]-.03:
            place(frame,cap,352,987+6*(1-step((t-start)/.11)),step((t-start+.015)/.080))
            break
    return frame

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    narr=previous.narrate()
    target=OUT/"saturn-six-corners-25d.mp4"
    interim=OUT/"encoded.mp4"
    if not args.preview:
        cmd=["ffmpeg","-v","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}",
             "-framerate","30","-i","pipe:0","-i",str(OUT/"mix.wav"),"-map","0:v","-map","1:a",
             "-vf","scale=1080:1920:flags=lanczos:out_color_matrix=bt709","-pix_fmt","yuv420p",
             "-c:v","libx264","-crf","17","-preset","fast","-threads","4","-maxrate","10M","-bufsize","14M",
             "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
             "-af","loudnorm=I=-14.5:TP=-1.5:LRA=8","-c:a","aac","-b:a","192k","-ar","48000",str(interim)]
        enc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for key,phrases,_,frames,marks,_ in narr:
            print("Animating",key,frames,flush=True)
            captions=[overlay_text(phrase,37) for phrase in phrases]
            frames_to_draw=(int(frames*.30),int(frames*.70)) if args.preview else range(frames)
            for index in frames_to_draw:
                frame=frame_at(key,captions,index/FPS,index/(frames-1),marks)
                if args.preview:
                    cv2.imwrite(str(OUT/f"{key}-{index}.jpg"),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
                else:
                    enc.stdin.write(frame.tobytes())
    finally:
        if not args.preview:
            enc.stdin.close()
            if enc.wait():
                raise RuntimeError("Portrait encoder failed")
    if not args.preview:
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(interim),"-map","0:v","-map","0:a","-c","copy",
                        "-map_metadata","-1","-map_metadata:s","-1","-map_chapters","-1","-fflags","+bitexact",
                        "-movflags","+faststart",str(target)],check=True)
        interim.unlink()

if __name__=="__main__":
    main()
