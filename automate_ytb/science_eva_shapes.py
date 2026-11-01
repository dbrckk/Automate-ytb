"""Original rounded EVA suit and boot meshes projected by the science 3D camera.

Unlike a 2D sprite or stacked flat rectangles, the torso and boots have
curved three-dimensional vertex surfaces. Material response depends on the
real camera eye and the original CPU material model. Fixed tessellation means
rendered frames are deterministic, reproducible and require no paid assets.
"""
from __future__ import annotations

import math
from PIL import ImageDraw

from .science_materials import shade_surface


def _valid(center, extent):
    if (len(center) != 3 or len(extent) != 3 or
            any(type(x) not in (float,int) or not math.isfinite(x)
                for x in (*center,*extent)) or
            any(x <= 0 or x > 5 for x in extent)):
        raise ValueError("Invalid rounded suit geometry")


def _polygon(draw: ImageDraw.ImageDraw, camera, vertices, base, material,
             *, normal=None):
    projected=[camera.project(v) for v in vertices]
    if any(p is None for p in projected):
        return
    point=tuple(sum(v[k] for v in vertices)/len(vertices) for k in range(3))
    if normal is None:
        a=tuple(vertices[1][i]-vertices[0][i] for i in range(3))
        b=tuple(vertices[3][i]-vertices[0][i] for i in range(3))
        normal=(a[1]*b[2]-a[2]*b[1],
                a[2]*b[0]-a[0]*b[2],
                a[0]*b[1]-a[1]*b[0])
    color=shade_surface(base,normal,point,camera.eye,material)
    draw.polygon([(round(p[0]),round(p[1]-570)) for p in projected],
                 fill=color)


def torso_rings(center):
    """Author-controlled shoulder taper, waist, and non-cubical silhouette."""
    _valid(center,(.6,.7,.45))
    x,y,z=center
    rings=(
        (-.69,.26,.28),(-.62,.40,.36),(-.44,.47,.40),
        (-.25,.49,.42),(.02,.53,.44),(.33,.56,.43),
        (.55,.47,.36),(.68,.30,.24),
    )
    output=[]
    for h,rx,rz in rings:
        ring=[]
        for i in range(21):
            phi=i*math.tau/20
            ring.append((x+rx*math.sin(phi),y+h,
                         z-rz*math.cos(phi)))
        output.append(tuple(ring))
    return tuple(output)


def _torso_surface(center,h,phi,extra=0):
    x,y,z=center
    # Piecewise interpolation uses exactly the same authored ring silhouette.
    heights=(-.69,-.62,-.44,-.25,.02,.33,.55,.68)
    widths=(.26,.40,.47,.49,.53,.56,.47,.30)
    depths=(.28,.36,.40,.42,.44,.43,.36,.24)
    h=min(heights[-1],max(heights[0],h))
    k=next((j for j in range(len(heights)-1)
            if heights[j] <= h <= heights[j+1]),len(heights)-2)
    f=(h-heights[k])/(heights[k+1]-heights[k])
    rx=widths[k]*(1-f)+widths[k+1]*f
    rz=depths[k]*(1-f)+depths[k+1]*f
    return (x+(rx+extra)*math.sin(phi),y+h,
            z-(rz+extra)*math.cos(phi))


def render_torso(draw: ImageDraw.ImageDraw,camera,center):
    """Shade curved torso with three-dimensional seam and inset chest plate."""
    rings=torso_rings(center)
    faces=[]
    for j in range(len(rings)-1):
        for k in range(20):
            verts=(rings[j][k],rings[j][k+1],
                   rings[j+1][k+1],rings[j+1][k])
            theta=(k+.5)*math.tau/20
            h=(rings[j][k][1]+rings[j+1][k][1])/2-center[1]
            # Shoulder curvature contributes to the geometric surface normal.
            slope=.21 if h>.40 else -.11 if h<-.47 else .05
            normal=(math.sin(theta),slope,-math.cos(theta))
            depth=sum(camera.project(v)[2] for v in verts)/4
            base=(222,232,239) if k%5!=0 else (193,216,232)
            faces.append((depth,verts,normal,base))
    for _,verts,normal,base in sorted(faces,key=lambda a:a[0],reverse=True):
        _polygon(draw,camera,verts,base,"ceramic",normal=normal)

    # Seam lines and the curved instrument panel must stay attached to
    # the forward-facing 3D surface, also during the camera orbit.
    for angle in (-1.08,1.08):
        pts=[_torso_surface(center,h,angle,.012)
             for h in (-.53,-.40,-.24,.04,.30,.49)]
        projected=[camera.project(p) for p in pts]
        if all(p is not None for p in projected):
            draw.line([(round(p[0]),round(p[1]-570)) for p in projected],
                      fill=(132,198,229,218),width=4,joint="curve")
    for h in (-.54,.49):
        pts=[_torso_surface(center,h,-1.13+i*2.26/22,.018)
             for i in range(23)]
        projected=[camera.project(p) for p in pts]
        if all(p is not None for p in projected):
            draw.line([(round(p[0]),round(p[1]-570)) for p in projected],
                      fill=(109,165,198,225),width=3,joint="curve")

    # Five-piece curved instrument panel wrapped around the front surface.
    for k in range(5):
        left=-.69+k*1.38/5
        right=-.69+(k+1)*1.38/5
        quad=(_torso_surface(center,.30,left,.023),
              _torso_surface(center,.30,right,.023),
              _torso_surface(center,-.12,right,.023),
              _torso_surface(center,-.12,left,.023))
        normal=(math.sin((left+right)/2),0,-math.cos((left+right)/2))
        _polygon(draw,camera,quad,(38,91,130),"glass",normal=normal)
    for k in range(4):
        phi=-.43+k*.28
        patch=(
            _torso_surface(center,.17,phi,.040),
            _torso_surface(center,.17,phi+.13,.040),
            _torso_surface(center,.24,phi+.13,.040),
            _torso_surface(center,.24,phi,.040))
        _polygon(draw,camera,patch,
                 (248,192,112) if k%2 else (75,177,207),
                 "gold" if k%2 else "alloy",
                 normal=(math.sin(phi+.07),0,-math.cos(phi+.07)))


def _signed_pow(x: float,power: float):
    return math.copysign(abs(x)**power,x)


def rounded_boot_vertices(center,extent,lat=9,lon=16):
    """Lat/lon superquadric: broad insulated toe and softly bevelled edges."""
    _valid(center,extent)
    if type(lat) is not int or type(lon) is not int or lat<4 or lon<8:
        raise ValueError("Unsafe boot tessellation")
    x,y,z=center
    rings=[]
    for j in range(lat+1):
        theta=-math.pi/2+j*math.pi/lat
        ry=_signed_pow(math.sin(theta),.63)
        rr=_signed_pow(math.cos(theta),.63)
        ring=[]
        for i in range(lon+1):
            phi=i*math.tau/lon
            ring.append((
                x+extent[0]*rr*_signed_pow(math.cos(phi),.72),
                y+extent[1]*ry,
                z+extent[2]*rr*_signed_pow(math.sin(phi),.72)))
        rings.append(tuple(ring))
    return tuple(rings)


def render_boot(draw: ImageDraw.ImageDraw,camera,center,
                extent=(.27,.19,.39)):
    """Rounded insulated shell with separate darker projected rubber sole."""
    _valid(center,extent)
    # Rubber base is deliberately below the upper boot: leg remains visible.
    sole=(center[0],center[1]-extent[1]*.61,center[2]-.045)
    _render_boot_shell(draw,camera,sole,
                       (extent[0]*1.06,extent[1]*.39,extent[2]*1.06),
                       (60,116,158),"alloy")
    _render_boot_shell(draw,camera,center,extent,(210,226,237),"ceramic")


def _render_boot_shell(draw,camera,center,extent,base,material):
    rings=rounded_boot_vertices(center,extent)
    faces=[]
    for j in range(len(rings)-1):
        for i in range(len(rings[0])-1):
            verts=(rings[j][i],rings[j][i+1],
                   rings[j+1][i+1],rings[j+1][i])
            depth=sum(camera.project(v)[2] for v in verts)/4
            point=tuple(sum(v[k] for v in verts)/4 for k in range(3))
            normal=tuple((point[k]-center[k])/extent[k]
                         for k in range(3))
            if math.sqrt(sum(v*v for v in normal))<1e-6:
                continue
            faces.append((depth,verts,normal))
    for _,verts,normal in sorted(faces,key=lambda a:a[0],reverse=True):
        _polygon(draw,camera,verts,base,material,normal=normal)
