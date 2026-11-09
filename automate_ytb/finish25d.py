"""Shared, purely 2.5D art direction for locally authored moving video.

Applies a restrained but tangible, scene-independent finishing pass to the
WORLD before screen-space editorial lettering, not a fake 3D renderer.
The same function works on science episodes and character-driven animation.
It cannot invent complex geometry: asset richness is separately audited.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

VERSION = "extreme-25d-world-finishing-p55-v1"


@dataclass(frozen=True)
class Look25D:
    contrast: float
    saturation: float
    sharpness: int
    glow: tuple[int,int,int]
    glow_gain: float
    focal_x: float = .52
    focal_y: float = .40

    def __post_init__(self):
        if any(type(x) not in (float,int) or not math.isfinite(x)
               for x in (self.contrast,self.saturation,self.glow_gain,
                         self.focal_x,self.focal_y)):
            raise ValueError("Nonfinite 2.5D look")
        if not (.9<=self.contrast<=1.25 and
                .9<=self.saturation<=1.3 and
                0<=self.glow_gain<=.35 and
                0<=self.focal_x<=1 and 0<=self.focal_y<=1):
            raise ValueError("Unsafe 2.5D finishing gain")
        if type(self.sharpness) is not int or not 0<=self.sharpness<=160:
            raise ValueError("Unsafe 2.5D detail contrast")
        if (not isinstance(self.glow,tuple) or len(self.glow)!=3 or
                any(type(n) is not int or not 0<=n<=255
                    for n in self.glow)):
            raise ValueError("Invalid 2.5D motivated glow color")


LOOKS: dict[str,Look25D]={
    # These are authored LIGHT/COLOR intents, not invented model-generated
    # geometry; original world-layer artists keep full control of assets.
    "storm": Look25D(1.16,1.13,82,(166,200,244),.20,.53,.34),
    "volcano": Look25D(1.17,1.16,75,(254,170,113),.21,.50,.47),
    "aurora": Look25D(1.13,1.22,65,(116,233,203),.20,.50,.31),
    "ocean": Look25D(1.13,1.18,67,(119,212,244),.19,.54,.44),
    "rainbow": Look25D(1.10,1.18,65,(249,222,171),.14,.54,.33),
    "daylight": Look25D(1.09,1.11,60,(250,218,162),.12,.57,.31),
    "forest": Look25D(1.13,1.15,73,(246,208,142),.17,.56,.33),
    "neutral": Look25D(1.11,1.12,66,(199,219,235),.10),
}


def science_look(*, lightning=False, aurora=False, volcano=False,
                 rainbow=False, mode="orbital") -> str:
    """One shared art direction from existing authored scene classification."""
    if lightning:
        return "storm"
    if volcano:
        return "volcano"
    if aurora:
        return "aurora"
    if rainbow:
        return "rainbow"
    if mode=="ocean":
        return "ocean"
    return "daylight"


@lru_cache(maxsize=32)
def _focal_falloff(width:int,height:int,look:str) -> Image.Image:
    """A cached real image-space low-frequency light field, no random flicker.

    Process only 64x64 pixels before interpolation: transparent overlay can
    never contaminate high-frequency captions because those are drawn later.
    """
    style=LOOKS[look]
    low=Image.new("L",(64,64))
    pix=low.load()
    for y in range(64):
        for x in range(64):
            nx=(x/63-style.focal_x)/.48
            ny=(y/63-style.focal_y)/.60
            fall=math.exp(-1.65*(nx*nx+ny*ny))
            pix[x,y]=round(min(30,30*style.glow_gain*fall))
    return low.resize((width,height),Image.Resampling.BICUBIC)


def finish_world(picture:Image.Image, *, bounds:tuple[int,int,int,int],
                 look:str, t:float, duration:float) -> None:
    """In-place 2.5D WORLD finish without changing alpha or caption layers.

    The operation is spatially bounded, repeatable and original-audio neutral.
    No synthetic random frame-noise, camera shake, geometry interpolation or
    extra title cards. Input/output preserve exact RGBA dimensions.
    """
    if (not isinstance(picture,Image.Image) or picture.mode!="RGBA"
            or look not in LOOKS or
            not isinstance(bounds,tuple) or len(bounds)!=4 or
            any(type(v) is not int for v in bounds)):
        raise ValueError("Invalid 2.5D world finishing arguments")
    left,top,right,bottom=bounds
    if not (0<=left<right<=picture.width and
            0<=top<bottom<=picture.height and
            right-left>=32 and bottom-top>=32):
        raise ValueError("Unsafe art-only finishing region")
    if (type(t) not in (float,int) or
            type(duration) not in (float,int) or
            not math.isfinite(t) or not math.isfinite(duration) or
            not 0<=t<=duration<=180):
        raise ValueError("Invalid 2.5D finishing timeline")

    style=LOOKS[look]
    original=picture.crop(bounds)
    alpha=original.getchannel("A")
    rgb=original.convert("RGB")
    # Local contrast reveals author-painted ridges, texture, edge light.
    # Threshold avoids amplifying low-level pixel/encoder noise in shadows.
    if style.sharpness:
        rgb=rgb.filter(ImageFilter.UnsharpMask(
            radius=1.15,percent=style.sharpness,threshold=5))
    rgb=ImageEnhance.Contrast(rgb).enhance(style.contrast)
    rgb=ImageEnhance.Color(rgb).enhance(style.saturation)
    if style.glow_gain:
        # Bright details, not the whole scene, motivate a subtle diffuse
        # bounce; stable across time and independent of source frame noise.
        low=rgb.convert("L").resize(
            (max(16,rgb.width//5),max(16,rgb.height//5)),
            Image.Resampling.BILINEAR)
        mask=low.point(lambda x: max(0,round((x-125)*.28)))
        mask=mask.filter(ImageFilter.GaussianBlur(6)).resize(
            rgb.size,Image.Resampling.BILINEAR)
        mask=ImageOps.autocontrast(mask,cutoff=0) if mask.getextrema()[1]>0 else mask
        # Protect physically dark scenes from a full-screen overexposure.
        falloff=_focal_falloff(rgb.width,rgb.height,look)
        from PIL import ImageChops
        strength=ImageChops.multiply(mask,falloff)
        tint=Image.new("RGBA",rgb.size,(*style.glow,0))
        tint.putalpha(strength)
        rgb=Image.alpha_composite(rgb.convert("RGBA"),tint).convert("RGB")
    result=rgb.convert("RGBA")
    result.putalpha(alpha)
    picture.paste(result,bounds)


def artwork_diagnostics(picture:Image.Image, *,bounds:tuple[int,int,int,int]
                        ) -> dict:
    """Objective descriptive art signals, never a fake AAA quality score."""
    if picture.mode not in ("RGB","RGBA") or not isinstance(bounds,tuple):
        raise ValueError("Invalid artwork diagnosis")
    if len(bounds)!=4 or any(type(v) is not int for v in bounds):
        raise ValueError("Invalid artwork region")
    x0,y0,x1,y1=bounds
    if not (0<=x0<x1<=picture.width and
            0<=y0<y1<=picture.height):
        raise ValueError("Out-of-bounds artwork diagnosis")
    source=picture.crop(bounds).convert("RGB").resize(
        (128,128),Image.Resampling.BILINEAR)
    hsv=source.convert("HSV")
    saturation=ImageStat.Stat(hsv.getchannel("S")).mean[0]
    gray=source.convert("L")
    edges=gray.filter(ImageFilter.FIND_EDGES)
    detail=ImageStat.Stat(edges).mean[0]
    palette=source.quantize(colors=24,method=Image.Quantize.MEDIANCUT)
    groups=len(palette.getcolors(maxcolors=24) or [])
    signals=[]
    if saturation<28:
        signals.append("limited-color-separation")
    if detail<14:
        signals.append("low-fine-detail")
    if groups<=4:
        signals.append("flat-color-geometry")
    return {"version":VERSION,
            "colorSaturation":round(saturation,2),
            "edgeDetail":round(detail,2),
            "paletteFamilies":groups,
            "reviewSignals":signals,
            "editorialApproval":False}
