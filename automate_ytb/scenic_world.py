"""Original FR/EN location-aware storybook landscape illustrations.

Selection is entirely based on authored narration, with explicit location
changes persisting until another named setting appears. No external images,
AI model calls, copyrighted assets or invented story changes.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from random import Random

from PIL import ImageDraw

WORLD_VERSION = "original-landscapes-v1"
LANDSCAPES = ("forest", "river", "village", "meadow")
PATTERNS = (
    ("river", r"\b(riviere\w*|fleuve\w*|ruisseau\w*|torrent\w*|river\w*|stream\w*|brook\w*)\b"),
    ("village", r"\b(village\w*|bourg\w*|hameau\w*|maison\w*|cabane\w*|cottage\w*|house\w*|town\w*)\b"),
    ("meadow", r"\b(prairie\w*|pre\w*|champ\w*|pelouse\w*|meadow\w*|field\w*|grassland\w*)\b"),
    ("forest", r"\b(foret\w*|bois\w*|sous-bois\w*|wood\w*|forest\w*|grove\w*|woodland\w*)\b"),
)


def detect_landscape(narration: str) -> str | None:
    """Earliest explicit location mention wins, or None when not described."""
    if not isinstance(narration, str):
        raise ValueError("Narration must be original text")
    folded = unicodedata.normalize("NFKD", narration.casefold())
    words = "".join(ch for ch in folded if not unicodedata.combining(ch))
    hits = [(match.start(), name) for name, pattern in PATTERNS
            if (match := re.search(pattern, words))]
    return min(hits)[1] if hits else None


def landscapes_for_scenes(scenes: list[dict]) -> list[str]:
    """Follow locations from one authored scene to the next, default forest."""
    if not isinstance(scenes, list):
        raise ValueError("Expected ordered original scenes")
    setting = "forest"
    result = []
    for scene in scenes:
        if not isinstance(scene, dict) or not isinstance(scene.get("narration"), str):
            raise ValueError("Every original scene needs authored narration")
        setting = detect_landscape(scene["narration"]) or setting
        result.append(setting)
    return result


def draw_landscape_details(draw: ImageDraw.ImageDraw, *, kind: str,
                           night: bool, seed: int) -> None:
    """Distinct foreground landmarks, mostly right of original character.

    The background sky and weather stay under the shared renderer; details
    remain deterministic in the same 1280x720 coordinate system.
    """
    if kind not in LANDSCAPES:
        raise ValueError("Unsupported authored landscape")
    rnd = Random(seed ^ 0xACBC11)
    if kind == "forest":
        return
    if kind == "river":
        # Winding stream, layered riverbanks, reflected ripples and bridge.
        bank = (37, 96, 86) if night else (69, 148, 99)
        water = (47, 100, 134) if night else (80, 174, 198)
        bright = (109, 166, 194) if night else (155, 220, 223)
        draw.polygon([(622, 720), (665, 613), (800, 548), (1088, 538),
                      (1280, 578), (1280, 720)], fill=bank)
        draw.polygon([(660, 720), (728, 629), (876, 585), (1098, 578),
                      (1280, 603), (1280, 720)], fill=water)
        draw.line([(667, 718), (742, 637), (880, 599), (1112, 592),
                   (1278, 621)], fill=bright, width=9, joint="curve")
        for _ in range(24):
            x = rnd.randrange(780, 1258)
            y = rnd.randrange(625, 703)
            width = rnd.randrange(8, 37)
            draw.arc((x, y, x + width, y + 11), 5, 170,
                     fill=bright, width=2)
        # Original wooden footbridge and reflected support posts.
        draw.polygon([(808, 562), (1030, 544), (1049, 564), (814, 582)],
                     fill=(121, 75, 56))
        for x, y in ((830, 561), (911, 553), (1006, 546)):
            draw.line((x, y - 34, x+5, y+12), fill=(86, 56, 47), width=8)
            draw.ellipse((x-6, y-39, x+7, y-28), fill=(196, 139, 83))
        draw.line([(832, 526), (917, 521), (1011, 510)],
                  fill=(194, 139, 93), width=7)
    elif kind == "village":
        hill = (58, 95, 87) if night else (104, 162, 119)
        draw.polygon([(583, 656), (692, 547), (860, 560),
                      (992, 511), (1185, 547), (1280, 505),
                      (1280, 720), (583, 720)], fill=hill)
        for x, y, scale in ((680, 505, 1.0), (971, 485, 1.25),
                             (1157, 514, 0.86)):
            w, h = round(112*scale), round(102*scale)
            x, y = int(x), int(y)
            wall = (134, 123, 130) if night else (238, 208, 167)
            roof = (83, 62, 89) if night else (157, 79, 78)
            draw.rectangle((x, y, x+w, y+h), fill=wall,
                           outline=(74, 66, 70), width=4)
            draw.polygon([(x-12, y+6), (x+w//2, y-round(h*.63)),
                          (x+w+11, y+6)], fill=roof)
            draw.line((x-12, y+6, x+w//2, y-round(h*.63),
                       x+w+11, y+6), fill=(76, 48, 69), width=6)
            glow = (255, 218, 111) if night else (122, 172, 184)
            for ox in (.18, .67):
                wx = int(x+ox*w)
                draw.rectangle((wx, y+24, wx+round(19*scale), y+48),
                               fill=glow, outline=(88, 70, 71), width=3)
            draw.rectangle((x+w//2-13, y+h-42, x+w//2+13, y+h),
                           fill=(109, 73, 60))
        # Cobble path leads the eye toward the central cottage.
        draw.polygon([(791, 720), (881, 594), (978, 598), (1090, 720)],
                     fill=(153, 148, 139) if night else (207, 193, 157))
        for row in range(3):
            y = 621 + row*35
            for x in range(858-row*21, 1013+row*19, 46):
                draw.line((x, y, x+18, y+4), fill=(126, 120, 112), width=3)
    elif kind == "meadow":
        hill = (46, 97, 85) if night else (101, 172, 113)
        light = (66, 113, 101) if night else (134, 195, 121)
        draw.polygon([(570, 604), (714, 531), (867, 547), (1043, 512),
                      (1280, 565), (1280, 720), (570, 720)], fill=hill)
        draw.polygon([(662, 720), (745, 627), (928, 591),
                      (1120, 631), (1280, 582), (1280, 720)], fill=light)
        petal_colors = ((190, 164, 201), (245, 217, 137), (240, 180, 174))
        if night:
            petal_colors = ((151, 137, 175), (198, 181, 115), (185, 131, 143))
        for _ in range(65):
            x = rnd.randrange(600, 1262)
            y = rnd.randrange(591, 716)
            sz = rnd.randrange(3, 8)
            color = rnd.choice(petal_colors)
            draw.line((x, y, x+2, y+sz*3), fill=(44, 103, 78), width=2)
            for dx, dy in ((-sz, 0), (sz, 0), (0, -sz), (0, sz)):
                draw.ellipse((x+dx-sz//2, y+dy-sz//2,
                              x+dx+sz//2, y+dy+sz//2), fill=color)
            draw.ellipse((x-2, y-2, x+2, y+2), fill=(241, 200, 93))
        for bx, by in ((760, 469), (1042, 434), (1190, 492)):
            wing = (212, 209, 244) if night else (245, 235, 206)
            draw.ellipse((bx-19, by-10, bx, by+5), fill=wing)
            draw.ellipse((bx, by-10, bx+19, by+5), fill=wing)
            draw.line((bx, by-11, bx, by+12), fill=(74, 72, 78), width=2)
