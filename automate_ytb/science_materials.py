"""Deterministic, view-dependent studio material shading for science 3D scenes.

Original CPU-only material model: Lambert diffuse, Blinn specular, Schlick
grazing Fresnel and an artistic edge fill. It approximates material appearance
without claiming full physically based rendering, HDRI, texture mapping or
ray tracing. Inputs are world-space normals and real 3D view coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Material:
    roughness: float
    metallic: float
    coating: float
    rim: float

    def __post_init__(self):
        for value in (self.roughness,self.metallic,self.coating,self.rim):
            if type(value) not in (float,int) or not math.isfinite(value):
                raise ValueError("Invalid science shading material")
        if not .08 <= self.roughness <= 1:
            raise ValueError("Science material roughness out of range")
        if any(not 0 <= v <= 1 for v in (
                self.metallic,self.coating,self.rim)):
            raise ValueError("Science material parameter out of range")


MATERIALS = {
    "fabric": Material(.88,.00,.03,.13),
    "ceramic": Material(.38,.08,.25,.26),
    "alloy": Material(.29,.70,.20,.18),
    "glass": Material(.15,.12,.92,.37),
    "solar": Material(.23,.42,.23,.16),
    "gold": Material(.18,.82,.35,.23),
}


def _unit(v):
    if len(v)!=3 or any(type(x) not in (int,float) or
                        not math.isfinite(x) for x in v):
        raise ValueError("Non-finite material surface vector")
    mag=math.sqrt(sum(x*x for x in v))
    if mag < 1e-8:
        raise ValueError("Degenerate material surface normal")
    return tuple(x/mag for x in v)


def shade_surface(
    base_rgb: tuple[int,int,int], normal: tuple[float,float,float],
    surface: tuple[float,float,float], eye: tuple[float,float,float],
    material: str = "fabric",
) -> tuple[int,int,int,int]:
    """Shade a real 3D surface, maintaining a fully opaque video color.

    The view vector is camera.eye - world surface. A rough suit and polished
    helmet produce distinct highlights; moving the camera changes them.
    """
    if material not in MATERIALS:
        raise ValueError("Unknown trusted material")
    if len(base_rgb)!=3 or any(type(v) is not int or not 0<=v<=255
                                for v in base_rgb):
        raise ValueError("Invalid RGB albedo")
    n=_unit(normal)
    v=_unit(tuple(eye[i]-surface[i] for i in range(3)))
    light=_unit((.28,.72,-.635))
    halfv=_unit(tuple(light[i]+v[i] for i in range(3)))
    ndl=max(0.,sum(n[i]*light[i] for i in range(3)))
    ndv=max(0.,sum(n[i]*v[i] for i in range(3)))
    ndh=max(0.,sum(n[i]*halfv[i] for i in range(3)))
    m=MATERIALS[material]
    gloss_power=min(180.,max(4.,(2./(m.roughness**2)-2.)))
    specular=(ndh**gloss_power)*(0.62+0.38*ndl)*(0.28+0.40*m.coating)
    clearcoat=(ndh**max(30.,gloss_power*1.40))*m.coating*.24
    grazing=(1.-ndv)**5
    edge=(1.-ndv)**2 *m.rim
    # Preserve visible suit/panel albedo in a dark science scene: polished
    # materials should gain a highlight, not become near-black silhouettes.
    diffuse=(.58+.45*ndl+.05*max(0.,n[1]))*(1.-.23*m.metallic)
    shaded=[]
    for i,c in enumerate(base_rgb):
        f0=.045*(1.-m.metallic)+(c/255.)*m.metallic
        fresnel=f0+(1.-f0)*grazing
        raw=c*diffuse+255.*(specular*fresnel+clearcoat*.25)+(
            (77,157,216)[i]*edge)
        shaded.append(max(0,min(255,round(raw))))
    return (*shaded,255)
