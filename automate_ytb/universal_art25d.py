"""Original, license-declared independent 2.5D illustration layers for any subject.

Supports user-authored PNG/WebP assets. No network fetches, scraping, automatic
rights claims, paid image provider, or topic-word-specific drawing routines.
Reuses the repository's material-aware Scene25D with the correct stage size.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

from PIL import Image, ImageOps

from .scene25d import Layer25D, Scene25D
from .surface25d import MATERIALS, relight_surface

VERSION = "universal-mixed-owned-and-inline-bezier-art-v3"


def validate_layers(raw) -> list[dict]:
    if raw is None:
        return []
    if type(raw) is not list or len(raw) > 6:
        raise ValueError("visualLayers must contain at most six original assets")
    result = []
    depth = set()
    for entry in raw:
        if type(entry) is not dict or set(entry) != {
                "file", "z", "parallaxX", "parallaxY", "material",
                "rights", "rightsConfirmed"}:
            raise ValueError("Invalid original visual layer schema")
        name = entry["file"]
        if (type(name) is not str or not 1 <= len(name) <= 180
                or Path(name).is_absolute() or ".." in Path(name).parts
                or Path(name).suffix.lower() not in (".png", ".webp")
                or ":" in name or "\\" in name or name.startswith("/")):
            raise ValueError("Unsafe original visual asset path")
        z = entry["z"]
        if type(z) is not int or not 0 <= z <= 100 or z in depth:
            raise ValueError("Invalid or duplicated layer depth")
        depth.add(z)
        material = entry["material"]
        if material not in MATERIALS:
            raise ValueError("Unsupported original 2.5D surface")
        xs = []
        for axis in ("parallaxX", "parallaxY"):
            raw_axis = entry[axis]
            if (type(raw_axis) not in (int, float) or
                    not math.isfinite(raw_axis) or not -2 <= raw_axis <= 2):
                raise ValueError("Invalid independent parallax")
            xs.append(float(raw_axis))
        rights = entry["rights"]
        if (type(rights) is not str or not 12 <= len(rights.strip()) <= 500
                or entry["rightsConfirmed"] is not True):
            raise ValueError("Explicit approved asset rights are required")
        result.append({"file": name, "z": z, "parallaxX": xs[0],
                       "parallaxY": xs[1], "material": material,
                       "rights": rights.strip(), "rightsConfirmed": True})
    return result


def _image(path: Path, size: tuple[int,int], *, background: bool) -> Image.Image:
    if not path.is_file() or path.stat().st_size > 20*1024*1024:
        raise ValueError("Missing or oversized approved artwork")
    try:
        with Image.open(path) as source:
            if (source.format not in ("PNG", "WEBP") or
                    source.width < 16 or source.height < 16 or
                    source.width*source.height > 16_000_000):
                raise ValueError("Unsupported bounded owned illustration")
            source.load()
            image = source.convert("RGBA")
    except (OSError, OverflowError) as exc:
        raise ValueError("Unreadable owned visual artwork") from exc
    if background:
        return ImageOps.fit(image,size,method=Image.Resampling.LANCZOS,
                            centering=(.5,.5))
    # Transparent hero/foreground silhouettes maintain their native aspect.
    # Never stretch an animal, person, product or symbol to the stage aspect.
    contained=ImageOps.contain(image,size,method=Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",size)
    canvas.alpha_composite(contained,((size[0]-contained.width)//2,
                                    (size[1]-contained.height)//2))
    return canvas


def load_art_scenes(story: dict, brief_path: Path, width: int, height: int):
    """Prepare expensive textures once, never once per video frame."""
    root=brief_path.resolve().parent
    pad=round(width*.045)
    # Cinematic world: broad portrait composition with real bottom detail,
    # not a 40-50% height slide floating within empty screen space.
    stage_size=(width-2*pad,round(height*.685))
    scenes={}
    manifest=[]
    vector_cache={}
    for index, beat in enumerate(story["beats"]):
        layers=beat.get("visualLayers",[])
        vectors=beat.get("visualVectors",[])
        if not layers and not vectors:
            continue
        scene=Scene25D(stage_size)
        owned_layers=[]
        for n, item in enumerate(layers):
            path=(root/item["file"]).resolve()
            if not path.is_relative_to(root) or path.is_symlink():
                raise ValueError("Visual asset must remain inside story folder")
            canvas=_image(path,stage_size,background=item["z"] <= 10)
            # Relight exactly once: native Scene25D supports animated parallax
            # while redoing full-resolution relief for 30 fps is wasteful.
            canvas=relight_surface(canvas,item["material"])
            layer=Layer25D(
                name=f"visual-{index:02d}-{n:02d}",z=item["z"],image=canvas,
                parallax_x=item["parallaxX"],parallax_y=item["parallaxY"],
                material="none")
            scene.add(layer)
            owned_layers.append(layer)
            manifest.append({
                "beat": index,"fileName":path.name,"depth":item["z"],
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "rightsStatement":item["rights"],
                "rightsManuallyConfirmedByAuthor":True,
            })
        if vectors:
            from .universal_vector25d import (
                render_vector_layer,vector_fingerprint)
            for n,item in enumerate(vectors):
                fingerprint=vector_fingerprint(item)
                if fingerprint not in vector_cache:
                    canvas=render_vector_layer(item,stage_size)
                    # Shading and 2x supersampling are shared across any
                    # subsequent beat reusing the exact same authored world.
                    vector_cache[fingerprint]=relight_surface(
                        canvas,item["material"])
                canvas=vector_cache[fingerprint]
                layer=Layer25D(
                    name=f"vector-{index:02d}-{n:02d}",
                    z=item["z"],image=canvas,
                    parallax_x=item["parallaxX"],
                    parallax_y=item["parallaxY"],material="none")
                scene.add(layer)
                owned_layers.append(layer)
                manifest.append({
                    "beat":index,"fileName":None,"depth":item["z"],
                    "sourceType":"original-inline-vector",
                    "vectorName":item["name"],
                    "shapes":len(item["shapes"]),
                    "sha256":fingerprint,
                    "rightsStatement":"Original storyboard-defined geometry; requires human review",
                    "rightsManuallyConfirmedByAuthor":False,
                })
        if beat.get("actorTracks"):
            from .universal_actor_rig import RiggedArtScene
            scenes[index]=RiggedArtScene(
                scene,owned_layers,beat["actorTracks"],beat["actorLinks"])
        else:
            scenes[index]=scene
    return scenes, manifest


def bind_actor_camera_world(story: dict, scenes: dict,
                            boundaries: list[int]) -> list[dict]:
    """Keep the camera and visual identity across contiguous shared actors.

    The author must explicitly reuse the same layer files, Z identities and
    end/start object poses. For a different source, editing still cuts freely.
    """
    from .universal_actor_rig import RiggedArtScene, same_authored_actor_world
    beats=story["beats"]
    if (type(boundaries) is not list or len(boundaries)!=len(beats)+1
            or any(type(x) is not int for x in boundaries)
            or any(a>=b for a,b in zip(boundaries,boundaries[1:]))):
        raise ValueError("Invalid shot boundaries for continuous actor world")
    groups=[]
    start=0
    for edge in range(1,len(beats)+1):
        continuation=(
            edge<len(beats)
            and same_authored_actor_world(beats[edge-1],beats[edge]))
        if continuation:
            continue
        if edge-start>=2:
            for shot in range(start,edge):
                candidate=scenes.get(shot)
                if not isinstance(candidate,RiggedArtScene):
                    raise ValueError("Continuity requires original rigged art in every shot")
                candidate.set_camera_window(boundaries[start],boundaries[edge])
            groups.append({
                "firstBeat":start,"lastBeat":edge-1,
                "cameraStartFrame":boundaries[start],
                "cameraEndFrame":boundaries[edge]})
        start=edge
    return groups


def render_art_stage(scene: Scene25D, frame: int,
                     first: int, last: int) -> Image.Image:
    if type(frame) is not int or not first <= frame < last:
        raise ValueError("Frame outside original visual sequence")
    from .universal_actor_rig import RiggedArtScene
    if isinstance(scene,RiggedArtScene):
        return scene.render(frame,first,last)
    # Smooth directed 2.5D dolly for still illustration layers.
    # Authored actor tracks use their own sampled frame clock above.
    phase=(frame-first)/max(1,last-first)
    smooth=phase*phase*(3-2*phase)
    return scene.render(camera_x=round(28*(smooth*2-1)),
                        camera_y=round(12*math.sin(math.pi*phase)))
