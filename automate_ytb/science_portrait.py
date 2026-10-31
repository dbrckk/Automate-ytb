"""Native 9:16 original science motion graphics, designed for mobile Shorts.

Not a 16:9 crop or an external asset; all 1080x1920 pixels are drawn locally.
Narration is editorial material, not independently fact-checked physics.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
import math
from pathlib import Path
import random
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter

from .science_motion import _font, _planet, scene_mode, GOLD, CYAN
from .captions import timed_cues_for_scene
from .science_storyboards import classify as classify_storyboard, draw_storyboard, BADGES as STORYBOARD_BADGES
from .science_rainbow import (classify as classify_rainbow, draw_rainbow,
                              daylight_background, BADGES as RAINBOW_BADGES)

from .science_earth_stop import (classify as classify_earth_stop,
                                 draw as draw_earth_stop, LABELS as EARTH_STOP_LABELS)

PORTRAIT_SIZE = (1080, 1920)
PORTRAIT_VERSION = "original-science-shorts-v9-causal-earth-stop-scenes-native-portrait"
INK = (238, 247, 250, 255)


@lru_cache(maxsize=512)
def _fit_lines(content: str, *, size: int, width: int,
               maximum: int, minimum: int) -> tuple[tuple[str, ...], int]:
    """Fit *every* authored glyph in a mobile-safe area without truncation.

    The SRT continues to contain the exact source phrase. Reducing text size
    and wrapping oversized words are preferable to silently omitting facts.
    Unreadable input fails the render instead of fabricating an ellipsis.
    """
    if not 1 <= minimum <= size <= 80 or not 1 <= maximum <= 4 or width <= 0:
        raise ValueError("Unsafe portrait text layout dimensions")
    words = content.split()
    if not words:
        return (), size
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for font_size in range(size, minimum - 1, -1):
        font = _font(font_size, bold=True)
        lines: list[str] = []
        row = ""
        for word in words:
            if probe.textbbox((0, 0), word, font=font)[2] > width:
                # Preserve the full spelling of long URLs/technical terms:
                # split into visual runs without dropping any characters.
                if row:
                    lines.append(row)
                    row = ""
                chunk = ""
                for char in word:
                    candidate = chunk + char
                    if chunk and probe.textbbox(
                            (0, 0), candidate, font=font)[2] > width:
                        lines.append(chunk)
                        chunk = char
                    else:
                        chunk = candidate
                row = chunk
            else:
                candidate = (row + " " + word).strip()
                if row and probe.textbbox(
                        (0, 0), candidate, font=font)[2] > width:
                    lines.append(row)
                    row = word
                else:
                    row = candidate
            if len(lines) >= maximum:
                break
        if row:
            lines.append(row)
        if len(lines) <= maximum and all(
                probe.textbbox((0, 0), line, font=font)[2] <= width
                for line in lines):
            # Prohibit clipping even when the input contains unusually wide
            # Unicode glyphs: every source codepoint must be displayed.
            original = "".join(words)
            actual = "".join(line.replace(" ", "") for line in lines)
            if actual == original:
                return tuple(lines), font_size
    raise ValueError(
        "Original portrait text cannot fit safely; shorten the title "
        "or split the narration into smaller authored phrases")


def _sky(seed: int) -> Image.Image:
    w, h = PORTRAIT_SIZE
    rng = random.Random(seed)
    plate = Image.new("RGBA", PORTRAIT_SIZE)
    d = ImageDraw.Draw(plate)
    for y in range(h):
        frac = y / h
        d.line((0, y, w, y),
               fill=(7 + round(11*frac), 21 + round(18*frac),
                     47 + round(31*frac), 255))
    for _ in range(510):
        x, y = rng.randrange(24, w - 24), rng.randrange(50, 1770)
        r = rng.choice((1, 1, 1, 2, 2, 3))
        b = rng.randrange(125, 230)
        d.ellipse((x-r, y-r, x+r, y+r), fill=(b//2, b-18, b, 178))
    glow = Image.new("RGBA", PORTRAIT_SIZE)
    ImageDraw.Draw(glow).ellipse(
        (0, 425, 1080, 1505), fill=(42, 158, 220, 56))
    return Image.alpha_composite(
        plate, glow.filter(ImageFilter.GaussianBlur(126)))


def _ocean_currents(draw: ImageDraw.ImageDraw, t: float) -> None:
    """Original layered 2D currents and eddies, animated by the frame clock.

    This is an illustrative flow field, not a geographic or fluid-dynamics
    prediction. All paths stay inside the 9:16 visual band (y=900..1460).
    No downloaded textures, model inference or pseudorandom frame jitter.
    """
    # Independent streams drift at different speeds and depths. Each glowing
    # tracer has a short curved tail and moving arrow tip, not a static row of
    # particles disguised as fluid motion.
    for lane in range(3):
        baseline = 1033 + lane * 164
        speed = (34, 49, 62)[lane]
        for index in range(10):
            x = (index * 153 + t * speed + lane * 53) % 1350 - 135
            path = []
            for segment in range(10):
                xx = x - segment * 8
                yy = baseline + 15 * math.sin(xx / 124 + lane * .9 + t * .36)
                path.append((round(xx), round(yy)))
            # A wide blue trail under the bright narrow trace; computed
            # analytically for each frame with no pose snapping.
            draw.line(path, fill=(36, 151, 216, 95), width=9, joint="curve")
            draw.line(path[:7], fill=(167, 234, 252, 187), width=3,
                      joint="curve")
            px, py = path[0]
            draw.ellipse((px-4, py-4, px+4, py+4),
                         fill=(241, 253, 255, 215))
            draw.polygon([(px+4, py), (px-10, py-6), (px-10, py+6)],
                         fill=(244, 209, 116, 205))
    # Offset eddies make the central regions read as directed circulation,
    # rather than five parallel scrolling wave textures.
    for idx, (cx, cy, rx, ry) in enumerate(
            ((335, 1150, 93, 64), (750, 1343, 104, 69))):
        spin = round(t * (24 if idx == 0 else -21)) % 360
        for ring in range(2):
            inset = ring * 18
            draw.arc((cx-rx+inset, cy-ry+inset, cx+rx-inset,
                      cy+ry-inset), spin + ring*87,
                     spin + ring*87 + 191,
                     fill=(141, 232, 249, 177-ring*40), width=4)
        theta = math.radians(spin + 190)
        px = round(cx + rx * math.cos(theta))
        py = round(cy + ry * math.sin(theta))
        draw.ellipse((px-5, py-5, px+5, py+5),
                     fill=(255, 205, 99, 225))


class PortraitScienceScene:
    """Dedicated safe-area composition independent of landscape coordinates."""
    def __init__(self, *, topic: str, narration: str, scene_index: int,
                 caption_segments: list[dict] | None = None,
                 scene_start_ms: int = 0):
        if (type(scene_start_ms) is not int or not 0 <= scene_start_ms <= 3_600_000):
            raise ValueError("Unsafe science caption scene start")
        if caption_segments is not None and not isinstance(caption_segments, list):
            raise ValueError("Invalid audio caption markers")
        if not isinstance(topic, str) or not 1 <= len(topic.strip()) <= 180:
            raise ValueError("Science Shorts require an authored topic")
        if not isinstance(narration, str) or not 1 <= len(narration.strip()) <= 9000:
            raise ValueError("Science Shorts require authored narration")
        folded = unicodedata.normalize("NFKD", topic.casefold())
        folded = "".join(c for c in folded if not unicodedata.combining(c))
        is_earth = bool(re.search(r"\b(earth|terre|oceans?|oceanique)\b", folded))
        is_rainbow = bool(re.search(r"\b(rainbows?|arcs?[- ]en[- ]ciel)\b", folded))
        if not (is_earth or is_rainbow):
            raise ValueError("Science Shorts support Earth/ocean or authored rainbow topics only")
        if type(scene_index) is not int or not 1 <= scene_index <= 1200:
            raise ValueError("Invalid science scene index")
        self.topic, self.narration, self.scene_index = topic, narration, scene_index
        self.mode = scene_mode(narration)
        self.beat = classify_storyboard(topic, narration)
        self.rainbow_beat = classify_rainbow(topic, narration)
        self.earth_stop_beat = classify_earth_stop(topic, narration)
        if is_rainbow and self.rainbow_beat is None:
            raise ValueError(
                "Rainbow Shorts need authored narration on sunlight, refraction, "
                "internal reflection, emerging light or the observed arc")
        self.english = bool(re.search(
            r"\b(the|what|earth|would|could|ocean|oceans|wind|winds|"
            r"because|sunlight|waters|heats|currents|sinks|gyres|climate|"
            r"sun|white|colors|light|raindrop|rainbow|reflects|"
            r"entering|refracts|leaving|millions|observer|arc)\b",
            narration, flags=re.IGNORECASE))
        seed = int.from_bytes(hashlib.sha256(
            f"{topic}|{scene_index}|portrait".encode()).digest()[:8], "big")
        self.base = daylight_background(seed) if is_rainbow else _sky(seed)
        self._globes: dict[tuple[int, int], Image.Image] = {}
        self.scene_start_ms = scene_start_ms
        self.caption_segments = caption_segments
        self._caption_duration_ms: int | None = None
        self._caption_cues: list[dict] = []
        self._caption_layouts: dict[str, tuple[tuple[str, ...], int]] = {}
        self._title_layout = _fit_lines(
            self.topic, size=47, width=860, maximum=2, minimum=22)

    def active_caption(self, t: float, duration: float) -> str:
        """Return the exact phrase selected by the same timing as the SRT.

        With narration, boundaries are measured at synth-phrase level, not
        guessed per word. Silent previews use the existing estimated SRT
        timings and remain clearly identified as estimates.
        """
        if (not isinstance(t, (int, float)) or
                not isinstance(duration, (int, float)) or
                not math.isfinite(t) or not math.isfinite(duration) or
                not 0 <= t <= duration <= 180):
            raise ValueError("Unsafe portrait caption clock")
        duration_ms = round(duration * 1000)
        if duration_ms != self._caption_duration_ms:
            item = {
                "narration": self.narration,
                "startMs": self.scene_start_ms,
                "endMs": self.scene_start_ms + duration_ms,
            }
            if self.caption_segments is not None:
                item["captionSegments"] = self.caption_segments
            cues = timed_cues_for_scene(
                item, use_audio_boundaries=self.caption_segments is not None)
            # Validate every caption before FFmpeg gets past the first frame.
            # An unusually long phrase must fail rather than disappear from
            # a later part of a video after minutes of expensive encoding.
            layouts = {cue["text"]: _fit_lines(
                cue["text"], size=40, width=842, maximum=3, minimum=22)
                for cue in cues}
            self._caption_cues = cues
            self._caption_layouts = layouts
            self._caption_duration_ms = duration_ms
        when = self.scene_start_ms + round(t * 1000)
        for cue in self._caption_cues:
            if cue["startMs"] <= when < cue["endMs"]:
                return cue["text"]
        # An endpoint frame may land precisely at the scene's final ms.
        return self._caption_cues[-1]["text"]

    def _planet_pose(self, step: int, size: int) -> Image.Image:
        """Cache six independent projected Earth orientations by pose and size."""
        key = (step, size)
        if key not in self._globes:
            if len(self._globes) >= 6:
                del self._globes[next(iter(self._globes))]
            self._globes[key] = _planet(size=size, yaw=(step*.027) % math.tau)
        return self._globes[key]

    def _planet_at(self, t: float, *, size: int = 680) -> Image.Image:
        """Interpolate native Earth poses for smooth per-frame 30fps motion.

        Only two adjacent projected globes are blended: expensive original
        projections remain sampled at 2.5Hz, without a full re-render at
        30fps. This is a cinematic interpolation, not a physical simulation.
        """
        if (not isinstance(t, (int, float)) or not math.isfinite(t)
                or t < 0 or type(size) is not int or not 32 <= size <= 1080):
            raise ValueError("Unsafe planet interpolation parameters")
        progress = t * 2.5
        step = int(progress)
        fraction = progress - step
        first = self._planet_pose(step, size)
        if fraction < 1e-10:
            return first
        second = self._planet_pose(step + 1, size)
        return Image.blend(first, second, fraction)

    def frame(self, t: float, duration: float) -> Image.Image:
        if not isinstance(t, (float, int)) or not isinstance(duration, (float, int)):
            raise ValueError("Invalid portrait animation clock")
        if not math.isfinite(t) or not math.isfinite(duration) or not 0 <= t <= duration <= 180:
            raise ValueError("Unsafe portrait animation clock")
        picture = self.base.copy()
        d = ImageDraw.Draw(picture, "RGBA")
        # Explicit mobile-safe composition: keep title below top UI and
        # captions above the lower controls. Never crop original content.
        d.rounded_rectangle((55, 190, 1025, 407), radius=34,
                            fill=(7, 20, 41, 232), outline=CYAN+(125,), width=3)
        title, title_size = self._title_layout
        for i, row in enumerate(title):
            d.text((104, 234 + 68*i), row,
                   font=_font(title_size, bold=True), fill=INK)
        badges = {
            "orbital": ("EARTH IN MOTION", "LA TERRE EN MOUVEMENT"),
            "daylight": ("DAY AND NIGHT", "JOUR ET NUIT"),
            "ocean": ("OCEAN CURRENTS", "MOUVEMENTS DES OCÉANS"),
            "atmosphere": ("ATMOSPHERE", "ATMOSPHÈRE"),
        }
        d.rounded_rectangle((80, 477, 750, 537), radius=22,
                            fill=(12, 47, 72, 234))
        science_badge = (
            EARTH_STOP_LABELS[self.earth_stop_beat] if self.earth_stop_beat
            else RAINBOW_BADGES[self.rainbow_beat] if self.rainbow_beat
            else STORYBOARD_BADGES[self.beat] if self.beat
            else badges[self.mode])
        d.text((113, 488), science_badge[0 if self.english else 1],
               font=_font(36, bold=True), fill=GOLD+(255,))
        if self.earth_stop_beat is not None:
            draw_earth_stop(picture, self.earth_stop_beat, t, duration,
                            self.english, self._planet_at)
            d = ImageDraw.Draw(picture, "RGBA")
        elif self.rainbow_beat is not None:
            draw_rainbow(d, self.rainbow_beat, t, duration, self.english)
        elif self.beat is not None:
            draw_storyboard(d, self.beat, t, self.english, duration=duration)
        elif self.mode in ("orbital", "daylight"):
            globe = self._planet_at(t)
            center_x = 540 + round(16 * math.sin(t*.32))
            center_y = 955 + round(12 * math.sin(t*.40))
            top_left = (center_x - globe.width//2, center_y - globe.height//2)
            picture.alpha_composite(globe, top_left)
            d = ImageDraw.Draw(picture, "RGBA")
            if self.mode == "orbital":
                for rad in (386, 409):
                    advance = round(12*t)
                    d.arc((center_x-rad, center_y-rad,
                           center_x+rad, center_y+rad),
                          32+advance, 245+advance, fill=CYAN+(140,),
                          width=3)
                for i in range(9):
                    angle = i*math.tau/9 + .27*t
                    x = center_x + round(397*math.cos(angle))
                    y = center_y + round(397*math.sin(angle))
                    d.ellipse((x-4, y-4, x+4, y+4), fill=GOLD+(235,))
            else:
                radius = 340
                # Stylized terminator; schematic lighting, never presented
                # as a scientific simulation of the Earth-Sun geometry.
                d.pieslice((center_x-radius, center_y-radius,
                            center_x+radius, center_y+radius),
                           270, 90, fill=(7, 14, 31, 86))
                d.rounded_rectangle((101, 1350, 520, 1426), radius=19,
                                    fill=(15, 52, 75, 239))
                d.rounded_rectangle((557, 1350, 974, 1426), radius=19,
                                    fill=(7, 21, 42, 239))
                d.text((132, 1367), "DAY" if self.english else "JOUR",
                       font=_font(36, True), fill=GOLD+(255,))
                d.text((593, 1367), "NIGHT" if self.english else "NUIT",
                       font=_font(36, True), fill=CYAN+(255,))
        elif self.mode == "atmosphere":
            # Large independent cloud masses and moving current lines.
            for i, (cx, cy, radius) in enumerate(
                    ((243, 781, 117), (654, 941, 172), (382, 1202, 137))):
                dx = round(28*math.sin(t*(.38+i*.14)+i))
                d.ellipse((cx-radius+dx, cy-radius//2,
                           cx+radius+dx, cy+radius//2),
                          fill=(89+i*14, 153+i*10, 181+i*7, 177))
                d.ellipse((cx-55+dx, cy-radius, cx+104+dx, cy+radius//2),
                          fill=(139, 196, 220, 144))
            for i in range(15):
                y = 698 + i*44
                x = (i*118 + t*(64+i%3*17))%1190 - 95
                d.arc((x, y-55, x+230, y+34), 178, 353,
                      fill=CYAN+(165,), width=5)
                d.polygon([(x+211, y-18), (x+232, y-11),
                           (x+207, y+1)], fill=GOLD+(182,))
        else:
            # Full-width independently moving wave sheets; no horizontal crop.
            d.ellipse((117, 640, 963, 1470), fill=(27, 96, 136, 90))
            waves = [
                ((31, 110, 169, 218), 31, .72, 931),
                ((51, 169, 206, 227), 40, .84, 1075),
                ((24, 108, 174, 238), 34, 1.04, 1242),
                ((15, 80, 147, 246), 27, 1.24, 1405),
            ]
            for i, (color, amp, speed, baseline) in enumerate(waves):
                points = [(0, 1510)]
                for x in range(0, 1081, 9):
                    y = baseline + amp * math.sin(x / 152 + speed*t + i*.62)
                    points.append((x, round(y)))
                points.append((1080, 1510))
                d.polygon(points, fill=color)
                d.line(points[1:-1], fill=(188, 240, 248, 127), width=3)
            for i in range(20):
                x = round((i*113+t*29)%1010)+35
                y = 810+(i*67)%590
                d.ellipse((x-2, y-2, x+2, y+2),
                          fill=(215, 241, 249, 170))
            _ocean_currents(d, t)
        # Compact subtitle excerpt in a dedicated lower-middle safe band.
        d.rounded_rectangle((65, 1522, 1015, 1722), radius=31,
                            fill=(5, 17, 37, 240),
                            outline=(84, 165, 190, 150), width=2)
        # Resolve the active phrase first: this lazily validates and fills
        # _caption_layouts. Evaluating the dict before active_caption() would
        # hold a stale empty reference on the first video frame.
        active_text = self.active_caption(t, duration)
        summary, summary_size = self._caption_layouts[active_text]
        for i, line in enumerate(summary):
            d.text((111, 1551 + 46*i), line,
                   font=_font(summary_size, True), fill=INK)
        return picture.convert("RGB")
