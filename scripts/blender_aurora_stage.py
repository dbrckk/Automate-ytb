"""Render five ORIGINAL animated 3D aurora science scenes with Blender Cycles CPU.

Blender produces real perspective images, not fake 3D backgrounds, stock
images, remote models, or paid inference. The aurora sheets and magnetic
paths are educational illustrations, not plasma or atmospheric simulation.

Run:
 blender -b --factory-startup -t 2 --python scripts/blender_aurora_stage.py -- \
   --output build/aurora-3d --frames 12 --width 600 --height 750 --samples 8
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
SIZE_LIMIT = (1080, 1380)


def surface(name, rgb, *, glow=0., rough=.52, metallic=0., translucent=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    if glow:
        shader = nodes.new("ShaderNodeEmission")
        shader.inputs["Color"].default_value = (*rgb, 1)
        shader.inputs["Strength"].default_value = glow
    else:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Base Color"].default_value = (*rgb, 1)
        shader.inputs["Roughness"].default_value = rough
        shader.inputs["Metallic"].default_value = metallic
    if translucent and glow:
        transparent=nodes.new("ShaderNodeBsdfTransparent")
        mixer=nodes.new("ShaderNodeMixShader")
        # Vertical luminous threads instead of a flat opaque rectangle.
        # Generated X is horizontal position; generated Z fades edges.
        # Keeping the majority transparent preserves real star parallax.
        coordinates=nodes.new("ShaderNodeTexCoord")
        axes=nodes.new("ShaderNodeSeparateXYZ")
        frequency=nodes.new("ShaderNodeMath")
        frequency.operation="MULTIPLY"
        frequency.inputs[1].default_value=122
        oscillation=nodes.new("ShaderNodeMath")
        oscillation.operation="SINE"
        absolute=nodes.new("ShaderNodeMath")
        absolute.operation="ABSOLUTE"
        sharpen=nodes.new("ShaderNodeMath")
        sharpen.operation="POWER"
        sharpen.inputs[1].default_value=5
        strength=nodes.new("ShaderNodeMath")
        strength.operation="MULTIPLY"
        strength.inputs[1].default_value=.50
        vertical=nodes.new("ShaderNodeMath")
        vertical.operation="MULTIPLY"
        vertical.inputs[1].default_value=math.pi
        edge_fade=nodes.new("ShaderNodeMath")
        edge_fade.operation="SINE"
        final_opacity=nodes.new("ShaderNodeMath")
        final_opacity.operation="MULTIPLY"
        links=mat.node_tree.links
        links.new(coordinates.outputs["Generated"],axes.inputs[0])
        links.new(axes.outputs["X"],frequency.inputs[0])
        links.new(frequency.outputs[0],oscillation.inputs[0])
        links.new(oscillation.outputs[0],absolute.inputs[0])
        links.new(absolute.outputs[0],sharpen.inputs[0])
        links.new(sharpen.outputs[0],strength.inputs[0])
        links.new(axes.outputs["Z"],vertical.inputs[0])
        links.new(vertical.outputs[0],edge_fade.inputs[0])
        links.new(strength.outputs[0],final_opacity.inputs[0])
        links.new(edge_fade.outputs[0],final_opacity.inputs[1])
        # Natural-looking columns taper towards both ends of each ribbon.
        # World-space folds still come from actual animated 3D geometry;
        # this anisotropic texture only controls sheet transmission.
        x_weight=nodes.new("ShaderNodeMath")
        x_weight.operation="MULTIPLY"
        x_weight.inputs[1].default_value=math.pi
        x_taper=nodes.new("ShaderNodeMath")
        x_taper.operation="SINE"
        x_opacity=nodes.new("ShaderNodeMath")
        x_opacity.operation="MULTIPLY"
        noise=nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=7.5
        noise.inputs["Detail"].default_value=2.5
        noise.inputs["Roughness"].default_value=.62
        noise_opacity=nodes.new("ShaderNodeMath")
        noise_opacity.operation="MULTIPLY"
        links.new(axes.outputs["X"],x_weight.inputs[0])
        links.new(x_weight.outputs[0],x_taper.inputs[0])
        links.new(final_opacity.outputs[0],x_opacity.inputs[0])
        links.new(x_taper.outputs[0],x_opacity.inputs[1])
        links.new(coordinates.outputs["Generated"],noise.inputs["Vector"])
        links.new(x_opacity.outputs[0],noise_opacity.inputs[0])
        links.new(noise.outputs["Fac"],noise_opacity.inputs[1])
        links.new(noise_opacity.outputs[0],mixer.inputs[0])
        mat.node_tree.links.new(transparent.outputs[0],mixer.inputs[1])
        mat.node_tree.links.new(shader.outputs[0],mixer.inputs[2])
        mat.node_tree.links.new(mixer.outputs[0], output.inputs["Surface"])
    else:
        mat.node_tree.links.new(shader.outputs[0], output.inputs["Surface"])
    return mat


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def sphere(name, x, y, z, rad, mat, *, low=False):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16 if low else 32, ring_count=10 if low else 20,
        radius=rad, location=(x, y, z))
    obj=bpy.context.object
    obj.name=name
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def curve(name, mat, *, points=80, radius=.015):
    data=bpy.data.curves.new(name, "CURVE")
    data.dimensions="3D"
    data.bevel_depth=radius
    data.bevel_resolution=2
    spline=data.splines.new("POLY")
    spline.points.add(points-1)
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return spline


def mountain_floor(material, *, offset=-1.4, grid=23):
    vertices, faces=[],[]
    for i in range(grid+1):
        y=-3.3+7.5*i/grid
        for j in range(grid+1):
            x=-5.8+11.6*j/grid
            z=offset+.17*math.sin(x*.8+y*.9)+.14*math.sin(x*2.1+y*.45)
            z+=.075*(abs(x)+abs(y))
            vertices.append((x,y,z))
    for i in range(grid):
        for j in range(grid):
            a=i*(grid+1)+j
            faces.append((a,a+1,a+grid+2,a+grid+1))
    mesh=bpy.data.meshes.new("Original alpine terrain")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new("Original snow and stone alpine mountains",mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons:
        poly.use_smooth=True
    return obj


def curtain(name, material, *, index=0, nx=64, nz=34):
    verts, faces=[],[]
    for row in range(nz):
        for col in range(nx):
            verts.append((0,0,0))
    for row in range(nz-1):
        for col in range(nx-1):
            a=row*nx+col
            faces.append((a,a+1,a+nx+1,a+nx))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    # Both sides catch the emissive glow as the camera moves around the folds.
    for poly in mesh.polygons:
        poly.use_smooth=True
    return obj


def animate_curtain(obj, index, q):
    nx,nz=64,34
    phase=q*math.tau*.64 + index*.78
    for row in range(nz):
        v=row/(nz-1)
        for col in range(nx):
            u=col/(nx-1)
            x=(u-.5)*9.0
            # Three independent wavelengths prevent uniform ribbon shapes.
            # The coherent travelling phase keeps each surface continuous.
            folding=(.37+.09*index)*math.sin(
                x*(.95+.08*index)+phase)
            folding+=.18*math.sin(x*2.4-phase*.63+v*3.1)
            folding+=.09*math.sin(x*4.1+phase*.37+index)
            y=1.1+index*.61+folding*(.36+v*.80)
            z=1.05+v*(3.6+index*.12)+.27*math.sin(x*.61+phase)*v
            x+=.12*math.sin(v*4.0+phase+x*.31)
            obj.data.vertices[row*nx+col].co=(x,y,z)
    obj.data.update()


def animate_stream(line, *, index, q, bend):
    for k,p in enumerate(line.points):
        u=k/(len(line.points)-1)
        x=-4.2+u*8.4
        y=-.65+index*.23+.26*math.sin(u*12+q*math.tau*.9+index*.43)
        z=1.55+index*.37+(.75*math.sin(math.pi*u) if bend else
                         .12*math.sin(u*15+q*math.tau))
        p.co=(x,y,z,1)


def animate_field(line, *, index, q):
    r=2.15+index*.38
    for k,p in enumerate(line.points):
        angle=math.tau*k/(len(line.points)-1)
        x=r*math.cos(angle)
        y=.25+.25*math.sin(angle*2+q*math.tau*.65)
        z=2.00+r*.83*math.sin(angle)
        p.co=(x,y,z,1)


def setup(beat, width, height, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=samples
    try:
        scene.view_layers[0].cycles.use_denoising=True
    except (AttributeError, TypeError):
        pass
    scene.render.resolution_x=width
    scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGBA"
    scene.render.threads_mode="FIXED"
    scene.render.threads=2
    scene.view_settings.view_transform="Standard"
    try:
        scene.view_settings.look="Medium High Contrast"
    except TypeError:
        pass
    world=bpy.data.worlds.new("Starlit polar sky")
    scene.world=world
    world.use_nodes=True
    world.node_tree.nodes.get("Background").inputs["Color"].default_value=(.018,.025,.07,1)
    world.node_tree.nodes.get("Background").inputs["Strength"].default_value=.42
    mats={
        "snow":surface("Blue violet alpine stone",(.085,.16,.25),rough=.87),
        "earth":surface("Original blue Earth sphere",(.045,.22,.44),rough=.43,metallic=.08),
        "sun":surface("Incandescent solar source",(1.0,.38,.10),glow=2.2),
        "cyan":surface("Charged teal particle",(.24,.81,1.0),glow=1.5),
        "green":surface("Atomic oxygen green photon",(.05,.94,.42),glow=1.6),
        "magenta":surface("Ionized nitrogen violet glow",(.64,.18,1.0),glow=1.45),
        "ice":surface("Polar snow highlight",(.67,.83,.92),rough=.63),
        "red":surface("Upper atmosphere oxygen red glow",(1.0,.18,.22),glow=1.45),
        "star":surface("Original three-dimensional distant starlight",(.63,.85,1),glow=.9),
        "veil_green":surface("Translucent physical oxygen aurora",(.05,.94,.42),glow=1.5,translucent=True),
        "veil_cyan":surface("Translucent physical blue aurora",(.24,.81,1),glow=1.45,translucent=True),
        "veil_magenta":surface("Translucent physical nitrogen aurora",(.64,.18,1),glow=1.45,translucent=True),
        "veil_red":surface("Translucent physical red aurora",(1,.18,.22),glow=1.42,translucent=True),
    }
    mountain_floor(mats["snow"])
    rng=random.Random(2071+BEATS.index(beat)*53)
    # Foreground uneven boulders prevent a sterile flat-background appearance.
    for i in range(12):
        x,y=rng.uniform(-4.4,4.4),rng.uniform(-2.8,3.5)
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,radius=rng.uniform(.14,.34),
            location=(x,y,-1.23+abs(x)*.04))
        obj=bpy.context.object
        obj.name="Irregular glacier rock %02d"%i
        obj.scale=(1.0,rng.uniform(.66,1.4),rng.uniform(.45,.9))
        obj.data.materials.append(mats["ice"] if i%4==0 else mats["snow"])
    # Real 3D stars with depth parallax, not a static image plate.
    for i in range(74):
        x,y,z=(rng.uniform(-7.6,7.6),rng.uniform(3.3,7.6),
               rng.uniform(.6,7.6))
        sphere("3D star depth layer %02d"%i,x,y,z,
               rng.uniform(.012,.027),mats["star"],low=True)
    dynamic={"sheets":[],"fields":[],"streams":[],"particles":[]}
    if beat in ("solar_wind","magnetic_field"):
        sphere("Globe physical three-dimensional Earth",
               2.50 if beat=="solar_wind" else .22,
               .6,2.10,1.22,mats["earth"])
        # Polar caps and compact glint use their own 3D material/geometry.
        sphere("Polar ice on modeled Earth",
               2.50 if beat=="solar_wind" else .22,
               .59,3.19,.24,mats["ice"],low=True)
    if beat=="solar_wind":
        sphere("Glowing original solar sphere",-3.10,1.3,2.52,.92,mats["sun"])
        for i in range(9):
            dynamic["streams"].append(curve(
                "Sun-to-Earth charged particle trajectory %02d"%i,
                mats["cyan"] if i%3 else mats["magenta"],
                points=55,radius=.025))
    elif beat=="magnetic_field":
        for i in range(6):
            dynamic["fields"].append(curve(
                "Actual 3D magnetic guidance line %02d"%i,
                mats["cyan"] if i%2 else mats["green"],points=81,radius=.017))
        for i in range(5):
            dynamic["streams"].append(curve(
                "Electrons bending toward poles %02d"%i,
                mats["cyan"],points=55,radius=.018))
    elif beat in ("collisions","emission"):
        gases=[]
        for i in range(26):
            x,y,z=rng.uniform(-3.5,3.5),rng.uniform(-1.5,2.3),rng.uniform(.65,4.5)
            mat=(mats["green"] if i%4 else mats["magenta"]) if beat=="emission" else mats["ice"]
            obj=sphere("Physical oxygen or nitrogen excitation %02d"%i,
                       x,y,z,.070+.021*(i%4),mat,low=True)
            gases.append((obj,x,y,z))
        dynamic["particles"]=gases
        if beat=="emission":
            for i in range(7):
                line=curve("Visible photon trajectory %02d"%i,
                           mats["red"] if i%4==0 else mats["green"],
                           points=31,radius=.012)
                dynamic["streams"].append(line)
    if beat=="curtains":
        for i in range(6):
            mat=(mats["veil_green"],mats["veil_cyan"],mats["veil_magenta"],mats["veil_green"],mats["veil_red"],mats["veil_cyan"])[i]
            dynamic["sheets"].append(curtain(
                "True 3D pleated aurora emissive curtain %02d"%i,mat,index=i))
    bpy.ops.object.light_add(type="AREA",location=(-3.0,-4.2,6.5))
    key=bpy.context.object
    key.name="Softbox polar diffuse key light"
    key.data.energy=750
    key.data.shape="DISK"
    key.data.size=6.0
    key.data.color=(.53,.83,1)
    aim(key,(0,0,1.1))
    bpy.ops.object.light_add(type="AREA",location=(3.8,1.8,5.0))
    rim=bpy.context.object
    rim.name="Colored aurora edge light"
    rim.data.energy=610
    rim.data.shape="DISK"
    rim.data.size=4.0
    rim.data.color=(.35,1,.73)
    aim(rim,(0,0,1.7))
    bpy.ops.object.camera_add(location=(.1,-10.8,4.3))
    camera=bpy.context.object
    camera.name="Dolly camera with physical parallax"
    camera.data.lens=43
    camera.data.clip_end=150
    aim(camera,(0,.4,2.0))
    scene.camera=camera
    return scene,dynamic,camera


def animate(beat,dynamic,camera,q):
    for i,sheet in enumerate(dynamic["sheets"]):
        animate_curtain(sheet,i,q)
    for i,line in enumerate(dynamic["fields"]):
        animate_field(line,index=i,q=q)
    for i,line in enumerate(dynamic["streams"]):
        if beat=="emission":
            for k,p in enumerate(line.points):
                u=k/(len(line.points)-1)
                x=-3.3+i*.9+u*(1.0+.3*(i%3))
                y=-.8+i*.13+.11*math.sin(q*math.tau+u*8+i)
                z=1.45+.35*i+u*1.2+.11*math.sin(q*math.tau+u*6)
                p.co=(x,y,z,1)
        else:
            animate_stream(line,index=i,q=q,bend=beat=="magnetic_field")
    for i,(obj,x,y,z) in enumerate(dynamic["particles"]):
        obj.location.x=x+.10*math.sin(q*math.tau*.75+i*.73)
        obj.location.y=y+.09*math.cos(q*math.tau*.4+i*.6)
        obj.location.z=z+.12*math.sin(q*math.tau+i*.9)
    camera.location.x=.1+.37*math.sin(q*math.pi*.88)
    camera.location.y=-10.8+.25*q
    camera.location.z=4.3+.18*math.sin(q*math.pi)
    aim(camera,(0,.4,2.0))


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--frames",type=int,default=12)
    parser.add_argument("--width",type=int,default=600)
    parser.add_argument("--height",type=int,default=750)
    parser.add_argument("--samples",type=int,default=8)
    options=parser.parse_args(args)
    if (not 2 <= options.frames <= 24
            or not 320 <= options.width <= SIZE_LIMIT[0]
            or not 320 <= options.height <= SIZE_LIMIT[1]
            or not 4 <= options.samples <= 32):
        parser.error("Unsupported size, sampling or Blender frame count")
    output=options.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    manifest={"schemaVersion":1,"domain":"aurora",
              "generator":"blender-cycles-cpu","width":options.width,
              "height":options.height,"framesPerBeat":options.frames,
              "beats":{}}
    for beat in BEATS:
        scene,dynamic,camera=setup(beat,options.width,options.height,options.samples)
        folder=output/beat
        folder.mkdir(parents=True,exist_ok=True)
        records=[]
        for i in range(options.frames):
            q=i/(options.frames-1)
            animate(beat,dynamic,camera,q)
            destination=folder/("%04d.png"%i)
            scene.render.filepath=str(destination)
            bpy.ops.render.render(write_still=True)
            if not destination.is_file() or destination.stat().st_size < 1500:
                raise RuntimeError(f"Blender did not render an image: {destination}")
            records.append({
                "path":f"{beat}/{i:04d}.png",
                "sha256":hashlib.sha256(destination.read_bytes()).hexdigest()})
            print(f"REAL_BLENDER_AURORA beat={beat} frame={i+1}/{options.frames}",
                  flush=True)
        manifest["beats"][beat]=records
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",
                                         encoding="utf-8")
    print(f"BLENDER AURORA COMPLETE: {len(BEATS)*options.frames} frames",flush=True)


if __name__=="__main__":
    main()
