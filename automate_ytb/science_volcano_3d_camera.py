"""CPU 3D camera for the original volcanic eruption geometry.

Unlike a zoom on an existing flat plate, every output frame projects the
same heightfield triangles from a different azimuth. Triangles have world
space normals, rock-stratum colors and deterministic roughness variations.
The crater is the camera pivot, so the existing eruption VFX remains aligned.
This is a painter-sorted orthographic 3D renderer, not raytracing/PBR.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageChops

from .science_volcano_mesh import (
    SIZE, RINGS, SEGMENTS, CONE_OUTLINE, height_at,
)

VERSION = "volcano-worldspace-camera-v1-azimuth-mesh-parallax"


def _safe_time(t: float, duration: float) -> float:
    if (type(t) not in (int, float) or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration):
        raise ValueError("Invalid world-space volcanic camera time")
    q=t/duration
    return q*q*(3-2*q)


def camera_yaw(t: float, duration: float) -> float:
    """Real camera orbit of 19.5 degrees about the fixed vent pivot."""
    return -.17 + .34 * _safe_time(t, duration)


def world_to_screen(x: float, y: float, z: float, yaw: float
                    ) -> tuple[float, float]:
    """Project a 3D point after a true horizontal camera rotation."""
    if not all(type(v) in (int,float) and math.isfinite(v)
               for v in (x,y,z,yaw)) or not -.18<=yaw<=.18:
        raise ValueError("Invalid volcanic world point or camera")
    co,si=math.cos(yaw),math.sin(yaw)
    xr=x*co-y*si
    yr=x*si+y*co
    # Mild depth-dependent foreshortening makes different elevations and
    # front/back faces move by different amounts, not a global 2D warp.
    perspective=1+.055*yr/520
    return (540+(.91*xr+.13*yr)*perspective,
            1050+(.30*yr-1.03*z)*perspective)


@lru_cache(maxsize=1)
def _geometry() -> tuple:
    """Cache actual 3D triangles and precomputed world-space materials."""
    rings=[]
    for radius in RINGS:
        vertices=[]
        for i in range(SEGMENTS):
            az=i*math.tau/SEGMENTS
            r=radius*(1+.022*math.sin(11*az)+.018*math.sin(19*az))
            vertices.append((r*math.cos(az),r*math.sin(az),
                             height_at(radius,az)))
        rings.append(vertices)
    triangles=[]
    for index in range(len(rings)-1):
        for j in range(SEGMENTS):
            j1=(j+1)%SEGMENTS
            a,b=rings[index][j],rings[index][j1]
            c,d=rings[index+1][j],rings[index+1][j1]
            for v0,v1,v2 in ((a,c,d),(a,d,b)):
                ux,uy,uz=(v1[k]-v0[k] for k in range(3))
                vx,vy,vz=(v2[k]-v0[k] for k in range(3))
                nx,ny,nz=(uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx)
                normal=math.sqrt(nx*nx+ny*ny+nz*nz)
                if normal<1e-8:
                    continue
                nx,ny,nz=nx/normal,ny/normal,nz/normal
                mx=sum(p[0] for p in (v0,v1,v2))/3
                my=sum(p[1] for p in (v0,v1,v2))/3
                mz=sum(p[2] for p in (v0,v1,v2))/3
                strata=.5+.5*math.sin(mz*.058+mx*.012)
                grain=math.sin(mx*.075+my*.048)*math.sin(my*.093+mz*.11)
                diffuse=.28+.72*max(0.,-.63*nx-.46*ny+.77*nz)
                brightness=diffuse*(.91+grain*.12+strata*.08)
                color=(min(255,max(10,round(115*brightness+14))),
                       min(255,max(10,round(104*brightness+12))),
                       min(255,max(12,round(104*brightness+14))),255)
                triangles.append((v0,v1,v2,nx,ny,nz,mx,my,color))
    return tuple(triangles)


@lru_cache(maxsize=1)
def _clip_and_fade() -> Image.Image:
    silhouette=Image.new("L",SIZE)
    ImageDraw.Draw(silhouette).polygon(CONE_OUTLINE,fill=255)
    fade=Image.new("L",SIZE,255)
    fd=ImageDraw.Draw(fade)
    for y in range(865,1100):
        q=(y-865)/235
        u=q*q*(3-2*q)
        fd.line((0,y,SIZE[0]-1,y),fill=round(255*(1-u)))
    fd.rectangle((0,1100,SIZE[0],SIZE[1]),fill=0)
    return ImageChops.multiply(silhouette,fade)


def render_orbit_terrain(t: float, duration: float) -> Image.Image:
    """Project mesh with moving camera at original 1080x1380 resolution.

    This is the actual moving surface used by the final eruption shot. Its
    alpha is bounded to the rock and the lower ground transition, leaving
    the existing sky and caption compositing transparent.
    """
    yaw=camera_yaw(t,duration)
    co,si=math.cos(yaw),math.sin(yaw)
    faces=[]
    for v0,v1,v2,nx,ny,nz,mx,my,color in _geometry():
        # Camera-space backface culling: the front-facing triangles change
        # as the viewpoint orbits, unlike a 2D scaling of a single image.
        if -(nx*si+ny*co)*.96+nz*.29<=0:
            continue
        depth=mx*si+my*co
        faces.append((depth,(world_to_screen(*v0,yaw),
                             world_to_screen(*v1,yaw),
                             world_to_screen(*v2,yaw)),color))
    image=Image.new("RGBA",SIZE)
    draw=ImageDraw.Draw(image)
    for _,polygon,color in sorted(faces,key=lambda face:face[0],reverse=True):
        draw.polygon(polygon,fill=color)
    image.putalpha(ImageChops.multiply(image.getchannel("A"),_clip_and_fade()))
    return image
