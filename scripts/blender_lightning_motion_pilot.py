"""P5.4: five genuine, causally different Blender/Cycles storm shots.

This is a bounded 3D motion *proof* for choosing the future production engine.
It does not replace the Kokoro 1080x1920 release pipeline or claim to be a
finished Short. Every image is ray-traced from real meshes and lights.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blender_lightning_pilot as pilot

BEATS=("charge","leader","connection","return","thunder")
STORY_VERSION="storm-3d-causal-motion-p54-v1"


def enhance_materials() -> None:
    """Add correlated albedo/roughness material detail, not a painted texture."""
    for name in ("Cumulonimbus illuminated textured microrelief",
                 "Storm-cloud self-shaded lower faces"):
        mat=bpy.data.materials[name]
        nodes=mat.node_tree.nodes
        links=mat.node_tree.links
        p=nodes.get("Principled BSDF")
        noise=nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=2.5
        noise.inputs["Detail"].default_value=6.
        noise.inputs["Roughness"].default_value=.72
        ramp=nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position=.19
        ramp.color_ramp.elements[0].color=(.018,.030,.057,1.)
        ramp.color_ramp.elements[1].position=.79
        ramp.color_ramp.elements[1].color=(.23,.31,.40,1.)
        mid=ramp.color_ramp.elements.new(.52)
        mid.color=(.073,.115,.17,1.)
        links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"],p.inputs["Base Color"])
        p.inputs["Roughness"].default_value=.96
    # Compact real-scale machining, vents and facade depth, instead of
    # window dots pasted onto nineteen simple cuboids.
    steel=bpy.data.materials["Dark galvanized braces"]
    for building in sorted([o for o in bpy.data.objects
                            if o.name.startswith("Building ")],key=lambda o:o.name):
        index=int(building.name.split()[1])
        if index%2: continue
        x,y,z=building.location
        width,depth,height=building.dimensions
        for side in (-1,1):
            pilot.block("Facade vertical rib %02d %s"%(index,side),
                        (x+side*width*.36,y-depth*.515,z),
                        (.045,.08,height*.92),steel)
        pilot.block("Machine-top parapet %02d"%index,
                    (x,y-depth*.45,z+height*.48),
                    (width+.06,.09,.09),steel)
        if index%4==0:
            for j in range(3):
                pilot.block("Louver ventilation %02d %d"%(index,j),
                            (x-width*.20+j*width*.18,
                             y-depth*.525,z+height*.27),
                            (.12,.05,.035),steel)
    for obj in [o for o in bpy.data.objects
                if o.name.startswith("Fused cumulonimbus")]:
        # Macro/meso silhouette turbulence: preserve joined meshes but
        # break mechanically round, cotton-ball scallops from the pilot.
        for v in obj.data.vertices:
            x,y,z=v.co
            v.co.z += (.21*math.sin(x*.84+y*.42)
                       +.11*math.sin(x*2.34-y*.72)
                       +.16*math.sin(x*.35+z*1.3))
            v.co.y += .13*math.sin(x*.93+z*.49)
        obj.data.update()
        modifier=next((m for m in obj.modifiers
                       if m.type=="DISPLACE"),None)
        if modifier:
            modifier.strength=.25
    # Existing disk-shaped black puddles are too repetitive and toy-like.
    # Break their silhouettes and orient them to the terrain perspective.
    for obj in [o for o in bpy.data.objects
                if o.name.startswith("Wet specular puddle")]:
        idx=int(obj.name.split()[-1])
        obj.rotation_euler.z=.22*math.sin(idx*1.3)
        for vertex in obj.data.vertices:
            x,y,z=vertex.co
            angle=math.atan2(y,x)
            fac=1+.24*math.sin(3*angle+idx)+.15*math.cos(5*angle+idx*.7)
            vertex.co.x=x*fac
            vertex.co.y=y*fac
        obj.data.update()


def electrical_charges():
    cyan=bpy.data.materials["Electrical blue outer tendrils"]
    amber=bpy.data.materials["Warm amber industrial windows"]
    rng=random.Random(17715)
    objects=[]
    for i in range(28):
        x=rng.uniform(-5.5,6.5)
        y=rng.uniform(2.2,5.2)
        z=rng.uniform(6.0,7.8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,
                                radius=.038+rng.random()*.018,
                                location=(x,y,z))
        ob=bpy.context.object
        ob.name="Charge ion particle %02d"%i
        ob.data.materials.append(cyan if i%2 else amber)
        ob["base_z"]=float(z)
        objects.append(ob)
    return objects


def pressure_wave():
    mat=pilot.shader("Thunder pressure wave illustrated in 3D",
                     (.10,.43,.61),emission=.14)
    bpy.ops.mesh.primitive_torus_add(major_segments=80,
        minor_segments=5,location=(1.2,0,3.7),
        major_radius=1.0,minor_radius=.009)
    wave=bpy.context.object
    wave.name="Thunder expansion 3D annulus"
    wave.data.materials.append(mat)
    return wave


def pose(beat: str, progress: float, charges, ring) -> dict:
    """Pose actual geometry, field energy and perspective for one shot.

    The pilot intentionally uses a fresh camera and changing world positions
    at EVERY timestamp. Same seed / beat / time always yields same frame.
    """
    if beat not in BEATS or not 0<=progress<=1 or not math.isfinite(progress):
        raise ValueError("Invalid 3D story action clock")
    index=BEATS.index(beat)
    start_end=[
        ((6.4,-11.8,9.8),(5.9,-11.4,9.2),(-.8,2.9,6.8)),
        ((5.7,-12.3,8.2),(4.7,-10.8,6.7),(.2,2.3,5.6)),
        ((4.4,-9.2,5.5),(4.0,-8.6,5.0),(1.15,.7,3.88)),
        ((6.2,-11.4,7.6),(5.7,-10.6,7.1),(.5,1.4,5.2)),
        ((7.6,-14.4,8.2),(8.4,-15.7,8.7),(.2,2.2,4.4)),
    ]
    start,finish,target=start_end[index]
    smooth=progress*progress*(3-2*progress)
    camera=bpy.context.scene.camera
    camera.location=Vector(tuple(a+(b-a)*smooth
                                   for a,b in zip(start,finish)))
    pilot.aim(camera,target)
    camera.data.lens=(52,59,62,52,43)[index]
    for depth in range(3):
        bank=bpy.data.objects["Fused cumulonimbus bank %d"%depth]
        bank.location.x=(depth-1)*.12+.10*progress*(1+depth*.3)
        bank.location.y=.08*math.sin(progress*math.pi+depth)
    bolt=bpy.data.objects["Main skyward channel 3D"]
    forks=[ob for ob in bpy.data.objects
           if ob.name.startswith("Electrical side fork ")]
    # Leader grows from cloud toward the tower; connection reaches upward.
    # The return stroke then lights the complete path in the reverse causal
    # direction. Visibility cannot invent new independent flashes.
    if beat=="charge":
        bolt.hide_render=True
        lead_fraction=0.
        power=.02
    elif beat=="leader":
        bolt.hide_render=False
        lead_fraction=.12+.82*smooth
        bolt.data.bevel_factor_start=1-lead_fraction
        bolt.data.bevel_factor_end=1.
        power=.06
    elif beat=="connection":
        bolt.hide_render=False
        lead_fraction=.87+.13*smooth
        bolt.data.bevel_factor_start=1-lead_fraction
        bolt.data.bevel_factor_end=1.
        power=.12+.22*smooth
    elif beat=="return":
        bolt.hide_render=False
        lead_fraction=1.
        bolt.data.bevel_factor_start=0.
        bolt.data.bevel_factor_end=1.
        power=.33+2.0*math.exp(-((progress-.34)/.19)**2)
    else:
        bolt.hide_render=False
        lead_fraction=1.
        bolt.data.bevel_factor_start=0.
        bolt.data.bevel_factor_end=1.
        power=.12*(1-progress)
    for j,ob in enumerate(forks):
        ob.hide_render=beat not in ("return","thunder") or (beat=="thunder" and progress>.50)
    for j,ob in enumerate(charges):
        ob.hide_render=beat!="charge"
        ob.location.z = ob["base_z"]+.09*math.sin(progress*3+1.7*j)
    # Absolute placement avoids cumulative frame-to-frame charge drift.
    energy=230+330*power
    bpy.data.objects["Blue-white lightning motivated key"].data.energy=energy
    bpy.data.objects["Warm industrial sodium backlight"].data.energy=930
    bpy.data.objects["Cold atmospheric fill"].data.energy=680+140*power
    ring.hide_render=beat!="thunder"
    if beat=="thunder":
        scale=.8+4.5*smooth
        ring.scale=(scale,scale,1.)
    return {"beat":beat,"progress":round(progress,4),
            "cameraPosition":[round(v,4) for v in camera.location],
            "visibleChannelFraction":round(lead_fraction,4),
            "electricalLightPower":round(power,4)}


def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True)
    ap.add_argument("--width",type=int,default=320)
    ap.add_argument("--height",type=int,default=400)
    ap.add_argument("--frames-per-beat",type=int,default=4)
    ap.add_argument("--fps",type=int,default=8)
    ap.add_argument("--samples",type=int,default=8)
    conf=ap.parse_args(args)
    if (not 320<=conf.width<=720 or not 400<=conf.height<=900
            or not 2<=conf.frames_per_beat<=12 or
            not 4<=conf.fps<=24 or not 4<=conf.samples<=32):
        ap.error("Unsafe 3D pilot budget")
    root=Path(conf.out).resolve()
    root.mkdir(parents=True,exist_ok=True)
    scene,cloud_vertices=pilot.build()
    enhance_materials()
    charges=electrical_charges()
    wave=pressure_wave()
    scene.cycles.samples=conf.samples
    for layer in scene.view_layers:
        if hasattr(layer,"cycles") and hasattr(layer.cycles,"use_denoising"):
            layer.cycles.use_denoising=True
    scene.render.resolution_x=conf.width
    scene.render.resolution_y=conf.height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    manifest={"schemaVersion":1,"version":STORY_VERSION,
              "generator":"blender-cycles-cpu-animated",
              "beatOrder":list(BEATS),
              "width":conf.width,"height":conf.height,
              "fps":conf.fps,"samples":conf.samples,
              "framesPerBeat":conf.frames_per_beat,
              "cloudVertices":cloud_vertices,
              "frameEvidence":[]}
    count=0
    for beat in BEATS:
        for i in range(conf.frames_per_beat):
            t=(i+.35)/(conf.frames_per_beat+.1)
            details=pose(beat,t,charges,wave)
            scene.frame_set(count+1)
            filename=root/("frame-%04d.png"%count)
            scene.render.filepath=str(filename)
            bpy.ops.render.render(write_still=True)
            record={"file":filename.name,
                    "sha256":hashlib.sha256(filename.read_bytes()).hexdigest(),
                    **details}
            manifest["frameEvidence"].append(record)
            count+=1
    manifest["frameCount"]=count
    manifest["meshObjects"]=sum(o.type=="MESH" for o in bpy.data.objects)
    manifest["actual3dCloudMeshes"]=len([
        o for o in bpy.data.objects
        if o.type=="MESH" and o.name.startswith("Fused cumulonimbus")])
    (root/"manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf8")
    print("P54_ANIMATED_CYCLES_PROOF", json.dumps({
        "frames":count,"materialMeshes":manifest["meshObjects"],
        "beats":list(BEATS),"cloudVertices":cloud_vertices},sort_keys=True))


if __name__=="__main__":
    main()
