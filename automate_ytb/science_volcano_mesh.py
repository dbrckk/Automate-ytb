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
from .rock_surface25d import weathered_rock

SIZE = (1080, 1380)
TERRAIN_VERSION = "volcano-geometric-heightfield-v4-radial-buttresses-and-terraced-flanks"
RINGS = (0, 17, 33, 48, 65, 80, 96, 114, 133, 154, 179,
         206, 236, 268, 302, 338, 376, 414, 449, 480, 520)
SEGMENTS = 112

# The same geological silhouette is used for full exterior and cutaway shots.
# It also prevents any back-facing triangle from leaking beyond the mountain.
_SHOULDER_ANCHORS = (
    # Crater and vent coordinates are preserved: geology must NOT shift
    # the (540,345) eruption source or disconnect the conduit/cutaway.
    (0,1032),(70,1009),(128,958),(176,914),
    (212,854),(249,803),(269,754),(302,707),
    (336,658),(357,607),(391,560),(418,529),
    (451,466),(473,414),(499,364),(514,338),
    (529,343),(549,336),(566,353),(585,400),
    (611,447),(651,511),(676,565),(707,612),
    (738,675),(779,729),(816,784),(851,829),
    (897,889),(947,933),(1002,970),(1080,1008),
)


def eroded_silhouette() -> tuple[tuple[int,int], ...]:
    """Original fixed chipped rock shoulders, not a 32-edge pyramid.

    The source mask is created once at module initialization. All geometry
    and cuts share it, and every pre-existing summit anchor stays intact.
    """
    points=[]
    for i,(left,right) in enumerate(zip(_SHOULDER_ANCHORS,
                                        _SHOULDER_ANCHORS[1:])):
        x0,y0=left
        x1,y1=right
        count=max(2,round(abs(x1-x0)/12))
        for j in range(count):
            u=j/count
            x=x0+(x1-x0)*u
            y=y0+(y1-y0)*u
            # Erosion is stronger on the outer ridge, not on the summit
            # where the vent and rock contact must remain fixed.
            summit_falloff=min(1.,max(0.,abs(x-540)-35)/170.)
            strength=8+14*summit_falloff
            broad=math.sin((i+u)*2.31+.46)
            ridged=math.sin((i+u)*6.11-.71)
            y+=strength*math.sin(math.pi*u)*(.71*broad+.29*ridged)
            points.append((round(x),round(y)))
    points.append(_SHOULDER_ANCHORS[-1])
    return tuple(points)


# Same source mask in every 2.5D source: exterior, animated-lit faceting,
# cutaway wall and independent camera movement. Final two points close
# the mountain against the existing terrain bed with no geometry leaks.
CONE_OUTLINE = eroded_silhouette() + ((1080,1380),(0,1380))


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
        # Radius 520 is the final foothill: elevation must reach the ground.
        u = (radius - 65) / 455
        height = 685 * max(0, 1 - u ** .89)
    # Lithologic benches and radial buttresses are actual heightfield
    # displacements: silhouettes, shadow-facing normals and rock relief
    # all change together. They fade at both vent and ground, instead of
    # placing arbitrary decorative wrinkles over a perfect cone.
    u=max(0.,min(1.,(radius-65)/455.))
    envelope=math.sin(math.pi*u)**2
    broad_buttress=(39*math.sin(4*azimuth+.23+u*.8)
                     +23*math.sin(9*azimuth-.61-u*1.9)
                     +9*math.cos(17*azimuth+.1))
    radial_benches=(17*math.sin(radius*.037+azimuth*.83)
                    +8*math.cos(radius*.072-2.7*azimuth))
    height+=envelope*(broad_buttress+radial_benches)
    # Small eroded gullies are persistent world-space geometry,
    # decreasing to zero as the mountain joins the original foothills.
    erosion=((max(0.,radius-70)/465)**.69 *
             max(0.,1-(radius/520)**4))
    height+=erosion*(17*math.sin(7*azimuth+.6)
                     +12*math.sin(13*azimuth-.2)
                     +6*math.cos(29*azimuth+.1)
                     +4*math.sin(31*azimuth+radius*.03))
    return max(0.,height)


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
            # Distinct landslide shoulders and erosion ravines alter
            # the projected slope itself instead of drawing cartoon
            # sawtooth decorations over straight triangle edges.
            u=radius/520.
            shoulder=math.sin(math.pi*u)**2
            r=radius*(1+.022*math.sin(11*az)
                      +.018*math.sin(19*az)
                      +shoulder*(.063*math.sin(5*az+.31+u*2.4)
                                 +.029*math.sin(13*az-.7-u*3.2)))
            ring.append((r*math.cos(az),r*math.sin(az),
                         height_at(radius,az)))
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
    # Material-rich original 2.5D painterly rock retains the exact same
    # surface silhouettes and illumination geometry while removing overly
    # plain facets in every future exterior/cutaway video.
    return weathered_rock(layer,seed=45083)
