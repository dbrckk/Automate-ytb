"""Original world-space astronaut animation for the Earth-stop explainer.

A genuinely perspective-projected articulated spacesuit, curved helmet shell,
multi-face metal backpack, satellite solar panels, and a tether attached to
both moving suit and station. The camera, surfaces and lighting are computed
from 3D coordinates on the CPU using existing Pillow only. Original stylized
visualization, NOT a photorealistic Blender render or a physical EVA simulation.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw

from .science_city3d import Camera3D, SCENE_TOP, SCENE_BOTTOM

CANVAS = (1080, 1920)
LIGHT = (.29, .67, -.69)
SUIT = (218, 230, 239)
TRIM = (70, 158, 200)
GOLD = (248, 192, 112)


def _validate(t: float, duration: float):
    if (type(t) not in (int, float) or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 <= t <= duration <= 180 or duration == 0):
        raise ValueError("Invalid 3D astronaut scene clock")


def _unit(v):
    norm=math.sqrt(sum(q*q for q in v))
    if norm < 1.e-8:
        raise ValueError("Degenerate astronaut 3D geometry")
    return tuple(q/norm for q in v)


def camera_pose(t: float, duration: float) -> Camera3D:
    """Genuine pinhole camera with a slow, world-space orbit and dolly."""
    _validate(t,duration)
    phase=t/duration
    return Camera3D((.48*math.sin(t*.23),2.05+.10*math.sin(t*.25),
                     -4.25+.56*phase),
                    (.06*math.sin(t*.14),1.9,7.4),focal=1040)


def astronaut_pose(t: float, duration: float) -> dict:
    """Joint positions share a clock; hips, limbs and tether move together."""
    _validate(t,duration)
    sway=math.sin(t*.76)
    px=.28*math.sin(t*.72)
    py=.23*math.sin(t*.9)
    pz=3.8+.16*math.cos(t*.38)
    def point(x,y,z=0.):
        return (px+x,py+y,pz+z)
    hip=point(0,1.32)
    head=point(.05,3.16,-.05)
    shoulder_l=point(-.52,2.32)
    shoulder_r=point(.52,2.32)
    elbow_l=point(-.93-.17*sway,1.87+.09*math.sin(t*1.3),-.13)
    elbow_r=point(1.05+.11*sway,1.93+.13*math.sin(t*1.6),-.20)
    hand_l=point(-1.19-.20*sway,1.54+.08*math.sin(t*1.5),-.19)
    hand_r=point(1.26+.17*sway,1.75+.13*math.sin(t*1.25),-.28)
    knee_l=point(-.44-.12*math.sin(t*1.08),.70,.10)
    knee_r=point(.43+.15*math.sin(t*1.05+.7),.73,.08)
    foot_l=point(-.50-.19*math.sin(t*1.08),.19,-.18)
    foot_r=point(.52+.18*math.sin(t*1.05+.7),.17,-.18)
    tether=point(-.58,1.93,.48)
    return locals() | {"torso":point(0,1.92)}


def _screen(camera: Camera3D, point):
    p=camera.project(point)
    return None if p is None else (round(p[0]),round(p[1]-SCENE_TOP))


def _face(draw, camera, points, fill):
    projected=[_screen(camera,p) for p in points]
    if all(p is not None for p in projected):
        draw.polygon(projected,fill=fill)


def _line(draw, camera, points, fill, width=3):
    projected=[_screen(camera,p) for p in points]
    if all(p is not None for p in projected):
        draw.line(projected,fill=fill,width=width,joint="curve")


def _lit(rgb,normal,ambient=.45):
    light=max(0.,sum(a*b for a,b in zip(_unit(normal),_unit(LIGHT))))
    fac=ambient+.52*light
    return tuple(min(255,round(c*fac)) for c in rgb)+(255,)


def _box(draw,camera,center,extent,rgb):
    x,y,z=center
    w,h,d=extent
    vertices=[
        (x-w,y-h,z-d),(x+w,y-h,z-d),(x+w,y+h,z-d),(x-w,y+h,z-d),
        (x-w,y-h,z+d),(x+w,y-h,z+d),(x+w,y+h,z+d),(x-w,y+h,z+d)]
    facets=[
        ((0,1,2,3),(0,0,-1)),
        ((4,5,6,7),(0,0,1)),
        ((0,4,7,3),(-1,0,0)),
        ((1,5,6,2),(1,0,0)),
        ((3,2,6,7),(0,1,0)),
        ((0,1,5,4),(0,-1,0))]
    ranked=[]
    for indices,normal in facets:
        pts=[vertices[i] for i in indices]
        depths=[camera.project(p) for p in pts]
        if any(p is None for p in depths):
            continue
        ranked.append((sum(p[2] for p in depths)/4,pts,normal))
    for _,pts,normal in sorted(ranked,reverse=True,key=lambda x:x[0]):
        _face(draw,camera,pts,_lit(rgb,normal))


def _tube(draw,camera,start,end,radius,rgb):
    axis=tuple(end[i]-start[i] for i in range(3))
    direction=_unit(axis)
    if abs(direction[1])>.95:
        a=(1.,0.,0.)
    else:
        a=_unit((-direction[2],0.,direction[0]))
    b=_unit((direction[1]*a[2]-direction[2]*a[1],
             direction[2]*a[0]-direction[0]*a[2],
             direction[0]*a[1]-direction[1]*a[0]))
    faces=[]
    for k in range(10):
        phi=k*math.tau/10
        nxt=(k+1)*math.tau/10
        def offset(v):
            return tuple(radius*(math.cos(v)*a[i]+math.sin(v)*b[i])
                         for i in range(3))
        p0,p1=offset(phi),offset(nxt)
        points=[
            tuple(start[i]+p0[i] for i in range(3)),
            tuple(start[i]+p1[i] for i in range(3)),
            tuple(end[i]+p1[i] for i in range(3)),
            tuple(end[i]+p0[i] for i in range(3))]
        mid=(phi+nxt)*.5
        normal=tuple(math.cos(mid)*a[i]+math.sin(mid)*b[i] for i in range(3))
        samples=[camera.project(q) for q in points]
        if any(p is None for p in samples):
            continue
        faces.append((sum(p[2] for p in samples)/4,points,normal))
    for _,points,normal in sorted(faces,reverse=True,key=lambda x:x[0]):
        _face(draw,camera,points,_lit(rgb,normal))


def _helmet(draw,camera,center):
    """Latitude/longitude shell mesh, depth ordered; curved glass in front."""
    x,y,z=center
    surfaces=[]
    lat,lon=11,20
    for j in range(lat):
        t0=math.pi*j/lat
        t1=math.pi*(j+1)/lat
        for i in range(lon):
            p0=math.tau*i/lon
            p1=math.tau*(i+1)/lon
            def vertex(theta,phi):
                return (x+.51*math.sin(theta)*math.cos(phi),
                        y+.55*math.cos(theta),
                        z+.49*math.sin(theta)*math.sin(phi))
            points=[vertex(t0,p0),vertex(t0,p1),
                    vertex(t1,p1),vertex(t1,p0)]
            projections=[camera.project(q) for q in points]
            if any(q is None for q in projections):
                continue
            cx=sum(q[0] for q in points)/4
            cy=sum(q[1] for q in points)/4
            cz=sum(q[2] for q in points)/4
            normal=( (cx-x)/.51,(cy-y)/.55,(cz-z)/.49 )
            surfaces.append((sum(q[2] for q in projections)/4,points,normal))
    for _,poly,normal in sorted(surfaces,key=lambda x:x[0],reverse=True):
        _face(draw,camera,poly,_lit((220,235,243),normal,ambient=.50))
    # Curved multi-facet gold/blue glass facing the real perspective camera.
    for k in range(8):
        xx=-.38+k*.095
        xa=xx
        xb=xx+.095
        za=z-.47+.16*(abs(xa)/.45)**2
        zb=z-.47+.16*(abs(xb)/.45)**2
        _face(draw,camera,[
            (x+xa,y+.24,za),(x+xb,y+.24,zb),
            (x+xb,y-.27,zb),(x+xa,y-.27,za)],
            (23+3*k,95+8*k,137+6*k,255))
    # Glass bevel and projected reflected sunlight, attached to helmet.
    _line(draw,camera,[(x-.39,y+.25,z-.32),
                      (x-.19,y+.33,z-.45),(x+.25,y+.31,z-.41)],
          (238,250,249,255),5)
    _line(draw,camera,[(x-.23,y+.17,z-.51),(x+.09,y+.20,z-.54)],
          (168,234,250,255),4)
    _line(draw,camera,[(x-.4,y-.28,z-.32),(x+.40,y-.28,z-.32)],
          (254,202,118,255),6)


def _satellite(draw,camera,t):
    """A fixed docking anchor with actual thickness and solar-panel grids."""
    anchor=(-3.22,2.95,8.1)
    _box(draw,camera,anchor,(.43,.37,.33),(113,153,175))
    for side in (-1,1):
        _tube(draw,camera,(-3.22+side*.38,2.95,8.1),
              (-3.22+side*.95,2.95,8.1),.045,(190,211,215))
        center_x=-3.22+side*1.34
        _box(draw,camera,(center_x,2.96,8.1),
             (.44,.73,.055),(60,123,168))
        for j in range(1,5):
            y=2.96-.73+j*.29
            _line(draw,camera,[(center_x-.43,y,8.035),
                               (center_x+.43,y,8.035)],
                  (140,219,241,245),2)
        for j in range(1,3):
            x=center_x-.44+j*.29
            _line(draw,camera,[(x,2.23,8.035),(x,3.69,8.035)],
                  (160,232,248,240),2)
    _tube(draw,camera,(-3.22,3.32,8.1),
          (-3.22,3.86,8.1),.036,(234,228,195))
    return (-2.93,2.78,7.79)


def _tether(draw,camera,anchor,attachment,t):
    """Taut-with-slack spline in actual 3D, endpoints fixed to station/suit."""
    points=[]
    for i in range(33):
        s=i/32
        sag=.32*math.sin(math.pi*s)
        wave=.19*math.sin(s*math.pi*3+t*.78)*math.sin(math.pi*s)
        points.append((
            anchor[0]*(1-s)+attachment[0]*s,
            anchor[1]*(1-s)+attachment[1]*s-sag+wave,
            anchor[2]*(1-s)+attachment[2]*s-.30*math.sin(math.pi*s)))
    # Perspective-correct varying width as cable approaches the camera.
    for i in range(len(points)-1):
        local=camera.project(points[i])
        if local is None:
            continue
        width=max(2,min(8,round(54/local[2])))
        _line(draw,camera,points[i:i+2],(22,82,123,255),width+2)
        _line(draw,camera,points[i:i+2],(198,231,240,255),max(1,width-1))
    # Couplers are volumetric; no flat screen-space blue ribbon.
    _box(draw,camera,anchor,(.12,.12,.13),(238,189,110))
    _box(draw,camera,attachment,(.13,.13,.11),(250,201,126))


def draw_astronaut3d(picture: Image.Image, t: float, duration: float) -> None:
    """Paint a complete original 3D EVA character into native portrait safe area."""
    if picture.mode!="RGBA" or picture.size!=CANVAS:
        raise ValueError("Astronaut needs 1080x1920 RGBA scene")
    pose=astronaut_pose(t,duration)
    camera=camera_pose(t,duration)
    layer=Image.new("RGBA",(1080,SCENE_BOTTOM-SCENE_TOP))
    d=ImageDraw.Draw(layer,"RGBA")
    docking=_satellite(d,camera,t)
    # World-space cable and backpack are occluded by the suit where appropriate.
    _tether(d,camera,docking,pose["tether"],t)
    hip=pose["hip"]
    center=pose["torso"]
    _box(d,camera,(center[0],center[1],center[2]+.46),
         (.46,.67,.30),(114,153,175))
    # Back leg armor and joints, then volumetric torso and forward arms.
    for sign in (-1,1):
        knee=pose["knee_l"] if sign<0 else pose["knee_r"]
        foot=pose["foot_l"] if sign<0 else pose["foot_r"]
        upper=(hip[0]+sign*.33,hip[1]-.08,hip[2])
        _tube(d,camera,upper,knee,.19,SUIT)
        _tube(d,camera,knee,foot,.17,(201,220,236))
        _box(d,camera,(foot[0],foot[1],foot[2]-.10),
             (.23,.16,.36),(112,155,189))
        _box(d,camera,knee,(.18,.15,.19),(77,158,188))
    _box(d,camera,center,(.55,.68,.41),SUIT)
    # Detailed chest panel and four independent suit light markers.
    _box(d,camera,(center[0],center[1]+.15,center[2]-.438),
         (.36,.26,.035),(53,102,137))
    for i in range(4):
        x=center[0]-.23+i*.16
        _box(d,camera,(x,center[1]+.19,center[2]-.483),
             (.043,.044,.018),GOLD if i%2 else TRIM)
    for side in (-1,1):
        shoulder=pose["shoulder_l"] if side<0 else pose["shoulder_r"]
        elbow=pose["elbow_l"] if side<0 else pose["elbow_r"]
        hand=pose["hand_l"] if side<0 else pose["hand_r"]
        _tube(d,camera,shoulder,elbow,.17,(207,225,238))
        _box(d,camera,elbow,(.16,.16,.17),(74,156,189))
        _tube(d,camera,elbow,hand,.15,(209,224,235))
        _box(d,camera,hand,(.17,.14,.17),(228,193,139))
    _tube(d,camera,(center[0],center[1]+.61,center[2]),
          (pose["head"][0],pose["head"][1]-.41,pose["head"][2]),
          .26,(91,151,180))
    _helmet(d,camera,pose["head"])
    # One tiny 3D thruster pulse correlated with drift; not a 2D boot decal.
    foot=pose["foot_r"]
    for i in range(4):
        phase=(t*.75+i*.27)%1
        xx=foot[0]+.04*math.sin(i+t)
        yy=foot[1]-.20-.30*phase
        zz=foot[2]+.03*i
        radius=.035+.075*phase
        _box(d,camera,(xx,yy,zz),(radius,radius,radius),
             (99+round(75*(1-phase)),185,220))
    picture.alpha_composite(layer,(0,SCENE_TOP))
