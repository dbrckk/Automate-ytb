"""Original, declarative vector illustrations for the universal 2.5D engine.

Renders bounded author-supplied bezier curves, polygons, ellipses and rounded
rectangles into RGBA artwork with smooth vertical material gradients. These
are original **drawn** pixels, not inferred facts, fetched images, AI models,
SVG/XML, fonts or executable code. The resulting transparent layer can be
rigged by the existing actor hierarchy. Story rights and editorial review
remain explicit; no publication approval is inferred.
"""
from __future__ import annotations

import hashlib
import json
import math
import re

from PIL import Image, ImageDraw, ImageOps

from .surface25d import MATERIALS

VERSION = "original-bounded-antialiased-vector-layers-v1"
_ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
_RGB = re.compile(r"#[0-9a-fA-F]{6}\Z")
_KINDS = frozenset(("ellipse", "roundedRect", "polygon", "bezier", "line"))
_COMMON = frozenset(("kind", "fill", "stroke", "strokeWidth"))
MAX_LAYERS = 6
MAX_SHAPES = 48
MAX_POINTS = 360


def _unit(value, name, *, low=0., high=1.):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"Invalid vector coordinate: {name}")
    return float(value)


def _color(value):
    if type(value) is not str or _RGB.fullmatch(value) is None:
        raise ValueError("Vector colors must be #RRGGBB")
    return value.upper()


def _fill(value):
    if value is None:
        return None
    if type(value) is str:
        return _color(value)
    if type(value) is list and len(value) == 2:
        return [_color(x) for x in value]
    raise ValueError("Vector fill must be a color, two gradient stops, or null")


def _point(raw):
    if type(raw) is not list or len(raw) != 2:
        raise ValueError("Vector point must be a two-dimensional list")
    return [_unit(raw[0], "x"), _unit(raw[1], "y")]


def validate_vector_layers(raw, owned_layers=None) -> list[dict]:
    if raw is None:
        return []
    if type(raw) is not list or len(raw) > MAX_LAYERS:
        raise ValueError("visualVectors supports at most six original layers")
    owned=owned_layers or []
    used={l["z"] for l in owned}
    names=set()
    results=[]
    for layer in raw:
        fields={"id","z","parallaxX","parallaxY","material",
                "rights","rightsConfirmed","shapes"}
        if type(layer) is not dict or set(layer)!=fields:
            raise ValueError("Invalid original vector layer schema")
        name,z=layer["id"],layer["z"]
        if (type(name) is not str or not _ID.fullmatch(name) or name in names
                or type(z) is not int or z not in range(101) or z in used):
            raise ValueError("Duplicate or invalid original vector layer ID / Z")
        names.add(name);used.add(z)
        rights=layer["rights"]
        if (layer["rightsConfirmed"] is not True or type(rights) is not str
                or not 12 <= len(rights.strip()) <= 500):
            raise ValueError("Author must confirm the rights of every vector layer")
        material=layer["material"]
        if type(material) is not str or material not in MATERIALS:
            raise ValueError("Invalid authored vector surface")
        parallax=[_unit(layer[axis],axis,low=-2,high=2)
                  for axis in ("parallaxX","parallaxY")]
        shapes=layer["shapes"]
        if type(shapes) is not list or not 1 <= len(shapes) <= MAX_SHAPES:
            raise ValueError("Vector layer requires 1-48 original shapes")
        parsed=[]
        points_used=0
        for shape in shapes:
            if type(shape) is not dict or shape.get("kind") not in _KINDS:
                raise ValueError("Unknown original vector primitive")
            kind=shape["kind"]
            required=(_COMMON|{"box"} if kind=="ellipse" else
                      _COMMON|{"box","radius"} if kind=="roundedRect" else
                      _COMMON|{"points"} if kind in ("line","polygon") else
                      _COMMON|{"points","closed"})
            if set(shape)!=required:
                raise ValueError("Unknown/missing vector primitive properties")
            fill=_fill(shape["fill"])
            stroke=shape["stroke"]
            if stroke is not None:
                stroke=_color(stroke)
            if fill is None and stroke is None:
                raise ValueError("Invisible vector geometry is rejected")
            line_width=_unit(shape["strokeWidth"],"strokeWidth",high=.045)
            if stroke is not None and line_width==0:
                raise ValueError("Stroke requires a positive bounded width")
            if stroke is None and line_width:
                raise ValueError("Stroke width without a stroke")
            if kind=="line" and (fill is not None or stroke is None):
                raise ValueError("Vector line must be stroke-only")
            record={"kind":kind,"fill":fill,
                    "stroke":stroke,"strokeWidth":line_width}
            if kind in ("ellipse","roundedRect"):
                box=shape["box"]
                if type(box) is not list or len(box)!=4:
                    raise ValueError("Vector box must be four normalized values")
                coords=[_unit(x,"box") for x in box]
                if not (coords[0]<coords[2] and coords[1]<coords[3]
                        and coords[2]-coords[0]>=.002
                        and coords[3]-coords[1]>=.002):
                    raise ValueError("Empty/inverted vector box")
                record["box"]=coords
                if kind=="roundedRect":
                    record["radius"]=_unit(shape["radius"],"radius",high=.35)
            else:
                pts=shape["points"]
                if type(pts) is not list or not pts:
                    raise ValueError("Vector points list is required")
                count=len(pts)
                if ((kind=="line" and not 2<=count<=28)
                        or (kind=="polygon" and not 3<=count<=28)
                        or (kind=="bezier" and not (4<=count<=31 and
                                                  (count-1)%3==0))):
                    raise ValueError("Invalid bounded vector point count")
                points_used+=count
                record["points"]=[_point(x) for x in pts]
                if kind=="bezier":
                    closed=shape["closed"]
                    if type(closed) is not bool:
                        raise ValueError("Bezier closed must be boolean")
                    if fill is not None and not closed:
                        raise ValueError("Filled bezier shapes must close")
                    record["closed"]=closed
            parsed.append(record)
        if points_used>MAX_POINTS:
            raise ValueError("Too many vector coordinates in one original layer")
        results.append({
            "id":name,"z":z,"parallaxX":parallax[0],
            "parallaxY":parallax[1],"material":material,
            "rights":rights.strip(),"rightsConfirmed":True,"shapes":parsed,
        })
    return results


def vector_sha256(layer: dict) -> str:
    """Hash exact validated raster instructions, not mutable file metadata."""
    blob=json.dumps(layer,sort_keys=True,separators=(",",":"),
                    ensure_ascii=False).encode("utf8")
    return hashlib.sha256(blob).hexdigest()


def _rgb(value: str):
    return tuple(int(value[i:i+2],16) for i in (1,3,5))


def _curve_points(nodes, width: int, height: int):
    def xy(x):return (x[0]*width,x[1]*height)
    out=[xy(nodes[0])]
    for j in range(1,len(nodes),3):
        a=out[-1]
        b,c,d=map(xy,nodes[j:j+3])
        # Fixed resolution ensures deterministic seeks and no geometry aliasing.
        for step in range(1,25):
            t=step/24
            mt=1-t
            out.append((
                mt**3*a[0]+3*mt*mt*t*b[0]+3*mt*t*t*c[0]+t**3*d[0],
                mt**3*a[1]+3*mt*mt*t*b[1]+3*mt*t*t*c[1]+t**3*d[1]))
    return out


def _rasterize(shape, size, antialias=2):
    w,h=size
    kind=shape["kind"]
    if kind in ("ellipse","roundedRect"):
        b=shape["box"]
        box=(round(b[0]*w),round(b[1]*h),round(b[2]*w),round(b[3]*h))
        return kind,box
    points=shape["points"]
    if kind=="bezier":
        return kind,_curve_points(points,w,h)
    return kind,[(p[0]*w,p[1]*h) for p in points]


def render_vector_layer(layer: dict, size: tuple[int,int]) -> Image.Image:
    """Draw original anti-aliased RGBA art ONCE per scene, never per frame."""
    if (type(size) is not tuple or len(size)!=2
            or any(type(n) is not int or not 64<=n<=1200 for n in size)):
        raise ValueError("Unsafe original vector raster dimensions")
    w,h=size
    # 2x supersampling is deliberate. High-res input controls are bounded;
    # all frames reuse these cached source pixels through existing actor rigs.
    factor=2
    work=Image.new("RGBA",(w*factor,h*factor))
    gradients={}
    for shape in layer["shapes"]:
        kind,geometry=_rasterize(shape,work.size)
        mask=Image.new("L",work.size)
        painter=ImageDraw.Draw(mask)
        rounding=round(shape.get("radius",0)*min(work.size))
        if kind=="ellipse":
            painter.ellipse(geometry,fill=255)
        elif kind=="roundedRect":
            painter.rounded_rectangle(geometry,radius=rounding,fill=255)
        elif kind=="polygon":
            painter.polygon(geometry,fill=255)
        elif kind=="bezier" and shape["closed"]:
            painter.polygon(geometry,fill=255)
        # A line or open bezier has no fill by construction.
        fill=shape["fill"]
        if fill is not None:
            if type(fill) is str:
                work.paste((*_rgb(fill),255),(0,0),mask)
            else:
                colors=tuple(fill)
                if colors not in gradients:
                    gradient=Image.linear_gradient("L").resize(
                        work.size,Image.Resampling.BILINEAR)
                    gradients[colors]=ImageOps.colorize(
                        gradient,_rgb(colors[0]),_rgb(colors[1])).convert("RGBA")
                work.paste(gradients[colors],(0,0),mask)
        if shape["stroke"] is not None:
            d=ImageDraw.Draw(work)
            color=(*_rgb(shape["stroke"]),255)
            thickness=max(1,round(shape["strokeWidth"]*min(work.size)))
            if kind=="ellipse":
                d.ellipse(geometry,outline=color,width=thickness)
            elif kind=="roundedRect":
                d.rounded_rectangle(geometry,radius=rounding,
                                    outline=color,width=thickness)
            elif kind=="polygon":
                d.line([*geometry,geometry[0]],fill=color,width=thickness,
                       joint="curve")
            elif kind=="bezier":
                line=[*geometry,geometry[0]] if shape["closed"] else geometry
                d.line(line,fill=color,width=thickness,joint="curve")
            else:
                d.line(geometry,fill=color,width=thickness,joint="curve")
    return work.resize(size,Image.Resampling.LANCZOS)
