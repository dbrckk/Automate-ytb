"""Original hand-directed atmospheric depth for the procedural story world.

Subtle diffuse solar/lunar bloom, sky shafts and horizon mist are composed
before the character/trees and subtitles; no photographic stock, downloaded
textures, 3D renderer, or external generator is involved.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

SCENIC_GRADE_VERSION = "cinematic-sky-v1-soft-bloom"


def _composite_rgb(scene: Image.Image, tint: Image.Image) -> None:
    combined = Image.alpha_composite(scene.convert("RGBA"), tint)
    scene.paste(combined.convert("RGB"))


def paint_sky_bloom(scene: Image.Image, *, weather: str) -> None:
    """Light the original sun/moon before foreground skyline and tree artwork."""
    if scene.mode != "RGB" or scene.size != (1280, 720):
        raise ValueError("Expected original RGB storybook background")
    if weather not in {"day","night","wind","rain","storm","cloudy"}:
        raise ValueError("Unsupported authored light condition")
    night = weather == "night"
    sun = (963, 160)
    warm = (255, 207, 129) if not night else (155, 187, 255)
    strength = 54 if night else 47 if weather in {"day","wind"} else 20
    glow = Image.new("RGBA", scene.size)
    brush = ImageDraw.Draw(glow)
    cx,cy=sun
    for radius, alpha in ((280,strength//3),(205,strength),(105,strength+15)):
        brush.ellipse((cx-radius,cy-radius*.65,cx+radius,cy+radius*.65),
                      fill=(*warm,min(100,alpha)))
    glow = glow.filter(ImageFilter.GaussianBlur(58))
    _composite_rgb(scene,glow)

    if weather not in {"day","wind"}:
        return
    shafts=Image.new("RGBA",scene.size)
    d=ImageDraw.Draw(shafts)
    # Broad triangular light shafts end before the central actor zone.
    d.polygon([(cx-16,cy+28),(733,551),(850,570)],
              fill=(255,226,174,16))
    d.polygon([(cx+15,cy+18),(1070,596),(1190,624)],
              fill=(255,232,191,13))
    d.polygon([(cx-5,cy+25),(881,590),(969,595)],
              fill=(255,229,184,9))
    shafts=shafts.filter(ImageFilter.GaussianBlur(21))
    _composite_rgb(scene,shafts)


def paint_horizon_mist(scene: Image.Image, *, weather: str) -> None:
    """Depth cue applied after distant silhouettes but before nearby trees."""
    if scene.mode != "RGB" or scene.size != (1280,720):
        raise ValueError("Expected original RGB storybook background")
    if weather not in {"day","night","wind","rain","storm","cloudy"}:
        raise ValueError("Unsupported authored atmosphere")
    tone = ((125,147,181) if weather=="night" else
            (171,191,203) if weather in {"rain","storm","cloudy"} else
            (205,225,209))
    strength=38 if weather in {"rain","cloudy","storm"} else 24
    mist=Image.new("RGBA",scene.size)
    d=ImageDraw.Draw(mist)
    for top,height in ((402,45),(504,35),(585,23)):
        d.ellipse((-150,top,1450,top+height),fill=(*tone,strength))
    mist=mist.filter(ImageFilter.GaussianBlur(34))
    _composite_rgb(scene,mist)
