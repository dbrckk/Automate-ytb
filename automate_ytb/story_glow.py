"""Narration-grounded original fireflies for storybook video scenes.

Only authored mentions of fireflies or lucioles activate a soft RGBA light
layer. The foreground remains clear around the central actor and the cues
are not inferred from irrelevant words like "light" or the episode title.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from random import Random
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter

STORY_GLOW_VERSION = "narrated-firefly-glow-v1"
_FIRE_FLY = re.compile(r"\b(?:lucioles?|firefl(?:y|ies)|glowworms?)\b")


def has_fireflies(narration: str) -> bool:
    """No implicit extras if the character only talks about other lights."""
    if not isinstance(narration, str):
        raise ValueError("Original narration must be text")
    if len(narration) > 200_000:
        raise ValueError("Original narration exceeds limit")
    folded = unicodedata.normalize("NFKD", narration.casefold())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return bool(_FIRE_FLY.search(folded))


def draw_story_glow(path: Path, *, narration: str, seed: str,
                    landscape: str = "forest") -> bool:
    """Draw a static 1280x720 transparent plate, only if script supports it."""
    if landscape not in {"forest", "river", "meadow", "village"}:
        raise ValueError("Unsupported source landscape")
    if not isinstance(seed, str) or len(seed) > 200_000:
        raise ValueError("Invalid authored scene seed")
    if not has_fireflies(narration):
        return False
    rng = Random(int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big"))
    light = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    ink = ImageDraw.Draw(light, "RGBA")
    cores = []
    # Keep points outside the central owl/fox eye and mouth region.
    for i in range(33):
        x = rng.randint(672, 1218)
        y = rng.randint(260, 613)
        radius = rng.choice((12, 16, 20, 25))
        ink.ellipse((x-radius,y-radius,x+radius,y+radius),
                    fill=(255,202,98,29))
        cores.append((x,y,rng.choice((2,3,4))))
    bloom = light.filter(ImageFilter.GaussianBlur(12))
    top = ImageDraw.Draw(bloom, "RGBA")
    for x,y,r in cores:
        top.ellipse((x-r*2,y-r*2,x+r*2,y+r*2),fill=(255,204,95,80))
        top.ellipse((x-r,y-r,x+r,y+r),fill=(255,246,169,215))
        top.ellipse((x-1,y-1,x+1,y+1),fill=(255,255,239,244))
        if landscape=="river" and y>410:
            top.ellipse((x-8,656,x+9,659),fill=(255,213,125,54))
    path.parent.mkdir(parents=True, exist_ok=True)
    bloom.save(path,"PNG")
    return True


def append_story_glow(*, graph: str, label: str,
                      names: list[str], enabled: bool) -> tuple[str,str,list[str]]:
    """Append separately moving, original firefly light plate to FFmpeg."""
    if not enabled:
        return graph,label,names
    if not isinstance(graph,str) or not isinstance(label,str) or not label:
        raise ValueError("Invalid FFmpeg storyboard graph")
    if "story_glow" in names:
        raise ValueError("Story glow already composited")
    idx=len(names)
    # Tiny periodic drift relative to character, weather and camera.
    graph += (f";[{label}][{idx}:v]overlay=x='3*sin(t*0.79)':"
              f"y='5*sin(t*1.13)':eval=frame:format=auto[storyglowdone]")
    return graph,"storyglowdone",names+["story_glow"]
