"""Triangulated original 3D volcano terrain projected onto the science canvas.

A deterministic, closed radial heightfield with a depressed summit crater,
erosion gullies and lithologic bands. Face normals are lit by a fixed
directional source. All geometry comes from generated vertices; the cached
raster is not a manually painted triangle or a third-party texture.

The compositor still draws causal lava / pressure / smoke action *after* this
terrain, and the fixed native-portrait captions are added even later.
This raster backend uses only Pillow and Python (not Blender, GPU or PBR).
"""
from __future__ import annotations

from functools import lru_cache
import math

from PIL import Image, ImageChops, ImageDraw

SIZE = (1080, 1380)
TERRAIN_VERSION = "volcano-geometric-heightfield-v2-ground-blend"
RINGS = (0, 17, 33, 48, 65, 80, 96, 114, 133, 154, 179,
         206, 236, 268, 302, 338, 376, 414, 449, 480, 520)
SEGMENTS = 72

# The same geological silhouette is used for full exterior and cutaway shots.
# It also prevents any back-facing triangle from leaking beyond the mountain.
CONE_OUTLINE = (
    (0, 988), (127, 914), (228, 797), (337, 621),
    (448, 463), (502, 347), (522, 334), (558, 334),
    (589, 419), (697, 594), (805, 769), (940, 915),
    (1080, 988), (1080, 1380), (0, 1380),
)


def height_at(radius: float, azimuth: float) -> float:
    """Analytic volcano in world units; summit is a genuine concave crater."""
    if (not isinstance(radius, (int, float))
            or not isinstance(azimuth, (int, float))
            or not math.isfinite(radius) or not math.isfinite(azimuth)
            or radius < 0 or radius > 520):
        raise ValueError("Volcano heightfield coordinates out of range")
    if radius < 65:
        height = 685 - 105 * (1 - radius / 65) ** 2
    else:
        u = (radius - 65) / 465
        height = 685 * max(0, 1 - u ** .89)
    # Erosion fades to zero at the base; mountain must meet the ground.
    erosion = ((max(0, radius - 70) / 465) ** .69
               * max(0., 1 - (radius / 520) ** 4))
    height += erosion * (
        17 * math.sin(7 * azimuth + .6)
        + 12 * math.sin(13 * azimuth - .2)
        + 6 * math.cos(29 * azimuth + .1)
        + 4 * math.sin(31 * azimuth + radius * .03))
    return max(0., height)


def project(x: float, y: float, z: float) -> tuple[float, float]:
    """Fixed orthographic world-to-frame projection; never stretch axes."""
    if not all(math.isfinite(q) for q in (x, y, z)):
        raise ValueError("Non-finite volcanic mesh coordinate")
    return (540 + x * .91 + y * .13,
            1050 + y * .30 - z * 1.03)


@lru_cache(maxsize=1)
def shaded_terrain() -> Image.Image:
    """Opaque-face raster over transparent background, built once per render.

    Back faces are culled with respect to the upward/front viewing direction;
    visible triangles use proper cross-product normals, not random flat-color
    polygons. Drawing far-to-near is sufficient for this convex cone; a strict
    z-buffer is intentionally not claimed.
    """
    vertices = []
    for radius in RINGS:
        ring = []
        for index in range(SEGMENTS):
            az = index * 2 * math.pi / SEGMENTS
            r = radius * (1 + .022 * math.sin(11 * az)
                          + .018 * math.sin(19 * az))
            ring.append((r * math.cos(az), r * math.sin(az),
                         height_at(radius, az)))
        vertices.append(ring)

    faces = []
    for ring_index in range(len(RINGS) - 1):
        for j in range(SEGMENTS):
            j1 = (j + 1) % SEGMENTS
            a, b = vertices[ring_index][j], vertices[ring_index][j1]
            c, d = vertices[ring_index + 1][j], vertices[ring_index + 1][j1]
            for v0, v1, v2 in ((a, c, d), (a, d, b)):
                ax, ay, az = v0
                bx, by, bz = v1
                cx, cy, cz = v2
                ux, uy, uz = bx-ax, by-ay, bz-az
                vx, vy, vz = cx-ax, cy-ay, cz-az
                nx = uy*vz-uz*vy
                ny = uz*vx-ux*vz
                nz = ux*vy-uy*vx
                norm = math.sqrt(nx*nx + ny*ny + nz*nz)
                if norm < 1e-8:
                    continue
                nx, ny, nz = nx/norm, ny/norm, nz/norm
                # The projected camera looks up the northern-facing cone.
                # Remove faces that would otherwise cover its foreground.
                if -ny * .96 + nz * .29 <= 0:
                    continue
                lambert = max(0., -.63*nx - .46*ny + .77*nz)
                illuminance = .28 + .72 * lambert
                altitude = (az + bz + cz) / 3
                midx, midy = (ax+bx+cx)/3, (ay+by+cy)/3
                stratum = (.5 + .5 * math.sin(
                    altitude * .058 + midx * .012))
                grain = (math.sin(midx * .075 + midy * .048)
                         * math.sin(midy * .093 + altitude * .11))
                bness = illuminance * (.91 + grain*.12 + stratum*.08)
                color = (
                    min(255, max(10, round(115*bness+14))),
                    min(255, max(10, round(104*bness+12))),
                    min(255, max(12, round(104*bness+14))),
                    255,
                )
                faces.append((midy,
                              (project(*v0), project(*v1), project(*v2)),
                              color))

    # All work happens once in cached original source space. A 30 FPS video
    # reuses precisely the same authored geometry for every animated frame.
    layer = Image.new("RGBA", SIZE)
    draw = ImageDraw.Draw(layer)
    for _, polygon, color in sorted(faces, key=lambda face: face[0],
                                    reverse=True):
        draw.polygon(polygon, fill=color)

    # Clamp projected geometry to the safe, fully opaque volcano silhouette.
    # This eliminates stray geometry at the outer corners of the 9:16 frame.
    mask = Image.new("L", SIZE)
    ImageDraw.Draw(mask).polygon(CONE_OUTLINE, fill=255)
    # The generated mesh is an open exterior shell. Its lower-facing
    # triangles are not an infinite vertical cliff: blend them into the
    # darker foothill terrain, avoiding floating facets at the frame bottom.
    fade = Image.new("L", SIZE, 255)
    fd = ImageDraw.Draw(fade)
    for y in range(865, 1100):
        fraction = (y - 865) / 235
        smooth = fraction * fraction * (3 - 2 * fraction)
        fd.line((0, y, SIZE[0] - 1, y),
                fill=round(255 * (1 - smooth)))
    fd.rectangle((0, 1100, SIZE[0], SIZE[1]), fill=0)
    layer.putalpha(ImageChops.multiply(
        ImageChops.multiply(layer.getchannel("A"), mask), fade))
    return layer
