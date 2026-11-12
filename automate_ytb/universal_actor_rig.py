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

VERSION = "universal-authored-actor-rig-continuous-world-v3"

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
        if (type(t) is not dict or set(t) != {"z", "keys"}
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
        parsed.append({"z": t["z"], "keys": output})
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
        layers=tuple(sorted((layer["z"],layer["file"])
                            for layer in beat["visualLayers"]))
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
        self.links = tuple(links)
        self.camera_window = None
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
        result = Image.new("RGBA", self.size)
        centres = {}
        for layer in self.layers:
            dx = cam_x*layer.parallax_x
            dy = cam_y*layer.parallax_y
            if layer.z not in self.tracks:
                # Keep all untouched authored art/parallax exactly as before.
                result.alpha_composite(translate_subpixel(layer.image, dx, dy))
                continue
            pose = sampled_pose(self.tracks[layer.z], phase)
            sprite, centre = self.crops[layer.z]
            cx = centre[0]+dx+pose["x"]*self.size[0]
            cy = centre[1]+dy+pose["y"]*self.size[1]
            centres[layer.z] = (cx,cy)
            w = max(1,round(sprite.width*pose["scale"]))
            h = max(1,round(sprite.height*pose["scale"]))
            transformed = sprite.resize((w,h),Image.Resampling.BICUBIC)
            if abs(pose["angle"]) > 1e-5:
                transformed = transformed.rotate(
                    pose["angle"],resample=Image.Resampling.BICUBIC,expand=True)
            result.alpha_composite(
                transformed,(round(cx-transformed.width/2),
                             round(cy-transformed.height/2)))
        if self.links:
            d = ImageDraw.Draw(result,"RGBA")
            for edge in self.links:
                pulse = max(0., 1-abs(phase-edge["at"])/.09)
                if pulse <= 0:
                    continue
                a,b = centres[edge["fromZ"]],centres[edge["toZ"]]
                w = max(1,round(self.size[0]*.009))
                d.line((round(a[0]),round(a[1]),round(b[0]),round(b[1])),
                       fill=(254,213,142,round(pulse*215)),width=w)
                for x,y in (a,b):
                    radius=round(self.size[0]*(.018+.030*pulse))
                    d.ellipse((round(x-radius),round(y-radius),
                               round(x+radius),round(y+radius)),
                              outline=(255,235,173,round(pulse*205)),
                              width=max(1,w//2))
        # A deterministic follow-camera uses the actual on-screen actor
        # centres, not a static slide-sized crop or a fictitious subject.
        # The crop stays strictly inside the authored source world.
        zoom=1.08+.18*camera_smooth
        w,h=self.size
        crop_w=max(16,round(w/zoom))
        crop_h=max(16,round(h/zoom))
        focus_x=sum(x for x,_ in centres.values())/len(centres)
        focus_y=sum(y for _,y in centres.values())/len(centres)
        focus_x=.42*(w/2)+.58*focus_x
        focus_y=.42*(h/2)+.58*focus_y
        left=max(0,min(w-crop_w,round(focus_x-crop_w/2)))
        top=max(0,min(h-crop_h,round(focus_y-crop_h/2)))
        crop=result.crop((left,top,left+crop_w,top+crop_h))
        return crop.resize(self.size,Image.Resampling.BICUBIC)
