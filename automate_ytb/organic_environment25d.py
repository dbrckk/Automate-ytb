"""Reusable, physically motivated *2.5D* environment assets for every topic.

These are original procedurally painted RGBA planes, not extruded meshes,
stock images, Ken Burns backgrounds, or unstructured pixel noise. Spatial
coherence, material bands, true alpha, and repeatable seeds are deliberate.
The layers can be used for science, nature, stories and product footage.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

VERSION = "organic-environment-25d-p59-v1"


def _check(size: tuple[int, int], seed: int, color: tuple[int,int,int]):
    if (not isinstance(size, tuple) or len(size) != 2
            or any(type(v) is not int or not 128 <= v <= 1920 for v in size)
            or type(seed) is not int or not 0 <= seed <= 1_000_000
            or not isinstance(color,tuple) or len(color) != 3
            or any(type(v) is not int or not 0 <= v <= 255 for v in color)):
        raise ValueError("Invalid bounded original 2.5D environment asset")


@lru_cache(maxsize=28)
def _field(size: tuple[int,int], seed: int) -> Image.Image:
    """Smooth, wavelength-separated density, deterministic at every pixel."""
    w,h=size
    rng=random.Random(seed)
    # Large undulations stay coherent; small spatial scales break the repeated
    # elementary ellipses and expose softly grouped material microstructure.
    bands=[]
    for scale in (100,42,15,5):
        sw,sh=max(3,(w+scale-1)//scale),max(3,(h+scale-1)//scale)
        data=bytes(rng.randrange(256) for _ in range(sw*sh))
        source=Image.frombytes("L",(sw,sh),data)
        bands.append(source.resize(size,Image.Resampling.BICUBIC))
    a=Image.blend(bands[0],bands[1],.39)
    b=Image.blend(bands[2],bands[3],.35)
    return Image.blend(a,b,.28)


def ridge_points(width: int, *, seed: int, horizon: float,
                 relief: float, step: int = 7) -> tuple[tuple[int,int], ...]:
    """Irregular multi-scale continuous strata, without triangular repetition."""
    if (type(width) is not int or not 128 <= width <= 1920
            or type(seed) is not int or not 0 <= seed <= 1_000_000
            or type(horizon) not in (int,float) or not math.isfinite(horizon)
            or not .10 <= horizon <= .90
            or type(relief) not in (int,float) or not math.isfinite(relief)
            or not .008 <= relief <= .28
            or type(step) is not int or not 3 <= step <= 15):
        raise ValueError("Invalid original natural ridge")
    rng=random.Random(seed)
    phases=[rng.uniform(0,math.tau) for _ in range(5)]
    freqs=(1.4,3.3,7.9,18.3,42.7)
    weights=(.53,.24,.12,.07,.04)
    coords=[]
    for x in list(range(0,width,step))+[width-1]:
        q=x/max(1,width-1)
        height=sum(w*math.sin(f*q*math.tau+phase)
                   for w,f,phase in zip(weights,freqs,phases))
        # Height is intentionally unitless; the caller scales it into the
        # actual material depth rather than inferring a false 3D volume.
        y=round((horizon+relief*height)*10000)
        coords.append((x,y))
    return tuple(coords)


def _scaled_ridge(width:int,height:int,seed:int,horizon:float,
                  relief:float) -> list[tuple[int,int]]:
    return [(x,max(0,min(height-1,round(y*height/10000))))
            for x,y in ridge_points(width,seed=seed,
                                    horizon=horizon,relief=relief)]


@lru_cache(maxsize=20)
def cloud_bank(size: tuple[int,int], seed: int,
               color: tuple[int,int,int] = (201,228,246),
               opacity: int = 116) -> Image.Image:
    """Irregular stratified cloud bands with density-derived alpha.

    One connected layered body has a coherent, fractured top contour;
    it is not constructed from a row of disconnected translucent circles.
    """
    _check(size,seed,color)
    if type(opacity) is not int or not 5<=opacity<=235:
        raise ValueError("Invalid cloud optical depth")
    w,h=size
    silhouette=Image.new("L",size)
    points=_scaled_ridge(w,h,seed,.32,.21)
    lower=[(w-1,round(h*.91)),(0,round(h*.91))]
    ImageDraw.Draw(silhouette).polygon(points+lower,fill=255)
    silhouette=silhouette.filter(ImageFilter.GaussianBlur(max(3,round(h*.024))))
    density=_field(size,seed+611)
    # Density makes local shadows/holes from multiple coherent wavelengths,
    # not noisy independent frame pixels; edges remain soft in alpha.
    body=density.point(lambda v: max(0,min(255,round((v-83)*1.9))))
    alpha=ImageChops.multiply(silhouette,body).point(
        lambda v: round(v*opacity/255))
    low=tuple(round(v*.37) for v in color)
    high=tuple(min(255,round(v*1.10)) for v in color)
    rgb=ImageOps.colorize(density,low,high,mid=color,blackpoint=38,
                          whitepoint=208,midpoint=121)
    result=rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


@lru_cache(maxsize=20)
def terrain_strata(size: tuple[int,int], seed: int,
                   color: tuple[int,int,int] = (64,78,87),
                   opacity: int = 180) -> Image.Image:
    """Four eroded 2D strata with correlated rock-face lines and depth."""
    _check(size,seed,color)
    if type(opacity) is not int or not 12<=opacity<=255:
        raise ValueError("Invalid sediment layer opacity")
    w,h=size
    image=Image.new("RGBA",size)
    rng=random.Random(seed)
    depths=((.28,.09,.54),(.44,.077,.72),(.59,.06,.92),(.73,.037,1.10))
    for index,(level,relief,mul) in enumerate(depths):
        ridge=_scaled_ridge(w,h,seed+index*173,level,relief)
        c=tuple(min(255,max(0,round(v*mul))) for v in color)
        plane=Image.new("RGBA",size)
        d=ImageDraw.Draw(plane)
        d.polygon(ridge+[(w-1,h-1),(0,h-1)],
                  fill=(*c,round(opacity*(.47+index*.125))))
        # Veins track the terrain's strata, never arbitrarily cross the
        # silhouette, and have real spatial frequency at several scales.
        for band in range(1,8):
            advance=band*12+index*4
            trace=[]
            for x,y in ridge[::2]:
                yy=y+advance+round(3.5*math.sin(x*.025+band+index))
                if yy<h-3:
                    trace.append((x,yy))
            if len(trace)>=2:
                shade=tuple(min(255,round(v*.70)) for v in c)
                d.line(trace,fill=(*shade,max(14,52-index*7)),
                       width=1 if band%3 else 2,joint="curve")
        image=Image.alpha_composite(image,plane)
    return image


@lru_cache(maxsize=15)
def water_caustics(size: tuple[int,int], seed: int,
                   color: tuple[int,int,int] = (100,221,240),
                   opacity: int = 48) -> Image.Image:
    """Flow-oriented refracted light paths with connected water-surface folds."""
    _check(size,seed,color)
    if type(opacity) is not int or not 2<=opacity<=130:
        raise ValueError("Invalid underwater caustic intensity")
    w,h=size
    image=Image.new("RGBA",size)
    d=ImageDraw.Draw(image)
    rng=random.Random(seed)
    for lane in range(23):
        base=h*(.08+.75*(lane/23))
        freq=1.7+rng.random()*3.4
        phase=rng.uniform(0,math.tau)
        skew=rng.uniform(-.11,.11)
        points=[]
        for x in range(0,w+9,9):
            q=x/max(1,w)
            y=base+h*(.014*math.sin(q*math.tau*freq+phase)
                      +.007*math.sin(q*math.tau*freq*2.11-phase*.43)
                      +skew*(q-.5)*.11)
            points.append((x,round(y)))
        power=round(opacity*(.30+.45*(1-lane/23)))
        d.line(points,fill=(*color,power),width=2 if lane%4 else 3,
               joint="curve")
    # Controllable, soft diffuse refraction around still-sharp caustic paths.
    bloom=image.filter(ImageFilter.GaussianBlur(8))
    bloom.putalpha(bloom.getchannel("A").point(lambda v:round(v*.48)))
    return Image.alpha_composite(bloom,image)

@lru_cache(maxsize=20)
def open_world_alpha(size: tuple[int,int], feather:int=72) -> Image.Image:
    """Reusable organic-scene alpha transition, without hard slideshow rails.

    Original moving artwork is rendered across the *whole stage*. Only the
    cropped edge of a deliberately composed art plate fades into neighboring
    atmosphere, preserving the 2.5D inner geometry and caption safe zones.
    This is not a blur of the source world or a fake camera zoom.
    """
    if (not isinstance(size,tuple) or len(size)!=2 or
            any(type(v) is not int or not 128<=v<=1920 for v in size)
            or type(feather) is not int or not 8<=feather<=192):
        raise ValueError("Invalid reusable open 2.5D world boundary")
    width,height=size
    margin=min(feather,(width-1)//3,(height-1)//3)
    def taper(index,extent):
        z=max(0.,min(1.,index/margin,(extent-1-index)/margin))
        return round(255*z*z*(3-2*z))
    horizontal=Image.new("L",(width,1))
    horizontal.putdata([taper(x,width) for x in range(width)])
    vertical=Image.new("L",(1,height))
    vertical.putdata([taper(y,height) for y in range(height)])
    return ImageChops.multiply(
        horizontal.resize(size,Image.Resampling.NEAREST),
        vertical.resize(size,Image.Resampling.NEAREST))
