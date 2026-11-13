"""Aspect-preserving world-first portrait composition for original 2.5D scenes.

The owned scene remains a real moving shot, never a stretched square or a
blurred enlarged background. A bounded edge matte gently joins the original
art to the portrait canvas. The text/caption renderer stays independent.
"""
from __future__ import annotations

import math

from PIL import Image, ImageChops

VERSION = "edge-matted-full-width-authored-world-v1"


def composite_authored_world(canvas: Image.Image, artwork: Image.Image) -> Image.Image:
    """Integrate a validated authored RGBA world into a 9:16 RGB frame.

    Full-width art receives up to 63% of the height, in the central visual
    region. Original aspect ratio is always preserved. Narrow pictures are
    centered without cropping away authored silhouettes; no AI infill.
    """
    if (not isinstance(canvas,Image.Image) or canvas.mode!="RGB"
            or not isinstance(artwork,Image.Image) or artwork.mode!="RGBA"
            or canvas.width not in (360,720,1080)
            or canvas.height!=canvas.width*16//9
            or not 64<=artwork.width<=1200
            or not 64<=artwork.height<=1200):
        raise ValueError("Expected bounded RGB portrait and approved RGBA art")
    width,height=canvas.size
    max_h=round(height*.63)
    scale=min(width/artwork.width,max_h/artwork.height)
    target=(max(1,round(artwork.width*scale)),
            max(1,round(artwork.height*scale)))
    picture=artwork.resize(target,Image.Resampling.LANCZOS)
    # Fade only the matte boundary, not the actual illustrated body or
    # subtitles. The authored picture itself is never cropped or distorted.
    feather=max(2,round(target[1]*.046))
    taper=[]
    for y in range(target[1]):
        strength=min(1.,(y+1)/feather,(target[1]-y)/feather)
        strength=strength*strength*(3-2*strength)
        taper.append(round(255*strength))
    mask_line=Image.new("L",(1,target[1]))
    mask_line.putdata(taper)
    alpha=ImageChops.multiply(
        picture.getchannel("A"),
        mask_line.resize(target,Image.Resampling.NEAREST))
    x=(width-target[0])//2
    y=round(height*.15)
    result=canvas.copy()
    result.paste(picture,(x,y),alpha)
    return result


def shot_title_alpha(frame: int, first: int, last: int) -> int:
    """A cinematic introductory caption fades instead of persisting all shot."""
    if (type(frame) is not int or type(first) is not int
            or type(last) is not int or last<=first
            or not first<=frame<last):
        raise ValueError("Invalid narrated frame span")
    hold=min(54,max(22,round((last-first)*.22)))
    decay=max(8,min(15,last-first-hold))
    elapsed=frame-first
    if elapsed<=hold:
        return 255
    if elapsed>=hold+decay:
        return 0
    u=(elapsed-hold)/decay
    smooth=u*u*(3-2*u)
    return max(0,min(255,round(255*(1-smooth))))
