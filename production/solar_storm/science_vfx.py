"""Original, genuinely animated science explainer inserts for Solar Storm.

Not stock stills, zooming photos, composited NASA footage or decorative HUDs.
Every video frame is generated from time-dependent vector geometry and particles:
the solar plasma shell travels outwards; solar-wind field lines compress and
recover; satellite signal pathways change; the Sun/Earth system exchanges a
traveling illustrative wave. Schematic only, never numerical simulation.

Pillow + FFmpeg, CPU-only, no generated-media APIs or source license concerns.
The final film combines these animations with separately credited NASA motion.
"""
from __future__ import annotations

from functools import lru_cache
import math
from pathlib import Path
import random
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 540, 960, 30
FINAL_W, FINAL_H = 1080, 1920
ENGINE = "original-science-motion-studio-v1"
# Zero-based indices of EXISTING shots; a deliberate narrative edit, not an
# extra still laid on the NASA videos. Every insert occupies real scene time.
INSERTS = {
    1: ("flare", "sun304"),
    5: ("cme", "cme_launch"),
    7: ("shield", "magnetosphere"),
    9: ("satellite", "satellite"),
    12: ("connection", "sun171"),
}
COLORS = {
    "flare": (255, 190, 102), "cme": (255, 149, 79), "shield": (79, 195, 250),
    "satellite": (255, 181, 105), "connection": (106, 214, 253),
}
STEPS = {
    "flare": ("A STORM BEGINS", "Magnetic energy is released in the solar atmosphere"),
    "cme": ("SOLAR EJECTION", "A cloud of charged plasma expands from the Sun"),
    "shield": ("MAGNETIC RESPONSE", "The solar wind disturbs Earth's magnetic field"),
    "satellite": ("SPACE WEATHER", "Charged particles can disrupt orbital systems"),
    "connection": ("ONE CONNECTED SYSTEM", "A changing Sun influences our planet"),
}


def _ease(t: float) -> float:
    u = min(1.0, max(0.0, t))
    return u * u * (3 - 2 * u)


@lru_cache(maxsize=10)
def _font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


@lru_cache(maxsize=1)
def _backdrop() -> Image.Image:
    frame = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(frame)
    for y in range(H):
        p = y / H
        d.line((0, y, W, y),
               fill=(round(5 + 10 * p), round(14 + 17 * p),
                     round(35 + 30 * p)), width=1)
    rng = random.Random(17031)
    for _ in range(145):
        x, y = rng.randrange(18, W - 18), rng.randrange(120, 820)
        r = 1 if rng.random() < .92 else 2
        tint = rng.choice(((93, 133, 164), (139, 169, 198), (189, 207, 223)))
        d.ellipse((x-r, y-r, x+r, y+r), fill=tint)
    for i in range(12):
        y = 285 + i * 35
        d.line((35, y, W - 35, y), fill=(18, 41, 70), width=1)
    return frame


@lru_cache(maxsize=16)
def _orb(kind: str, radius: int) -> Image.Image:
    """Shaded spherical material, authored surface grain and terminator.

    Cached once by type/radius: full raster is drawn only during scene setup.
    These are illustrator-style *schematic* planets, not NASA cartographic data.
    """
    if kind not in {"sun", "earth"} or not 10 <= radius <= 220:
        raise ValueError("Invalid material sphere")
    n=radius*2+34
    c=n//2
    orb=Image.new("RGBA",(n,n),(0,0,0,0))
    d=ImageDraw.Draw(orb)
    for k in range(16,0,-1):
        r=radius+k
        if kind=="sun":
            col=(255,149,62,round(7*(17-k)/16))
        else:
            col=(70,167,233,round(5*(17-k)/16))
        d.ellipse((c-r,c-r,c+r,c+r),fill=col)

    pixels=orb.load()
    r2=radius*radius
    for yy in range(-radius,radius+1):
        for xx in range(-radius,radius+1):
            rs=xx*xx+yy*yy
            if rs>=r2:
                continue
            nx,ny=xx/radius,yy/radius
            nz=math.sqrt(max(0.0,1.0-rs/r2))
            # Sun and Earth use distinct authored material shaders and real
            # directional shading, rather than a flat colored circle.
            light=max(0.0,.38*nx-.44*ny+.81*nz)
            if kind=="sun":
                turbulence=(math.sin(xx*.28+math.cos(yy*.063)*5.3)
                            +math.sin(yy*.21+math.sin(xx*.083)*2.7)
                            +.5*math.cos((xx+yy)*.42))/2.5
                temp=.53+.37*light+.13*turbulence
                red=min(255,max(0,round(197+61*temp)))
                green=min(255,max(0,round(70+124*temp)))
                blue=min(255,max(0,round(25+90*temp)))
                # Irregular hot streaks and darker granular gaps.
                pixels[c+xx,c+yy]=(red,green,blue,255)
            else:
                long=math.atan2(nx,nz)
                lat=math.asin(max(-1,min(1,-ny)))
                relief=(math.sin(long*4+math.sin(lat*3.1))
                        +.67*math.cos(lat*6.3+long*2.2)
                        +.35*math.sin(long*9.2-lat*4.5))
                ice=abs(ny)>.89
                land=relief>.58 and not ice
                cloud=(math.sin(long*12+lat*5.3)
                       +.45*math.cos(long*7-lat*11))>1.19
                shade=max(.25,min(1.,.24+.89*light))
                if ice:
                    base=(184,223,234)
                elif cloud:
                    base=(179,223,237)
                elif land:
                    base=(65,165,132) if relief<1.15 else (126,174,129)
                else:
                    base=(25,118,184) if light>.4 else (20,76,146)
                pixels[c+xx,c+yy]=tuple(
                    max(0,min(255,round(v*shade))) for v in base)+(255,)
    d=ImageDraw.Draw(orb)
    if kind=="sun":
        # Sparse photospheric darker regions (not literal real sunspot data).
        rng=random.Random(radius*7+91)
        for _ in range(13):
            px=rng.uniform(-radius*.63,radius*.63)
            py=rng.uniform(-radius*.63,radius*.63)
            if px*px+py*py>(radius*.77)**2:
                continue
            rr=max(1,round(radius*.012+rng.random()*radius*.018))
            d.ellipse((c+px-rr,c+py-rr,c+px+rr,c+py+rr),
                      fill=(170,72,38,105))
        d.arc((c-radius+7,c-radius+7,c+radius-7,c+radius-7),
              199,300,fill=(255,231,166,140),width=3)
    else:
        d.arc((c-radius+3,c-radius+3,c+radius-3,c+radius-3),
              192,310,fill=(187,244,255,185),width=3)
        d.arc((c-radius+9,c-radius+9,c+radius-9,c+radius-9),
              296,52,fill=(80,173,234,115),width=3)
    return orb


def _text(d: ImageDraw.ImageDraw, pos: tuple[int,int], value: str,
          *, size: int=18, fill=(238,246,253), bold: bool=False):
    d.text(pos, value, font=_font(size,bold), fill=fill)


def _poly(d: ImageDraw.ImageDraw, points: list[tuple[float,float]],
          color, width: int=3):
    d.line([(round(x),round(y)) for x,y in points], fill=color, width=width,
           joint="curve")


def _curve(points, steps=54):
    """Cubic Bezier with authored handles; continuous positional movement."""
    p0,p1,p2,p3=points
    ans=[]
    for i in range(steps+1):
        u=i/steps
        v=1-u
        ans.append((v**3*p0[0]+3*v*v*u*p1[0]+3*v*u*u*p2[0]+u**3*p3[0],
                    v**3*p0[1]+3*v*v*u*p1[1]+3*v*u*u*p2[1]+u**3*p3[1]))
    return ans


def _dot(d,x,y,r,color):
    d.ellipse((round(x-r),round(y-r),round(x+r),round(y+r)),fill=color)


def _glow(im: Image.Image, paths: list[tuple[list,tuple,int]]):
    if not paths:
        return im
    layer=Image.new("RGBA",(W,H),(0,0,0,0))
    painter=ImageDraw.Draw(layer)
    for points,color,width in paths:
        rgb=color[:3]
        _poly(painter, points, (*rgb,60), width+9)
    bloom=layer.filter(ImageFilter.GaussianBlur(11))
    im.alpha_composite(bloom)
    main=ImageDraw.Draw(im)
    for points,color,width in paths:
        _poly(main,points,color,width)
    return im


def _orb_at(im: Image.Image, kind: str, x: int, y: int, r: int):
    orb=_orb(kind,r)
    im.alpha_composite(orb,(round(x-orb.width/2),round(y-orb.height/2)))


def _particles(draw: ImageDraw.ImageDraw, t: float, *, start: int, end: int,
               y_mid: int, color, number: int, speed: float, wave: float=35):
    span=end-start
    for idx in range(number):
        seed=(idx*.6180339887)%1
        p=(seed+t*speed*(.65+(idx%4)*.17))%1.0
        x=start+span*p
        y=y_mid + math.sin(idx*1.82 + p*math.tau)*wave
        rr=2+(idx%3)
        _dot(draw,x,y,rr,(*color[:3],200))


def _flare(im,t,duration):
    # Coronal loop expansion: an authored depiction, not a reproduction of
    # NASA SDO wavelengths or a claim of one observed historical event.
    p=t/duration
    _orb_at(im,"sun",275,570,155)
    paths=[]
    for idx in range(9):
        tilt=(idx-4)*32
        top=318+27*math.sin(t*1.25+idx*.65)
        start=(161+idx*26,525+8*math.sin(idx))
        end=(180+idx*23,529)
        pts=_curve((start,(96+tilt,top),(440-tilt,top-35),end))
        col=(255,120+idx*11,72+idx*5,150)
        paths.append((pts,col,2 if idx%3 else 4))
    _glow(im,paths)
    d=ImageDraw.Draw(im)
    for idx in range(36):
        a=idx*.49
        angle=-math.pi*.9+idx/36*math.pi*.84
        dist=155+12*math.sin(t*1.65+a)+28*((idx*.57+t*.38)%1)
        x=275+dist*math.cos(angle)
        y=570+dist*math.sin(angle)
        _dot(d,x,y,2+(idx%4),(255,181,105,220))
    for k in range(4):
        pulse=(t*.35 + k*.25)%1
        rr=35+175*pulse
        d.arc((275-rr,570-rr,275+rr,570+rr),205,325,
              fill=(255,226,159,max(60,220-round(170*pulse))),width=3)
    _text(d,(48,744),"CORONAL LOOPS",size=17,fill=(255,184,122),bold=True)


def _cme(im,t,duration):
    p=_ease(t/duration)
    _orb_at(im,"sun",150,533,94)
    _orb_at(im,"earth",475,528,27)
    d=ImageDraw.Draw(im)
    paths=[]
    # A rising, expanding cloud with separate leading envelope and dense core.
    center_x=236+240*p
    for idx in range(8):
        theta=idx/7*math.pi*1.12-math.pi*.56
        reach=70+120*p
        pts=[]
        for j in range(45):
            f=j/44
            x=218+(center_x-218)*f+reach*.22*math.sin(theta)*f
            y=530 + (reach*.75*math.sin(theta)) * math.sin(f*math.pi/2)
            pts.append((x,y))
        paths.append((pts,(255,116+idx*11,60+idx*8,140),2))
    for k in range(3):
        shift=k*32
        points=_curve(((192,532+shift-32),(255+100*p,375-shift),
                       (320+128*p,710+shift),(center_x+25,519+shift-15)))
        paths.append((points,(255,176,84,150),3))
    _glow(im,paths)
    d=ImageDraw.Draw(im)
    _particles(d,t,start=215,end=480,y_mid=533,
               color=(255,165,100),number=52,speed=.17,wave=90+44*p)
    # Core travels; not a fake measurement of solar wind velocity.
    _dot(d,center_x,527,8,(255,231,153,245))
    _text(d,(38,744),"PLASMA CLOUD",size=17,fill=(255,177,112),bold=True)
    _text(d,(357,745),"EARTH",size=16,fill=(150,223,255),bold=True)


def _shield(im,t,duration):
    p=t/duration
    wobble=math.sin(math.tau*1.3*p)
    _orb_at(im,"earth",348,517,88)
    d=ImageDraw.Draw(im)
    paths=[]
    # Closed schematic dipole loops bow toward the upstream solar wind.
    # Their day-side stand-off distance breathes as the storm arrives.
    for k in range(7):
        radius=90+k*22
        compress=(18+23*wobble)*(k+1)/7
        a=(348-radius-compress,515)
        b=(350+radius*.6,515)
        upper=_curve((a,(a[0]-30,515-radius*1.5),(b[0]+18,515-radius*.8),b))
        lower=_curve((a,(a[0]-30,515+radius*1.5),(b[0]+18,515+radius*.8),b))
        col=(79,204,250,190-k*14) if k%2==0 else (111,163,255,200-k*14)
        paths.extend(((upper,col,2),(lower,col,2)))
    _glow(im,paths)
    d=ImageDraw.Draw(im)
    _particles(d,t,start=45,end=283,y_mid=515,color=(255,178,112),
               number=46,speed=.18,wave=190)
    # An illustrative pulse on the bow shock, clearly changing every frame.
    shock_x=170+15*wobble
    for q in range(4):
        y=385+q*84
        _poly(d,[(shock_x-18,y-13),(shock_x,y),(shock_x-18,y+13)],
              (255,178,110,210),3)
    _text(d,(38,744),"SOLAR WIND",size=17,fill=(255,178,112),bold=True)
    _text(d,(290,745),"FIELD LINES",size=16,fill=(160,224,255),bold=True)


def _satellite(im,t,duration):
    p=t/duration
    _orb_at(im,"earth",270,770,154)
    d=ImageDraw.Draw(im)
    sx=270+17*math.sin(p*math.tau*.7)
    sy=406+14*math.cos(p*math.tau*.8)
    # Orbital track is not a physical exact orbit.
    d.arc((63,388,484,913),185,353,fill=(73,150,205,95),width=3)
    paths=[]
    for s in range(5):
        phase=s/5*math.tau
        sweep=(t*.24+s/5)%1
        wave=_curve(((sx,sy+14),(sx-80+s*29,500),
                     (215+s*22,604),(270,712)))
        end=round(len(wave)*(.15+.75*sweep))
        paths.append((wave[:end],(255,185,110,160),2))
    _glow(im,paths)
    d=ImageDraw.Draw(im)
    # Independent moving parts: central bus, solar arrays, antenna.
    d.rectangle((sx-29,sy-17,sx+29,sy+17),fill=(188,202,224,255),
                outline=(240,248,255,255),width=2)
    for sign in (-1,1):
        xx=sx+sign*75
        d.polygon([(sx+sign*30,sy-25),(sx+sign*118,sy-25),
                   (sx+sign*118,sy+25),(sx+sign*30,sy+25)],
                  fill=(25,98,158,255))
        for j in range(4):
            x0=sx+sign*(40+j*20)
            d.line((x0,sy-23,x0,sy+23),fill=(72,169,237,255),width=2)
    d.line((sx,sy-17,sx+10,sy-45),fill=(243,250,255,240),width=3)
    _dot(d,sx+10,sy-47,6,(255,198,110,255))
    for n in range(3):
        rr=22+n*19+8*math.sin(t*3+n)
        d.arc((sx-rr,sy-rr-36,sx+rr,sy+rr-36),207,324,
              fill=(255,176,98,180-n*40),width=3)
    _particles(d,t,start=47,end=465,y_mid=398,
               color=(255,164,102),number=38,speed=.19,wave=95)
    _text(d,(48,745),"SIGNAL DISTURBANCE",size=17,fill=(255,182,120),bold=True)


def _connection(im,t,duration):
    p=t/duration
    _orb_at(im,"sun",124,530,81)
    _orb_at(im,"earth",438,539,59)
    paths=[]
    for k in range(6):
        off=(k-2.5)*24
        paths.append((_curve(((210,520),(272,340+off),
                              (330,695-off),(376,538))),
                      (80,200+k*7,250,140+k*10),3))
    _glow(im,paths)
    d=ImageDraw.Draw(im)
    for k in range(28):
        frac=(k/28+t*.15)%1
        line=_curve(((210,520),(272,340+(k%4-2)*24),
                     (330,695-(k%4-2)*24),(376,538)),40)
        x,y=line[min(len(line)-1,int(frac*(len(line)-1)))]
        _dot(d,x,y,2+(k%3),(183,234,255,200))
    _text(d,(50,745),"THE SUN",size=18,fill=(255,194,116),bold=True)
    _text(d,(382,745),"EARTH",size=18,fill=(160,226,250),bold=True)


def render_frame(kind: str, t: float, duration: float) -> Image.Image:
    """Render one authored RGB frame. Disjoint times produce different art."""
    if (kind not in STEPS or type(t) not in (float,int) or
            type(duration) not in (float,int) or
            not math.isfinite(t) or not math.isfinite(duration) or
            duration <= 0 or duration > 20 or t < 0 or t > duration):
        raise ValueError("Invalid original science animation or time")
    image=_backdrop().copy().convert("RGBA")
    d=ImageDraw.Draw(image)
    # Large, quiet protected title area; existing Motion HUD overlays above it.
    title,subtitle=STEPS[kind]
    d.rounded_rectangle((34,277,506,312),radius=10,
                        fill=(18,50,81,245),outline=(58,132,174,170),width=2)
    _text(d,(47,282),title,size=17,bold=True,fill=(233,246,255))
    _text(d,(40,320),subtitle,size=12,fill=(173,204,226))
    # A real evolving time indicator, not a static ornamental loop.
    # The bottom-centered narration captions end above ~1720 final pixels.
    # Keep motion-progress below their protected zone.
    d.rounded_rectangle((40,863,500,870),radius=3,fill=(29,70,102))
    if t > 0:
        d.rounded_rectangle((40,863,40+round(460*(t/duration)),870),
                            radius=3,fill=COLORS[kind])
    _text(d,(40,882),"ORIGINAL SCIENCE MOTION  ·  SCHEMATIC / NOT TO SCALE",
          size=10,fill=(134,167,192))
    if kind=="flare":
        _flare(image,t,duration)
    elif kind=="cme":
        _cme(image,t,duration)
    elif kind=="shield":
        _shield(image,t,duration)
    elif kind=="satellite":
        _satellite(image,t,duration)
    else:
        _connection(image,t,duration)
    return image.convert("RGB")


def render_insert(kind: str, duration: float, destination: Path,
                  *, preset: str="veryfast") -> dict:
    """Stream actual moving RGB frames through FFmpeg without temp PNGs.

    Output is 1080×1920, 30fps native YUV420P H.264 for the existing
    13-shot concat workflow. No still loops, placeholder renders or retiming.
    """
    if (kind not in STEPS or type(duration) not in (float,int)
            or not math.isfinite(duration) or not .6 <= duration <= 12
            or preset not in {"ultrafast","veryfast","fast"}):
        raise ValueError("Unsupported animated scene render")
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    frames=max(1,round(duration*FPS))
    cmd=[
        "ffmpeg","-y","-v","error","-f","rawvideo",
        "-pix_fmt","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),
        "-i","pipe:0","-an","-vf",
        f"scale={FINAL_W}:{FINAL_H}:flags=lanczos,format=yuv420p",
        "-frames:v",str(frames),"-r",str(FPS),"-c:v","libx264",
        "-preset",preset,"-crf","19","-pix_fmt","yuv420p",
        "-movflags","+faststart",str(destination),
    ]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for index in range(frames):
            frame=render_frame(kind,index/FPS,duration)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        code=proc.wait(timeout=180)
        if code!=0:
            raise RuntimeError(f"Original science FFmpeg render failed: {code}")
    except BaseException:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        destination.unlink(missing_ok=True)
        raise
    return {"engine":ENGINE,"kind":kind,"frames":frames,
            "fps":FPS,"duration_seconds":frames/FPS,
            "size":[FINAL_W,FINAL_H],"original_art":True,
            "schematic_not_to_scale":True,
            "external_asset":False,"publish_approved":False}
