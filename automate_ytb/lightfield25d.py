"""Reusable light-field and cinematic material response for any 2.5D world.

Works on authored RGBA plates at their original resolution; no 3D, AI,
external asset or paid service. Camera-independent lighting is computed in
stage coordinates and masked by each plate's original alpha silhouette.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math

from PIL import Image, ImageChops, ImageEnhance

VERSION="shared-25d-depth-lightfield-p57-v1"


@dataclass(frozen=True)
class Light25D:
    x: float
    y: float
    radius: float
    strength: float = .7
    color: tuple[int,int,int] = (255,197,126)
    ambient: float = .96

    def __post_init__(self):
        for key,value in (("x",self.x),("y",self.y),
                          ("radius",self.radius),("strength",self.strength),
                          ("ambient",self.ambient)):
            if type(value) not in (float,int) or not math.isfinite(value):
                raise ValueError("Nonfinite 2.5D lighting parameter: "+key)
        if (not -1920<=self.x<=3840 or not -1920<=self.y<=3840
                or not 4<=self.radius<=3000
                or not 0<=self.strength<=2
                or not .45<=self.ambient<=1.3
                or not isinstance(self.color,tuple)
                or len(self.color)!=3 or
                any(type(c) is not int or not 0<=c<=255 for c in self.color)):
            raise ValueError("Invalid authored 2.5D light")


@lru_cache(maxsize=24)
def _falloff(size:tuple[int,int],x:float,y:float,radius:float)->Image.Image:
    if (not isinstance(size,tuple) or len(size)!=2 or
            any(type(n) is not int or not 16<=n<=1920 for n in size)):
        raise ValueError("Invalid light field stage")
    w,h=size
    # Calculate 1/4-resolution radial field then interpolate; this is
    # smooth illumination, not a replacement for detailed source assets.
    fw,fh=max(16,(w+3)//4),max(16,(h+3)//4)
    small=Image.new("L",(fw,fh))
    pixels=small.load()
    for yy in range(fh):
        sy=(yy+.5)*h/fh
        for xx in range(fw):
            sx=(xx+.5)*w/fw
            d=math.hypot(sx-x,sy-y)/radius
            pixels[xx,yy]=round(255*max(0.,1.-d*d)**2) if d<1 else 0
    return small.resize(size,Image.Resampling.BICUBIC)


def illuminate(image:Image.Image,light:Light25D, *,
               z:int,shift_x:int=0,shift_y:int=0)->Image.Image:
    """Apply motivated illumination with depth attenuation and alpha safety.

    Source images are never modified. The original alpha channel is retained
    byte-for-byte; the light cannot draw outside the authored silhouette.
    """
    if (not isinstance(image,Image.Image) or image.mode!="RGBA" or
            not isinstance(light,Light25D) or
            type(z) is not int or not 0<=z<=100 or
            type(shift_x) is not int or type(shift_y) is not int or
            abs(shift_x)>400 or abs(shift_y)>400):
        raise ValueError("Invalid source/light/depth for 2.5D compositing")
    if light.strength==0 and light.ambient==1:
        return image
    alpha=image.getchannel("A")
    if alpha.getextrema()==(0,0):
        return image
    # Preserve color variation and existing authored material shading.
    rgb=Image.merge("RGB",image.split()[:3])
    if light.ambient!=1:
        rgb=ImageEnhance.Brightness(rgb).enhance(light.ambient)
    depth_gain=(.38+.62*z/100)*light.strength
    if depth_gain>0:
        field=_falloff(image.size,light.x-shift_x,
                       light.y-shift_y,light.radius)
        # Never boost outside the original source pixels. Color and
        # brightness respond smoothly to physically localized event lights.
        mask=field.point(lambda v:min(180,round(v*depth_gain*.66)))
        mask=ImageChops.multiply(mask,alpha)
        glow=Image.new("RGB",image.size,light.color)
        rgb=Image.composite(glow,rgb,mask)
    rgb.putalpha(alpha)
    return rgb
