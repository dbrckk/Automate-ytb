"""Original five-beat Blender/Cycles aurora cinematography for vertical science.

Call Blender headlessly with -- --output build/aurora-3d --frames 10
--width 600 --height 768 --samples 8. Produces original real 3D PNG
keyframes and their SHA256 manifest; no paid API, downloaded scene, GPU
or third-party textures. Stylized teaching illustration, not a simulation
of atmospheric particles or magnetohydrodynamics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

BEATS = ("solar_wind", "magnetic_field", "collisions", "emission", "curtains")
VERSION = "aurora-blender-cycles-v1"
GREEN = (.16, 1.0, .45)
VIOLET = (.53, .26, 1.0)
ICE = (.27, .75, 1.0)
MAGENTA = (1.0, .27, .54)
GOLD = (1.0, .57, .18)
WHITE = (.75, .94, 1.0)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat(
        "-Z", "Y").to_euler()


def material(name, rgb, *, rough=.45, emission=0., transparent=0.):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = (*rgb, 1)
    nt = mat.node_tree
    if transparent:
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*rgb, 1)
        emit.inputs["Strength"].default_value = emission
        see_through = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = transparent
        nt.links.new(emit.outputs["Emission"], mix.inputs[1])
        nt.links.new(see_through.outputs["BSDF"], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    else:
        p = nt.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value = (*rgb, 1)
        p.inputs["Roughness"].default_value = rough
        if "Metallic" in p.inputs:
            p.inputs["Metallic"].default_value = .09
        for field in ("Emission Color", "Emission"):
            if field in p.inputs:
                p.inputs[field].default_value = (*rgb, 1)
        if "Emission Strength" in p.inputs:
            p.inputs["Emission Strength"].default_value = emission
    return mat


def sphere(name, position, radius, mat, *, segments=24, rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=radius, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def curve(name, mat, *, segments=50, radius=.025):
    cv = bpy.data.curves.new(name, type="CURVE")
    cv.dimensions = "3D"
    cv.resolution_u = 12
    cv.bevel_depth = radius
    cv.bevel_resolution = 2
    spline = cv.splines.new(type="POLY")
    spline.points.add(segments - 1)
    obj = bpy.data.objects.new(name, cv)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return spline


def mountains(rock):
    verts = []
    faces = []
    width = 9.
    n = 90
    for i in range(n+1):
        x = -width/2 + width*i/n
        altitude = (.22 + .55*abs(math.sin(i*.17+.63))**2
                    + .19*math.sin(i*.67)**2)
        verts.extend(((x, 3.6, -.8), (x, 3.6, altitude)))
    for i in range(n):
        j = 2*i
        faces.append((j, j+2, j+3, j+1))
    mesh=bpy.data.meshes.new("Triangular arctic ridgeline mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj=bpy.data.objects.new("Original 3D distant polar mountains",mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(rock)


def star_field(mat):
    rng = random.Random(17291)
    for i in range(135):
        # Real camera-parallax points at two separated world depths.
        x = rng.uniform(-8.5, 8.5)
        y = rng.choice((4.0, 6.5))
        z = rng.uniform(1.8, 8.0)
        sphere(f"Independent 3D star {i:03d}", (x, y, z),
               rng.choice((.012, .019, .025)), mat,
               segments=8, rings=6)


def curtain_mesh(name, mat, *, width=1.35, rows=24, columns=22):
    verts=[]
    faces=[]
    for j in range(rows+1):
        z = .25+5.75*j/rows
        for i in range(columns+1):
            u = i/columns
            verts.append((u*width, 0, z))
    for j in range(rows):
        for i in range(columns):
            a=j*(columns+1)+i
            faces.append((a, a+1, a+columns+2, a+columns+1))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    return obj, rows, columns


def build_scene(beat, width, height, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.render.engine="CYCLES"
    sc.cycles.device="CPU"
    sc.cycles.samples=samples
    sc.render.resolution_x=width
    sc.render.resolution_y=height
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    sc.render.image_settings.color_mode="RGBA"
    sc.render.film_transparent=False
    sc.render.threads_mode="FIXED"
    sc.render.threads=2
    sc.view_settings.view_transform="Standard"
    try:
        sc.view_settings.look="Medium High Contrast"
    except TypeError:
        pass
    sc.view_settings.exposure=0
    sc.view_settings.gamma=1
    world=bpy.data.worlds.new("Midnight upper atmosphere environment")
    sc.world=world
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.005, .012, .035, 1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.28
    mats={
        "sun": material("Solar orange incandescent surface", GOLD, emission=2.5),
        "planet": material("Night side of pale blue Earth", (.028,.16,.31), rough=.38),
        "atmosphere": material("Atmospheric outer aura", ICE, emission=.75, transparent=.70),
        "oxygen": material("Oxygen green photon emission", GREEN, emission=2.1),
        "nitrogen": material("Nitrogen violet photon emission", VIOLET, emission=1.9),
        "red": material("High-altitude oxygen red emission", MAGENTA, emission=1.8),
        "cyan": material("Electric magnetic field glow", ICE, emission=1.5),
        "star": material("White-blue cosmic star field", WHITE, emission=1.8),
        "rock": material("Dark matte arctic ridges", (.015,.059,.074), rough=.96),
        "curtain_a": material("Emerald semi-transparent 3D aurora ribbon", GREEN,
                              emission=1.7, transparent=.38),
        "curtain_b": material("Electric blue aurora ribbon", ICE,
                              emission=1.45, transparent=.48),
        "curtain_c": material("Purple high atmosphere ribbon", VIOLET,
                              emission=1.5, transparent=.47),
    }
    mountains(mats["rock"])
    star_field(mats["star"])
    state={"beat":beat,"mats":mats,"particles":[],"fields":[],
           "molecules":[],"curtains":[],"planet":None,"sun":None}
    if beat=="solar_wind":
        state["sun"]=sphere("3D incandescent solar source",(-2.8,.2,3.4),.85,mats["sun"])
        state["planet"]=sphere("3D Earth receiving charged solar wind",(2.3,1.2,2.1),
                               .95,mats["planet"])
        for i in range(21):
            state["particles"].append(sphere(
                f"Charged solar particle {i:02d}",(-2,0,2),.056,
                mats["cyan"] if i%4 else mats["oxygen"],segments=12,rings=8))
        for k in range(5):
            state["fields"].append(curve(
                f"Solar wind stream trajectory {k}",mats["cyan"],segments=40,radius=.018))
    elif beat=="magnetic_field":
        state["planet"]=sphere("3D Earth with visible dipole field",(0,1.2,2.2),
                               1.07,mats["planet"])
        sphere("Faint Earth atmospheric halo",(0,1.2,2.2),1.13,mats["atmosphere"])
        for k in range(12):
            state["fields"].append(curve(
                f"Independent 3D magnetic field line {k}",
                mats["cyan"] if k%3 else mats["nitrogen"],
                segments=65,radius=.020))
        for i in range(25):
            state["particles"].append(sphere(
                f"Magnetic particle {i:02d}",(0,0,3),.042,mats["oxygen"],
                segments=10,rings=6))
    elif beat in ("collisions","emission"):
        for i in range(13):
            x=-2.8+(i%5)*1.35
            z=1.15+(i//5)*1.64
            y=.25+(i%3)*.65
            material_key = "oxygen" if (i%3) else "nitrogen"
            a=sphere(f"3D gas atom {i:02d}",(x,y,z),
                     .17+(i%3)*.039,mats[material_key],segments=18,rings=12)
            state["molecules"].append((a,(x,y,z)))
            if beat=="emission":
                sphere(f"3D photon halo shell {i:02d}",(x,y,z),.31,
                       mats["atmosphere"],segments=16,rings=10)
        for i in range(32):
            state["particles"].append(sphere(
                f"Collision electron/photon {i:02d}",(0,0,2),.042,
                mats["cyan"] if beat=="collisions" else
                mats["oxygen" if i%3 else "red"],segments=10,rings=6))
    else:
        # Each ribbon is an actual variable-depth 3D mesh, NOT a drawn 2D line.
        for i in range(9):
            layer=(
                "curtain_a" if i%4 in (0,1) else
                "curtain_b" if i%4==2 else "curtain_c"
            )
            state["curtains"].append(curtain_mesh(
                f"Animated draping 3D auroral sheet {i:02d}",
                mats[layer],width=1.55,rows=26,columns=22))
        for i in range(28):
            state["particles"].append(sphere(
                f"Upper atmosphere charged tracer {i:02d}",(0,0,2),
                .028,mats["cyan"],segments=8,rings=6))
    bpy.ops.object.light_add(type="AREA",location=(-3.9,-4.3,7.5))
    key=bpy.context.object
    key.name="Northern rim softbox"
    key.data.energy=900
    key.data.shape="DISK"
    key.data.size=6.0
    key.data.color=(.43,.72,1)
    look_at(key,(0,0,2.1))
    bpy.ops.object.light_add(type="AREA",location=(3.8,2.6,6.1))
    light=bpy.context.object
    light.name="Secondary rose atmosphere light"
    light.data.energy=580
    light.data.shape="DISK"
    light.data.size=4.7
    light.data.color=(.79,.47,1.0)
    look_at(light,(0,0,2.5))
    bpy.ops.object.camera_add(location=(0,-10.2,5.1))
    camera=bpy.context.object
    camera.name="Physically moving atmospheric perspective camera"
    camera.data.lens=36
    camera.data.clip_end=100
    look_at(camera,(0,0,2.6))
    sc.camera=camera
    state["camera"]=camera
    return sc,state


def animate(state, progress):
    beat=state["beat"]
    t=progress*7.0
    camera=state["camera"]
    camera.location.x=.20+.46*math.sin(progress*math.pi*.7)
    camera.location.y=-10.2+.65*progress
    camera.location.z=5.1+.23*math.sin(progress*math.pi)
    look_at(camera,(0,.25,2.5+.13*math.sin(progress*math.pi)))
    if state["planet"] is not None:
        state["planet"].rotation_euler[2]=t*.10
    if state["sun"] is not None:
        state["sun"].rotation_euler[2]=t*.19
    for i, spline in enumerate(state["fields"]):
        count=len(spline.points)
        for j, point in enumerate(spline.points):
            u=j/(count-1)
            if beat=="solar_wind":
                x=-2.5+4.7*u
                y=.12+.45*math.sin(u*3.1+i*.7)
                z=3.30-1.0*u+(.38+i*.14)*math.sin(math.pi*u)
                z+=.07*math.sin(u*12+t*.65+i)
            else:
                phi=math.tau*u
                size=1.43+(i%6)*.29
                angle=i*math.tau/12
                x=size*math.cos(phi)*math.cos(angle)
                y=1.2+size*math.cos(phi)*math.sin(angle)
                z=2.2+2.0*size*math.sin(phi)
                x+=.07*math.sin(t*.6+i)
            point.co=(x,y,z,1)
    for i, particle in enumerate(state["particles"]):
        if beat=="solar_wind":
            q=(i/len(state["particles"])+progress*.73)%1.0
            particle.location=(-2.5+4.7*q,
                               .1+.45*math.sin(i*.81),
                               3.30-1.12*q+.21*math.sin(q*5+i*.6))
        elif beat=="magnetic_field":
            angle=t*(.46+i%4*.1)+i*2.3999
            radius=1.5+(i%6)*.26
            particle.location=(radius*math.cos(angle),
                               1.2+.8*math.sin(angle),
                               2.4+radius*math.sin(angle))
        elif beat in ("collisions","emission"):
            k=i%13
            x=-2.8+(k%5)*1.35
            z=1.15+(k//5)*1.64
            drift=.13*math.sin(t*1.7+i)
            particle.location=(x+.48*math.cos(t*1.9+i*.61),
                               .0+drift, z+.42*math.sin(t*2.1+i*.53))
        else:
            x=-3.3+(i%10)*.71
            particle.location=(x+.31*math.sin(t*.51+i),
                               .75+.27*math.cos(t*.36+i),
                               1.5+(i%5)*.77+.37*math.sin(t*.66+i))
    for i,(obj,xyz) in enumerate(state["molecules"]):
        x,y,z=xyz
        obj.location=(x+.066*math.sin(t*1.7+i),
                      y+.045*math.sin(t*.83+i*.71),
                      z+.085*math.sin(t*1.15+i*.39))
        if beat=="emission":
            obj.scale=(1+.095*math.sin(t*2.8+i),)*3
    for i,(obj,rows,columns) in enumerate(state["curtains"]):
        base=-3.95+(i%5)*1.7
        depth= .32+(i//5)*.84
        for j in range(rows+1):
            v=j/rows
            z=.30+5.5*v
            for k in range(columns+1):
                u=k/columns
                idx=j*(columns+1)+k
                # Continuous waving in 3D x/y depth: real mesh vertices.
                ripple= .41*math.sin(u*math.tau*1.5+t*.57+i*.59+v*2.0)
                shear=.29*math.sin(v*5.3-t*.42+i)
                x=base+1.55*u + shear + ripple*.26
                y=depth+.35*math.sin(u*math.tau*2.8+t*.48+i+v*2.1)
                obj.data.vertices[idx].co=(x,y,z+.14*math.sin(t*.6+u*8+i))
        obj.data.update()


def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--frames",type=int,default=10)
    p.add_argument("--width",type=int,default=600)
    p.add_argument("--height",type=int,default=768)
    p.add_argument("--samples",type=int,default=8)
    a=p.parse_args(argv)
    if (not 2<=a.frames<=24 or not 320<=a.width<=1080
            or not 410<=a.height<=1380 or not 4<=a.samples<=32):
        p.error("Unsafe 3D render parameters")
    out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    manifest={"schemaVersion":1,"generator":"blender-cycles-aurora-v1",
              "width":a.width,"height":a.height,"framesPerBeat":a.frames,
              "beats":{}}
    for beat in BEATS:
        scene,state=build_scene(beat,a.width,a.height,a.samples)
        records=[]
        folder=out/beat
        folder.mkdir(parents=True,exist_ok=True)
        for index in range(a.frames):
            animate(state,index/(a.frames-1))
            frame=folder/("%04d.png"%index)
            scene.render.filepath=str(frame)
            bpy.ops.render.render(write_still=True)
            if not frame.is_file() or frame.stat().st_size<1500:
                raise RuntimeError("Real Blender aurora scene was not exported")
            records.append({"path":f"{beat}/{index:04d}.png",
                            "sha256":hashlib.sha256(frame.read_bytes()).hexdigest()})
            print(f"REAL_AURORA_3D {beat} {index+1}/{a.frames}",flush=True)
        manifest["beats"][beat]=records
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("DONE: 5 original real aurora 3D scenes",flush=True)


if __name__=="__main__":
    main()
