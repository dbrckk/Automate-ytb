"""Mobile-first cinematic lightning editorial, independent of the moving world.

Unlike a slide-like repeated episode title, the original hook is shown once,
then each physical lightning beat receives one compact contextual chapter
identifier. The captions are still rendered separately from measured speech.
Cached typography prevents needless FreeType work on every 30 FPS frame.
No third-party images, web assets or copied music.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw

from .science_motion import _font
from .science_lightning import BADGES, BEATS

VERSION = "lightning-cinematic-one-shot-hook-compact-chapters-p49-v1"
PLATE_SIZE = (1080, 335)
WHITE = (239, 248, 252, 255)
CYAN = (147, 222, 244, 255)
AMBER = (255, 201, 113, 255)


def _smooth(q: float) -> float:
    q = max(0., min(1., q))
    return q*q*(3.-2.*q)


@lru_cache(maxsize=24)
def _intro_plate(lines: tuple[str, ...], font_size: int) -> Image.Image:
    plate = Image.new("RGBA", PLATE_SIZE)
    d = ImageDraw.Draw(plate)
    d.rounded_rectangle((67, 112, 1013, 300), radius=24,
                        fill=(4, 14, 31, 183))
    d.text((96, 130), "A CINEMATIC SCIENCE SHORT",
           font=_font(25, True), fill=CYAN)
    for index, line in enumerate(lines):
        d.text((96, 177 + index*51), line,
               font=_font(font_size, True), fill=WHITE)
    d.line((96, 282, 261, 282), fill=AMBER, width=4)
    return plate


@lru_cache(maxsize=20)
def _chapter_plate(beat: str, english: bool) -> Image.Image:
    plate = Image.new("RGBA", PLATE_SIZE)
    d = ImageDraw.Draw(plate)
    index = BEATS.index(beat)
    label = BADGES[beat][0 if english else 1]
    font_size = 34
    while font_size > 22 and d.textbbox((0, 0), label,
                                      font=_font(font_size, True))[2] > 690:
        font_size -= 1
    d.rounded_rectangle((76, 133, 998, 223), radius=19,
                        fill=(3, 15, 32, 151))
    d.text((99, 153), label, font=_font(font_size, True),
           fill=WHITE)
    d.text((851, 158), f"{index+1:02d} / 05",
           font=_font(30, True), fill=AMBER)
    # A restrained editorial rail, not a repeating static diagram card.
    d.line((93, 234, 987, 234), fill=(118, 173, 203, 73), width=2)
    d.line((93, 234, 93+894*(index+1)//5, 234),
           fill=(141, 225, 245, 199), width=3)
    return plate


def _overlay(picture: Image.Image, plate: Image.Image, opacity: float) -> None:
    if opacity <= 0.:
        return
    if opacity >= 1.:
        picture.alpha_composite(plate, (0, 0))
        return
    # Make a detached copy; cached plates must never be changed by a frame.
    layer = plate.copy()
    alpha = plate.getchannel("A")
    lut = [round(v*opacity) for v in range(256)]
    layer.putalpha(alpha.point(lut))
    picture.alpha_composite(layer, (0, 0))


def render_lightning_editorial(picture: Image.Image, *,
                               beat: str, scene_index: int, t: float,
                               duration: float, english: bool,
                               title_lines: tuple[str, ...],
                               title_size: int) -> None:
    """Overlay a one-shot hook and a compact beat heading in the safe upper band.

    Every title frame is fully inside y=112..300, well above the scene camera
    (y=330..1710) and the native SRT-linked lower caption (y>=1586).
    """
    if (picture.mode != "RGBA" or picture.size != (1080, 1920)
            or beat not in BEATS
            or type(scene_index) is not int or scene_index < 1
            or type(t) not in (float, int)
            or type(duration) not in (float, int)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration
            or type(english) is not bool
            or type(title_lines) is not tuple
            or not 1 <= len(title_lines) <= 2
            or any(not isinstance(line, str) or not line.strip() or
                   len(line) > 80 for line in title_lines)
            or type(title_size) is not int or not 22 <= title_size <= 48):
        raise ValueError("Invalid cinematic lightning editorial state")
    if scene_index == 1:
        # Full hook exists ONLY in opening shot; crossfade into the chapter
        # heading without a jump or a title overlay covering every shot.
        reveal = _smooth(t/.30)
        release = 1.-_smooth((t-1.55)/.65)
        intro_opacity = reveal*release
        chapter_opacity = _smooth((t-1.63)/.65)
        _overlay(picture, _intro_plate(title_lines, title_size), intro_opacity)
    else:
        chapter_opacity = .25+.75*_smooth(t/.27)
    _overlay(picture, _chapter_plate(beat, english), chapter_opacity)
