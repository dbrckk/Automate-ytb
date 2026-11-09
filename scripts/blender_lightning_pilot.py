"""One-frame reproducible Blender/Cycles storm-material proof, not a video.

Original mesh geometry and shader nodes. No stock assets or downloaded models.
Run: blender -b --factory-startup -t 2 --python scripts/blender_lightning_pilot.py -- --out build/p53 --width 540 --height 690 --samples 8
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


def shader(name, rgb, *, rough=.55, metal=0., emission=0., bump=.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1.)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    p = nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1.)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    links = mat.node_tree.links
    if emission:
        e = nodes.new('ShaderNodeEmission')
        e.inputs['Color'].default_value = (*rgb, 1.)
        e.inputs['Strength'].default_value = emission
        out = nodes.get('Material Output')
        links.remove(next(l for l in links if l.to_node == out))
        links.new(e.outputs[0], out.inputs['Surface'])
    if bump and not emission:
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = 30.
        tex.inputs['Detail'].default_value = 3.
        normal = nodes.new('ShaderNodeBump')
        normal.inputs['Strength'].default_value = .19
        normal.inputs['Distance'].default_value = bump
        links.new(tex.outputs['Fac'], normal.inputs['Height'])
        links.new(normal.outputs['Normal'], p.inputs['Normal'])
    return mat


def block(name, position, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if name.startswith('Building'):
        edges=obj.modifiers.new('Machined edge bevel','BEVEL')
        edges.width=.034
        edges.segments=2
        obj.modifiers.new('Facet-weighted normals','WEIGHTED_NORMAL')
    return obj


def bar(name, a, b, radius, mat):
    p, q = Vector(a), Vector(b)
    delta = q-p
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=radius,
                                      depth=delta.length, location=(p+q)/2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    obj.data.materials.append(mat)
    return obj


def bolt(name, points, radius, material):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D'
    curve.resolution_u=2
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    poly=curve.splines.new('POLY')
    poly.points.add(len(points)-1)
    for p, xyz in zip(poly.points,points):
        p.co=(*xyz,1.)
    ob=bpy.data.objects.new(name,curve)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def aim(camera, target):
    delta=Vector(target)-camera.location
    camera.rotation_euler=delta.to_track_quat('-Z','Y').to_euler()


def cloud_bank(depth, material):
    """One physically joined implicit 3D storm mass, not 14 cotton balls.

    Each of three banks has fourteen independent density lobes. Blender
    converts the fused metaball surface to a genuine editable mesh before
    Cycles shades it. A low-amplitude noise displace adds microrelief.
    """
    family='Fused cumulonimbus bank %d'%depth
    implicit=bpy.data.metaballs.new(family)
    implicit.resolution=.30
    implicit.render_resolution=.22
    implicit.threshold=.58
    ob=bpy.data.objects.new(family,implicit)
    bpy.context.collection.objects.link(ob)
    for i in range(14):
        rng=random.Random(6800+depth*71+i)
        x=-8+i*1.27+rng.uniform(-.55,.55)
        y=2.5+depth*2.0+rng.uniform(-.6,.6)
        z=6.1+depth*.50+rng.uniform(-.30,.50)
        element=implicit.elements.new(type='BALL')
        element.co=(x,y,z)
        element.radius=1.05+rng.uniform(.05,.48)
        element.stiffness=2.0
    implicit.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH')
    ob=bpy.context.object
    if len(ob.data.vertices)<500:
        raise RuntimeError('Real 3D storm mesh did not emerge from clouds')
    for face in ob.data.polygons:
        face.use_smooth=True
    noise=bpy.data.textures.new('Bank billow microrelief %d'%depth,
                                type='CLOUDS')
    noise.noise_scale=.85
    displacement=ob.modifiers.new('Subtle cloud turbulence','DISPLACE')
    displacement.texture=noise
    displacement.strength=.14
    return len(ob.data.vertices)


def lamp(name, position, energy, color, size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.color=color
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=position
    aim(obj,(.1,2.,3.))


def build():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.max_bounces=3
    scene.world.use_nodes=True
    world_bg=scene.world.node_tree.nodes.get('Background')
    world_bg.inputs['Color'].default_value=(.012,.019,.058,1.)
    world_bg.inputs['Strength'].default_value=.43
    slate=shader('Coated slate terrain roughness microbump',(.045,.065,.090),rough=.23,metal=.28,bump=.019)
    puddle=shader('Reflective puddles with smooth irregular margins',(.023,.043,.068),rough=.095,metal=.48,bump=.006)
    steel=shader('Brushed aluminium PBR',(.22,.30,.35),rough=.33,metal=.81,bump=.008)
    steel_dark=shader('Dark galvanized braces',(.067,.11,.14),rough=.44,metal=.72,bump=.009)
    building=shader('Wet concrete procedural bump',(.045,.067,.080),rough=.59,metal=.04,bump=.019)
    cloud_mat=shader('Cumulonimbus illuminated textured microrelief',(.12,.17,.25),rough=.92,bump=.045)
    cloud_shadow=shader('Storm-cloud self-shaded lower faces',(.061,.082,.15),rough=.97,bump=.036)
    amber=shader('Warm amber industrial windows',(.95,.38,.12),emission=2.5)
    blue=shader('Cool industrial windows',(.24,.60,.85),emission=.95)
    hot=shader('Electrical plasma luminous core',(.72,.88,1.0),emission=8.0)
    branches=shader('Electrical blue outer tendrils',(.24,.58,.98),emission=3.3)
    red=shader('Mast aviation light',(.98,.16,.085),emission=2.0)
    # Actual 3D reflective terrain; not a 2D gradient or PNG plate.
    block('3D sea-level wet city substrate',(0,2,-.13),(36,26,.2),slate)
    puddle_rng=random.Random(1772)
    for j in range(30):
        px=puddle_rng.uniform(-7.,7.)
        py=puddle_rng.uniform(-3.4,3.5)
        radius=puddle_rng.uniform(.22,.73)
        bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=radius,
                                            depth=.008,
                                            location=(px,py,-.023))
        pool=bpy.context.object
        pool.name='Wet specular puddle %02d'%j
        pool.scale.y=puddle_rng.uniform(.33,.83)
        pool.data.materials.append(puddle)
    rng=random.Random(38017)
    for i in range(19):
        x=-8.+i*.84
        y=4.8+rng.random()*3.5
        h=.85+rng.random()*2.9
        width=.48+rng.random()*.41
        block('Building %02d'%i,(x,y,h/2),(width,.76,h),building)
        if i%3==0:
            block('Rooftop ventilation duct %02d'%i,
                  (x+.06,y,h+.17),(.24,.27,.29),steel_dark)
            bar('Roof aerial %02d'%i,(x-.16,y,h),(x-.16,y,h+.65),.018,steel)
        if i%4==1:
            block('Industrial cantilever roof %02d'%i,
                  (x,y-.09,h+.02),(width+.22,1.00,.09),steel_dark)
            bar('Exhaust stack %02d'%i,
                (x+.13,y+.12,h+.05),(x+.13,y+.12,h+.57),.055,steel)
        for floor in range(1,int(h/.36)):
            if (floor+i)%3==0:
                block('Light %02d %02d'%(i,floor),
                      (x-.18,y-.40,.25+floor*.36),(.095,.023,.073),
                      amber if (i+floor)%4==0 else blue)
    # A real spatial mast with tapered triangulated metal members.
    tip=(1.2,0,3.7)
    for leg in range(3):
        theta=leg*2*math.pi/3
        base=(tip[0]+.72*math.cos(theta),.72*math.sin(theta),.05)
        bar('Mast metal leg %d'%leg,base,tip,.046,steel)
    for level in range(1,12):
        z=level*.30
        spread=.72*(1-z/3.75)
        points=[(tip[0]+spread*math.cos(i*2*math.pi/3),
                 spread*math.sin(i*2*math.pi/3),z) for i in range(3)]
        for i in range(3):
            bar('Triangular lattice ring %d %d'%(level,i),points[i],points[(i+1)%3],.023,steel)
            if level>1:
                prevz=z-.30
                prevspread=.72*(1-prevz/3.75)
                prev=(tip[0]+prevspread*math.cos((i+1)*2*math.pi/3),
                      prevspread*math.sin((i+1)*2*math.pi/3),prevz)
                bar('Tension diagonals %d %d'%(level,i),points[i],prev,.015,steel_dark)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.085,location=tip)
    bpy.context.object.name='Physical tower beacon'
    bpy.context.object.data.materials.append(red)
    # Three coherent spatial storm banks with 42 sculpted billows,
    # instead of forty-two visibly separate shaded-sphere sprites.
    cloud_vertices=0
    for depth in range(3):
        cloud_vertices+=cloud_bank(
            depth,cloud_shadow if depth==2 else cloud_mat)
    # Irregular conductive curve in real 3D, anchored to actual tower tip.
    rng3=random.Random(14811)
    points=[tip]
    for i in range(1,23):
        f=i/22
        points.append((tip[0]-.9*f+.2*math.sin(f*10)+rng3.uniform(-.13,.13),
                       .35*f+rng3.uniform(-.15,.15),
                       tip[2]+4.5*f))
    bolt('Main skyward channel 3D',points,.028,hot)
    for j in (5,10,15,19):
        source=points[j]
        sgn=1 if j%2 else -1
        fork=[source]
        for k in range(1,6):
            fork.append((source[0]+sgn*(.16*k)+rng3.uniform(-.10,.10),
                         source[1]+.08*k+rng3.uniform(-.08,.08),
                         source[2]+.15*k))
        bolt('Electrical side fork %d'%j,fork,.008,branches)
    lamp('Blue-white lightning motivated key',(2,-3,9),1350,(.40,.65,1.0),7)
    lamp('Warm industrial sodium backlight',(-4,3,6),1400,(1.0,.42,.24),9)
    lamp('Cold atmospheric fill',(3,-1,10),1100,(.62,.75,1.0),12)
    bpy.ops.object.camera_add(location=(9,-15,8.2))
    camera=bpy.context.object
    aim(camera,(.2,2.1,4.1))
    camera.data.lens=45
    scene.camera=camera
    scene.view_settings.view_transform='Standard'
    return scene, cloud_vertices


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True)
    parser.add_argument('--width',type=int,default=540)
    parser.add_argument('--height',type=int,default=690)
    parser.add_argument('--samples',type=int,default=8)
    config=parser.parse_args(args)
    if not (320<=config.width<=900 and 400<=config.height<=1380 and
            4<=config.samples<=64):
        parser.error('Unsafe pilot render dimensions or samples')
    dest=Path(config.out).resolve()
    dest.mkdir(parents=True,exist_ok=True)
    scene, cloud_vertices=build()
    scene.cycles.samples=config.samples
    # Eight-sample Cycles previews were visibly grainy. Native Cycles
    # denoising is CPU/free and preserves authored geometry and lighting.
    for layer in scene.view_layers:
        if hasattr(layer, 'cycles') and hasattr(layer.cycles, 'use_denoising'):
            layer.cycles.use_denoising=True
    scene.render.resolution_x=config.width
    scene.render.resolution_y=config.height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    filename=dest/'storm-pbr-pilot.png'
    scene.render.filepath=str(filename)
    bpy.ops.render.render(write_still=True)
    manifest={
        'schemaVersion':1,'generator':'blender-cycles-cpu',
        'domain':'original-storm-pbr-pilot',
        'width':config.width,'height':config.height,'samples':config.samples,
        'meshObjects':sum(o.type=='MESH' for o in bpy.data.objects),
        'lightObjects':sum(o.type=='LIGHT' for o in bpy.data.objects),
        'proceduralMaterials':len(bpy.data.materials),
        'actual3dCloudMeshes':len([o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Fused cumulonimbus')]),
        'actual3dCloudLobes':42,
        'actual3dCloudVertices':cloud_vertices,
        'file':'storm-pbr-pilot.png',
        'sha256':hashlib.sha256(filename.read_bytes()).hexdigest(),
    }
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('P53_RENDER_EVIDENCE',json.dumps(manifest,sort_keys=True))


if __name__=='__main__':
    main()
