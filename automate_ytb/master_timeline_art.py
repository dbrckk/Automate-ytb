"""Original, opt-in, mobile-safe 2.5D actor marks from persistent world state.

The same actor ID and authored trajectory survives editorial scene boundaries;
the camera projection, short trail, glow and body are sampled from *absolute*
frame numbers. This does not invent a scientific value or replace world art.
"""
from __future__ import annotations

import hashlib
import math

from PIL import Image, ImageDraw

from .master_timeline_adapter import AuthoredScienceTimeline

VERSION = "persistent-actor-2p5d-visual-bridge-v1"
# The scientific stage is deliberately separate from the title and caption UI.
STAGE = (85, 610, 995, 1450)


def _coordinates(props: dict, camera: dict, width: int, height: int) -> tuple[float, float]:
    zoom = camera["zoom"]
    cam_x = camera["x"]
    cam_y = camera.get("y", 0.0)
    return (width * (.5 + (props["x"] - .5 - cam_x) * zoom),
            height * (.5 + (props["y"] - .5 - cam_y) * zoom))


def _actor_color(actor_id: str) -> tuple[int, int, int]:
    # Deterministic and visually cohesive, without random per-frame flicker.
    colors = ((105, 226, 221), (250, 189, 112), (170, 197, 255))
    digest = hashlib.sha256(actor_id.encode("ascii")).digest()
    return colors[digest[0] % len(colors)]


def paint_persistent_actors(picture: Image.Image, authored: AuthoredScienceTimeline,
                            absolute_frame: int) -> dict:
    """Composite actor(s) in the world region; never cover subtitles or headers."""
    if not isinstance(picture, Image.Image) or picture.mode != "RGBA" or picture.size != (1080, 1920):
        raise ValueError("Expected original 1080x1920 RGBA scientific canvas")
    if not isinstance(authored, AuthoredScienceTimeline):
        raise ValueError("Invalid authored MasterTimeline")
    timeline = authored.timeline
    if type(absolute_frame) is not int or not 0 <= absolute_frame < timeline.total_frames:
        raise ValueError("Frame outside the authored world timeline")
    l, t, r, b = STAGE
    width, height = r-l, b-t
    overlay = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(overlay, "RGBA")
    state = timeline.state_at(absolute_frame)
    camera = state["objects"][authored.camera_id]
    positions = {}
    for actor_id in authored.visual_actor_ids:
        props = state["objects"][actor_id]
        x, y = _coordinates(props, camera, width, height)
        # Trail is a causal history of this SAME persistent actor,
        # not noise or a random particle layer.
        color = _actor_color(actor_id)
        radius = max(5., min(50., 15. * props["scale"] * camera["zoom"]))
        for lag, weight in ((9, .12), (6, .18), (3, .27)):
            earlier = timeline.state_at(max(0, absolute_frame-lag))
            xy = _coordinates(earlier["objects"][actor_id],
                              earlier["objects"][authored.camera_id],
                              width, height)
            a = round(140 * weight * props["opacity"])
            rr = max(3, radius*(1 + weight))
            draw.ellipse((xy[0]-rr, xy[1]-rr, xy[0]+rr, xy[1]+rr),
                         fill=(*color, a))
        if not (radius < x < width-radius and radius < y < height-radius):
            positions[actor_id] = {"visible": False}
            continue
        opacity = props["opacity"]
        if opacity <= .005:
            positions[actor_id] = {"visible": False}
            continue
        # Three nested, alpha-weighted circles act as emissive material,
        # while the small opaque core remains legible at 360px downscale.
        for multiple, alpha in ((2.5, 22), (1.8, 42), (1.3, 76)):
            a = round(alpha * opacity)
            rr = radius * multiple
            draw.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(*color,a))
        draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                     fill=(*color, round(207*opacity)),
                     outline=(245, 250, 244, round(245*opacity)),
                     width=3)
        small = radius*.32
        draw.ellipse((x-small, y-small, x+small, y+small),
                     fill=(243, 251, 246, round(255*opacity)))
        positions[actor_id] = {
            "visible": True,
            "x": round(x+l, 3), "y": round(y+t, 3),
            "scale": round(props["scale"], 4),
            "worldX": round(props["x"], 5), "worldY": round(props["y"], 5),
        }
    picture.alpha_composite(overlay, (l, t))
    return {"absoluteFrame": absolute_frame, "beatId": state["beatId"],
            "visibleActors": positions, "engine": VERSION}
