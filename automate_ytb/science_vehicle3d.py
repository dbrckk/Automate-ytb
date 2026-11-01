"""Perspective 3D moving vehicle for the original Earth-stop inertial scene.

A real world-space body/cabin chassis with separate roof, side and bonnet
faces, four rotating wheel discs and shadows, projected by the exact camera
used for the city. No pre-rendered PNG or flat billboard; this is original
CPU-based 3D geometry rendered through Pillow. The scientific hypothetical
is schematic rather than a crash dynamics simulation.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw

from .science_city3d import camera_pose, SCENE_TOP, SCENE_BOTTOM

CAR_BODY = (237, 151, 103, 255)
CAR_DARK = (133, 76, 70, 255)
WINDOW = (91, 185, 212, 247)


def _smooth(u: float) -> float:
    u = max(0.,min(1.,u))
    return u*u*(3-2*u)


def vehicle_pose(t: float, duration: float) -> dict:
    """World-space trajectory used by body, axle rotation and contact testing."""
    if (type(t) not in (int,float) or type(duration) not in (int,float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or duration <= 0 or duration > 180 or t < 0 or t > duration):
        raise ValueError("Invalid original vehicle 3D scene clock")
    u=_smooth(t/duration)
    x=-5.75+8.55*u
    z=3.8+.18*math.sin(t*.8)
    # Axle angular displacement comes from distance travelled, not a
    # decorative loop. Both near and far wheels use the same angle.
    angle=(x+5.75)/.30
    return {"x":x,"z":z,"wheel_angle":angle,"progress":u}


def _project(camera, point):
    projected=camera.project(point)
    if projected is None:
        return None
    return round(projected[0]),round(projected[1]-SCENE_TOP)


def _face(draw, camera, points, color):
    visible=[_project(camera,p) for p in points]
    if any(p is None for p in visible):
        return
    draw.polygon(visible,fill=color)


def _segment(draw,camera,points,color,width=3):
    visible=[_project(camera,p) for p in points]
    if any(p is None for p in visible):
        return
    draw.line(visible,fill=color,width=width,joint="curve")


def _wheel(draw,camera,x,y,z,angle,*,near: bool):
    outer=[]
    inner=[]
    for i in range(25):
        a=i*math.tau/24
        outer.append((x+.315*math.cos(a),y+.315*math.sin(a),z))
        inner.append((x+.185*math.cos(a),y+.185*math.sin(a),z))
    _face(draw,camera,outer,(22,38,51,255))
    _face(draw,camera,inner,(126,166,181,255))
    for j in range(6):
        theta=angle+j*math.tau/6
        _segment(draw,camera,[(x,y,z-.011 if near else z+.011),
                              (x+.155*math.cos(theta),
                               y+.155*math.sin(theta),
                               z-.011 if near else z+.011)],
                 (230,233,207,255),width=3)
    _face(draw,camera,[
        (x-.057,y-.057,z-.025 if near else z+.025),
        (x+.057,y-.057,z-.025 if near else z+.025),
        (x+.057,y+.057,z-.025 if near else z+.025),
        (x-.057,y+.057,z-.025 if near else z+.025),
    ],(254,211,140,255))


def draw_vehicle3d(picture: Image.Image,t: float,duration: float) -> None:
    """Paint original moving 3D car into safe scenic region; no title changes."""
    if picture.mode!="RGBA" or picture.size!=(1080,1920):
        raise ValueError("3D vehicle requires native portrait RGBA scene")
    pose=vehicle_pose(t,duration)
    cam=camera_pose(t,duration,"inertia")
    layer=Image.new("RGBA",(1080,SCENE_BOTTOM-SCENE_TOP))
    d=ImageDraw.Draw(layer,"RGBA")
    x,z=pose["x"],pose["z"]
    angle=pose["wheel_angle"]
    L=1.42
    W=.66
    z_near=z-W
    z_far=z+W
    wheel_y=.34
    # Projected road shadow is a world-space footprint, not a static ellipse.
    _face(d,cam,[
        (x-L-.19,.018,z_near-.31),
        (x+L+.20,.018,z_near-.31),
        (x+L+.58,.018,z_far+.62),
        (x-L+.15,.018,z_far+.62),
    ],(7,22,37,108))
    for axle in (-.91,.92):
        _wheel(d,cam,x+axle,wheel_y,z_far,angle,near=False)
    # Side and bonnet have unique physically plausible brightness.
    _face(d,cam,[
        (x-L,.32,z_far),(x+L,.32,z_far),
        (x+L,.98,z_far),(x-L,.98,z_far)],
        CAR_DARK)
    _face(d,cam,[
        (x+L,.30,z_near),(x+L,.30,z_far),
        (x+L,.97,z_far),(x+L,.97,z_near)],
        (198,106,76,255))
    _face(d,cam,[
        (x-L,.33,z_near),(x+L,.33,z_near),
        (x+L,1.03,z_near),(x-L,1.03,z_near)],
        CAR_BODY)
    _face(d,cam,[
        (x-L,1.03,z_near),(x+L,1.03,z_near),
        (x+L,1.03,z_far),(x-L,1.03,z_far)],
        (255,197,132,255))
    # Trapezoidal 3D passenger cab: no two-dimensional roof sprite.
    _face(d,cam,[
        (x-.77,1.01,z_far),(x+.61,1.01,z_far),
        (x+.39,1.75,z_far-.11),(x-.45,1.75,z_far-.11)],
        (79,122,143,255))
    _face(d,cam,[
        (x-.75,1.01,z_near),(x+.58,1.01,z_near),
        (x+.36,1.75,z_near+.11),(x-.44,1.75,z_near+.11)],
        WINDOW)
    _face(d,cam,[
        (x-.46,1.75,z_near+.11),(x+.40,1.75,z_near+.11),
        (x+.40,1.75,z_far-.11),(x-.46,1.75,z_far-.11)],
        (251,200,152,255))
    # Stanchions and rear glass follow the 3D roofline.
    _segment(d,cam,[(x+.04,1.06,z_near-.01),
                    (x+.03,1.74,z_near+.10)],
             (238,223,194,255),width=6)
    _segment(d,cam,[(x-.72,1.01,z_near),(x-.44,1.75,z_near+.11)],
             (242,214,176,255),width=6)
    _segment(d,cam,[(x+.58,1.02,z_near),(x+.37,1.75,z_near+.11)],
             (243,210,181,255),width=6)
    # Distinct moving headlights and side striping visible during action.
    for side in (-1,1):
        zz=z+side*.44
        _face(d,cam,[
            (x+L-.025,.72,zz-.095),
            (x+L+.016,.72,zz-.095),
            (x+L+.016,.88,zz+.095),
            (x+L-.025,.88,zz+.095)],
            (255,226,145,255))
    _segment(d,cam,[(x-1.21,.68,z_near-.012),
                    (x+1.19,.68,z_near-.012)],
             (255,224,162,255),width=5)
    for axle in (-.91,.92):
        _wheel(d,cam,x+axle,wheel_y,z_near-.04,angle,near=True)
    picture.alpha_composite(layer,(0,SCENE_TOP))
