"""Shared original 2.5D continuous optical motion and alpha-safe subpixel parallax.

Source-space optical warping resamples ONLY existing authored pixels:
no random per-frame textures, image enlargement, external assets, 3D,
cloud inference or invented geometric objects. A continuous analytical
field makes water, rising heat, air and atmospheric curtains subtly
refract at real video frame rates. RGB scene text is drawn AFTER this
effect in the master science compositor.

The same CPU module also samples independent authored RGBA depth layers
at fractional pixels using premultiplied alpha, avoiding the stuttering
round(camera * parallax) quantization previously seen in camera moves.
"""
from __future__ import annotations

import math
from PIL import Image

VERSION = "shared-original-optical-motion-subpixel25d-p523-v1"

# Each preset is (peak displacement in original source pixels, temporal
# angular speed, x spatial wave count, y spatial wave count). These values
# are *illustrative* original art directions, not estimates of real ocean,
# atmospheric, magmatic or refractive-index physics.
PRESETS = {
    "storm": (1.25, 1.70, 3.7, 2.8),
    "volcano": (2.15, 1.85, 3.9, 3.2),
    "aurora": (1.70, .82, 2.1, 3.6),
    "ocean": (3.05, 1.20, 2.9, 2.3),
    "forest": (.95, .73, 3.0, 1.7),
    "rainbow": (0., 0., 0., 0.),
    "daylight": (0., 0., 0., 0.),
    "neutral": (0., 0., 0., 0.),
}
MESH_STEP = 64


def _clock(t: float, duration: float) -> None:
    if (type(t) not in (float, int) or
            type(duration) not in (float, int) or
            not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180):
        raise ValueError("Invalid optical source timeline")


def _displacement(x: int, y: int, w: int, h: int, *,
                  t: float, preset: tuple[float,float,float,float]
                  ) -> tuple[float,float]:
    """Continuous shared vertices: no seams between adjacent mesh tiles."""
    amp, speed, wave_x, wave_y = preset
    # Exact source-crop boundaries never change. The already existing
    # seamless world mask independently protects the post-process grade.
    edge=min(x, y, w-x, h-y)
    q=max(0.,min(1.,edge / max(16,min(80,min(w,h)//6))))
    fade=q*q*(3-2*q)
    if fade==0:
        return float(x),float(y)
    nx=x/w
    ny=y/h
    time_phase=t*speed
    # Two noncommensurate, smooth source-space movements. Critically,
    # no integer frame indexes or random seeds and no harsh tile boundary.
    dx=amp*fade*(.73*math.sin(math.tau*(nx*wave_x+ny*.61)+time_phase)
                 +.27*math.sin(math.tau*(ny*2.3-nx*.9)-time_phase*.47))
    dy=amp*fade*(.66*math.sin(math.tau*(ny*wave_y-nx*.56)+time_phase*.74)
                 +.34*math.cos(math.tau*(nx*1.9+ny*.62)+time_phase*.61))
    return max(0.,min(float(w),x+dx)),max(0.,min(float(h),y+dy))


def refract_source(image: Image.Image, *, look: str,
                   t: float, duration: float) -> Image.Image:
    """Warp authored RGB world material continuously without creating art.

    Runtime scales with a coarse ~64px mesh, not millions of Python pixel
    loops. Source corners and outer edges stay exactly invariant. Source
    pixels are never mutated. Neutral/daylight/precise optics stay unwarped.
    """
    if (not isinstance(image,Image.Image) or image.mode!="RGB"
            or not 32<=image.width<=1920 or not 32<=image.height<=1920
            or type(look) is not str or look not in PRESETS):
        raise ValueError("Invalid original optical source material")
    _clock(t,duration)
    preset=PRESETS[look]
    if preset[0]==0:
        return image
    w,h=image.size
    points={}
    def point(x:int,y:int)->tuple[float,float]:
        key=(x,y)
        if key not in points:
            points[key]=_displacement(x,y,w,h,t=t,preset=preset)
        return points[key]
    cells=[]
    for y in range(0,h,MESH_STEP):
        bottom=min(h,y+MESH_STEP)
        for x in range(0,w,MESH_STEP):
            right=min(w,x+MESH_STEP)
            tl=point(x,y)
            bl=point(x,bottom)
            br=point(right,bottom)
            tr=point(right,y)
            cells.append(((x,y,right,bottom),
                          (*tl,*bl,*br,*tr)))
    return image.transform(image.size,Image.Transform.MESH,cells,
                           resample=Image.Resampling.BILINEAR)


def translate_subpixel(source: Image.Image,
                       dx: float, dy: float) -> Image.Image:
    """Move a real RGBA 2.5D source plane with smooth premultiplied edges.

    Interpolating raw RGBA can add dark fringes around partially covered
    particles, hair, sparks and clouds. Pillow's RGBa mode interpolates
    premultiplied color, then conversion restores normal alpha for correct
    final source-over composition. Output is a new image unless identity.
    """
    if (not isinstance(source,Image.Image) or source.mode!="RGBA"
            or not 16<=source.width<=1920
            or not 16<=source.height<=1920
            or type(dx) not in (int,float) or type(dy) not in (int,float)
            or not math.isfinite(dx) or not math.isfinite(dy)
            or abs(dx)>400 or abs(dy)>400):
        raise ValueError("Invalid 2.5D subpixel source displacement")
    if dx==0 and dy==0:
        return source
    rgba=source.convert("RGBa")
    moved=rgba.transform(
        source.size,Image.Transform.AFFINE,(1.,0.,-dx,0.,1.,-dy),
        resample=Image.Resampling.BILINEAR,fillcolor=(0,0,0,0))
    return moved.convert("RGBA")
