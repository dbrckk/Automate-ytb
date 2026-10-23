"""Original procedural character art for the free Android episode preview.

A deliberately simple, original illustrated owl (not copied from a reference).
Uses deterministic poses and scene-specific props without third-party assets.
"""
from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .studio import PALETTES, WIDTH, HEIGHT, font


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float):
    return tuple(round((1 - t) * x + t * y) for x, y in zip(a, b))


def _ellipse(draw, box, fill, outline=None, width=1):
    draw.ellipse(tuple(round(x) for x in box), fill=fill, outline=outline, width=width)


def render_character_scene(*, topic: str, narration: str, scene_index: int,
                           scene_count: int, style: str, character: str,
                           destination: Path) -> None:
    if style not in PALETTES:
        raise ValueError("Unknown illustration style")
    if not character.strip():
        raise ValueError("Missing original character description")
    seed = int.from_bytes(sha256(f"{topic}|{scene_index}|{narration}".encode()).digest()[:8], "big")
    base, secondary, accent = PALETTES[style]
    image = Image.new("RGB", (WIDTH, HEIGHT), base)
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        t = y / HEIGHT
        draw.line((0, y, WIDTH, y), fill=_mix(base, secondary, t * .75))
    # Distinct, repeatable layered environment per shot.
    for layer in range(3):
        horizon = 410 + layer * 95
        fill = _mix(base, secondary, .24 + .20 * layer)
        coords = [(0, HEIGHT), (0, horizon)]
        for x in range(0, WIDTH + 80, 80):
            variation = ((seed >> (x // 80 + layer * 7) % 56) & 15) - 8
            coords.append((x, horizon + int(variation * (3 + layer))))
        coords.extend([(WIDTH, HEIGHT)])
        draw.polygon(coords, fill=fill)
    # Glowing moon/sun.
    cx = 995 + (seed % 150) - 75
    cy = 145 + (seed % 67)
    glow = Image.new("RGBA", (WIDTH, HEIGHT))
    gd = ImageDraw.Draw(glow)
    for radius in (130, 98, 72):
        alpha = {130: 14, 98: 22, 72: 42}[radius]
        _ellipse(gd, (cx-radius, cy-radius, cx+radius, cy+radius), accent + (alpha,))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    image = Image.alpha_composite(image.convert("RGBA"), glow)
    draw = ImageDraw.Draw(image)
    _ellipse(draw, (cx-46, cy-46, cx+46, cy+46), accent)

    # Recurring original owl with pose/expression variation.
    shift = ((seed // 9) % 5 - 2) * 12
    wing = ((scene_index * 7) % 5 - 2) * 12
    ox, oy = 355 + shift, 382
    # Ground shadow and tail.
    _ellipse(draw, (ox-165, 594, ox+150, 627), (16, 22, 42, 90))
    draw.polygon([(ox+72, oy+110), (ox+145, oy+200), (ox+66, oy+185)],
                 fill=(82, 55, 137))
    # Ears and wings.
    draw.polygon([(ox-95, oy-110), (ox-123, oy-218), (ox-30, oy-166)],
                 fill=(113, 77, 179))
    draw.polygon([(ox+27, oy-165), (ox+111, oy-219), (ox+92, oy-95)],
                 fill=(113, 77, 179))
    _ellipse(draw, (ox-170, oy-30+wing, ox-70, oy+151+wing), (98, 61, 162))
    _ellipse(draw, (ox+65, oy-36-wing, ox+163, oy+147-wing), (98, 61, 162))
    _ellipse(draw, (ox-112, oy-154, ox+112, oy+170), (134, 90, 199))
    _ellipse(draw, (ox-82, oy-23, ox+83, oy+152), (220, 195, 237))
    # Face and eyes.
    for dx in (-49, 49):
        _ellipse(draw, (ox+dx-51, oy-119, ox+dx+51, oy-10),
                 (239, 221, 251))
        _ellipse(draw, (ox+dx-31, oy-94, ox+dx+31, oy-29),
                 (31, 43, 69))
        _ellipse(draw, (ox+dx-20, oy-86, ox+dx-8, oy-74),
                 (255, 255, 255))
        _ellipse(draw, (ox+dx-55, oy-125, ox+dx+55, oy-5),
                 None, (81, 227, 217), 8)
    draw.line((ox, oy-72, ox, oy-44), fill=(81, 227, 217), width=7)
    draw.polygon([(ox-17, oy-25), (ox+17, oy-25), (ox, oy+8)],
                 fill=(251, 189, 69))
    if scene_index % 4 == 0:
        draw.arc((ox-23, oy+20, ox+24, oy+51), 0, 180,
                 fill=(67, 43, 99), width=5)
    # Scarf and feet.
    draw.arc((ox-84, oy+70, ox+84, oy+135), 0, 180,
             fill=(248, 200, 72), width=17)
    draw.polygon([(ox+65, oy+103), (ox+118, oy+172),
                  (ox+82, oy+181), (ox+49, oy+127)],
                 fill=(248, 200, 72))
    for dx in (-49, 49):
        draw.line((ox+dx, oy+156, ox+dx, oy+190),
                  fill=(251, 189, 69), width=10)
        draw.line((ox+dx-22, oy+188, ox+dx+20, oy+188),
                  fill=(251, 189, 69), width=9)

    # Separate legible narration card (text is not baked into AI images).
    draw.rounded_rectangle((680, 268, 1220, 600), radius=34,
                           fill=(18, 28, 55), outline=_mix(accent, (255,255,255), .2),
                           width=3)
    draw.text((719, 300), f"SCÈNE {scene_index:02d} / {scene_count:02d}",
              font=font(24), fill=accent)
    draw.line((717, 347, 1177, 347), fill=accent, width=3)
    words = narration.split()
    lines, current = [], ""
    f = font(31)
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=f)[2] <= 455:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) > 6:
        lines = lines[:5] + ["…"]
    for idx, line in enumerate(lines):
        draw.text((718, 368 + idx * 38), line, font=f, fill=(250, 250, 255))
    draw.rounded_rectangle((42, 38, 550, 98), radius=22, fill=(18, 28, 55))
    title = topic.strip()
    while draw.textbbox((0, 0), title, font=font(28))[2] > 450 and len(title) > 10:
        title = title[:-2]
    if title != topic.strip():
        title = title.rstrip() + "…"
    draw.text((63, 54), title, font=font(28), fill=(255, 250, 238))
    draw.text((48, 661), "ILLUSTRATION ORIGINALE  •  APERÇU",
              font=font(19), fill=(235, 236, 247))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(destination, format="PNG", optimize=True)
