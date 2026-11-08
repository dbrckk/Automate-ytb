"""Original cinematic painted forest depth plates and living light.

P3.6 replaces the flat primitive meadow with an authored world: warm/cool
atmospheric perspective, layered botanical silhouettes, veined canopy,
dappled ground, volumetric shafts, moving motes and a restrained filmic
vignette. Deterministic Pillow drawing; no stock photos, model credits, or
external image dependencies. Static heavy plates are built once per process.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageDraw, ImageFilter

VERSION = "original-forest-cinematic-painted-world-p36-v1"
SIZE = (1080, 1920)
_PALETTE = {
    "night": (17, 34, 67),
    "haze": (100, 150, 153),
    "warm": (250, 181, 119),
    "pine": (21, 63, 69),
    "moss": (48, 112, 78),
}


def _sky() -> Image.Image:
    image = Image.new("RGBA", SIZE)
    draw = ImageDraw.Draw(image)
    stops = ((0, (12, 31, 63)), (570, (43, 80, 112)),
             (1120, (146, 149, 132)), (1460, (210, 170, 121)),
             (1920, (219, 161, 109)))
    for y in range(SIZE[1]):
        for (a,c0),(b,c1) in zip(stops,stops[1:]):
            if y <= b:
                q = (y-a)/(b-a)
                # Atmospheric diffuse scatter: continuous color gradients.
                color = tuple(round(v+(w-v)*q) for v,w in zip(c0,c1))
                draw.line((0,y,SIZE[0],y),fill=color+(255,))
                break
    glow = Image.new("RGBA",SIZE)
    g = ImageDraw.Draw(glow)
    sx,sy = 810,660
    for radius,alpha in ((375,9),(285,13),(220,23),(155,32),(105,45)):
        g.ellipse((sx-radius,sy-radius,sx+radius,sy+radius),
                  fill=(255,208,145,alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(68))
    image.alpha_composite(glow)
    g = ImageDraw.Draw(image)
    g.ellipse((sx-43,sy-43,sx+43,sy+43),fill=(255,224,169,255))
    g.ellipse((sx-36,sy-36,sx+36,sy+36),fill=(255,239,196,250))
    return image


def _clouds() -> Image.Image:
    image=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(image)
    rng=random.Random(12701)
    for j in range(23):
        x=rng.randrange(-200,1300)
        y=rng.randrange(230,1000)
        rx=rng.randrange(85,220)
        ry=rng.randrange(15,46)
        for k in range(5):
            cx=x+(k-2)*rx*.37
            cy=y+math.sin(k*2.7+j)*ry*.6
            d.ellipse((cx-rx*.63,cy-ry,cx+rx*.63,cy+ry),
                      fill=(235,222,207,27 if j%3 else 42))
    return image.filter(ImageFilter.GaussianBlur(29))


def _ridges() -> Image.Image:
    plate=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(plate)
    d.polygon([(0,1170),(95,1109),(188,1152),(350,1004),
               (458,1101),(648,966),(820,1068),(972,989),
               (1080,1096),(1080,1920),(0,1920)],
              fill=(77,110,123,175))
    d.polygon([(0,1261),(142,1165),(284,1227),(461,1114),
               (643,1213),(872,1107),(1080,1186),
               (1080,1920),(0,1920)],fill=(51,102,111,222))
    for i in range(15):
        x=round(i*84-30)
        d.line((x,1167+(i%3)*11,x+26,1139+(i%4)*17),
               fill=(153,171,151,34),width=3)
    return plate


def _shafts() -> Image.Image:
    beams=Image.new("RGBA",SIZE)
    draw=ImageDraw.Draw(beams)
    for j in range(7):
        base=220+j*155
        span=67+j%3*21
        draw.polygon([(802+j*9,634),(815+j*12,658),
                      (base+span,1410),(base-span,1410)],
                     fill=(255,219,161,17+j%3*4))
    return beams.filter(ImageFilter.GaussianBlur(48))


def _leaf_cluster(d: ImageDraw.ImageDraw, x: int, y: int,
                  radius: int, *, near: bool, variant: int) -> None:
    rng=random.Random((x+2000)*4099+(y+2000)*7+variant)
    tones=( (28,89,83), (35,104,90), (49,120,94),
            (65,134,97), (85,141,103) ) if near else (
            (37,89,91), (51,100,101), (62,113,107))
    # Numerous overlapping small organic leaves, not a single oval crown.
    for k in range(34 if near else 17):
        angle=rng.random()*2*math.pi
        rr=radius*math.sqrt(rng.random())
        px=x+math.cos(angle)*rr*1.18
        py=y+math.sin(angle)*rr*.62
        leaf=rng.randint(7,22) if near else rng.randint(8,19)
        col=tones[(k+variant)%len(tones)]
        alpha=238 if near else 179
        d.ellipse((px-leaf,py-leaf*.56,px+leaf,py+leaf*.56),
                  fill=col+(alpha,))
        if near and k%5==0:
            d.arc((px-leaf/2,py-leaf*.5,px+leaf/2,py+leaf*.15),
                  190,345,fill=(174,193,131,110),width=2)


def _trees() -> Image.Image:
    plate=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(plate)
    rng=random.Random(6192)
    for j in range(24):
        x=rng.randrange(-55,1165)
        ground=rng.randrange(1214,1344)
        height=rng.randrange(165,425)
        lean=rng.randrange(-34,35)
        near=j%3==0
        root=(x,ground)
        apex=(x+lean,ground-height)
        d.line((root,apex),fill=(33,68,73,242 if near else 176),
               width=15 if near else 8)
        d.line(((x-4,ground),(apex[0]-4,apex[1]+12)),
               fill=(110,119,94,65),width=3)
        for side in (-1,1):
            for k in (0,1):
                ax=apex[0]+side*(55+k*25)
                ay=apex[1]+67+k*48
                d.line(((x+lean*.5,ground-height*.55),
                        (ax,ay)),fill=(35,77,76,205),width=6)
                _leaf_cluster(d,round(ax),round(ay),58 if near else 44,
                              near=near,variant=j*11+k)
        _leaf_cluster(d,apex[0],apex[1]+45,94 if near else 66,
                      near=near,variant=j)
    return plate


def _understory() -> Image.Image:
    plate=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(plate)
    rng=random.Random(8605)
    for j in range(52):
        x=rng.randint(-35,1120)
        y=rng.randint(1280,1453)
        rx=rng.randint(25,88)
        ry=rng.randint(20,53)
        col=((31+j%4*9),(89+j%5*10),(66+j%3*11),220)
        for k in range(5):
            cx=x+(k-2)*rx*.45
            cy=y+math.sin(k*1.8+j)*ry*.36
            d.ellipse((cx-rx*.65,cy-ry,cx+rx*.65,cy+ry),fill=col)
        for k in range(3):
            xx=x+rng.randint(-rx,rx)
            yy=y-rng.randint(4,ry+7)
            d.ellipse((xx-7,yy-3,xx+8,yy+4),fill=(156,186,115,114))
    return plate


def _meadow() -> Image.Image:
    image=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(image)
    d.polygon([(0,1361),(200,1351),(380,1364),(602,1353),
               (800,1361),(1080,1343),(1080,1920),(0,1920)],
              fill=(41,91,69,255))
    for j in range(18):
        y=1373+j*31
        hue=j%4
        d.polygon([(0,y+12*math.sin(j)),(270,y-17),(590,y+19),
                   (790,y-11),(1080,y+15),(1080,y+51),(0,y+51)],
                  fill=(43+hue*3,98+hue*4,70+hue*2,255))
    # Paint translucent botanical texture in a separate overlay: drawing
    # RGBA straight onto an opaque ground would punch alpha holes in it.
    texture=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(texture)
    rng=random.Random(11503)
    for j in range(1350):
        x=rng.randrange(0,1080)
        y=rng.randrange(1373,1920)
        blade=rng.randrange(6,32)
        col=(73+j%6*8,120+j%5*8,65+j%5*7,125)
        d.line((x,y,x+rng.randrange(-11,13),y-blade),
               fill=col,width=1+j%3)
        if j%14==0:
            d.ellipse((x-4,y-blade-2,x+4,y-blade+5),
                      fill=(232,192+j%3*8,135,190))
    # Pebbles and tiny local ambient occlusion anchors.
    for j in range(105):
        x=rng.randint(2,1075)
        y=rng.randrange(1430,1915)
        r=rng.randint(3,11)
        d.ellipse((x-r,y-r*.35,x+r,y+r*.4),fill=(18,61,57,92))
        d.arc((x-r,y-r*.6,x+r,y+r*.3),170,333,
              fill=(189,181,136,123),width=2)
    image.alpha_composite(texture)
    return image


def _foreground() -> Image.Image:
    plate=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(plate)
    rng=random.Random(4802)
    for j in range(185):
        x=rng.randint(-50,1130)
        y=rng.randint(1460,1990)
        length=rng.randint(46,190)
        tip=x+rng.randint(-43,43)
        color=(38+j%3*12,92+j%4*12,66+j%5*7,152+j%4*12)
        d.line((x,y,tip,y-length),fill=color,width=3+j%4)
        for side in (-1,1):
            if j%4:
                bx=x+(tip-x)*.56
                by=y-length*.55
                leaf_len=rng.randint(13,37)
                d.ellipse((bx+side*leaf_len-13,by-7,
                           bx+side*leaf_len+13,by+7),
                          fill=(61+j%4*9,126+j%3*14,80,113))
        if j%13==0:
            flower_y=y-length-8
            d.ellipse((tip-8,flower_y-8,tip+8,flower_y+8),
                      fill=(240,180,129,185))
            d.ellipse((tip-3,flower_y-3,tip+3,flower_y+3),
                      fill=(252,224,162,208))
    return plate


def _grade() -> Image.Image:
    # One-time feathered corner falloff (no flickering digital film grain).
    small=(270,480)
    mask=Image.new("L",small,0)
    pixels=mask.load()
    for y in range(small[1]):
        for x in range(small[0]):
            dx=(x-small[0]*.5)/(small[0]*.61)
            dy=(y-small[1]*.51)/(small[1]*.66)
            rr=math.sqrt(dx*dx+dy*dy)
            pixels[x,y]=max(0,min(77,round((max(0,rr-.51)**1.35)*83)))
    mask=mask.resize(SIZE,Image.Resampling.BICUBIC)
    plate=Image.new("RGBA",SIZE,(4,20,29,0))
    plate.putalpha(mask)
    return plate


@lru_cache(maxsize=1)
def plates() -> dict[str,Image.Image]:
    result=dict(sky=_sky(),clouds=_clouds(),ridges=_ridges(),
                sunbeams=_shafts(),trees=_trees(),understory=_understory(),
                meadow=_meadow(),foreground=_foreground(),grade=_grade())
    if any(img.size!=SIZE or img.mode!="RGBA" for img in result.values()):
        raise AssertionError("Cinematic world plate contract violated")
    return result


def drifting_clouds(t: float) -> Image.Image:
    if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=7.2:
        raise ValueError("Invalid cinematic world clock")
    # Natural slow travel, never a duplicated still background.
    src=plates()["clouds"]
    canvas=Image.new("RGBA",SIZE)
    canvas.alpha_composite(src,(round(9*math.sin(.23*t)),round(3*math.sin(.37*t))))
    return canvas


def living_light(t: float) -> Image.Image:
    """World anchored, wind-driven light motes; animation survives camera pans."""
    if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=7.2:
        raise ValueError("Invalid cinematic world clock")
    image=Image.new("RGBA",SIZE)
    d=ImageDraw.Draw(image)
    rng=random.Random(82761)
    for j in range(47):
        x=rng.randrange(100,1040)
        y=rng.randrange(620,1370)
        phase=rng.random()*math.tau
        x+=math.sin(.8*t+phase)*23 + t*(2+j%3)
        y+=math.sin(1.1*t+phase)*17 - t*(1+j%4)*1.4
        pulse=.5+.5*math.sin(2.2*t+phase)
        alpha=round(28+105*pulse)
        radius=(2+j%3)
        d.ellipse((x-radius*3,y-radius*3,x+radius*3,y+radius*3),
                  fill=(255,205,133,round(alpha*.19)))
        d.ellipse((x-radius,y-radius,x+radius,y+radius),
                  fill=(251,238,185,alpha))
    return image
