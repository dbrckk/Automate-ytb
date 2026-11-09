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
from .science_audio_cues import audio_event_fraction
from .science_ocean_depth import draw_depth
from .science_blender_aurora import stage_from_environment as aurora_blender_from_environment
from .science_blender_3d import stage_from_environment
from .captions import timed_cues_for_scene
from .science_storyboards import classify as classify_storyboard, draw_storyboard, BADGES as STORYBOARD_BADGES
from .science_rainbow import (classify as classify_rainbow, draw_rainbow,
                              daylight_background, BADGES as RAINBOW_BADGES)
from .science_lightning import (classify as classify_lightning, draw_lightning,
                                supports_topic as supports_lightning,
                                storm_background, BADGES as LIGHTNING_BADGES)
from .lightning_editorial25d import render_lightning_editorial
from .science_aurora import (classify as classify_aurora, draw_aurora,
                            supports_topic as supports_aurora,
                            portrait_background as aurora_background,
                            BADGES as AURORA_BADGES)
from .science_volcano import (classify as classify_volcano, draw_volcano,
                              supports_topic as supports_volcano,
                              portrait_background as volcano_background,
                              BADGES as VOLCANO_BADGES)

from .science_earth_stop import (classify as classify_earth_stop,
                                 draw as draw_earth_stop, LABELS as EARTH_STOP_LABELS)

PORTRAIT_SIZE = (1080, 1920)
PORTRAIT_VERSION = "original-science-shorts-v20-1080x1920-lossless-text-fluid-planet-ocean-flow-kinetic-volcano-magma-pressure-causal-camera-v21-ocean-phrase-driven-causal-interactions-depth-v1-blender-cycles-opt-in-v1-aurora3d-v1-motion-heldout-v1"
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
        is_lightning = supports_lightning(topic)
        is_aurora = supports_aurora(topic)
        is_volcano = supports_volcano(topic)
        if not (is_earth or is_rainbow or is_lightning or is_aurora or is_volcano):
            raise ValueError("Science Shorts require a supported Earth/ocean, rainbow, lightning, aurora or volcano topic")
        if type(scene_index) is not int or not 1 <= scene_index <= 1200:
            raise ValueError("Invalid science scene index")
        self.topic, self.narration, self.scene_index = topic, narration, scene_index
        self.mode = scene_mode(narration)
        self.beat = classify_storyboard(topic, narration)
        self._blender_stage = stage_from_environment() if self.beat is not None else None
        self.rainbow_beat = classify_rainbow(topic, narration)
        self.lightning_beat = classify_lightning(topic, narration)
        self.aurora_beat = classify_aurora(topic, narration)
        self._aurora_stage = (aurora_blender_from_environment()
                              if self.aurora_beat is not None else None)
        self.volcano_beat = classify_volcano(topic, narration)
        self.earth_stop_beat = classify_earth_stop(topic, narration)
        if is_lightning and self.lightning_beat is None:
            raise ValueError(
                "Lightning Shorts require authored charge, leader, upward "
                "connection, return stroke or thunder narration")
        if is_aurora and self.aurora_beat is None:
            raise ValueError("Aurora Shorts need authored solar wind, magnetic field, collisions, emission or curtains")
        if is_volcano and self.volcano_beat is None:
            raise ValueError("Volcano Shorts need authored magma, pressure, ascent, eruption or lava")
        if is_rainbow and self.rainbow_beat is None:
            raise ValueError(
                "Rainbow Shorts need authored narration on sunlight, refraction, "
                "internal reflection, emerging light or the observed arc")
        self.english = bool(re.search(
            r"\b(the|what|earth|would|could|ocean|oceans|wind|winds|"
            r"because|sunlight|waters|heats|currents|sinks|gyres|climate|"
            r"sun|white|colors|light|raindrop|rainbow|reflects|"
            r"lightning|electric|charge|thunder|cloud|storm|leader|"
            r"sun|solar|magnetic|field|particles|nitrogen|oxygen|aurora|"
            r"northern|southern|curtains|glowing|"
            r"volcano|volcanic|magma|lava|pressure|gas|rocks|ash|erupt|cracks|"
            r"entering|refracts|leaving|millions|observer|arc)\b",
            narration, flags=re.IGNORECASE)) or bool(
                is_lightning and re.search(
                    r"\b(how|why|lightning|thunderstorm|thunderstorms)\b",
                    topic, flags=re.IGNORECASE))
        seed = int.from_bytes(hashlib.sha256(
            f"{topic}|{scene_index}|portrait".encode()).digest()[:8], "big")
        self.base = (storm_background() if is_lightning else
                     aurora_background() if is_aurora else
                     volcano_background() if is_volcano else
                     daylight_background(seed) if is_rainbow else _sky(seed))
        self._globes: dict[tuple[int, int], Image.Image] = {}
        self.scene_start_ms = scene_start_ms
        self.caption_segments = caption_segments
        # Reuse PCM-derived *phrase* boundaries for the physical camera beat.
        # No word timing is invented; scenes lacking a cue keep authored timing.
        domain=("lightning" if self.lightning_beat is not None else
                "volcano" if self.volcano_beat is not None else
                "aurora" if self.aurora_beat is not None else
                "ocean" if self.beat is not None else None)
        action=(self.lightning_beat if domain=="lightning" else
                self.volcano_beat if domain=="volcano" else
                self.aurora_beat if domain=="aurora" else
                self.beat if domain=="ocean" else None)
        self._narrated_event_fraction=(
            audio_event_fraction(domain,action,caption_segments,scene_start_ms)
            if domain is not None else None)
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
        title, title_size = self._title_layout
        badges = {
            "orbital": ("EARTH IN MOTION", "LA TERRE EN MOUVEMENT"),
            "daylight": ("DAY AND NIGHT", "JOUR ET NUIT"),
            "ocean": ("OCEAN CURRENTS", "MOUVEMENTS DES OCÉANS"),
            "atmosphere": ("ATMOSPHERE", "ATMOSPHÈRE"),
        }
        science_badge = (
            EARTH_STOP_LABELS[self.earth_stop_beat] if self.earth_stop_beat
            else LIGHTNING_BADGES[self.lightning_beat] if self.lightning_beat
            else AURORA_BADGES[self.aurora_beat] if self.aurora_beat
            else VOLCANO_BADGES[self.volcano_beat] if self.volcano_beat
            else RAINBOW_BADGES[self.rainbow_beat] if self.rainbow_beat
            else STORYBOARD_BADGES[self.beat] if self.beat
            else badges[self.mode])
        if self.lightning_beat is not None:
            # P4.9: an original, briefly visible opening hook followed by a
            # small physical-action heading. The episode title no longer
            # sits above every cinematic shot like a PowerPoint slide.
            render_lightning_editorial(
                picture,beat=self.lightning_beat,
                scene_index=self.scene_index,t=t,duration=duration,
                english=self.english,title_lines=title,
                title_size=title_size)
        elif self.aurora_beat is not None or self.volcano_beat is not None:
            # Preserve the separately validated Aurora/Volcano typography.
            # UI is drawn *after* the moving camera for stable readability.
            header = Image.new("RGBA", picture.size)
            ui = ImageDraw.Draw(header)
            ui.rounded_rectangle((61, 109, 1019, 243), radius=25,
                                 fill=(4, 15, 30, 163),
                                 outline=(121, 185, 214, 92), width=2)
            for i, row in enumerate(title):
                ui.text((91, 130 + 51*i), row,
                        font=_font(title_size, bold=True), fill=INK)
            ui.rounded_rectangle((70, 265, 793, 319), radius=18,
                                 fill=(10, 38, 58, 156))
            ui.text((99, 273), science_badge[0 if self.english else 1],
                    font=_font(31, bold=True), fill=GOLD+(255,))
            beat_number = (list(AURORA_BADGES).index(self.aurora_beat)
                           if self.aurora_beat is not None else
                           list(VOLCANO_BADGES).index(self.volcano_beat))
            ui.line((75, 327, 1005, 327), fill=(128, 177, 199, 89), width=3)
            ui.line((75, 327, 75 + 930*(beat_number+1)//5, 327),
                    fill=(143, 225, 248, 204), width=4)
            picture.alpha_composite(header)
        # Compact subtitle excerpt in a dedicated lower-middle safe band.
        # Resolve speech-synthesized cues before drawing, not guessed timing.
        active_text = self.active_caption(t, duration)
        summary, summary_size = self._caption_layouts[active_text]
        if (self.lightning_beat is not None or self.aurora_beat is not None
                or self.volcano_beat is not None):
            captions = Image.new("RGBA", picture.size)
            cd = ImageDraw.Draw(captions)
            cd.rounded_rectangle((65, 1586, 1015, 1782), radius=24,
                                 fill=(4, 14, 30, 211),
                                 outline=(110, 187, 218, 94), width=2)
            for i, line in enumerate(summary):
                cd.text((108, 1619 + 47*i), line,
                        font=_font(summary_size, True), fill=INK)
            picture.alpha_composite(captions)
        else:
            d.rounded_rectangle((65, 1522, 1015, 1722), radius=31,
                                fill=(5, 17, 37, 240),
                                outline=(84, 165, 190, 150), width=2)
            for i, line in enumerate(summary):
                d.text((111, 1551 + 46*i), line,
                       font=_font(summary_size, True), fill=INK)
        return picture.convert("RGB")
