"""Reusable offline visual-quality diagnostics for EVERY 2.5D scene.

Measures visible detail, alpha-edge complexity, local chroma and real parallax.
Diagnostics are intentionally non-destructive: illustration style and scene
semantics cannot be judged reliably from image statistics alone.
"""
from __future__ import annotations

import math
from PIL import Image, ImageChops, ImageFilter, ImageStat

VERSION = "global-25d-visual-quality-audit-p55-v1"
SIZE = (160, 160)


def _finite_camera(value: float) -> float:
    if type(value) not in (float, int) or not math.isfinite(value) or abs(value)>180:
        raise ValueError("Invalid bounded 2.5D QA camera movement")
    return float(value)


def analyze_layer(image: Image.Image, *, name: str = "asset") -> dict:
    if (not isinstance(image, Image.Image) or image.mode!="RGBA"
            or image.width<16 or image.height<16
            or image.width>1920 or image.height>1920):
        raise ValueError("Expected bounded RGBA original 2.5D asset")
    thumb=image.resize(SIZE, Image.Resampling.BILINEAR)
    alpha=thumb.getchannel("A")
    coverage=ImageStat.Stat(alpha).mean[0]/255
    if coverage<.001:
        return {"name":name,"alphaCoverage":0.0,"edgeDensity":0.,
                "detailEnergy":0.,"chromaVariation":0.,
                "warnings":["Layer is effectively transparent."]}
    # Alpha-aware edge density: count visible organic silhouette boundaries,
    # but exclude the stage border so full-frame backgrounds are not penalized.
    edges=alpha.filter(ImageFilter.FIND_EDGES)
    edge=edges.crop((3,3,SIZE[0]-3,SIZE[1]-3))
    edge_density=sum(v>38 for v in edge.getdata())/len(edge.getdata())
    rgb=Image.new("RGB",SIZE,(0,0,0))
    rgb.paste(thumb.convert("RGB"),mask=alpha)
    # A coarse low-pass removes large gradients; remaining variation is
    # evidence of high-frequency material detail (not a subjective score).
    blur=rgb.filter(ImageFilter.GaussianBlur(3.0))
    difference=ImageChops.difference(rgb,blur)
    detail=round(sum(ImageStat.Stat(difference).mean)/3,3)
    channels=rgb.split()
    chroma=ImageChops.difference(channels[0],channels[2])
    chroma_variation=round(ImageStat.Stat(chroma).stddev[0],3)
    warnings=[]
    if detail<2.5 and coverage>.07:
        warnings.append("Low visible material detail; inspect flat shapes or blurred textures.")
    if edge_density<.008 and .015<coverage<.90:
        warnings.append("Very simple silhouette; inspect primitive geometry.")
    if chroma_variation<4 and coverage>.1:
        warnings.append("Low warm/cool color separation; inspect grading and palette.")
    return {"name":name,"alphaCoverage":round(coverage,4),
            "edgeDensity":round(edge_density,4),
            "detailEnergy":detail,"chromaVariation":chroma_variation,
            "warnings":warnings}


def analyze_scene(scene, *, camera_x: float = 32., camera_y: float = 14.) -> dict:
    """Evaluate an actual Scene25D and its source layers without mutations.

    This is a REVIEW gate, not automatic aesthetic approval. It can be
    applied to any topic, language, output orientation or visual asset set.
    """
    from .scene25d import Scene25D
    if not isinstance(scene,Scene25D):
        raise ValueError("Expected a composed 2.5D scene")
    cx,cy=_finite_camera(camera_x),_finite_camera(camera_y)
    if not scene._layers:
        raise ValueError("Cannot audit empty scene")
    layers=sorted(scene._layers,key=lambda layer:layer.z)
    analyses=[analyze_layer(layer.image,name=layer.name) for layer in layers]
    original=scene.render()
    moved=scene.render(camera_x=cx,camera_y=cy)
    sample=original.resize(SIZE,Image.Resampling.BILINEAR).convert("RGB")
    sample_moved=moved.resize(SIZE,Image.Resampling.BILINEAR).convert("RGB")
    motion=round(sum(ImageStat.Stat(
        ImageChops.difference(sample,sample_moved)).mean)/3,3)
    depths=len({layer.z for layer in layers})
    parallax_profiles=len({(round(layer.parallax_x,3),
                            round(layer.parallax_y,3)) for layer in layers})
    warnings=[f"{row['name']}: {message}"
              for row in analyses for message in row["warnings"]]
    if depths<3:
        warnings.append("Fewer than three authored depth planes; inspect spatial layering.")
    if parallax_profiles<3 or motion<.6:
        warnings.append("Limited visible independent parallax; inspect depth motion.")
    result={"version":VERSION,"status":"review" if warnings else "no-obvious-defects",
            "layerCount":len(layers),"depthPlanes":depths,
            "independentMotionProfiles":parallax_profiles,
            "visibleCameraDifference":motion,
            "layers":analyses,"warnings":warnings,
            "publicationApproved":False}
    return result
