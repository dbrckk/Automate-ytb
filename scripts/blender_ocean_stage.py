"""Generate original, physically illuminated 3D underwater scenes with Blender.

Run with:
  blender --background --factory-startup -t 2 --python scripts/blender_ocean_stage.py \
    -- --output build/ocean-3d --frames 10 --width 600 --height 580 --samples 8

No asset download, third-party model, GPU, paid API, or Python host-side bpy
dependency. CPU Cycles output is a real perspective-rendered animated 3D scene.
Ocean flow and latitudes are explanatory, NOT oceanographic CFD data.
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

BEATS = ("solar", "wind", "coriolis", "sinking", "heat")
TINTS = {
    "solar": {"water": (0.025, .26, .31), "beam": (1.0, .42, .10),
              "shore": (.16, .28, .23), "accent": (.96, .62, .23)},
    "wind": {"water": (.020, .29, .34), "beam": (.33, .91, .99),
             "shore": (.12, .29, .29), "accent": (.33, .92, 1.0)},
    "coriolis": {"water": (.055, .16, .34), "beam": (.47, .62, 1.0),
                 "shore": (.14, .18, .31), "accent": (.40, .82, 1.0)},
    "sinking": {"water": (.026, .22, .36), "beam": (.43, .83, 1.0),
                "shore": (.14, .24, .34), "accent": (.79, .93, 1.0)},
    "heat": {"water": (.06, .25, .34), "beam": (1.0, .35, .14),
             "shore": (.18, .23, .26), "accent": (.96, .48, .17)},
}


def material(name, color, *, metal=0., rough=.4, emission=0.):
    result = bpy.data.materials.new(name=name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    principled = result.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = (*color, 1)
    principled.inputs["Metallic"].default_value = metal
    principled.inputs["Roughness"].default_value = rough
    for input_name in ("Emission Color", "Emission"):
        if input_name in principled.inputs:
            principled.inputs[input_name].default_value = (*color, 1)
    for input_name in ("Emission Strength",):
        if input_name in principled.inputs:
            principled.inputs[input_name].default_value = emission
    return result


def look_at(obj, xyz):
    direction = Vector(xyz) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def new_mesh(name, coordinates, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(coordinates, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    return obj


def terrain(name, zbase, mat, *, n=26):
    coordinates, faces = [], []
    for iy in range(n+1):
        y = -4.8 + iy*9.6/n
        for ix in range(n+1):
            x = -4.8 + ix*9.6/n
            ripple = (.22*math.sin(x*1.6+y*.6) +
                      .14*math.cos(y*2.2-x*.5) +
                      .09*math.sin(x*3.1+y*1.9))
            basin = .12*(x*x+y*y)/20
            coordinates.append((x, y, zbase + ripple + basin))
    for iy in range(n):
        for ix in range(n):
            a = iy*(n+1)+ix
            faces.append((a, a+1, a+n+2, a+n+1))
    return new_mesh(name, coordinates, faces, mat)


def surface(mat, *, n=40):
    coordinates, faces = [], []
    for iy in range(n+1):
        y = -4.8 + iy*9.6/n
        for ix in range(n+1):
            x = -4.8 + ix*9.6/n
            coordinates.append((x, y, 0))
    for iy in range(n):
        for ix in range(n):
            a = iy*(n+1)+ix
            faces.append((a, a+1, a+n+2, a+n+1))
    return new_mesh("Ocean with 1600 articulated wave faces", coordinates, faces, mat)


def ribbon(name, mat, points=48, radius=.045):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 18
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    line = curve.splines.new(type="POLY")
    line.points.add(points-1)
    for p in line.points:
        p.co = (0, 0, 0, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return line


def rough_reef(rng, material_rock):
    """Organic displaced low-poly geology, rather than a default cube floor."""
    for index in range(16):
        x = rng.uniform(-4.0, 4.0)
        y = rng.uniform(-3.8, 3.8)
        z = -1.30 + .22*math.sin(x*1.6+y*.6)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1,
                                              location=(x, y, z))
        rock = bpy.context.object
        rock.name = "Submerged uneven basalt %02d" % index
        rock.scale = (rng.uniform(.17,.57),
                      rng.uniform(.17,.53), rng.uniform(.09,.42))
        for i, vert in enumerate(rock.data.vertices):
            strength = 1+.11*math.sin(i*7+index*3)
            vert.co *= strength
        rock.data.materials.append(material_rock)


def scenario_props(beat, mats):
    props = []
    if beat == "solar":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12,
                                            radius=.65, location=(-2.65, 1.5, 2.30))
        orb = bpy.context.object
        orb.name = "Warm high irradiance light source"
        orb.data.materials.append(mats["glow"])
        props.append(orb)
        # Multiple concentric light rings give source scale and direction.
        for radius in (.82, 1.03):
            loop = ribbon("3D solar halo", mats["glow"], points=65, radius=.020)
            for i, p in enumerate(loop.points):
                angle=2*math.pi*i/64
                p.co=(-2.65+radius*math.cos(angle),
                      1.5, 2.3+radius*math.sin(angle), 1)
    elif beat == "sinking":
        bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=.92, radius2=.13,
                                        depth=1.65, location=(2.0,1.1,.55))
        iceberg = bpy.context.object
        iceberg.name = "Faceted floating polar ice model"
        iceberg.data.materials.append(mats["ice"])
        iceberg.rotation_euler[2] = .24
        props.append(iceberg)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.48,
                                            location=(2.0,1.1,-.53))
        ice_root=bpy.context.object
        ice_root.name="Submerged ice volume"
        ice_root.scale=(1.25,.9,1.55)
        ice_root.data.materials.append(mats["ice"])
    elif beat == "heat":
        for i, x in enumerate((-2.35,2.35)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12,
                                                radius=.78, location=(x,.55,.85))
            globe=bpy.context.object
            globe.name=("3D warm reservoir" if i==0 else "3D cool reservoir")
            globe.scale=(1,.75,1.05)
            globe.data.materials.append(mats["glow"] if i==0 else mats["ice"])
            props.append(globe)
    elif beat == "coriolis":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12,
                                            radius=.35, location=(0,0,.92))
        core=bpy.context.object
        core.name="Gyre center vertical depth reference"
        core.data.materials.append(mats["glow"])
    return props


def set_ribbon_path(line, *, beat, lane, time):
    n = len(line.points)
    for i, point in enumerate(line.points):
        u = i/(n-1)
        if beat == "coriolis":
            theta = math.pi*(.3+u*3.7)+time*.13
            radius=3.55-2.85*u + lane*.12
            x=radius*math.cos(theta)
            y=radius*math.sin(theta)
            z=.31+lane*.21+.16*math.sin(theta*2)
        elif beat == "sinking":
            x=-3.2+6.1*u
            y=-.7+lane*.6
            z=.27 if u<.62 else .27-2.15*((u-.62)/.38)
            z+=.07*math.sin(u*12+time*.45)
        elif beat == "solar":
            x=-2.65+4.9*u
            y=1.5-3.0*u+lane*.27
            z=2.28-2.00*u+.07*math.sin(u*math.tau+time*.25)
        elif beat == "heat":
            x=-2.45+4.9*u
            y=.58+lane*.36
            z=.65+.30*math.sin(math.pi*u)+.09*math.sin(u*15-time*.8)
        else:
            x=-3.7+7.4*u
            y=-1.5+lane*.73
            z=.72+.13*math.sin(u*17+time*.65+lane)
        point.co=(x,y,z,1)


def setup(beat, width, height, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast" if "Medium High Contrast" in (
        [item.identifier for item in scene.view_settings.bl_rna.properties["look"].enum_items]
    ) else "Medium High Contrast"  # compatible Blender installations
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    color = TINTS[beat]
    world = bpy.data.worlds.new("Deep water blue environmental fill")
    scene.world = world
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value=(
        .035,.10,.16,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.50
    mats={
        "water": material("Ocean blue wave PBR",color["water"],metal=.18,rough=.26),
        "rock": material("Submerged irregular geologic substrate",color["shore"],rough=.92),
        "glow": material("Volumetric-looking current emission",color["beam"],
                         metal=.1,rough=.19,emission=1.85),
        "ice":material("Light blue diffused ice",(.45,.80,.97),metal=.0,rough=.19),
    }
    floor=terrain("Sculpted non-flat seafloor", -1.50, mats["rock"])
    ocean=surface(mats["water"])
    rough_reef(random.Random(1204+BEATS.index(beat)*73),mats["rock"])
    ribbons=[ribbon("Animated physical 3D flow lane %d"%i,mats["glow"],
                    points=48,radius=.028+.010*i) for i in range(4)]
    props=scenario_props(beat,mats)
    for index in range(24):
        rng=random.Random(index*77+BEATS.index(beat)*31)
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1, radius=.025+(.013*(index%3)),
            location=(rng.uniform(-3.5,3.5),rng.uniform(-3.4,3.4),
                      rng.uniform(.2,1.0)))
        particle=bpy.context.object
        particle.name="Original suspended light particle %02d"%index
        particle.data.materials.append(mats["ice"] if index%3 else mats["glow"])
        props.append(particle)
    bpy.ops.object.light_add(type="AREA", location=(-3.5,-2.5,6.5))
    key=bpy.context.object
    key.name="Warm softbox sunlight"
    key.data.energy=1150
    key.data.shape="DISK"
    key.data.size=6.0
    key.data.color=(1.0,.83,.63) if beat in ("solar","heat") else (.64,.86,1.0)
    look_at(key,(0,0,0))
    bpy.ops.object.light_add(type="AREA", location=(3.8,3.1,4.2))
    rim=bpy.context.object
    rim.name="Glacial edge rim light"
    rim.data.energy=800
    rim.data.shape="DISK"
    rim.data.size=4.5
    rim.data.color=(.45,.76,1.0)
    look_at(rim,(0,0,0))
    bpy.ops.object.camera_add(location=(.20,-9.2,5.5))
    camera=bpy.context.object
    camera.name="Moving cinematic perspective camera"
    camera.data.lens=42
    camera.data.clip_end=200
    look_at(camera,(0,0,.06))
    scene.camera=camera
    return scene,ocean,ribbons,props,camera


def animate(beat, ocean, ribbons, props, camera, progress):
    t = progress*6.
    for v in ocean.data.vertices:
        x,y=v.co.x,v.co.y
        v.co.z= (.18*math.sin(x*1.45+t*.57)
                 +.12*math.sin(y*1.8-t*.43)
                 +.052*math.sin((x+y)*3.2+t*.8))
    ocean.data.update()
    for index, line in enumerate(ribbons):
        set_ribbon_path(line,beat=beat,lane=index,time=t)
    for index, prop in enumerate(props):
        if prop.name.startswith("Original suspended light particle"):
            prop.location.x += .004*math.sin(t*.4+index*.25)
            prop.location.z += .036*math.sin(t*.6+index*.92)
    camera.location.x=.20+.32*math.sin(progress*math.pi*.7)
    camera.location.y=-9.2+.25*progress
    camera.location.z=5.5+.22*math.sin(progress*math.pi)
    look_at(camera,(0,.08,.06))


def main():
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--frames",type=int,default=10)
    parser.add_argument("--width",type=int,default=600)
    parser.add_argument("--height",type=int,default=580)
    parser.add_argument("--samples",type=int,default=8)
    args=parser.parse_args(argv)
    if (not 2<=args.frames<=24 or not 320<=args.width<=920
            or not 320<=args.height<=890 or not 4<=args.samples<=32):
        parser.error("Unsafe/expensive Blender render configuration")
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    manifest={"schemaVersion":1,"generator":"blender-cycles-cpu",
              "width":args.width,"height":args.height,
              "framesPerBeat":args.frames,"beats":{}}
    for beat in BEATS:
        scene,ocean,ribbons,props,camera=setup(
            beat,args.width,args.height,args.samples)
        records=[]
        folder=out/beat
        folder.mkdir(parents=True,exist_ok=True)
        for i in range(args.frames):
            animate(beat,ocean,ribbons,props,camera,i/(args.frames-1))
            destination=folder/("%04d.png"%i)
            scene.render.filepath=str(destination)
            bpy.ops.render.render(write_still=True)
            if not destination.is_file() or destination.stat().st_size<1500:
                raise RuntimeError("Blender did not export a real 3D PNG frame")
            records.append({"path":f"{beat}/{i:04d}.png",
                            "sha256":hashlib.sha256(destination.read_bytes()).hexdigest()})
            print(f"REAL_BLENDER_3D beat={beat} frame={i+1}/{args.frames}",flush=True)
        manifest["beats"][beat]=records
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"3D COMPLETE: {len(BEATS)} real scenes, "
          f"{args.frames*len(BEATS)} verified Cycles frames",flush=True)


if __name__=="__main__":
    main()
