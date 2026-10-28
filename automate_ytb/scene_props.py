"""Original story-specific props and limited script-grounded character interactions.

This is a 2D stage gesture, not physically simulated object manipulation:
recognized written phrases control only trusted FFmpeg overlay expressions.
No unmentioned props, external image assets, LLMs or raw filter arguments.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw

PROP_VERSION = "scene-props-v3-gaze-pose"

NOUNS = (
    ("apple", r"\b(pomme\w*|apple\w*)\b"),
    ("flower", r"\b(fleur\w*|flower\w*|blossom\w*)\b"),
    ("book", r"\b(livre\w*|book\w*)\b"),
    ("stone", r"\b(pierre\w*|caillou\w*|rocher\w*|stone\w*|rock\w*)\b"),
)
PICKUP = re.compile(
    r"\b(ramass\w*|saisi\w*|attrap\w*|prend|prendre|"
    r"cueille\w*|cueillir|pick\w*|grabs?|grabbed|takes?|took|"
    r"collect\w*|gather\w*)\b")
OBSERVE = re.compile(
    r"\b(regard\w*|observ\w*|examin\w*|admir\w*|"
    r"discover\w*|look\w*|watch\w*|inspect\w*|notice\w*|"
    r"decouvr\w*|trouv\w*|find\w*|found)\b")
OBSTACLE = re.compile(
    r"\b(saut\w*|bond\w*|jump\w*|hop\w*|leap\w*)\b")


def select_interaction(narration: str) -> dict[str, str] | None:
    """Explicit written noun + action required; earliest supported noun wins."""
    if not isinstance(narration, str):
        raise ValueError("Original scene narration must be text")
    plain = unicodedata.normalize("NFKD", narration.casefold())
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    found = [(match.start(), name) for name, pattern in NOUNS
             if (match := re.search(pattern, plain))]
    if not found:
        return None
    name = min(found)[1]
    if name != "stone" and PICKUP.search(plain):
        action = "pickup"
    elif name == "stone" and OBSTACLE.search(plain):
        action = "obstacle"
    elif OBSERVE.search(plain):
        action = "inspect"
    else:
        return None
    return {"prop": name, "action": action, "version": PROP_VERSION}


# Deliberately require both a release verb and an explicit noun: the script
# must actually say that the character has put down/used the carried object.
RELEASE = re.compile(
    r"\b(depose\w*|pose\w*|laisse\w*|abandonne\w*|jette\w*|mange\w*|"
    r"eat\w*|eaten|put\w*|drop\w*|discard\w*|leave\w*|left|release\w*)\b")


def _normalized(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in plain if not unicodedata.combining(c))


def carried_props_for_scenes(scenes: list[dict]) -> list[str | None]:
    """Object carried *during* each scene, determined solely by prior writing.

    A pickup becomes visibly carried in the *next* scene. A release that
    explicitly names the held object removes it immediately. Inspecting an
    unrelated object temporarily foregrounds that object, but does not
    discard the existing inventory. Only one object is tracked.
    """
    if not isinstance(scenes, list):
        raise ValueError("Expected ordered scene list")
    held: str | None = None
    states = []
    for scene in scenes:
        if not isinstance(scene, dict) or not isinstance(scene.get("narration"), str):
            raise ValueError("Every scene must have authored narration")
        plain = _normalized(scene["narration"])
        action = select_interaction(scene["narration"])
        if held and RELEASE.search(plain):
            pattern = dict(NOUNS)[held]
            if re.search(pattern, plain):
                held = None
        # The new pickup animates its own stage prop. A different subject
        # being inspected gets the visual focus, without losing inventory.
        visible = held if (action is None or (
            action["prop"] == held and action["action"] == "inspect")) else None
        states.append(visible)
        if action and action["action"] == "pickup":
            held = action["prop"]
    return states


def cue_for_scene(narration: str, *, held_prop: str | None = None
                  ) -> dict[str, str] | None:
    if held_prop is not None and held_prop not in {"apple", "flower", "book"}:
        raise ValueError("Unsupported carried scene object")
    cue = select_interaction(narration)
    # A carried object can be contemplated without teleporting back to the
    # ground. Current pickups and newly inspected props have precedence.
    if held_prop is not None and (cue is None or
            (cue["prop"] == held_prop and cue["action"] == "inspect")):
        return {"prop": held_prop, "action": "carry",
                "version": PROP_VERSION}
    return cue


GAZE_VERSION = "script-directed-attention-v1"
# Script-grounded French/English glances. A directional noun without a
# *looking* verb is insufficient: walking left must not redirect the eyes.
_LOOK_VERB = re.compile(
    r"\\b(?:regard\\w*|observ\\w*|fix\\w*|"
    r"look\\w*|glanc\\w*|watch\\w*)\\b")
_GAZE_DIRECTIONS = (
    ("left", re.compile(r"\\b(?:gauche|left)\\b")),
    ("right", re.compile(r"\\b(?:droite|right)\\b")),
    ("up", re.compile(r"\\b(?:haut|ciel|etoiles?|sky|stars?|above|up)\\b")),
    ("down", re.compile(r"\\b(?:bas|sol|terre|ground|down|feet)\\b")),
)


def gaze_target(narration: str, *, held_prop: str | None = None) -> str:
    """Select a small illustrated glance, never a fabricated eye tracker.

    A narrated/carrying prop keeps precedence over generic direction cues.
    Otherwise the first explicit gaze verb and nearby direction wins; a
    location or movement direction without a gaze verb changes nothing.
    """
    if not isinstance(narration, str) or len(narration) > 150_000:
        raise ValueError("Invalid gaze narration")
    cue = cue_for_scene(narration, held_prop=held_prop)
    if cue is not None:
        return "down-right" if cue["action"] == "carry" else "right"
    plain = _normalized(narration)
    candidates = []
    for gaze_verb in _LOOK_VERB.finditer(plain):
        # Punctuation terminates the local clause, so a later unrelated
        # direction is never attached to an earlier glance.
        phrase = re.split(r"[.!?;]", plain[gaze_verb.end():gaze_verb.end()+65], maxsplit=1)[0]
        for name, pattern in _GAZE_DIRECTIONS:
            if match := pattern.search(phrase):
                candidates.append((gaze_verb.start(), match.start(), name))
    return min(candidates)[2] if candidates else "forward"


def draw_prop(path: Path, *, kind: str) -> None:
    """Draw a modest, distinctly recognizable, original transparent prop."""
    if kind not in {name for name, _ in NOUNS}:
        raise ValueError("Unsupported hand-drawn prop")
    image = Image.new("RGBA", (138, 138), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    outline = (33, 48, 68, 255)
    if kind == "apple":
        d.ellipse((26, 39, 110, 123), fill=(220, 64, 74, 255),
                  outline=outline, width=5)
        d.ellipse((39, 50, 75, 97), fill=(248, 111, 100, 255))
        d.line((68, 43, 79, 20), fill=(86, 62, 47, 255), width=8)
        d.ellipse((80, 15, 122, 33), fill=(80, 175, 98, 255),
                  outline=(49, 103, 82, 255), width=3)
        d.arc((43, 49, 75, 86), 150, 260, fill=(255, 203, 183, 255), width=4)
    elif kind == "flower":
        d.line((68, 77, 72, 128), fill=(65, 145, 87, 255), width=8)
        d.ellipse((39, 100, 69, 116), fill=(74, 168, 92, 255))
        for x, y in ((49, 51), (85, 51), (52, 83), (83, 83), (67, 34)):
            d.ellipse((x-22, y-22, x+22, y+22),
                      fill=(238, 134, 176, 255), outline=outline, width=3)
        d.ellipse((55, 56, 81, 83), fill=(248, 207, 91, 255),
                  outline=(152, 107, 46, 255), width=2)
    elif kind == "book":
        d.polygon([(21, 37), (67, 49), (117, 37), (117, 115),
                   (68, 126), (21, 114)], fill=(241, 220, 172, 255))
        d.polygon([(20, 35), (65, 45), (65, 120), (20, 110)],
                  fill=(80, 143, 172, 255))
        d.polygon([(70, 45), (117, 34), (117, 110), (70, 121)],
                  fill=(94, 176, 175, 255))
        d.line((68, 49, 68, 124), fill=outline, width=4)
        d.line([(20, 35), (65, 45), (117, 34), (117, 113),
                (68, 125), (20, 112), (20, 35)], fill=outline, width=4)
        for y in (60, 73, 86):
            d.line((34, y, 53, y+5), fill=(200, 222, 233, 255), width=3)
    else:
        d.polygon([(17, 94), (37, 50), (83, 28), (118, 63), (130, 109),
                   (98, 123), (33, 121)], fill=(124, 144, 155, 255))
        d.line([(17, 94), (37, 50), (83, 28), (118, 63), (130, 109),
                (98, 123), (33, 121), (17, 94)], fill=outline, width=5)
        d.line([(37, 50), (74, 77), (118, 63)], fill=(183, 197, 196, 255),
               width=4)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


def draw_reach(path: Path, *, actor: str) -> None:
    """Small foreground gesture, deliberately stylized rather than IK."""
    fur = {"owl": (131, 86, 200, 255),
           "fox": (226, 116, 58, 255),
           "rabbit": (219, 205, 224, 255),
           "cat": (90, 144, 171, 255)}
    if actor not in fur:
        raise ValueError("Unsupported local articulated actor")
    image = Image.new("RGBA", (120, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.line((5, 60, 91, 40), fill=(33, 45, 70, 255), width=38)
    d.line((5, 60, 91, 40), fill=fur[actor], width=28)
    d.ellipse((76, 20, 116, 63), fill=fur[actor],
              outline=(33, 45, 70, 255), width=4)
    d.ellipse((94, 30, 113, 47), fill=(248, 225, 206, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG")


def create_layers(folder: Path, *, narration: str,
                  actor: str, held_prop: str | None = None) -> dict | None:
    interaction = cue_for_scene(narration, held_prop=held_prop)
    if interaction is None:
        return None
    draw_prop(folder / "prop.png", kind=interaction["prop"])
    if interaction["action"] == "pickup":
        draw_reach(folder / "reach.png", actor=actor)
    return interaction


def append_overlays(*, graph: str, label: str, names: list[str],
                    narration: str, duration: float,
                    body_x: str, body_y: str,
                    held_prop: str | None = None) -> tuple[str, str, list[str]]:
    """Append trusted overlays *before* weather and camera transforms.

    Exactly one extra image for observing/jumping and two for pickup.
    No audio, scene durations or author-edited narration are altered.
    """
    cue = cue_for_scene(narration, held_prop=held_prop)
    if cue is None:
        return graph, label, names
    if not 0 < duration <= 3600:
        raise ValueError("Invalid scene duration")
    if label not in "efghij":
        raise ValueError("Unexpected filter graph label")
    # Forest rigs now contain 11 trusted base plates (independent ears).
    # Keep the limit bounded while allowing those plates plus the optional
    # pickup reach/prop overlays appended after this integrity check.
    if not 1 <= len(names) <= 12:
        raise ValueError("Unexpected filter input count")
    # Use safe coordinate expressions bound to stage 1280x720.
    if cue["action"] == "pickup":
        begin = min(.70, duration * .20)
        end = min(1.65, duration * .62)
        delta = max(.1, end - begin)
        progress = f"min(1,max(0,(t-{begin:.3f})/{delta:.3f}))"
        # Actor follows the prop after a brief reach movement. Body sway
        # is included in the held position (no physics-based grip claim).
        held_x = f"({body_x})+301"
        held_y = f"({body_y})+253"
        prop_x = f"652*(1-({progress}))+({held_x})*({progress})"
        prop_y = f"474*(1-({progress}))+({held_y})*({progress})"
        reach_x = f"422+24*({progress})"
        reach_y = f"443-10*({progress})"
        index = len(names)
        next_label = chr(ord(label) + 1)
        graph += (f";[{label}][{index}:v]overlay=x='{reach_x}':"
                  f"y='{reach_y}':eval=frame:format=auto[{next_label}]")
        label = next_label
        names.append("reach")
    elif cue["action"] == "carry":
        prop_x = f"({body_x})+301"
        prop_y = f"({body_y})+253"
    else:
        prop_x = "652+4*sin(t*1.3)" if cue["action"] == "inspect" else "652"
        prop_y = "474+3*sin(t*2.0)" if cue["action"] == "inspect" else "500"
    index = len(names)
    next_label = chr(ord(label) + 1)
    graph += (f";[{label}][{index}:v]overlay=x='{prop_x}':"
              f"y='{prop_y}':eval=frame:format=auto[{next_label}]")
    names.append("prop")
    return graph, next_label, names
