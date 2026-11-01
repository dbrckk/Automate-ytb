"""Projected 3D geometry for original science city scenes.

Real three-dimensional building/road vertices, perspective camera, world-space
parallax and per-face shading are projected directly at native 1080x1920.
This deliberately lightweight CPU mesh renderer is NOT Blender, photorealism,
physically based shading or a geophysical simulation. It needs only Pillow.

The rendering is deterministic, independently timed per frame and clipped to
the image's scenic rectangle; original headers/subtitles are never altered.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image, ImageDraw

BEATS = frozenset({"inertia", "wind", "ocean"})
VIEWPORT = (1080, 1920)
SCENE_TOP = 570
SCENE_BOTTOM = 1455
FOCAL = 825.0
BACKGROUND = (68, 130, 163)


def _dot(a, b) -> float:
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]


def _normalize(v):
    d = math.sqrt(_dot(v, v))
    if d <= 1.e-7 or not math.isfinite(d):
        raise ValueError("Unsafe 3D camera direction")
    return tuple(c/d for c in v)


def _smooth(u: float) -> float:
    u = min(1., max(0., u))
    return u*u*(3-2*u)


@dataclass(frozen=True)
class Camera3D:
    """Genuine pinhole camera in world-space, with a stable look-at basis."""
    eye: tuple[float, float, float]
    target: tuple[float, float, float]
    focal: float = FOCAL

    def __post_init__(self):
        for value in (*self.eye, *self.target, self.focal):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Non-finite 3D camera coordinate")
        if not 200 <= self.focal <= 2000:
            raise ValueError("Unsafe camera focal length")
        _normalize(tuple(self.target[i]-self.eye[i] for i in range(3)))

    def basis(self):
        forward = _normalize(tuple(self.target[i]-self.eye[i] for i in range(3)))
        right = _normalize((forward[2], 0., -forward[0]))
        # forward cross right: points towards world-up, including camera pitch.
        up = _normalize((
            -forward[1]*right[2],
            forward[2]*right[0]-forward[0]*right[2],
            forward[0]*right[1]-forward[1]*right[0],
        ))
        return forward, right, up

    def project(self, point: tuple[float, float, float]):
        if len(point) != 3 or any(not math.isfinite(c) for c in point):
            raise ValueError("Invalid projected world point")
        rel = tuple(point[i]-self.eye[i] for i in range(3))
        forward, right, up = self.basis()
        depth = _dot(rel, forward)
        if depth <= .35:
            return None
        return (540+self.focal*_dot(rel,right)/depth,
                1024-self.focal*_dot(rel,up)/depth,
                depth)


def camera_pose(t: float, duration: float, beat: str) -> Camera3D:
    if (beat not in BEATS or type(t) not in (int, float)
            or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration == 0):
        raise ValueError("Invalid city camera frame clock")
    fraction = _smooth(t/duration)
    travel = {"inertia": 3.8, "wind": 1.8, "ocean": 1.1}[beat]
    eye_x = -.65+1.0*math.sin(t*.24+.2)
    eye_y = 7.0+.18*math.sin(t*.37)
    eye_z = -9.6+travel*fraction
    target_x = .55*math.sin(t*.21)
    return Camera3D((eye_x,eye_y,eye_z), (target_x,2.7,18.))


def _screen(camera: Camera3D, point, *, offset=SCENE_TOP):
    sample = camera.project(point)
    return None if sample is None else (round(sample[0]), round(sample[1]-offset))


def _surface(draw: ImageDraw.ImageDraw, camera: Camera3D, points, fill):
    projected = [_screen(camera,p) for p in points]
    if any(point is None for point in projected):
        return
    draw.polygon(projected,fill=fill)


def _line(draw: ImageDraw.ImageDraw, camera: Camera3D, points, fill, width=3):
    projected = [_screen(camera,p) for p in points]
    if any(p is None for p in projected):
        return
    draw.line(projected,fill=fill,width=width,joint="curve")


def _color(tone, exposure: float, depth: float, *, alpha: int = 245):
    fog = max(0., min(.48,(depth-16.)/68.))
    rgb = tuple(round(min(255,max(0,channel*exposure*(1-fog)+
                                BACKGROUND[i]*fog)))
                for i,channel in enumerate(tone))
    return (*rgb,alpha)


def city_blocks():
    """Immutable authored building meshes: left/right street, six distances."""
    for row in range(6):
        for side in (-1, 1):
            i=row*2+(1 if side>0 else 0)
            x=side*(3.65+(i%3)*.48)
            z=7.2+row*5.0+(i%2)*1.2
            width=2.2+(i%4)*.24
            depth=2.2+(i%3)*.35
            height=3.7+(i*7%10)*.62
            yield (i,x,z,width,depth,height)


def _building(d: ImageDraw.ImageDraw, camera: Camera3D,
              block, *, beat: str, t: float):
    i,x,z,w,deep,h=block
    front=z-deep/2
    back=z+deep/2
    left=x-w/2
    right=x+w/2
    tone = (
        (54+(i%4)*9, 112+(i%3)*10, 145+(i%5)*6)
        if beat != "wind" else
        (60+(i%4)*8,98+(i%3)*10,118+(i%5)*7)
    )
    center_depth = max(1., camera.project((x,h/2,z))[2])
    view_left = camera.eye[0] <= x
    facade_x = left if view_left else right
    side_exp = .66 if view_left else .73
    side_color=_color(tone,side_exp,center_depth)
    front_color=_color(tone,.91,center_depth)
    _surface(d,camera,[
        (facade_x,0,front),(facade_x,0,back),
        (facade_x,h,back),(facade_x,h,front)],side_color)
    _surface(d,camera,[
        (left,0,front),(right,0,front),
        (right,h,front),(left,h,front)],front_color)
    if camera.eye[1]>h:
        _surface(d,camera,[
            (left,h,front),(right,h,front),
            (right,h,back),(left,h,back)],
            _color(tone,1.28,center_depth))
    # Architectural trim is attached to true 3D edges, so it obeys camera
    # translation and roof perspective instead of being a screen-space decal.
    _line(d,camera,[(left,h,front),(right,h,front)],
          (177,218,222,173),width=3)
    _line(d,camera,[(facade_x,0,front),(facade_x,h,front)],
          (171,224,241,120),width=3)
    for floor in range(1,max(2,int(h/.90))):
        bottom = floor*.91
        if bottom+.47>h-.2:
            break
        for col in range(3):
            xx=left+w*(.14+col*.295)
            ww=w*.155
            lit = (col+floor+i*3)%4!=0
            glow=(255,205,135,225) if lit else (79,142,181,192)
            _surface(d,camera,[
                (xx,bottom,front-.018),(xx+ww,bottom,front-.018),
                (xx+ww,bottom+.46,front-.018),
                (xx,bottom+.46,front-.018)],glow)
        for col in range(2):
            zz=front+deep*(.21+col*.38)
            dz=deep*.17
            _surface(d,camera,[
                (facade_x+( -.019 if view_left else .019),bottom,zz),
                (facade_x+( -.019 if view_left else .019),bottom,zz+dz),
                (facade_x+( -.019 if view_left else .019),bottom+.43,zz+dz),
                (facade_x+( -.019 if view_left else .019),bottom+.43,zz)],
                (125,188,212,145))
    # Footprint shadow moves with the projected perspective geometry.
    _surface(d,camera,[
        (left,0,back),(right,0,back),
        (right+1.9,0,back+2.8),(left+1.9,0,back+2.8)],
        (9,37,54,90))


def _ground(d: ImageDraw.ImageDraw, camera: Camera3D,
            beat: str,t: float,duration: float):
    road=(20,48,67,244) if beat=="wind" else (26,58,79,248)
    _surface(d,camera,[
        (-2.8,0,1),(2.8,0,1),(2.8,0,55),(-2.8,0,55)],road)
    # Proper world-space curb faces and lane strips recede by projection.
    for side in (-1,1):
        _surface(d,camera,[
            (side*2.65,0,1),(side*2.92,0,1),
            (side*2.92,0,55),(side*2.65,0,55)],
            (122,151,157,226))
        _line(d,camera,[(side*1.68,.02,2),(side*1.68,.02,52)],
              (192,205,191,138),3)
    for z in range(5,54,6):
        _surface(d,camera,[
            (-.115,.026,z),(.115,.026,z),
            (.115,.026,z+2.7),(-.115,.026,z+2.7)],
            (238,217,167,212))
    # Road studs have their own world-space fixed positions.
    for z in range(4,50,4):
        for side in (-1,1):
            _surface(d,camera,[
                (side*2.44,.04,z), (side*2.50,.04,z),
                (side*2.50,.04,z+.18),(side*2.44,.04,z+.18)],
                (236,200,123,184))


def draw_city_mesh(picture: Image.Image, beat: str,
                   t: float, duration: float) -> None:
    """Render a dynamic 3D street into the fixed mobile-safe scene rectangle."""
    if picture.mode!="RGBA" or picture.size!=VIEWPORT:
        raise ValueError("3D city requires native 1080x1920 RGBA frame")
    camera=camera_pose(t,duration,beat)
    layer=Image.new("RGBA",(1080,SCENE_BOTTOM-SCENE_TOP))
    d=ImageDraw.Draw(layer,"RGBA")
    _ground(d,camera,beat,t,duration)
    # Painter's order: distant meshes first, nearby meshes last. Boxes never
    # intersect, and each has lit front/side/top surfaces with 3D windows.
    for block in reversed(tuple(city_blocks())):
        _building(d,camera,block,beat=beat,t=t)
    picture.alpha_composite(layer,(0,SCENE_TOP))
