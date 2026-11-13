"""Cinematic phrase captions synchronized to synthesized PCM boundaries.

No word-level alignments are invented. Every caption preserves all normalized
original words, fits within the portrait safe region and fades briefly on its
measured phrase boundaries. Painting only the local panel avoids expensive
full-frame alpha conversions at 30 FPS.
"""
from __future__ import annotations

from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

VERSION = "pcm-phrase-cinematic-safe-caption-v1"
MIN_PORTRAIT_WIDTH = 240
MAX_PORTRAIT_WIDTH = 1200


def _portrait_dimensions(width: int, height: int) -> bool:
    # Delivery is restricted by the producer to 360/720/1080. Internal
    # tests and editorial previews also use valid 480x853 portrait frames.
    return (type(width) is int and MIN_PORTRAIT_WIDTH <= width <= MAX_PORTRAIT_WIDTH
            and type(height) is int and
            abs(height - width*16/9) <= 1)


def _text(raw: str) -> str:
    if (type(raw) is not str or not raw or len(raw) > 800
            or any(ord(c) < 32 and c not in "\n\r\t" for c in raw)):
        raise ValueError("Invalid original caption text")
    result = " ".join(raw.split())
    if not result:
        raise ValueError("Empty original caption")
    return result


@lru_cache(maxsize=256)
def _cached_layout(original: str, width: int, height: int) -> tuple:
    """Cache expensive exact font measurements as immutable evidence."""
    if not _portrait_dimensions(width,height):
        raise ValueError("Expected bounded 9:16 original frame or preview")
    inset = round(width * .088)
    pad_x = max(9, round(width * .022))
    pad_y = max(7, round(width * .018))
    available = width - 2 * inset - 2 * pad_x
    # Real font metrics, not char counts; long French words and scientific
    # units must remain visible in full instead of _fit's ellipsis/truncation.
    first_size = max(14, round(width * .052))
    floor = max(10, round(width * .023))
    tokens = original.split(" ")
    for font_size in range(first_size, floor - 1, -1):
        font = _font(font_size)
        lines, current = [], ""
        too_wide = False
        for word in tokens:
            if font.getlength(word) > available:
                too_wide = True
                break
            candidate = (current + " " + word).strip()
            if font.getlength(candidate) <= available:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        if too_wide or not 1 <= len(lines) <= 3:
            continue
        line_height = max(font_size + 4, round(font_size * 1.30))
        panel_height = len(lines) * line_height + 2 * pad_y
        if panel_height > round(height * .164):
            continue
        panel_width = max(round(font.getlength(line)) for line in lines) + 2 * pad_x
        if panel_width > width - 2 * inset:
            continue
        x = (width - panel_width) // 2
        # Keep the panel over the lower part of the moving world, but above
        # the right-hand TikTok/Shorts player and lower navigation region.
        cy = round(height * .811)
        y = cy - panel_height // 2
        if y < round(height * .69) or y + panel_height > round(height * .89):
            continue
        assert " ".join(lines) == original
        return (original,tuple(lines),font_size,line_height,
                panel_width,panel_height,x,y,pad_x,pad_y)
    raise ValueError(
        "Original caption cannot fit the mobile-safe region without omitting text")


@lru_cache(maxsize=64)
def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("DejaVuSans-Bold.ttf", size)


def caption_layout(text: str, *, width: int, height: int) -> dict:
    """Safe copy of a cached exact-fit caption layout, never truncated."""
    original = _text(text)
    values = _cached_layout(original, width, height)
    return dict(zip(
        ("text","lines","fontSize","lineHeight","panelWidth",
         "panelHeight","x","y","paddingX","paddingY"),
        (values[0], list(values[1]), *values[2:]),
    ))


def phrase_opacity(frame: int, start: int, end: int) -> int:
    """A bounded short fade, never fabricated intra-phrase karaoke timing."""
    if (type(frame) is not int or type(start) is not int
            or type(end) is not int or not 0 <= start <= frame < end):
        raise ValueError("Invalid PCM-synchronized phrase frame")
    n = end - start
    fade = min(5, max(1, n // 5))
    value = min(1., (frame-start+1)/fade, (end-frame)/fade)
    value = value * value * (3-2*value)
    return max(0, min(255, round(value*255)))


def paint_phrase_caption(canvas: Image.Image, text: str, *,
                         frame: int, start: int, end: int,
                         layout: dict | None = None) -> Image.Image:
    """Render a small frosted subtitle patch onto a real RGB portrait frame."""
    if (not isinstance(canvas, Image.Image) or canvas.mode != "RGB"
            or not _portrait_dimensions(canvas.width,canvas.height)):
        raise ValueError("Original caption requires a bounded 9:16 RGB frame")
    expected = caption_layout(text, width=canvas.width, height=canvas.height)
    # Validated reusable precomputed layout is optional; it may not silently
    # substitute a different phrase, omit words or escape the safe area.
    if layout is not None and layout != expected:
        raise ValueError("Caption cache is stale or belongs to another phrase")
    used = expected if layout is None else layout
    alpha = phrase_opacity(frame, start, end)
    if not alpha:
        return canvas
    w, h = used["panelWidth"], used["panelHeight"]
    x, y = used["x"], used["y"]
    plate = Image.new("RGBA", (w,h))
    painter = ImageDraw.Draw(plate)
    radius = max(5, round(canvas.width*.016))
    painter.rounded_rectangle(
        (0,0,w-1,h-1), radius=radius,
        fill=(3, 10, 22, round(alpha*.60)),
    )
    font = _font(used["fontSize"])
    for index, line in enumerate(used["lines"]):
        measured = font.getlength(line)
        left = round((w - measured)/2)
        top = used["paddingY"] + index*used["lineHeight"]
        stroke = max(1, round(canvas.width * .0028))
        painter.text(
            (left, top), line, font=font,
            fill=(251, 253, 255, alpha),
            stroke_width=stroke,
            stroke_fill=(4, 8, 17, round(alpha * .88)),
        )
    # Local alpha compositing avoids per-frame RGBA conversion of the whole
    # 1080x1920 image; the illustrated source remains unchanged outside box.
    section = canvas.crop((x,y,x+w,y+h)).convert("RGBA")
    section.alpha_composite(plate)
    canvas.paste(section.convert("RGB"), (x,y))
    return canvas
