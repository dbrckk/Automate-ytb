"""Shared original 2.5D light-and-shadow relief of authored scene pigments.

Everything derives from the ALREADY rendered scene's own luminance:
no random microtextures, stock imagery, brand assets, model downloads,
GPU, web requests, 3D normals or synthetic source geometry. At every
frame the same pigment yields the same local shading, avoiding shimmer.
This is a restrained screen-space art treatment, not physical ray tracing.
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter

VERSION="source-derived-directional-material-relief-p524-v1"

# (local warm bounce, opposite cool occlusion, bounded gain).
# Semantic palettes match the global science/forest scene look names.
MATERIALS={
    "ocean":((165,231,251),(11,41,78),1.15),
    "volcano":((255,198,141),(30,25,44),1.27),
    "aurora":((176,255,222),(20,28,65),1.06),
    "storm":((184,217,253),(13,27,56),1.13),
    "forest":((252,229,169),(18,42,36),1.21),
    "rainbow":(None,None,0.),
    "daylight":(None,None,0.),
    "neutral":(None,None,0.),
}


def sculpt_authored_material(image:Image.Image, *, look:str)->Image.Image:
    """Emphasize actual material ridges while preserving existing geometry.

    Source is one RGB world crop, never the final subtitle/title layer.
    Luminance forms a 1/3-resolution smooth normal-proxy: raking shadows
    and bounce derive only from gradients of AUTHOR-PRESENT pigmentation.
    Any constant input is bit-for-bit unchanged. This is intentionally a
    material lighting pass, NOT new geometry/photorealism generation.
    """
    if (not isinstance(image,Image.Image) or image.mode!="RGB"
            or not 32<=image.width<=1920 or not 32<=image.height<=1920
            or type(look) is not str or look not in MATERIALS):
        raise ValueError("Invalid original source material light pass")
    light_rgb,shadow_rgb,gain=MATERIALS[look]
    if not gain:
        return image
    w,h=image.size
    sw,sh=max(32,w//3),max(32,h//3)
    height=image.convert("L").resize((sw,sh),Image.Resampling.BILINEAR)
    height=height.filter(ImageFilter.GaussianBlur(1.0))
    # Opposing authored surface light: local gradients indicate curvature.
    # Fixed source-space direction prevents time-incoherent frame shimmer.
    east=ImageChops.offset(height,2,0)
    south=ImageChops.offset(height,0,2)
    west=ImageChops.offset(height,-2,0)
    north=ImageChops.offset(height,0,-2)
    highlight=ImageChops.add(ImageChops.subtract(height,east),
                             ImageChops.subtract(height,south),scale=2)
    shadow=ImageChops.add(ImageChops.subtract(height,west),
                          ImageChops.subtract(height,north),scale=2)
    light=highlight.point(lambda v:min(69,round(v*2.35*gain)))
    dark=shadow.point(lambda v:min(58,round(v*2.00*gain)))
    result=image.convert("RGBA")
    for color,alpha in ((shadow_rgb,dark),(light_rgb,light)):
        mask=alpha.resize(image.size,Image.Resampling.BILINEAR)
        layer=Image.new("RGBA",image.size,(*color,0))
        layer.putalpha(mask)
        result=Image.alpha_composite(result,layer)
    return result.convert("RGB")
