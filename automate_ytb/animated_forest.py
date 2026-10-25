"""Original animated fox, rabbit and cat for local cartoon video previews.

Character art and frames are drawn procedurally with Pillow; no asset
downloads, model API calls, copyrighted images or fake 3D representation.
Characters have distinct silhouettes, independent tail motion, body bounce
and brief blinks. The outdoor world, weather, and safe camera profiles are
shared with the original owl animator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile
import unicodedata

from PIL import Image, ImageDraw

from .animated_owl import _bg, _weather_overlay
from .cinematic_camera import framing_filter
from .director import validate_direction

FOREST_RIG_VERSION = "forest-animals-v1"


def character_kind(character: str) -> str | None:
    """Detect only explicitly named supported animal characters.

    Generic humanoid, celebrity or unspecified subjects remain static local
    cards instead of misleadingly showing a random animal.
    """
    if not isinstance(character, str):
        raise ValueError("Character description must be text")
    folded = unicodedata.normalize("NFKD", character.casefold())
    words = "".join(ch for ch in folded if not unicodedata.combining(ch))
    if re.search(r"\b(renard\w*|fox|foxes)\b", words):
        return "fox"
    if re.search(r"\b(lapin\w*|lievre\w*|rabbit\w*|bunn\w*|hare|hares)\b", words):
        return "rabbit"
    if re.search(r"\b(chat|chats|chatte\w*|chaton\w*|cat|cats|kitten\w*)\b", words):
        return "cat"
    return None


COLORS = {
    "fox": {"fur": (226, 116, 58, 255), "dark": (149, 64, 65, 255),
            "belly": (255, 234, 198, 255), "ear": (249, 162, 140, 255)},
    "rabbit": {"fur": (219, 205, 224, 255), "dark": (118, 111, 155, 255),
               "belly": (252, 244, 236, 255), "ear": (248, 168, 188, 255)},
    "cat": {"fur": (90, 144, 171, 255), "dark": (43, 84, 112, 255),
            "belly": (190, 224, 227, 255), "ear": (242, 151, 175, 255)},
}
INK = (32, 38, 66, 255)
SCARF = (243, 187, 74, 255)
HIGHLIGHT = (255, 255, 255, 255)


def _sprite_body(path: Path, *, kind: str, blink: bool, emotion: str):
    palette = COLORS[kind]
    fur, dark, belly, ear = (
        palette[name] for name in ("fur", "dark", "belly", "ear"))
    image = Image.new("RGBA", (350, 440), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    # Feet reach the visual ground. Rounded limbs give the characters an
    # unmistakably non-owl mammal silhouette.
    for x in (119, 237):
        d.rounded_rectangle((x - 30, 348, x + 33, 419), radius=23,
                            fill=dark, outline=INK, width=4)
        d.ellipse((x - 36, 395, x + 43, 430), fill=fur,
                  outline=INK, width=4)
    d.ellipse((61, 160, 289, 385), fill=fur, outline=INK, width=6)
    d.ellipse((105, 229, 243, 364), fill=belly)
    for x, tilt in ((64, -1), (267, 1)):
        d.ellipse((x - 25, 258, x + 27, 344),
                  fill=fur, outline=INK, width=5)
        d.ellipse((x - 12, 314, x + 14, 342), fill=dark)
    if kind == "rabbit":
        for x, bend in ((105, -24), (225, 26)):
            d.ellipse((x - 31 + bend, 6, x + 24 + bend, 225),
                      fill=fur, outline=INK, width=6)
            d.ellipse((x - 16 + bend, 24, x + 11 + bend, 188), fill=ear)
    else:
        for x in (77, 273):
            if kind == "fox":
                points = [(x - 62, 177), (x - 8, 8), (x + 61, 149)]
            else:
                points = [(x - 51, 174), (x - 5, 44), (x + 53, 159)]
            d.polygon(points, fill=dark)
            d.polygon([(x - 37, 151), (x - 8, 58), (x + 35, 144)],
                      fill=ear)
    d.ellipse((45, 112, 306, 330), fill=fur, outline=INK, width=6)
    if kind == "fox":
        d.polygon([(66, 231), (173, 337), (286, 231),
                   (267, 295), (187, 336), (83, 289)], fill=belly)
    else:
        d.ellipse((95, 239, 259, 324), fill=belly)
    for eye_x in (117, 235):
        if blink:
            d.arc((eye_x - 31, 206, eye_x + 31, 235),
                  start=0, end=180, fill=INK, width=7)
        else:
            d.ellipse((eye_x - 24, 184, eye_x + 24, 240), fill=INK)
            d.ellipse((eye_x - 15, 191, eye_x - 4, 205), fill=HIGHLIGHT)
        if emotion == "worried":
            d.line((eye_x - 28, 182, eye_x + 27, 175), fill=dark, width=5)
    d.ellipse((165, 245, 192, 265), fill=dark)
    if kind == "cat":
        for y in (253, 271):
            d.line((75, y, 152, y + 8), fill=INK, width=3)
            d.line((202, y + 8, 275, y), fill=INK, width=3)
    if emotion == "surprised":
        d.ellipse((170, 270, 188, 292), fill=INK)
    elif emotion == "worried":
        d.arc((149, 277, 207, 309), start=180, end=350,
              fill=dark, width=5)
    else:
        d.arc((150, 261, 207, 298), start=0, end=180, fill=dark, width=5)
    # Signature golden scarf across the torso ensures character consistency.
    d.arc((65, 293, 291, 353), start=3, end=178, fill=SCARF, width=14)
    d.polygon([(245, 323), (283, 379), (260, 393), (211, 330)],
              fill=SCARF)
    image.save(path, "PNG")


def _sprite_tail(path: Path, *, kind: str):
    image = Image.new("RGBA", (230, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    fur, dark, belly = (COLORS[kind][name]
                        for name in ("fur", "dark", "belly"))
    if kind == "fox":
        d.polygon([(200, 205), (139, 169), (78, 112), (25, 12),
                   (17, 132), (57, 203), (160, 228)],
                  fill=fur)
        d.polygon([(25, 12), (17, 132), (39, 166), (63, 119)],
                  fill=belly)
        d.line([(200, 205), (139, 169), (78, 112), (25, 12)],
               fill=dark, width=5, joint="curve")
    elif kind == "rabbit":
        d.ellipse((40, 74, 182, 216), fill=fur, outline=dark, width=8)
        d.ellipse((66, 99, 148, 182), fill=belly)
    else:
        d.arc((26, 4, 222, 242), start=35, end=258,
              fill=dark, width=53)
        d.arc((28, 8, 214, 236), start=35, end=258,
              fill=fur, width=33)
        d.ellipse((185, 188, 229, 230), fill=dark)
    image.save(path, "PNG")


def render_layers(folder: Path, *, kind: str, topic: str,
                  narration: str, scene_index: int, scene_count: int,
                  style: str = "cartoon",
                  direction: dict | None = None) -> dict[str, Path]:
    if kind not in COLORS or style != "cartoon":
        raise ValueError("Only original cartoon fox/rabbit/cat are animated")
    if direction is not None:
        direction = validate_direction(direction)
    folder.mkdir(parents=True, exist_ok=True)
    outputs = {name: folder / (name + ".png")
               for name in ("background", "tail", "body", "blink", "effects")}
    _bg(outputs["background"], topic=topic, narration=narration,
        scene_index=scene_index, scene_count=scene_count,
        style=style, direction=direction)
    _sprite_tail(outputs["tail"], kind=kind)
    emotion = direction["emotion"] if direction else "neutral"
    _sprite_body(outputs["body"], kind=kind, blink=False, emotion=emotion)
    _sprite_body(outputs["blink"], kind=kind, blink=True, emotion=emotion)
    return outputs


def render_character_poster(*, kind: str, topic: str, narration: str,
                            scene_index: int, scene_count: int,
                            style: str, destination: Path,
                            direction: dict | None = None):
    """Return a real static pose using exactly the approved motion layers."""
    with tempfile.TemporaryDirectory(prefix="automate-ytb-forest-poster-") as folder:
        layers = render_layers(Path(folder), kind=kind, topic=topic,
                               narration=narration, scene_index=scene_index,
                               scene_count=scene_count, style=style,
                               direction=direction)
        with Image.open(layers["background"]) as background:
            combined = background.convert("RGBA")
        for name, pos in (("tail", (115, 360)), ("body", (180, 184))):
            with Image.open(layers[name]) as sprite:
                combined.alpha_composite(sprite.convert("RGBA"), pos)
        destination.parent.mkdir(parents=True, exist_ok=True)
        combined.convert("RGB").save(destination, "PNG", optimize=True)


def render_motion_clip(*, kind: str, topic: str, narration: str,
                       scene_index: int, scene_count: int, style: str,
                       duration: float, width: int, height: int, fps: int,
                       destination: Path, direction: dict | None = None):
    if not 0 < duration <= 3600 or fps not in (24, 30):
        raise ValueError("Invalid forest animation duration or FPS")
    if (width, height) not in ((1280, 720), (1920, 1080)):
        raise ValueError("Invalid forest animation resolution")
    if direction is not None:
        direction = validate_direction(direction)
    from .production import _run
    with tempfile.TemporaryDirectory(prefix="automate-ytb-forest-") as folder:
        layers = render_layers(Path(folder), kind=kind, topic=topic,
                               narration=narration, scene_index=scene_index,
                               scene_count=scene_count, style=style,
                               direction=direction)
        action = direction["action"] if direction else "idle"
        bounce = {"fly": 23, "walk": 15, "talk": 5, "surprise": 19,
                  "rest": 2, "idle": 7}[action]
        speed = {"fly": 6.5, "walk": 5.7, "talk": 2.8,
                 "surprise": 3.4, "rest": 1.2, "idle": 2.3}[action]
        fps_graph = (
            "[0:v][1:v]overlay=x='113+8*sin(t*2.4)':"
            "y='357+23*sin(t*3.1)':eval=frame:format=auto[a];"
            "[a][2:v]overlay=x='180+7*sin(t*1.1)':"
            f"y='184+{bounce}*sin(t*{speed})':eval=frame:format=auto[b];"
            "[b][3:v]overlay=x='180+7*sin(t*1.1)':"
            f"y='184+{bounce}*sin(t*{speed})':"
            "enable='lt(mod(t+0.15,4.1),0.14)':eval=frame:format=auto[c]"
        )
        final = "c"
        names = ["background", "tail", "body", "blink"]
        if direction and direction["weather"] in {"rain", "storm", "wind", "cloudy"}:
            _weather_overlay(
                layers["effects"],
                seed=f"{kind}|{topic}|{narration}|{scene_index}",
                weather=direction["weather"])
            speed_fx = 240 if direction["weather"] in {"rain", "storm"} else 35
            fps_graph += (
                f";[c][4:v]overlay=x=0:"
                f"y='-720+mod(t*{speed_fx},720)':eval=frame:format=auto[d]")
            final = "d"
            names.append("effects")
        shot = direction["shot"] if direction else "wide"
        camera = framing_filter(
            shot, width=width, height=height, fps=fps,
            scene_index=scene_index)
        fps_graph += f";[{final}]{camera}[out]"
        args = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel",
                "error", "-y"]
        for name in names:
            args += ["-loop", "1", "-framerate", str(fps),
                     "-i", str(layers[name])]
        args += ["-filter_complex", fps_graph, "-map", "[out]",
                 "-frames:v", str(max(1, round(duration * fps))),
                 "-r", str(fps), "-c:v", "libx264", "-preset",
                 "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                 "-an", str(destination)]
        _run(args)


def art_brief_sha256(*, kind: str, topic: str, narration: str,
                     character: str, style: str, scene_id: str,
                     direction: dict | None = None) -> str:
    if kind not in COLORS:
        raise ValueError("Unknown original forest character")
    normalized = validate_direction(direction) if direction is not None else None
    source = json.dumps(
        [FOREST_RIG_VERSION, kind, topic, narration, character, style,
         scene_id, normalized], ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(source).hexdigest()
