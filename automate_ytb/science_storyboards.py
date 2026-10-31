"""Original explanatory motion storyboards for ocean-currents Shorts.

Five explicitly topic-matched diagrams replace repeated generic ocean plates.
All primitives are drawn locally at native portrait resolution, with continuous
frame-clock animation, no image APIs and no geographic or CFD simulation.
"""
from __future__ import annotations

import math
import re
import unicodedata

from PIL import ImageDraw

from .science_motion import _font

GOLD = (253, 192, 97, 255)
CYAN = (119, 225, 241, 255)
WHITE = (232, 248, 250, 255)
NAVY = (10, 38, 63, 242)
WARM = (252, 128, 75, 235)
COLD = (81, 167, 246, 225)

BEATS = ("solar", "wind", "coriolis", "sinking", "heat")
BADGES = {
    "solar": ("SOLAR HEATING", "ÉNERGIE SOLAIRE"),
    "wind": ("WIND FORCING", "VENTS DE SURFACE"),
    "coriolis": ("CORIOLIS EFFECT", "EFFET CORIOLIS"),
    "sinking": ("DENSITY & DEPTH", "DENSITÉ ET PROFONDEUR"),
    "heat": ("HEAT TRANSPORT", "TRANSPORT DE CHALEUR"),
}


def classify(topic: str, narration: str) -> str | None:
    """Opt in only for authored ocean-circulation explanations, never by shot index."""
    if not isinstance(topic, str) or not isinstance(narration, str):
        raise ValueError("Science beat matching requires authored text")
    def plain(value: str) -> str:
        value = unicodedata.normalize("NFKD", value.casefold())
        return "".join(c for c in value if not unicodedata.combining(c))
    subject = plain(topic)
    if not (re.search(r"\bocean currents?\b", subject)
            or re.search(r"\bcourants? oceaniques?\b", subject)):
        return None
    text = plain(narration)
    if re.search(r"\b(sun|sunlight|solar|soleil|ensoleillement)\b", text):
        return "solar"
    if re.search(r"\b(winds?|vents?|alizes)\b", text):
        return "wind"
    if re.search(r"\b(coriolis|gyres?|rotation|rotat|tourbillons?)\b", text):
        return "coriolis"
    if re.search(r"\b(sinks?|sinking|dense|density|salty|poles?|plonge|salinite|densite)\b", text):
        return "sinking"
    if re.search(r"\b(redistribut|transport|climate|climat|weather|chaleur|heat|energie)\b", text):
        return "heat"
    return None


def _label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str,
           *, color=WHITE, size: int = 36) -> None:
    draw.text(xy, value, font=_font(size, True), fill=color)


def _arrow(draw: ImageDraw.ImageDraw, a: tuple[float, float],
           b: tuple[float, float], color, width: int = 8) -> None:
    ax, ay = a
    bx, by = b
    vx, vy = bx-ax, by-ay
    length = math.hypot(vx, vy)
    if length < 2:
        return
    ux, uy = vx/length, vy/length
    draw.line((round(ax), round(ay), round(bx), round(by)),
              fill=color, width=width, joint="curve")
    back_x, back_y = bx-ux*21, by-uy*21
    sx, sy = -uy*10, ux*10
    draw.polygon(((round(bx), round(by)),
                  (round(back_x+sx), round(back_y+sy)),
                  (round(back_x-sx), round(back_y-sy))), fill=color)


def _marker(draw: ImageDraw.ImageDraw, x: float, y: float, color,
            radius: int = 7) -> None:
    x, y = round(x), round(y)
    draw.ellipse((x-radius-6, y-radius-6, x+radius+6, y+radius+6),
                 fill=(color[0], color[1], color[2], 58))
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)


def _solar(d: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    sun_x, sun_y = 312, 968
    for rad, alpha in ((183, 20), (151, 36), (121, 74)):
        d.ellipse((sun_x-rad, sun_y-rad, sun_x+rad, sun_y+rad),
                  fill=(248, 169, 73, alpha))
    d.ellipse((sun_x-93, sun_y-93, sun_x+93, sun_y+93),
              fill=(255, 192, 91, 255))
    for n in range(12):
        phi = n*math.tau/12+t*.35
        start = (sun_x+105*math.cos(phi), sun_y+105*math.sin(phi))
        end = (sun_x+135*math.cos(phi), sun_y+135*math.sin(phi))
        d.line((*start, *end), fill=(255, 204, 116, 215), width=6)
    # Latitude model rather than a false global insolation map.
    for y, color, title in (
        (795, COLD, "POLAR" if english else "POLAIRE"),
        (1015, WARM, "TROPICAL" if english else "TROPICAL"),
        (1235, COLD, "POLAR" if english else "POLAIRE"),
    ):
        d.rounded_rectangle((611, y, 915, y+145), radius=19,
                            fill=(color[0], color[1], color[2], 46),
                            outline=color, width=3)
        _label(d, (638, y+25), title, size=36)
        _label(d, (638, y+79), 
               ("WARM" if y==1015 else "COOL") if english else
               ("CHAUD" if y==1015 else "FROID"), color=color, size=42)
    for i, end_y in enumerate((868, 1086, 1306)):
        _arrow(d, (410, sun_y+(i-1)*19),
               (590, end_y), GOLD if i==1 else (172, 212, 236, 170), 5)
        _marker(d, 432+((t*53+i*97)%136), 
                sun_y+(i-1)*19+((end_y-(sun_y+(i-1)*19))*((t*53+i*97)%136)/158),
                GOLD if i==1 else CYAN, 5)
    _label(d, (165, 1401), "UNEQUAL HEATING" if english else "CHAUFFAGE INÉGAL",
           color=GOLD, size=40)


def _wind(d: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    # A moving wind field drives visible surface water underneath.
    d.rounded_rectangle((120, 800, 960, 1050), radius=38,
                        fill=(42, 78, 112, 85))
    for k in range(5):
        y = 840+k*42
        phase = t*(78+k*9)
        for j in range(3):
            x = (145+j*325+phase+k*43)%1020
            if 133 < x < 914:
                _arrow(d, (x-61, y+9*math.sin(t+k)),
                       (min(926, x+52), y+9*math.sin(t+k)),
                       CYAN if k%2 else WHITE, 5)
    d.line((130, 1101, 950, 1101), fill=(164, 234, 246, 220), width=8)
    for k in range(3):
        y = 1170 + 91*k
        d.line([(145+x, round(y+17*math.sin(x/83+t*.7+k)))
                for x in range(0, 785, 12)],
               fill=(69+k*25, 160+k*19, 222, 190), width=7)
        x = 190 + ((t*(39+k*8)+k*151)%660)
        _marker(d, x, y+17*math.sin((x-145)/83+t*.7+k), GOLD, 9)
        _arrow(d, (min(827,x-33), y+38), (min(905,x+53),y+38),
               (146, 227, 252, 202), 5)
    _label(d, (162, 742), "WIND" if english else "VENT", size=44)
    _label(d, (162, 1370), "SURFACE CURRENT" if english else "COURANT DE SURFACE",
           color=CYAN, size=39)


def _coriolis(d: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    cx, cy = 540, 1090
    d.ellipse((205, 755, 875, 1425), fill=(32, 92, 146, 90),
              outline=(84, 184, 213, 105), width=3)
    # Schematic rotating gyre: direction is illustrative, not hemisphere-specific.
    for r in (138, 212, 284):
        d.arc((cx-r, cy-r, cx+r, cy+r), 8, 350, fill=CYAN, width=5)
        for n in range(3):
            theta = .48*t+n*math.tau/3+r/120
            x, y = cx+r*math.cos(theta), cy+r*math.sin(theta)
            _marker(d, x, y, GOLD if r==212 else CYAN, 7)
            angle = theta + .20
            _arrow(d, (cx+r*math.cos(theta-.19), cy+r*math.sin(theta-.19)),
                   (cx+r*math.cos(angle), cy+r*math.sin(angle)),
                   GOLD if r==212 else WHITE, 5)
    d.ellipse((cx-62, cy-62, cx+62, cy+62),
              fill=(13, 47, 72, 245), outline=GOLD, width=5)
    _label(d, (cx-40, cy-19), "↻", color=GOLD, size=49)
    _label(d, (213, 1435), "CURVED PATH · SCHEMATIC" if english else "TRAJET COURBE · SCHÉMA",
           color=CYAN, size=34)


def _sinking(d: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    d.rounded_rectangle((130, 755, 950, 1376), radius=26,
                        fill=(20, 84, 133, 123))
    d.line((145, 901, 933, 901), fill=(175, 229, 246, 210), width=5)
    for y in (1040, 1177, 1315):
        d.line((160, y, 920, y), fill=(134, 205, 232, 60), width=2)
    # Orange surface advection toward cold latitudes.
    _arrow(d, (210, 965), (775, 965), WARM, 13)
    # Cold saline water sinks and returns along the deep layer.
    _arrow(d, (803, 1016), (803, 1276), COLD, 16)
    _arrow(d, (767, 1296), (242, 1296), CYAN, 11)
    phase = (t*.38)%1
    _marker(d, 220+535*phase, 965, WARM, 12)
    _marker(d, 803, 1016+245*phase, COLD, 12)
    _marker(d, 755-475*phase, 1296, CYAN, 9)
    # Stylized polar ice; no real-world polar location claim.
    d.polygon(((740, 895),(779, 840),(833, 895),(892, 895)),
              fill=(216, 241, 253, 210))
    _label(d, (160, 791), "SURFACE" if english else "SURFACE", size=36)
    _label(d, (161, 1214), "DEEP WATER" if english else "EAU PROFONDE",
           color=CYAN, size=36)
    _label(d, (514, 1378), "DENSE WATER SINKS" if english else "L'EAU DENSE PLONGE",
           color=COLD, size=36)


def _heat(d: ImageDraw.ImageDraw, t: float, english: bool) -> None:
    # Separate hot and cool reservoirs linked by actual animated transfer.
    for x, hue, text in ((170, WARM, "WARM" if english else "CHAUD"),
                         (695, COLD, "COOL" if english else "FROID")):
        d.rounded_rectangle((x, 860, x+220, 1130), radius=36,
                            fill=(hue[0], hue[1], hue[2], 60),
                            outline=hue, width=5)
        # A hue-colored caption on the same hue-colored filled card is invisible
        # in the final H.264 export. Use neutral text and retain the warm/cold
        # color as the meaningful background encoding.
        _label(d, (x+38, 982), text, color=WHITE, size=42)
    for lane in range(4):
        y = 1175+lane*55
        points = [(150+x, round(y+25*math.sin(x/83+t*.35+lane)))
                  for x in range(0, 788, 9)]
        d.line(points, fill=(113, 205, 244, 120+lane*24), width=5)
        u = (t*(55+lane*7)+lane*191)%755
        _marker(d, 150+u, y+25*math.sin(u/83+t*.35+lane),
                GOLD if lane%2 else CYAN, 9)
    _arrow(d, (408, 993), (675, 993), GOLD, 11)
    _label(d, (201, 753), "MOVING HEAT" if english else "CHALEUR EN MOUVEMENT",
           color=GOLD, size=44)
    _label(d, (195, 1426),
           "CLIMATE CONNECTIONS" if english else "LIENS CLIMATIQUES",
           color=CYAN, size=39)



# Script-specific conceptual waypoints, not generated or user-controlled facts.
# These are qualitative descriptions of the visual diagram, never claims of a
# numerical climate model. They live in the 43-pixel band between badge and art.
PROGRESSION = {
    "solar": (
        ("CAUSE · SUNLIGHT", "INPUT · LATITUDES", "RESULT · HEATING"),
        ("CAUSE · SOLEIL", "ÉCART · LATITUDES", "EFFET · CHALEUR")),
    "wind": (
        ("CAUSE · WIND", "TRANSFER · DRAG", "EFFECT · CURRENTS"),
        ("CAUSE · VENTS", "TRANSFERT · FRICTION", "EFFET · COURANTS")),
    "coriolis": (
        ("CAUSE · ROTATION", "EFFECT · DEFLECTION", "RESULT · GYRES"),
        ("CAUSE · ROTATION", "EFFET · DÉVIATION", "RÉSULTAT · GYRES")),
    "sinking": (
        ("CAUSE · COLD + SALT", "EFFECT · DENSITY", "RESULT · SINKING"),
        ("CAUSE · FROID + SEL", "EFFET · DENSITÉ", "RÉSULTAT · PLONGÉE")),
    "heat": (
        ("CAUSE · CURRENTS", "TRANSFER · HEAT", "EFFECT · CLIMATE"),
        ("CAUSE · COURANTS", "TRANSFERT · CHALEUR", "EFFET · CLIMAT")),
}


def _progress_ribbon(draw: ImageDraw.ImageDraw, beat: str,
                     progress: float, english: bool) -> None:
    """Show three authored causal stages, with continuous time-driven filling.

    The concise ribbon is outside the main 600..1490 illustration and the
    1522..1722 subtitle area, so it cannot conceal scientific explanation or
    any original subtitle. No per-frame textures, blurs, network calls or RNG.
    """
    if beat not in BEATS or not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Invalid storyboard progress")
    stage = min(2, int(3 * progress))
    steps = PROGRESSION[beat][0 if english else 1]
    draw.rounded_rectangle((80, 548, 1000, 595), radius=14,
                           fill=(8, 30, 53, 242),
                           outline=(86, 161, 197, 122), width=2)
    _label(draw, (104, 556), steps[stage], size=29)
    for index in range(3):
        left, top, width, height = 686 + index * 100, 572, 82, 7
        draw.rounded_rectangle((left, top, left + width, top + height),
                               radius=3, fill=(46, 77, 104, 255))
        fraction = min(1.0, max(0.0, 3 * progress - index))
        painted = round(width * fraction)
        if painted >= 2:
            draw.rounded_rectangle((left, top, left + painted, top + height),
                                   radius=3, fill=GOLD if index == stage else CYAN)
    # A moving point makes progress continuous even while the text holds.
    marker_x = 686 + round(282 * progress)
    draw.ellipse((marker_x - 4, 567, marker_x + 4, 575), fill=GOLD)

def draw_storyboard(draw: ImageDraw.ImageDraw, beat: str,
                    t: float, english: bool, *,
                    duration: float | None = None) -> None:
    """Draw native educational motion; optionally show real-time causal progression."""
    if (beat not in BEATS or type(t) not in (int, float)
            or not math.isfinite(t) or t < 0 or type(english) is not bool):
        raise ValueError("Invalid ocean storyboard animation")
    if duration is not None and (
            type(duration) not in (int, float) or not math.isfinite(duration)
            or not 0 < duration <= 180 or t > duration):
        raise ValueError("Invalid storyboard duration")
    if duration is not None:
        _progress_ribbon(draw, beat, t / duration, english)
    draw.rounded_rectangle((80, 600, 1000, 1490), radius=40,
                           fill=NAVY, outline=(97, 176, 210, 124), width=3)
    for x in range(140, 990, 105):
        draw.line((x, 620, x, 1470), fill=(71, 123, 164, 32), width=1)
    for y in range(750, 1460, 105):
        draw.line((112, y, 972, y), fill=(71, 123, 164, 32), width=1)
    if beat == "solar":
        _solar(draw, t, english)
    elif beat == "wind":
        _wind(draw, t, english)
    elif beat == "coriolis":
        _coriolis(draw, t, english)
    elif beat == "sinking":
        _sinking(draw, t, english)
    elif beat == "heat":
        _heat(draw, t, english)
    _label(draw, (115, 620),
           "SCHEMATIC · NOT TO SCALE" if english else "SCHÉMA · HORS ÉCHELLE",
           color=(158, 195, 211, 225), size=29)
