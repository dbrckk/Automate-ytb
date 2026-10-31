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

WORLD_VERSION = "original-landscapes-v2-forest-ground-details"
LANDSCAPES = ("forest", "river", "village", "meadow")
PATTERNS = (
    ("river", r"\b(riviere\w*|fleuve\w*|ruisseau\w*|torrent\w*|river\w*|stream\w*|brook\w*)\b"),
    ("village", r"\b(village\w*|bourg\w*|hameau\w*|maison\w*|cabane\w*|cottage\w*|house\w*|town\w*)\b"),
    ("meadow", r"\b(prairie\w*|pres?|champ\w*|pelouse\w*|meadow\w*|field\w*|grassland\w*)\b"),
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
        # A separate forest silhouette is needed: generic background trees
        # alone cannot communicate a woodland floor at small mobile sizes.
        # Keep the original 0..600px actor area completely unobstructed.
        earth = (33, 61, 65) if night else (58, 94, 72)
        root = (43, 47, 57) if night else (82, 75, 65)
        stone = (73, 91, 100) if night else (132, 147, 133)
        stone_edge = (117, 139, 143) if night else (187, 198, 168)
        moss = (50, 93, 82) if night else (96, 151, 95)
        fern = (58, 109, 97) if night else (73, 145, 101)
        fern_light = (98, 141, 120) if night else (132, 185, 115)
        # Low irregular bank, rather than a full-screen flat grass block.
        draw.polygon(
            [(602, 700), (651, 669), (717, 680), (777, 644),
             (841, 657), (906, 632), (983, 660), (1052, 641),
             (1118, 666), (1214, 637), (1280, 657),
             (1280, 720), (602, 720)],
            fill=earth)
        # Bark roots lead the eye toward the background trees without
        # entering the body/shadow area of any original rig.
        for x, y, span in ((711, 674, 70), (910, 658, 84),
                           (1106, 674, 76), (1239, 669, 52)):
            draw.arc((x-span, y-27, x+span, y+34), 184, 346,
                     fill=root, width=7)
            draw.arc((x-span//2, y-15, x+span//2, y+25), 185, 338,
                     fill=moss, width=3)
        # Small mossy boulders, distinct overlapping planes and contact
        # shadows; never use photos or external protected assets.
        for x, y, scale in ((732, 631, 1.0), (970, 642, .78),
                             (1178, 610, 1.14)):
            w, h = round(64*scale), round(32*scale)
            draw.ellipse((x-w-8, y+h-8, x+w+10, y+h+14),
                         fill=(27, 47, 56) if night else (42, 79, 65))
            draw.polygon(
                [(x-w, y+8), (x-w//2, y-h//2), (x+9, y-h),
                 (x+w-9, y-h//2), (x+w, y+h//2),
                 (x+w-15, y+h), (x-w+8, y+h)],
                fill=stone, outline=root, width=3)
            draw.line([(x-w+11, y+5), (x-w//2, y-h//2+8),
                       (x+8, y-h+9), (x+w-13, y-h//2+7)],
                      fill=stone_edge, width=3)
            draw.arc((x-w//2, y-h//2-1, x+w//2, y+10),
                     183, 321, fill=moss, width=5)
        # Fern fronds alternate directions for a layered, natural woodland.
        for x, y, height in ((663, 664, 67), (814, 688, 87),
                             (1047, 677, 72), (1244, 699, 93)):
            direction = -1 if (x // 100) % 2 else 1
            top = (x+direction*17, y-height)
            draw.line([(x, y), (x+direction*9, y-height//2), top],
                      fill=fern, width=4)
            for index in range(1, 8):
                fraction = index/9
                px = x+direction*(9*fraction+8*fraction*fraction)
                py = y-height*fraction
                leaf_len = round(16*(1-.45*fraction))
                for side in (-1, 1):
                    draw.line(
                        [(px, py), (px+side*leaf_len, py-8-5*fraction)],
                        fill=fern_light if index % 2 else fern, width=4)
        # Small unmistakable toadstools add a mobile-legible woodland cue.
        for x, y, radius in ((779, 696, 16), (1014, 698, 13),
                              (1193, 680, 19)):
            cap = (129, 89, 113) if night else (185, 90, 81)
            highlight = (183, 150, 168) if night else (242, 197, 149)
            draw.line((x, y, x+2, y-radius), fill=stone_edge, width=6)
            draw.ellipse((x-radius, y-radius*2, x+radius, y-radius//2),
                         fill=cap, outline=root, width=2)
            for offset in (-radius//2, radius//3):
                draw.ellipse((x+offset-2, y-radius*2+5,
                              x+offset+3, y-radius*2+10),
                             fill=highlight)
        # Seed-sensitive but controlled ground detail across the right side.
        for _ in range(32):
            x = rnd.randrange(624, 1256)
            y = rnd.randrange(690, 716)
            width = rnd.randrange(3, 8)
            draw.arc((x-width, y-width, x+width, y+width),
                     215, 345, fill=fern, width=2)
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
