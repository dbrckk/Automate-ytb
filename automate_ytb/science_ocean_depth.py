"""Layered cinematic color and moving underwater depth for ocean storyboards.

Original CPU-rendered illustration, not photography, CFD, or geographic data.
The static lighting plate is cached per semantic scene. Only a small number of
light traces/particles move per frame, maintaining practical 30 FPS export cost.
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageDraw, ImageFilter, ImageChops
from .organic_environment25d import (
    terrain_strata, water_caustics,
)
from .material_ribbons25d import draw_material_ribbon
from .world_volume25d import world_volume_alpha

VERSION = "ocean-depth-v2-open-feathered-underwater-world"
SIZE = (920, 890)
ORIGIN = (80, 600)
# Unique color stories instead of recoloring the same stock background.
PALETTES = {
    "solar": ((21, 63, 83), (8, 32, 70), (255, 192, 108)),
    "wind": ((24, 101, 118), (8, 39, 78), (146, 241, 234)),
    "coriolis": ((48, 62, 121), (13, 20, 60), (166, 173, 255)),
    "sinking": ((38, 100, 140), (7, 19, 60), (147, 218, 255)),
    "heat": ((87, 62, 67), (10, 55, 88), (255, 176, 106)),
}


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


@lru_cache(maxsize=5)
def lighting_plate(beat: str) -> Image.Image:
    """Opaque rounded scenic panel with full-resolution gradients and hazy light."""
    if beat not in PALETTES:
        raise ValueError("Unknown illustrated ocean action")
    w, h = SIZE
    top, bottom, highlight = PALETTES[beat]
    panel = Image.new("RGBA", SIZE)
    d = ImageDraw.Draw(panel)
    for y in range(h):
        q = y / (h - 1)
        # Accelerating depth darkening, retaining a bright surface layer.
        depth = q * q * (3 - 2*q)
        rgb = tuple(_lerp(top[i], bottom[i], depth) for i in range(3))
        d.line((0, y, w, y), fill=(*rgb, 255), width=1)
    # Broad and diffuse physical-looking glow, NOT a solid spot or bitmap.
    light = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    ld = ImageDraw.Draw(light)
    source_x = 180 if beat in ("solar", "heat") else 640 if beat == "sinking" else 460
    for i, (rad, alpha) in enumerate(((230, 39), (155, 34), (86, 40))):
        ld.ellipse((source_x-rad, 135-rad, source_x+rad, 135+rad),
                   fill=(*highlight, alpha))
    # A second illuminated pool separates mid-ground from deeper silhouette.
    ld.ellipse((420, 320, 1130, 790), fill=(*highlight, 18))
    panel = Image.alpha_composite(panel, light.filter(ImageFilter.GaussianBlur(46)))
    d = ImageDraw.Draw(panel, "RGBA")
    # Actual original organic seafloor and refracted light paths, not
    # a repeated five-point underwater triangle or a generic dark panel.
    # Original material plates are cached across all subsequent 30fps frames.
    identity=list(PALETTES).index(beat)
    panel.alpha_composite(terrain_strata(
        (920,470),seed=24109+identity*613,
        color=(26,53,68),opacity=192),(0,420))
    panel.alpha_composite(water_caustics(
        SIZE,seed=35119+identity*517,
        color=highlight,opacity=44))
    d=ImageDraw.Draw(panel,"RGBA")
    for layer in range(5):
        y = 115 + layer*138
        for side in range(7):
            x = 39 + side*147 + ((layer*53) % 87)
            d.line((x, y, min(w-25, x+60), y-13),
                   fill=(*highlight, max(9, 35-layer*5)), width=2)
    # The entire source world now fades organically into the already
    # established underwater atmosphere, rather than a large rectangular
    # slideshow panel with short 85px edge feathering.
    panel.putalpha(world_volume_alpha(
        SIZE,kind="water",seed=51803+identity*271))
    return panel


def draw_depth(canvas: Image.Image, beat: str, *,
               t: float, duration: float) -> None:
    """Composite cached 920x890 scene with modest continuous parallax lighting.

    Never enters the title (y<600), the caption area (y>=1522) or the
    horizontal mobile-safe margins.
    """
    if (canvas.mode != "RGBA" or canvas.size != (1080, 1920)
            or beat not in PALETTES or type(t) not in (int, float)
            or type(duration) not in (int, float)
            or not math.isfinite(t) or not math.isfinite(duration)
            or not 0 < duration <= 180 or not 0 <= t <= duration):
        raise ValueError("Unsupported ocean depth canvas or animation clock")
    plate=lighting_plate(beat)
    canvas.alpha_composite(plate, ORIGIN)
    # All dynamic ribbons, particles and sources are drawn inside the same
    # 920x890 physical volume. Clipping them to its original alpha avoids
    # sharp floating chart lines extending beyond diffuse material edges.
    moving=Image.new("RGBA",SIZE)
    d = ImageDraw.Draw(moving, "RGBA")
    _, _, color = PALETTES[beat]
    # Four translucent wave traces at different depths/speeds; their phase
    # changes smoothly instead of swapping static image backgrounds.
    for layer in range(4):
        y = 720 + 176*layer
        amplitude = 13 + layer*4
        speed = .25 + layer*.065
        phase = (layer*1.71 + speed*t)
        pts = []
        for x in range(118, 969, 22):
            delta = amplitude*math.sin(x/125 + phase)
            delta += 4*math.sin(x/59 - phase*.72)
            pts.append((x-ORIGIN[0], round(y + delta)-ORIGIN[1]))
        # Same original 2.5D light-path material system as optical rays and
        # molten rivers, but with a water-specific cool underside and moving
        # curved highlight following the real authored current trajectory.
        draw_material_ribbon(
            d,pts,material="water",
            color=(*color,max(18,70-layer*11)),
            width=max(2,5-layer),
            progress=(t*(.085+layer*.014)+layer*.21)%1.)
    # Independent suspended matter adds natural depth without expensive noise
    # or random variation between reruns. Coordinates never leave the panel.
    for particle in range(24):
        depth = particle % 4
        x = 130 + ((particle*117 + t*(15+depth*8)) % 820)
        y = 680 + ((particle*91 + 37*depth) % 730)
        radius = 1 + (particle % 3)
        d.ellipse((round(x-radius-ORIGIN[0]),
                   round(y-radius-ORIGIN[1]),
                   round(x+radius-ORIGIN[0]),
                   round(y+radius-ORIGIN[1])),
                  fill=(*color, max(24, 85 - depth*12)))
    # Stable highlight near the original source; the causal interaction module
    # independently handles arrival flashes after a particle reaches its goal.
    sx = 290 if beat in ("solar", "heat") else 720 if beat == "sinking" else 540
    sy = 785
    shimmer = 0.55 + .45*math.sin(t*.63)
    d.arc((sx-115-ORIGIN[0], sy-31-ORIGIN[1],
           sx+115-ORIGIN[0], sy+47-ORIGIN[1]), 198, 340,
          fill=(*color, round(78*shimmer)), width=3)
    moving.putalpha(ImageChops.multiply(
        moving.getchannel("A"),plate.getchannel("A")))
    canvas.alpha_composite(moving,ORIGIN)
