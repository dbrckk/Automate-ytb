"""Shared 2.5D surface relief from actual authored alpha silhouettes.

A fast, deterministic painter's rim-light/shadow on each independently
composited RGBA plate. No reconstructed 3D meshes, AI imagery, random frames,
coloring outside silhouettes, or blurred enlargement of simple shapes.
"""
from __future__ import annotations

from PIL import Image, ImageChops

VERSION="material-aware-2p5d-silhouette-light-v1"

# (offset pixels, warm/cool top-rim highlight, highlight strength,
#  broad shadow hue, shadow strength). Settings tuned conservatively.
MATERIALS={
    "none": (0,(0,0,0),0,(0,0,0),0),
    "soft": (4,(169,210,242),46,(15,28,50),26),
    "metal": (3,(228,234,238),89,(16,32,43),55),
    "fabric": (3,(255,233,208),48,(27,35,58),31),
    "foliage": (4,(202,234,161),63,(21,53,47),39),
    "mineral": (4,(229,207,165),65,(36,33,45),42),
    "water": (2,(177,226,244),51,(15,36,59),35),
}


def _shift(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    # Affine fill with zero; unlike ImageChops.offset this never wraps
    # the right edge to the left and creates a frame-border artifact.
    return mask.transform(mask.size,Image.Transform.AFFINE,
                          (1,0,-dx,0,1,-dy),
                          resample=Image.Resampling.NEAREST,fillcolor=0)


def relight_surface(image:Image.Image,material:str) -> Image.Image:
    if (not isinstance(image,Image.Image) or image.mode!="RGBA"
            or material not in MATERIALS):
        raise ValueError("Unsupported original 2.5D surface material")
    if material=="none":
        return image
    depth,top_color,top_gain,shadow_color,shadow_gain=MATERIALS[material]
    mask=image.getchannel("A")
    # No invented rim for complete opaque backgrounds: those have no
    # alpha silhouette and receive only the global authored color pass.
    if mask.getextrema() in ((0,0),(255,255)):
        return image
    # Only the true inside edge is shaded. The original author's fine
    # details, spatial color and alpha remain intact.
    away=_shift(mask,depth,depth)
    toward=_shift(mask,-depth,-depth)
    highlight=ImageChops.subtract(mask,away).point(
        lambda value: min(100,round(value*top_gain/255)))
    shadow=ImageChops.subtract(mask,toward).point(
        lambda value: min(88,round(value*shadow_gain/255)))
    result=image.copy()
    for color,alpha in ((shadow_color,shadow),(top_color,highlight)):
        if alpha.getextrema()[1]:
            rim=Image.new("RGBA",image.size,(*color,0))
            rim.putalpha(alpha)
            result=Image.alpha_composite(result,rim)
    result.putalpha(mask)
    return result
