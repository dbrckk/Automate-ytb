"""P5.2 original 2.5D storm materials, offline and fully deterministic.

Layered convective cloud density, painted internal shadows, warm/cool material
variation and a grounded truss mast with dimensional industrial scenery.
Original procedural illustrations; not claims of photographic simulation.
"""
from __future__ import annotations
from functools import lru_cache
import math
import random
from PIL import Image, ImageDraw, ImageFilter

ART_VERSION = "storm-materials-p52-sculpted-billows-truss-and-urban-depth"


def _noise(width: int, height: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    layers = []
    for scale, weight in ((29, .43), (13, .28), (6, .19), (3, .10)):
        w, h = max(4, width // scale), max(4, height // scale)
        raw = Image.frombytes("L", (w, h),
                              bytes(rng.randrange(256) for _ in range(w*h)))
        layers.append((raw.resize((width, height),
                      Image.Resampling.BICUBIC).load(), weight))
    out = Image.new("L", (width, height))
    pixels = out.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = round(sum(p[x, y] * weight for p, weight in layers))
    return out


@lru_cache(maxsize=9)
def detailed_cloud_volume(depth: int, variant: int) -> Image.Image:
    """Sculpted alpha silhouettes with multi-octave cloud-face material.

    Soft feathers on ALL four sprite edges prevent rectangular seams.
    Different near/mid/far depths vary scale, hue, density and parallax.
    """
    if (type(depth) is not int or depth not in (0, 1, 2)
            or type(variant) is not int or not 0 <= variant < 3):
        raise ValueError("Invalid storm cloud material")
    width, height = ((620, 300) if depth == 0 else
                     (670, 285) if depth == 1 else (760, 265))
    rng = random.Random(1717 + variant*83 + depth*1021)
    silhouette = Image.new("L", (width, height))
    d = ImageDraw.Draw(silhouette)
    foundation = []
    for i in range(15):
        x = round(-55 + i*(width+110)/14)
        y = round(height*(.59+.07*math.sin(i*.65+variant))
                  + rng.uniform(-13, 13))
        foundation.append((x, y))
    d.polygon(foundation + [(width+10, height*.90), (-10, height*.90)],
              fill=177)
    for i in range(29):
        x = round(-25+i*(width+60)/28+rng.uniform(-24, 24))
        rise = .15+.20*math.sin(i*.71+variant*2)**2
        y = round(height*(.57-rise)+rng.uniform(-19, 19))
        radius = round(width*.040+rng.uniform(width*.018, width*.092))
        sy = round(radius*rng.uniform(.48, .96))
        d.ellipse((x-radius, y-sy, x+radius, y+sy),
                  fill=190+rng.randrange(45))
    for j in range(13):
        cx = rng.randrange(-60, width+60)
        cy = round(height*.72+rng.uniform(-10, 30))
        rx, ry = rng.randrange(26, 93), rng.randrange(9, 30)
        d.ellipse((cx-rx, cy-ry, cx+rx, cy+ry),
                  fill=125+rng.randrange(65))
    silhouette = silhouette.filter(
        ImageFilter.GaussianBlur(5+depth*1.5))
    field = _noise(width, height, 917+variant*137+depth*181)
    contours, noise = silhouette.load(), field.load()
    accents = Image.new("L", (width, height))
    hd = ImageDraw.Draw(accents)
    hi_rng = random.Random(717+variant*51+depth*95)
    for _ in range(18):
        x = round(hi_rng.uniform(0, width))
        y = round(height*hi_rng.uniform(.20, .55))
        rx = hi_rng.randrange(18, 67)
        hd.ellipse((x-rx, y-13, x+rx, y+15),
                   fill=hi_rng.randrange(50, 145))
    highlights = accents.filter(ImageFilter.GaussianBlur(16)).load()
    material = Image.new("RGBA", (width, height))
    pixels = material.load()
    for y in range(height):
        v = y / height
        edge_y = max(0., min(1., y/55., (height-1-y)/86.))
        edge_y = edge_y*edge_y*(3-2*edge_y)
        for x in range(width):
            alpha = contours[x, y]
            if alpha < 3:
                continue
            n = (noise[x, y]-126)/126
            striation = math.sin(x*.032+y*.058+n*4)*6
            brightness = (52*(1-v)**1.8 - 38*v**1.6 +
                          n*47 + highlights[x, y]*.28 + striation)
            base = (39+depth*12+variant*2, 51+depth*13+variant*2,
                    72+depth*14)
            warmth = 10*max(0, 1-v)*max(0, math.sin(x*.009+variant))
            red = round(base[0]+brightness*.92+warmth)
            green = round(base[1]+brightness+warmth*.35)
            blue = round(base[2]+brightness*1.10)
            edge_x = max(0., min(1., x/92., (width-1-x)/112.))
            feather = edge_x*edge_x*(3-2*edge_x)*edge_y
            opacity = round((alpha*(.69+depth*.02)+n*14)*feather)
            pixels[x, y] = (max(0, min(255, red)),
                            max(0, min(255, green)),
                            max(0, min(255, blue)),
                            max(0, min(243, opacity)))
    return material


def paint_industrial_detail(draw: ImageDraw.ImageDraw, t: float) -> None:
    """Layered perspective city, lit materials and triangulated metal mast.

    Tower tip stays at (700,695), preserving the electrical contact contract.
    """
    if type(t) not in (int, float) or not math.isfinite(t):
        raise ValueError("Invalid terrain time")
    draw.polygon([(0,775),(104,766),(207,779),(323,748),(430,763),
                  (540,750),(657,775),(771,746),(903,765),(1080,750),
                  (1080,811),(0,811)], fill=(25,43,57,231))
    for i in range(14):
        x = 18+i*81+(i*i*7)%28
        w = 35+(i*13)%46
        top = 741-(i*23)%72
        body = (20+i%3*4,37+i%4*3,54+i%3*3,240)
        draw.polygon([(x,top),(x+w-9,top-8),(x+w+2,top+1),
                      (x+2,top+10)], fill=(41,61,75,245))
        draw.polygon([(x+2,top+10),(x+w+2,top+1),
                      (x+w+2,810),(x+2,810)], fill=body)
        draw.polygon([(x+w-6,top+6),(x+w+2,top+1),
                      (x+w+2,810),(x+w-6,807)],
                     fill=(12,27,44,234))
        if i%3 == 0:
            draw.rectangle((x+7,top-31,x+14,top+4),
                           fill=(43,58,66,245))
            draw.line((x+5,top-31,x+17,top-31),
                      fill=(99,120,127,185),width=3)
        for yy in range(top+24,804,21):
            for xx in range(x+11,x+w-9,18):
                warm = ((185,148,103,87) if (i+xx+yy)%5 == 0
                        else (101,138,157,63))
                draw.rectangle((xx,yy,xx+6,yy+3),fill=warm)
    draw.line((0,806,1080,806), fill=(113,149,164,83),width=3)
    apex = (700,695)
    left, right = (655,814),(746,814)
    draw.polygon((apex,(717,688),(763,807),right),
                 fill=(20,42,55,245))
    draw.line((apex,(717,688),(763,807)),
              fill=(62,91,108,241),width=4,joint="curve")
    draw.line((apex,left),fill=(52,79,94,255),width=11)
    draw.line((apex,right),fill=(36,64,79,255),width=11)
    draw.line((apex,left),fill=(182,203,210,255),width=4)
    draw.line((apex,right),fill=(119,152,169,255),width=4)
    draw.line((700,699,700,805),fill=(139,164,177,213),width=3)
    for i in range(11):
        q=(i+1)/12
        y=695+q*119
        l,r=700-q*45,700+q*46
        draw.line((l,y,r,y),fill=(117,155,172,247),
                  width=3 if i%3 else 4)
        if i<10:
            y2=695+(i+2)/12*119
            l2,r2=700-(i+2)/12*45,700+(i+2)/12*46
            draw.line((l,y,r2,y2),fill=(113,147,163,210),width=2)
            draw.line((r,y,l2,y2),fill=(52,80,99,206),width=2)
        if i%2==0:
            draw.ellipse((l-2,y-2,l+2,y+2),fill=(222,225,210,206))
            draw.ellipse((r-2,y-2,r+2,y+2),fill=(191,206,213,198))
    draw.line((655,814,746,814),fill=(147,170,178,242),width=6)
    draw.rectangle((690,690,710,697),fill=(95,121,133,255))
    draw.ellipse((695,690,705,700),fill=(246,99,81,255))
    draw.ellipse((698,692,702,696),fill=(255,226,177,255))
    draw.line((700,708,591,812),fill=(111,145,155,124),width=2)
    draw.line((700,708,807,812),fill=(111,145,155,124),width=2)
    draw.line((591,810,598,813),fill=(157,172,163,173),width=3)
    draw.line((799,813,808,812),fill=(157,172,163,173),width=3)
    for i in range(110):
        x=(i*191+63)%1135-22
        y=823+(i*43)%109
        closeness=(y-820)/110
        length=round(5+closeness*44+(i%4)*3)
        shimmer=round(8*math.sin(t*.72+i*.71))
        tint=(91+round(25*closeness),128+round(21*closeness),
              145+round(23*closeness),round(25+42*closeness))
        draw.line((x+shimmer,y,x+shimmer+length,y),
                  fill=tint,width=1 if i%3 else 2)
