"""Original, completely local vector illustrations for any authored subject.

The storyboard supplies explicit bezier/polygon/ellipse geometry. This
renderer does not guess the subject, claim factual review, download an image,
execute SVG/CSS, or call a remote model. A compact JSON geometry language is
rasterized once at 2x resolution with color gradients, soft material glow,
anti-aliased curves and genuine alpha for independent 2.5D animation.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
import re

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .surface25d import MATERIALS

VERSION = "original-inline-bezier-2p5d-v1"
_HEX = re.compile(r"#[0-9A-Fa-f]{6}\Z")
_ALLOWED = frozenset(("ellipse", "polygon", "path"))
_SS = 2


def _real(number, low=-.15, high=1.15):
    if (type(number) not in (int, float) or not math.isfinite(number)
            or not low <= number <= high):
        raise ValueError("Vector coordinate must be finite and bounded")
    return float(number)


def _point(raw):
    if type(raw) not in (list, tuple) or len(raw) != 2:
        raise ValueError("Vector point must be an x/y pair")
    return [_real(raw[0]), _real(raw[1])]


def _color(raw):
    if type(raw) is not str or not _HEX.fullmatch(raw):
        raise ValueError("Vector fill/stroke needs literal #RRGGBB")
    return raw.upper()


def _fill(raw):
    if raw is None:
        return None
    if type(raw) is str:
        return _color(raw)
    if type(raw) is dict and set(raw) == {"top", "bottom"}:
        return {"top": _color(raw["top"]), "bottom": _color(raw["bottom"])}
    raise ValueError("Vector fill must be a color or two-stop gradient")


def _geometry(kind, raw):
    if kind == "ellipse":
        if type(raw) not in (list, tuple) or len(raw) != 4:
            raise ValueError("Ellipse geometry requires four coordinates")
        x0,y0,x1,y1 = [_real(n) for n in raw]
        if x1 <= x0 or y1 <= y0:
            raise ValueError("Ellipse bounds must be ordered")
        return [x0,y0,x1,y1]
    if kind == "polygon":
        if type(raw) is not list or not 3 <= len(raw) <= 64:
            raise ValueError("Polygon needs 3–64 points")
        return [_point(p) for p in raw]
    if type(raw) is not list or not 2 <= len(raw) <= 60:
        raise ValueError("Bezier path needs 2–60 commands")
    out=[]
    for i, command in enumerate(raw):
        if type(command) is not dict:
            raise ValueError("Bezier command must be a dictionary")
        op = command.get("op")
        if op == "M" and i == 0 and set(command) == {"op","p"}:
            out.append({"op":"M", "p":_point(command["p"])})
        elif op == "L" and i > 0 and set(command) == {"op","p"}:
            out.append({"op":"L", "p":_point(command["p"])})
        elif op == "C" and i > 0 and set(command) == {"op","c1","c2","p"}:
            out.append({"op":"C", "c1":_point(command["c1"]),
                        "c2":_point(command["c2"]), "p":_point(command["p"])})
        elif op == "Z" and i == len(raw)-1 and set(command) == {"op"}:
            out.append({"op":"Z"})
        else:
            raise ValueError("Unsupported, repeated or unsafe Bezier command")
    if out[-1]["op"] == "M":
        raise ValueError("Empty Bezier path")
    return out


def validate_vector_layers(raw) -> list[dict]:
    """Reject unsafe/oversized arbitrary markup before creating any pixels."""
    if raw is None:
        return []
    if type(raw) is not list or len(raw) > 6:
        raise ValueError("visualVectors requires at most six vector layers")
    result=[]
    z_seen=set()
    for layer in raw:
        if type(layer) is not dict or set(layer) != {
                "name", "z", "parallaxX", "parallaxY", "material", "shapes"}:
            raise ValueError("Unsupported visualVectors layer keys")
        name=layer["name"]
        if (type(name) is not str or not re.fullmatch(
                r"[a-z][a-z0-9-]{1,50}",name)):
            raise ValueError("Vector layer requires a safe unique name")
        z=layer["z"]
        if type(z) is not int or not 0 <= z <= 100 or z in z_seen:
            raise ValueError("Vector Z must be a unique integer in 0..100")
        z_seen.add(z)
        if layer["material"] not in MATERIALS:
            raise ValueError("Unknown original vector material")
        shapes=layer["shapes"]
        if type(shapes) is not list or not 1 <= len(shapes) <= 48:
            raise ValueError("Vector layer requires 1–48 shapes")
        clean_shapes=[]
        for shape in shapes:
            if (type(shape) is not dict or set(shape) != {
                    "type","geometry","fill","stroke",
                    "strokeWidth","opacity","glow"}):
                raise ValueError("Unknown vector shape or missing keys")
            kind=shape["type"]
            if type(kind) is not str or kind not in _ALLOWED:
                raise ValueError("Unsupported vector shape")
            fill=_fill(shape["fill"])
            stroke=None if shape["stroke"] is None else _color(shape["stroke"])
            if fill is None and stroke is None:
                raise ValueError("Invisible vector shapes are not permitted")
            sw=_real(shape["strokeWidth"],0,.04)
            opacity=_real(shape["opacity"],.02,1)
            glow=_real(shape["glow"],0,.06)
            if stroke is None and sw != 0 or stroke is not None and sw <= 0:
                raise ValueError("Vector strokes require a real stroke and width")
            geom=_geometry(kind,shape["geometry"])
            if fill is not None and kind == "path" and geom[-1]["op"] != "Z":
                raise ValueError("Filled paths must be closed")
            clean_shapes.append({
                "type":kind,"geometry":geom,"fill":fill,
                "stroke":stroke,"strokeWidth":sw,
                "opacity":opacity,"glow":glow})
        result.append({"name":name,"z":z,
                       "parallaxX":_real(layer["parallaxX"],-2,2),
                       "parallaxY":_real(layer["parallaxY"],-2,2),
                       "material":layer["material"],"shapes":clean_shapes})
    if len({l["name"] for l in result}) != len(result):
        raise ValueError("Duplicate vector layer name")
    if sum(len(l["shapes"]) for l in result) > 120:
        raise ValueError("Vector storyboard complexity exceeds 120 shapes")
    return result


def vector_fingerprint(layer: dict) -> str:
    return hashlib.sha256(json.dumps(
        layer,sort_keys=True,separators=(",",":"),ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def _px(point, width, height):
    return (round(point[0]*width),round(point[1]*height))


def _bezier(commands, width, height):
    path=[]
    start=None
    cursor=None
    for cmd in commands:
        if cmd["op"] == "M":
            cursor=_px(cmd["p"],width,height)
            start=cursor
            path.append(cursor)
        elif cmd["op"] == "L":
            cursor=_px(cmd["p"],width,height)
            path.append(cursor)
        elif cmd["op"] == "C":
            dest=_px(cmd["p"],width,height)
            a=_px(cmd["c1"],width,height)
            b=_px(cmd["c2"],width,height)
            prev=cursor
            distance=max(abs(dest[0]-prev[0]),abs(dest[1]-prev[1]),
                         abs(a[0]-prev[0]),abs(b[0]-prev[0]))
            steps=max(12,min(96,math.ceil(distance/7)))
            for i in range(1,steps+1):
                t=i/steps
                u=1-t
                x=(u*u*u*prev[0]+3*u*u*t*a[0]
                   +3*u*t*t*b[0]+t*t*t*dest[0])
                y=(u*u*u*prev[1]+3*u*u*t*a[1]
                   +3*u*t*t*b[1]+t*t*t*dest[1])
                path.append((round(x),round(y)))
            cursor=dest
        elif cmd["op"] == "Z":
            if cursor != start:
                path.append(start)
    return path


@lru_cache(maxsize=8)
def _vertical_ramp(size):
    w,h=size
    # A small sample column is scaled in x: the gradient is smooth in y.
    ramp=Image.new("L",(1,h))
    ramp.putdata([round(255*y/max(1,h-1)) for y in range(h)])
    return ramp.resize(size,Image.Resampling.NEAREST)


def _colored_layer(size, fill, mask):
    if isinstance(fill,str):
        return Image.new("RGBA",size,(*bytes.fromhex(fill[1:]),255))
    top=(*bytes.fromhex(fill["top"][1:]),255)
    bottom=(*bytes.fromhex(fill["bottom"][1:]),255)
    return Image.composite(Image.new("RGBA",size,bottom),
                           Image.new("RGBA",size,top),
                           _vertical_ramp(size))


def _draw_geometry(draw, shape, size, *, stroke=False):
    width,height=size
    kind=shape["type"]
    color=255
    if kind == "ellipse":
        x0,y0,x1,y1=shape["geometry"]
        path=(round(x0*width),round(y0*height),
              round(x1*width),round(y1*height))
        if stroke:
            draw.ellipse(path,outline=color,
                         width=max(1,round(shape["strokeWidth"]*width)))
        else:
            draw.ellipse(path,fill=color)
    else:
        path=([_px(p,width,height) for p in shape["geometry"]]
              if kind=="polygon" else
              _bezier(shape["geometry"],width,height))
        if stroke:
            if len(path)>1:
                draw.line(path,fill=color,
                          width=max(1,round(shape["strokeWidth"]*width)),
                          joint="curve")
                if kind=="polygon" and path[0]!=path[-1]:
                    draw.line((path[-1],path[0]),fill=color,
                              width=max(1,round(shape["strokeWidth"]*width)))
        else:
            draw.polygon(path,fill=color)


def render_vector_layer(layer: dict, size: tuple[int,int]) -> Image.Image:
    """Cacheable source raster; no expensive vector parsing per video frame."""
    if (type(size) is not tuple or len(size)!=2
            or any(type(x) is not int or not 100<=x<=1200 for x in size)):
        raise ValueError("Vector stage must use bounded pixel dimensions")
    clean=validate_vector_layers([layer])[0]
    w,h=size
    full=(w*_SS,h*_SS)
    output=Image.new("RGBA",full,(0,0,0,0))
    for shape in clean["shapes"]:
        mask=Image.new("L",full,0)
        if shape["fill"] is not None:
            _draw_geometry(ImageDraw.Draw(mask),shape,full)
            if shape["glow"]>0:
                radius=max(1,round(shape["glow"]*w*_SS))
                glow=mask.filter(ImageFilter.GaussianBlur(radius))
                alpha=glow.point(lambda v:round(v*.27*shape["opacity"]))
                glow_layer=Image.new("RGBA",full,
                                     (*bytes.fromhex(
                                         (shape["stroke"] or (
                                             shape["fill"] if isinstance(
                                                 shape["fill"],str) else
                                             shape["fill"]["bottom"]))[1:]),0))
                glow_layer.putalpha(alpha)
                output.alpha_composite(glow_layer)
            fill_layer=_colored_layer(full,shape["fill"],mask)
            alpha=mask.point(lambda v:round(v*shape["opacity"]))
            fill_layer.putalpha(alpha)
            output.alpha_composite(fill_layer)
        if shape["stroke"] is not None:
            stroke_mask=Image.new("L",full,0)
            _draw_geometry(ImageDraw.Draw(stroke_mask),shape,full,stroke=True)
            alpha=stroke_mask.point(lambda v:round(v*shape["opacity"]))
            stroke_layer=Image.new("RGBA",full,
                                   (*bytes.fromhex(shape["stroke"][1:]),0))
            stroke_layer.putalpha(alpha)
            output.alpha_composite(stroke_layer)
    return output.resize(size,Image.Resampling.LANCZOS)
