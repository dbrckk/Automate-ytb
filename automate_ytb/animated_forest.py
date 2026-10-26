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
from .scenic_world import WORLD_VERSION
from .voice_activity import mouth_gate_expression
from .action_timeline import choreograph
from .material_shading import shade_sprite
from .animal_microtexture import paint_microtexture
from .character_finishing import finish_forest_face
from .choreography import body_position, secondary_position, mouth_expression, blink_enable, leg_position
from .director import validate_direction
from .atmospheric_light import draw_lighting, overlay_lighting
from .ground_contact import draw_contact_shadow, shadow_stage
from .joint_motion import joint_angle
from .depth_layers import draw_foreground, overlay_foreground
from .scene_props import create_layers as create_prop_layers, cue_for_scene, gaze_target, append_overlays

FOREST_RIG_VERSION = "forest-animals-v22-microtexture"


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


def _draw_ear(d: ImageDraw.ImageDraw, *, kind: str, side: str) -> None:
    """The original ear geometry, preserved across still and moving poses."""
    if kind not in COLORS or side not in ("left", "right"):
        raise ValueError("Unsupported original animal ear")
    palette = COLORS[kind]
    fur, dark, ear = (palette[name] for name in ("fur", "dark", "ear"))
    if kind == "rabbit":
        x, bend = (105, -24) if side == "left" else (225, 26)
        d.ellipse((x - 31 + bend, 6, x + 24 + bend, 225),
                  fill=fur, outline=INK, width=6)
        d.ellipse((x - 16 + bend, 24, x + 11 + bend, 188), fill=ear)
    else:
        x = 77 if side == "left" else 273
        if kind == "fox":
            points = [(x - 62, 177), (x - 8, 8), (x + 61, 149)]
        else:
            points = [(x - 51, 174), (x - 5, 44), (x + 53, 159)]
        d.polygon(points, fill=dark)
        d.polygon([(x - 37, 151), (x - 8, 58), (x + 35, 144)],
                  fill=ear)


def _sprite_ear(path: Path, *, kind: str, side: str) -> None:
    """Small, transparent independently rotating ear (150x240)."""
    image = Image.new("RGBA", (350, 440), (0, 0, 0, 0))
    _draw_ear(ImageDraw.Draw(image), kind=kind, side=side)
    origin = 0 if side == "left" else 200
    cropped = image.crop((origin, 0, origin + 150, 240))
    shade_sprite(cropped, kind=kind, part="ear")
    paint_microtexture(cropped, kind=kind, part="ear")
    cropped.save(path, "PNG")


def _sprite_body(path: Path, *, kind: str, blink: bool,
                 emotion: str, gaze: str = "forward",
                 include_ears: bool = True):
    palette = COLORS[kind]
    fur, dark, belly, ear = (
        palette[name] for name in ("fur", "dark", "belly", "ear"))
    image = Image.new("RGBA", (350, 440), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    # The legs are now independent articulated sprites. Keeping them out of
    # the torso image allows each foot to lift and stride on its own.
    d.ellipse((61, 160, 289, 385), fill=fur, outline=INK, width=6)
    d.ellipse((105, 229, 243, 364), fill=belly)
    for x, tilt in ((64, -1), (267, 1)):
        d.ellipse((x - 25, 258, x + 27, 344),
                  fill=fur, outline=INK, width=5)
        d.ellipse((x - 12, 314, x + 14, 342), fill=dark)
    if include_ears:
        for side in ("left", "right"):
            _draw_ear(d, kind=kind, side=side)
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
            if gaze not in ("forward", "right", "down-right"):
                raise ValueError("Unsupported original forest eye pose")
            shift_x, shift_y = {
                "forward": (0, 0), "right": (12, 1),
                "down-right": (8, 8)}[gaze]
            focus_x = eye_x + shift_x
            d.ellipse((focus_x - 24, 184 + shift_y,
                       focus_x + 24, 240 + shift_y), fill=INK)
            d.ellipse((focus_x - 15, 191 + shift_y,
                       focus_x - 4, 205 + shift_y), fill=HIGHLIGHT)
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
    shade_sprite(image, kind=kind, part="body")
    paint_microtexture(image, kind=kind, part="body")
    finish_forest_face(image, kind=kind)
    image.save(path, "PNG")


def _sprite_leg(path: Path, *, kind: str, side: str):
    """A distinct lower limb that can stride without moving the whole torso."""
    if kind not in COLORS or side not in ("left", "right"):
        raise ValueError("Unsupported animal leg")
    image = Image.new("RGBA", (100, 125), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    fur = COLORS[kind]["fur"]
    dark = COLORS[kind]["dark"]
    d.rounded_rectangle((20, 6, 79, 98), radius=25,
                        fill=dark, outline=INK, width=4)
    d.rounded_rectangle((27, 13, 72, 94), radius=22, fill=fur)
    # Clear separate paw/foot silhouette and toes; facing direction is
    # slightly asymmetric to keep right and left legs visually distinct.
    d.ellipse((8, 80, 95, 119), fill=fur, outline=INK, width=4)
    for offset in (33, 55, 73):
        toe = offset + (3 if side == "right" else -3)
        d.line((toe, 107, toe - 3, 116), fill=dark, width=3)
    d.arc((15, 83, 89, 117), 186, 351, fill=(249, 220, 181, 255), width=2)
    shade_sprite(image, kind=kind, part="leg")
    image.save(path, "PNG")


def _sprite_mouth(path: Path, *, kind: str):
    """A small mouth-only pose that can switch without resetting the blink."""
    if kind not in COLORS:
        raise ValueError("Unknown animal mouth")
    image = Image.new("RGBA", (350, 440), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    # Restore the fur beneath the still-pose mouth before drawing the
    # open, tongue-highlighted vowel shape.
    d.ellipse((149, 258, 210, 302), fill=COLORS[kind]["belly"])
    d.ellipse((165, 268, 194, 300), fill=INK)
    d.arc((170, 282, 191, 301), 0, 180, fill=(238, 139, 161, 255), width=6)
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
    shade_sprite(image, kind=kind, part="tail")
    paint_microtexture(image, kind=kind, part="tail")
    image.save(path, "PNG")


def render_layers(folder: Path, *, kind: str, topic: str,
                  narration: str, scene_index: int, scene_count: int,
                  style: str = "cartoon",
                  direction: dict | None = None,
                  held_prop: str | None = None,
                  landscape: str | None = None) -> dict[str, Path]:
    if kind not in COLORS or style != "cartoon":
        raise ValueError("Only original cartoon fox/rabbit/cat are animated")
    if direction is not None:
        direction = validate_direction(direction)
    folder.mkdir(parents=True, exist_ok=True)
    outputs = {name: folder / (name + ".png")
               for name in ("background", "tail", "neutral", "body", "blink", "mouth", "left_leg", "right_leg", "effects", "foreground", "lighting", "shadow", "left_ear", "right_ear")}
    _bg(outputs["background"], topic=topic, narration=narration,
        scene_index=scene_index, scene_count=scene_count,
        style=style, direction=direction,landscape=landscape)
    draw_foreground(outputs["foreground"], landscape=landscape or "forest",
                    seed=f"{topic}|{narration}|{scene_index}",
                    night=bool(direction and direction["weather"] == "night"))
    draw_lighting(outputs["lighting"],
                  weather=direction["weather"] if direction else "day",
                  landscape=landscape or "forest",
                  seed=f"{topic}|{narration}|{scene_index}")
    draw_contact_shadow(outputs["shadow"], actor=kind,
                        weather=direction["weather"] if direction else "day",
                        action=direction["action"] if direction else "idle")
    _sprite_tail(outputs["tail"], kind=kind)
    _sprite_ear(outputs["left_ear"], kind=kind, side="left")
    _sprite_ear(outputs["right_ear"], kind=kind, side="right")
    emotion = direction["emotion"] if direction else "neutral"
    gaze = gaze_target(narration, held_prop=held_prop)
    _sprite_body(outputs["neutral"], kind=kind, blink=False,
                 emotion=emotion, gaze="forward", include_ears=False)
    _sprite_body(outputs["body"], kind=kind, blink=False,
                 emotion=emotion, gaze=gaze, include_ears=False)
    _sprite_body(outputs["blink"], kind=kind, blink=True,
                 emotion=emotion, gaze=gaze, include_ears=False)
    _sprite_mouth(outputs["mouth"], kind=kind)
    _sprite_leg(outputs["left_leg"], kind=kind, side="left")
    _sprite_leg(outputs["right_leg"], kind=kind, side="right")
    cue = create_prop_layers(folder, narration=narration, actor=kind,
                              held_prop=held_prop)
    if cue:
        outputs["prop"] = folder / "prop.png"
        if cue["action"] == "pickup":
            outputs["reach"] = folder / "reach.png"
    return outputs


def render_character_poster(*, kind: str, topic: str, narration: str,
                            scene_index: int, scene_count: int,
                            style: str, destination: Path,
                            direction: dict | None = None,
                            held_prop: str | None = None,
                            landscape: str | None = None):
    """Return a real static pose using exactly the approved motion layers."""
    with tempfile.TemporaryDirectory(prefix="automate-ytb-forest-poster-") as folder:
        layers = render_layers(Path(folder), kind=kind, topic=topic,
                               narration=narration, scene_index=scene_index,
                               scene_count=scene_count, style=style,
                               direction=direction, held_prop=held_prop,
                               landscape=landscape)
        with Image.open(layers["background"]) as background:
            combined = background.convert("RGBA")
        with Image.open(layers["shadow"]) as shade:
            combined.alpha_composite(shade.convert("RGBA"), (225, 608))
        for name, pos in (("left_ear", (180, 184)),
                          ("right_ear", (380, 184)),
                          ("tail", (115, 360)), ("body", (180, 184)),
                          ("left_leg", (248, 519)),
                          ("right_leg", (366, 519))):
            with Image.open(layers[name]) as sprite:
                combined.alpha_composite(sprite.convert("RGBA"), pos)
        cue = cue_for_scene(narration, held_prop=held_prop)
        if cue:
            location = (481, 437) if cue["action"] == "carry" else (652, 474)
            with Image.open(layers["prop"]) as prop:
                combined.alpha_composite(prop.convert("RGBA"), location)
        with Image.open(layers["foreground"]) as front:
            combined.alpha_composite(front.convert("RGBA"), (0, 0))
        with Image.open(layers["lighting"]) as light:
            combined.alpha_composite(light.convert("RGBA"), (0, 0))
        destination.parent.mkdir(parents=True, exist_ok=True)
        combined.convert("RGB").save(destination, "PNG", optimize=True)


def render_motion_clip(*, kind: str, topic: str, narration: str,
                       scene_index: int, scene_count: int, style: str,
                       duration: float, width: int, height: int, fps: int,
                       destination: Path, direction: dict | None = None,
                       held_prop: str | None = None,
                       caption_segments: list[dict] | None = None,
                       scene_start_ms: int = 0,
                       mouth_intervals: list[tuple[float, float]] | None = None,
                       landscape: str | None = None):
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
                               direction=direction, held_prop=held_prop,
                               landscape=landscape)
        action = direction["action"] if direction else "idle"
        blink = blink_enable(action, scene_index=scene_index)
        # Within-scene actions follow the authored order (walk, then jump,
        # then talk). Short scenes or single-action lines remain unchanged.
        settings = dict(narration=narration, duration=duration,
                        fallback_action=action,
                        caption_segments=caption_segments,
                        scene_start_ms=scene_start_ms)
        body_x, body_y = choreograph(
            **settings, pose=lambda a: body_position(a, x=180, y=184))
        left_x, left_y = choreograph(
            **settings, pose=lambda a: leg_position(a, side="left"))
        right_x, right_y = choreograph(
            **settings, pose=lambda a: leg_position(a, side="right"))
        (tail_offset_y,) = choreograph(
            **settings, pose=lambda a: (
                secondary_position(a, base=173, side="tail"),))
        tail_x = f"({body_x})-67+8*sin(t*2.4)-52"
        tail_y = f"({body_y})+({tail_offset_y})-47"
        (tail_angle,) = choreograph(
            **settings, pose=lambda a: (joint_angle(a, part="tail", side="tail"),))
        (left_angle,) = choreograph(
            **settings, pose=lambda a: (joint_angle(a, part="leg", side="left"),))
        (right_angle,) = choreograph(
            **settings, pose=lambda a: (joint_angle(a, part="leg", side="right"),))
        (left_ear_angle,) = choreograph(
            **settings, pose=lambda a: (joint_angle(a, part="ear", side="left"),))
        (right_ear_angle,) = choreograph(
            **settings, pose=lambda a: (joint_angle(a, part="ear", side="right"),))
        (mouth,) = choreograph(
            **settings, pose=lambda a: (mouth_expression(a),),
            blend=False)
        gate = mouth_gate_expression(mouth_intervals)
        if gate is not None:
            # Never display speech-mouth animation during digital silence.
            # The separate authored action cue still must be "talk".
            mouth = f"({mouth})*({gate})"
        # A transparent fade affects only the pupil pose: the underlying
        # original sprite is identical in every other detail. Closed-eye
        # poses are composited last and remain intact throughout the gaze.
        shadow_graph = shadow_stage(
            body_x=body_x, ground_y=608,
            offset_x=45, image_index=8)
        rotation_graph = (
            f"[1:v]format=rgba,rotate=a='{tail_angle}':ow=334:oh=334:c=none[tailspin];"
            f"[6:v]format=rgba,rotate=a='{left_angle}':ow=162:oh=162:c=none[legleft];"
            f"[7:v]format=rgba,rotate=a='{right_angle}':ow=162:oh=162:c=none[legright];"
            f"[9:v]format=rgba,rotate=a='{left_ear_angle}':ow=180:oh=280:c=none[earleft];"
            f"[10:v]format=rgba,rotate=a='{right_ear_angle}':ow=180:oh=280:c=none[earright];"
        )
        fps_graph = (
            f"[shadowstage][earleft]overlay=x='({body_x})-15':"
            f"y='({body_y})-20':eval=frame:format=auto[earsA];"
            f"[earsA][earright]overlay=x='({body_x})+185':"
            f"y='({body_y})-20':eval=frame:format=auto[earsB];"
            f"[earsB][tailspin]overlay=x='{tail_x}':"
            f"y='{tail_y}':eval=frame:format=auto[a];"
            f"[a][2:v]overlay=x='{body_x}':"
            f"y='{body_y}':eval=frame:format=auto[b];"
            "[3:v]format=rgba,fade=t=in:st=0.18:d=0.42:alpha=1[look];"
            f"[b][look]overlay=x='{body_x}':"
            f"y='{body_y}':eval=frame:format=auto[c];"
            f"[c][4:v]overlay=x='{body_x}':"
            f"y='{body_y}':"
            f"enable='{blink}':eval=frame:format=auto[d];"
            f"[d][5:v]overlay=x='{body_x}':"
            f"y='{body_y}':"
            f"enable='{mouth}':eval=frame:format=auto[e];"
            f"[e][legleft]overlay=x='({left_x})-31':"
            f"y='({left_y})-19':eval=frame:format=auto[f];"
            f"[f][legright]overlay=x='({right_x})-31':"
            f"y='({right_y})-19':eval=frame:format=auto[g]"
        )
        fps_graph = shadow_graph + rotation_graph + fps_graph
        final = "g"
        names = ["background", "tail", "neutral", "body", "blink", "mouth",
                 "left_leg", "right_leg", "shadow", "left_ear", "right_ear"]
        fps_graph, final, names = append_overlays(
            graph=fps_graph, label=final, names=names,
            narration=narration, duration=duration,
            body_x=body_x, body_y=body_y, held_prop=held_prop)
        if direction and direction["weather"] in {"rain", "storm", "wind", "cloudy", "night", "day"}:
            _weather_overlay(
                layers["effects"],
                seed=f"{kind}|{topic}|{narration}|{scene_index}",
                weather=direction["weather"])
            speed_fx = {"rain": 240, "storm": 310, "wind": 55,
                        "cloudy": 25, "night": 22, "day": 18}[direction["weather"]]
            source_index = len(names)
            next_label = chr(ord(final) + 1)
            fps_graph += (
                f";[{final}][{source_index}:v]overlay=x=0:"
                f"y='-720+mod(t*{speed_fx},720)':eval=frame:format=auto[{next_label}]")
            final = next_label
            names.append("effects")
        fps_graph, final, names = overlay_foreground(
            graph=fps_graph, label=final, names=names,
            scene_index=scene_index, duration=duration)
        fps_graph, final, names = overlay_lighting(
            graph=fps_graph, label=final, names=names)
        shot = direction["shot"] if direction else "wide"
        camera = framing_filter(
            shot, width=width, height=height, fps=fps,
            scene_index=scene_index, duration=duration)
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
                     direction: dict | None = None,
                     held_prop: str | None = None,
                     landscape: str | None = None) -> str:
    if kind not in COLORS:
        raise ValueError("Unknown original forest character")
    normalized = validate_direction(direction) if direction is not None else None
    source = json.dumps(
        [FOREST_RIG_VERSION, kind, topic, narration, character, style,
         scene_id, normalized, held_prop, landscape, WORLD_VERSION], ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(source).hexdigest()
