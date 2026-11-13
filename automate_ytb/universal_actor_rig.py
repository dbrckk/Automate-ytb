"""Reusable, authored 2.5D action rigs for original transparent subjects.

No semantic actions are guessed from narration or filenames. The storyteller
supplies deterministic keyframes for existing, rights-checked visual layers.
A subject can translate, grow/shrink and rotate in one smooth temporal track;
optional links pulse between two actors at an explicitly authored time.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

from .optical_motion25d import translate_subpixel
from .universal_contact_glints import paint_contact_glints
from .universal_deformation25d import validate_deformation, warp_sway_sprite
from .universal_joint_hierarchy import (
    resolved_actor_geometry, validate_joint_tree)

VERSION = "universal-actor-rig-local-event-contact-glints-v8"

_KEYS = frozenset(("at", "x", "y", "scale", "angle"))


def _real(value, name: str, low: float, high: float) -> float:
    if (type(value) not in (int, float) or not math.isfinite(value)
            or not low <= value <= high):
        raise ValueError(f"Actor keyframe {name} must be finite and in range")
    return float(value)


def validate_actor_rig(tracks, links, layers: list[dict]) -> tuple[list[dict], list[dict]]:
    """Fail before file IO on misspelled keys, missing layers or fake motion."""
    if tracks is None:
        tracks = []
    if links is None:
        links = []
    if type(tracks) is not list or len(tracks) > 6:
        raise ValueError("actorTracks must be a list of <=6 actors")
    if type(links) is not list or len(links) > 6:
        raise ValueError("actorLinks must be a list of <=6 relationships")
    layer_z = {l["z"] for l in layers}
    foreground = {z for z in layer_z if z > 10}
    parsed = []
    seen = set()
    for t in tracks:
        if (type(t) is not dict or not {"z", "keys"} <= set(t)
                or set(t) - {"z", "keys", "pivot", "parentZ", "attach", "deform"}
                or type(t["z"]) is not int or t["z"] not in foreground
                or t["z"] in seen):
            raise ValueError("Actors require a unique non-background approved layer z")
        seen.add(t["z"])
        keys = t["keys"]
        if type(keys) is not list or not 2 <= len(keys) <= 8:
            raise ValueError("Each actor needs 2-8 authored keyframes")
        previous = -1.0
        output = []
        for k in keys:
            if type(k) is not dict or set(k) != _KEYS:
                raise ValueError("Actor keys must have at/x/y/scale/angle")
            at = _real(k["at"], "at", 0, 1)
            if at <= previous:
                raise ValueError("Actor keyframe times must increase")
            output.append({
                "at": at,
                "x": _real(k["x"], "x", -.4, .4),
                "y": _real(k["y"], "y", -.4, .4),
                "scale": _real(k["scale"], "scale", .45, 1.75),
                "angle": _real(k["angle"], "angle", -65, 65),
            })
            previous = at
        if output[0]["at"] != 0 or output[-1]["at"] != 1:
            raise ValueError("Actor keyframes must span the full scene 0..1")
        if all(all(abs(k[p] - output[0][p]) < 1e-9
                   for p in ("x", "y", "scale", "angle")) for k in output[1:]):
            raise ValueError("Static art does not need an actor action track")
        pivot=t.get("pivot", [0.5,0.5])
        if (type(pivot) is not list or len(pivot)!=2):
            raise ValueError("Actor pivot must be two normalized coordinates")
        px=_real(pivot[0],"pivot x",0,1)
        py=_real(pivot[1],"pivot y",0,1)
        result={"z":t["z"],"keys":output,"pivot":[px,py]}
        if "parentZ" in t or "attach" in t:
            if (set(t) & {"parentZ", "attach"}) != {"parentZ","attach"}:
                raise ValueError("A joint needs a parentZ and an attach point")
            anchor=t["attach"]
            if type(anchor) is not list or len(anchor)!=2:
                raise ValueError("Joint attachment must be a normalized 2D point")
            result["parentZ"]=t["parentZ"]
            result["attach"]=[
                _real(anchor[0],"attach x",0,1),
                _real(anchor[1],"attach y",0,1)]
        if "deform" in t:
            result["deform"]=validate_deformation(t["deform"])
            if result["deform"] is None:
                raise ValueError("Deform must be a complete motion specification")
        parsed.append(result)
    validate_joint_tree(parsed)
    if links and len(seen) < 2:
        raise ValueError("An authored interaction needs two independently rigged actors")
    edges = []
    for link in links:
        if (type(link) is not dict or set(link) != {"fromZ", "toZ", "at"}
                or type(link["fromZ"]) is not int
                or type(link["toZ"]) is not int
                or link["fromZ"] == link["toZ"]
                or link["fromZ"] not in seen or link["toZ"] not in seen):
            raise ValueError("An interaction must connect two different rigged actors")
        edges.append({
            "fromZ": link["fromZ"], "toZ": link["toZ"],
            "at": _real(link["at"], "interaction at", .07, .93),
        })
    return parsed, edges


def _ease(t: float) -> float:
    t = max(0., min(1., t))
    return t*t*(3-2*t)


def _extend_edge(source: Image.Image, margin: int) -> Image.Image:
    """Repeat authored edge pixels into a bounded camera overscan area.

    A blossom may move a little beyond the original illustration viewport.
    The picture must not be truncated *before* the camera can frame it.
    The extensions are real source pixels, not invented new scene objects.
    """
    w,h=source.size
    out=Image.new("RGBA",(w+margin*2,h+margin*2))
    out.alpha_composite(source,(margin,margin))
    out.alpha_composite(source.crop((0,0,1,h)).resize(
        (margin,h),Image.Resampling.NEAREST),(0,margin))
    out.alpha_composite(source.crop((w-1,0,w,h)).resize(
        (margin,h),Image.Resampling.NEAREST),(margin+w,margin))
    out.alpha_composite(source.crop((0,0,w,1)).resize(
        (w,margin),Image.Resampling.NEAREST),(margin,0))
    out.alpha_composite(source.crop((0,h-1,w,h)).resize(
        (w,margin),Image.Resampling.NEAREST),(margin,margin+h))
    for x,y,color in (
        (0,0,source.getpixel((0,0))),
        (w+margin,0,source.getpixel((w-1,0))),
        (0,h+margin,source.getpixel((0,h-1))),
        (w+margin,h+margin,source.getpixel((w-1,h-1)))):
        out.paste(color,(x,y,x+margin,y+margin))
    return out


def fit_actor_camera(size: tuple[int,int], geometry: dict,
                     phase: float, overscan: int) -> tuple[int,int,int,int]:
    """Bounded camera crop containing authored rotated actor silhouettes.

    Operates on actual resolved parent-child actor transforms, not an average
    of object centers. Returns source-world crop coordinates (may be negative).
    Zoom can withdraw slightly if an extended wing/flower needs headroom.
    """
    if not geometry or not 0<=phase<=1 or not math.isfinite(phase):
        raise ValueError("Valid authored actor geometry is required")
    w,h=size
    if type(overscan) is not int or overscan<=0:
        raise ValueError("Invalid bounded camera overscan")
    edges=[]
    for item in geometry.values():
        cx,cy=item["centre"]
        sw,sh=item["spriteSize"]
        angle=math.radians(item["angle"])
        ax=abs(math.cos(angle))*sw/2+abs(math.sin(angle))*sh/2
        ay=abs(math.sin(angle))*sw/2+abs(math.cos(angle))*sh/2
        edges.append((cx-ax,cy-ay,cx+ax,cy+ay))
    xmin=min(p[0] for p in edges)
    ymin=min(p[1] for p in edges)
    xmax=max(p[2] for p in edges)
    ymax=max(p[3] for p in edges)
    room_x=w*.045
    room_y=h*.045
    desired=1.08+.18*phase*phase*(3-2*phase)
    possible=min(w/max(1,xmax-xmin+room_x*2),
                 h/max(1,ymax-ymin+room_y*2))
    zoom=max(.78,min(desired,possible))
    cw=min(w+2*overscan,max(16,round(w/zoom)))
    ch=min(h+2*overscan,max(16,round(h/zoom)))
    # Track the whole visible silhouette with a weak stable-centre prior.
    focus_x=.12*(w/2)+.88*(xmin+xmax)/2
    focus_y=.12*(h/2)+.88*(ymin+ymax)/2
    def place(focus,lo,hi,crop,stage,pad,room):
        world_min=-pad
        world_max=stage+pad-crop
        desired_start=max(world_min,min(world_max,round(focus-crop/2)))
        # Keep the padded silhouette fully visible whenever geometrically
        # possible without forcing a jump between adjacent narration shots.
        allowed_min=max(world_min,math.ceil(hi+room-crop))
        allowed_max=min(world_max,math.floor(lo-room))
        if allowed_min<=allowed_max:
            return max(allowed_min,min(allowed_max,desired_start))
        return desired_start
    left=place(focus_x,xmin,xmax,cw,w,overscan,room_x)
    top=place(focus_y,ymin,ymax,ch,h,overscan,room_y)
    return left,top,cw,ch


def sampled_pose(keys: list[dict], phase: float) -> dict:
    """No frame history: random access, replay and seek produce equal pixels."""
    if not math.isfinite(phase) or not 0 <= phase <= 1:
        raise ValueError("Invalid actor time")
    if phase >= keys[-1]["at"]:
        return keys[-1].copy()
    for a, b in zip(keys, keys[1:]):
        if a["at"] <= phase < b["at"]:
            f = _ease((phase-a["at"])/(b["at"]-a["at"]))
            return {
                name: (a[name]+(b[name]-a[name])*f)
                for name in ("x", "y", "scale", "angle")
            }
    raise ValueError("Incomplete actor keyframe track")


def same_authored_actor_world(a: dict, b: dict) -> bool:
    """Only identical licensed source layers and actor identities may persist.

    A new shot using a different picture is a real edit, not a presumed
    continuous physical object. No filename keyword interpretation occurs.
    """
    if not a.get("actorTracks") or not b.get("actorTracks"):
        return False
    def ids(beat):
        from .universal_vector_art import vector_sha256
        layers=tuple(sorted(
            [(layer["z"],"file:"+layer["file"])
             for layer in beat.get("visualLayers",[])] +
            [(layer["z"],"vector:"+layer["id"]+":"+vector_sha256(layer))
             for layer in beat.get("visualVectors",[])]))
        actors=tuple(sorted(track["z"] for track in beat["actorTracks"]))
        return layers,actors
    return ids(a)==ids(b)


def validate_cut_continuity(story: dict) -> int:
    """Reject jumps for repeatedly drawn original actors in adjacent shots."""
    count=0
    for before,after in zip(story["beats"],story["beats"][1:]):
        if not same_authored_actor_world(before,after):
            continue
        old={t["z"]:t for t in before["actorTracks"]}
        new={t["z"]:t for t in after["actorTracks"]}
        for z,track in old.items():
            if track.get("pivot",[0.5,0.5]) != new[z].get("pivot",[0.5,0.5]):
                raise ValueError("A repeated original joint cannot change its pivot")
            if (track.get("parentZ")!=new[z].get("parentZ") or
                    track.get("attach")!=new[z].get("attach")):
                raise ValueError("A repeated original child cannot change its attachment")
            if track.get("deform")!=new[z].get("deform"):
                raise ValueError("A repeated original flexible actor cannot change its deformation")
            last=track["keys"][-1]
            first=new[z]["keys"][0]
            if any(abs(last[k]-first[k]) > 1e-8
                   for k in ("x","y","scale","angle")):
                raise ValueError(
                    "A repeated original actor cannot jump between adjacent scenes")
        count+=1
    return count


class RiggedArtScene:
    """Composite original RGBA layers and sampled authored object trajectories."""

    def __init__(self, scene, layers, tracks, links):
        self.size = scene.size
        self.layers = tuple(sorted(layers, key=lambda item: item.z))
        self.tracks = {t["z"]: t["keys"] for t in tracks}
        self.pivots = {t["z"]: t.get("pivot",[0.5,0.5]) for t in tracks}
        self.parents = {
            t["z"]:(t["parentZ"],t["attach"]) for t in tracks
            if "parentZ" in t}
        self.deformations={
            t["z"]:t["deform"] for t in tracks if t.get("deform")}
        self.links = tuple(links)
        self.camera_window = None
        # Reserve camera room for animated petals, wings and long tools.
        # Pre-extend only static backdrops once, never once per video frame.
        self.overscan=round(max(self.size)*.30)
        self.extended_layers={
            layer.z:_extend_edge(layer.image,self.overscan)
            for layer in self.layers if layer.z not in self.tracks}
        self.crops = {}
        for layer in self.layers:
            if layer.z not in self.tracks:
                continue
            alpha = layer.image.getchannel("A")
            counts = alpha.histogram()
            occupied = sum(counts[32:]) / (self.size[0]*self.size[1])
            bbox = alpha.getbbox()
            if bbox is None or not .005 <= occupied <= .75:
                raise ValueError(
                    "Moving owned subjects must have meaningful transparency; "
                    "put opaque backdrops on layers z<=10")
            self.crops[layer.z] = (layer.image.crop(bbox),
                                   ((bbox[0]+bbox[2])/2,
                                    (bbox[1]+bbox[3])/2))

    def set_camera_window(self, first: int, last: int) -> None:
        if (type(first) is not int or type(last) is not int
                or first < 0 or last <= first):
            raise ValueError("Invalid continuous camera time window")
        self.camera_window=(first,last)

    def render(self, frame: int, first: int, last: int) -> Image.Image:
        if (type(frame) is not int or type(first) is not int
                or type(last) is not int or not first <= frame < last):
            raise ValueError("Invalid authored actor frame")
        phase = (frame-first)/max(1,last-first)
        camera_first,camera_last=(
            self.camera_window if self.camera_window is not None
            else (first,last))
        if not camera_first <= frame < camera_last:
            raise ValueError("Actor frame is outside its continuous camera")
        camera_phase=(frame-camera_first)/max(1,camera_last-camera_first)
        camera_smooth=_ease(camera_phase)
        cam_x = 28*(camera_smooth*2-1)
        cam_y = 12*math.sin(math.pi*camera_phase)
        w_stage,h_stage=self.size
        margin=self.overscan
        result = Image.new("RGBA",(w_stage+2*margin,h_stage+2*margin))
        centres = {}
        geometries = {}
        for layer in self.layers:
            dx=cam_x*layer.parallax_x
            dy=cam_y*layer.parallax_y
            if layer.z not in self.tracks:
                result.alpha_composite(translate_subpixel(
                    self.extended_layers[layer.z],dx,dy))
                continue
            pose=sampled_pose(self.tracks[layer.z],phase)
            sprite,centre=self.crops[layer.z]
            parent_info=self.parents.get(layer.z)
            parent_geometry=(
                geometries[parent_info[0]] if parent_info else None)
            geometry=resolved_actor_geometry(
                layer=(centre[0],centre[1],layer.parallax_x,layer.parallax_y),
                pose=pose,pivot=self.pivots[layer.z],
                stage_size=self.size,sprite_size=sprite.size,
                camera_x=cam_x,camera_y=cam_y,
                parent=parent_geometry,
                attach=parent_info[1] if parent_info else None)
            geometries[layer.z]=geometry
            centres[layer.z]=geometry["centre"]
            w=max(1,round(geometry["spriteSize"][0]))
            h=max(1,round(geometry["spriteSize"][1]))
            transformed=sprite.resize((w,h),Image.Resampling.BICUBIC)
            px,py=self.pivots[layer.z]
            pivot_x,pivot_y=px*w,py*h
            if layer.z in self.deformations:
                transformed,(pivot_x,pivot_y)=warp_sway_sprite(
                    transformed,pivot=self.pivots[layer.z],
                    deform=self.deformations[layer.z],
                    phase=camera_phase)
                w,h=transformed.size
            joint_x,joint_y=geometry["joint"]
            angle=geometry["angle"]
            if abs(angle)>1e-5:
                side=math.ceil(math.hypot(w,h)*2)+4
                workspace=Image.new("RGBA",(side,side))
                origin=(side/2,side/2)
                workspace.alpha_composite(
                    transformed,(round(origin[0]-pivot_x),
                                 round(origin[1]-pivot_y)))
                transformed=workspace.rotate(
                    angle,resample=Image.Resampling.BICUBIC,expand=False)
                result.alpha_composite(
                    transformed,(round(joint_x+margin-side/2),
                                 round(joint_y+margin-side/2)))
            else:
                result.alpha_composite(
                    transformed,(round(joint_x+margin-pivot_x),
                                 round(joint_y+margin-pivot_y)))
        if self.links:
            for edge in self.links:
                pulse=max(0.,1-abs(phase-edge["at"])/.09)
                if pulse<=0:
                    continue
                a,b=centres[edge["fromZ"]],centres[edge["toZ"]]
                paint_contact_glints(
                    result,(a[0]+margin,a[1]+margin),
                    (b[0]+margin,b[1]+margin),pulse,
                    stage_width=w_stage)
        left,top,crop_w,crop_h=fit_actor_camera(
            self.size,geometries,camera_phase,margin)
        crop=result.crop((margin+left,margin+top,
                          margin+left+crop_w,margin+top+crop_h))
        return crop.resize(self.size,Image.Resampling.BICUBIC)
