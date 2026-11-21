"""Reusable original 2.5D animated water-vortex material for science and nature.

A cached opaque-to-translucent 2D source plane is combined with independent
moving streamlines. This is a qualitative visualization of circulation, not
latitude-specific Coriolis direction, a fluid simulation, or physical 3D.
No stock photos, paid inference, stochastic frame noise or downloaded media.
"""
from __future__ import annotations

from functools import lru_cache
import math
import random

from PIL import Image, ImageChops, ImageDraw
from .dynamic_material25d import moving_material

VERSION = "shared-organic-water-mass-p526-reusable-vortex-p514-v1"

PALETTES = {
    "ocean": (30, 111, 162),
    "lagoon": (25, 131, 146),
    "storm": (41, 79, 120),
}


def _validate(diameter: int, palette: str, seed: int) -> None:
    if (type(diameter) is not int or not 128 <= diameter <= 900
            or not isinstance(palette,str) or palette not in PALETTES
            or type(seed) is not int or not 0 <= seed <= 1_000_000):
        raise ValueError("Invalid original fluid-material source")


def _byte(v: float) -> int:
    return max(0, min(255, round(v)))


@lru_cache(maxsize=18)
def vortex_source(diameter: int, *, palette: str = "ocean",
                  seed: int = 385) -> Image.Image:
    """Cached source with organic rim, shaded spiral fabric and real RGBA."""
    _validate(diameter,palette,seed)
    # Low-frequency lighting is authored once on a bounded original plate;
    # high-frequency moving detail is rendered independently at full size.
    resolution=min(256,max(96,diameter//3))
    source=Image.new("RGBA",(resolution,resolution))
    px=source.load()
    rnd=random.Random(seed)
    phase=rnd.uniform(0,math.tau)
    tint=PALETTES[palette]
    mid=(resolution-1)/2
    half=resolution/2
    for y in range(resolution):
        ny=(y-mid)/half
        for x in range(resolution):
            nx=(x-mid)/half
            r=math.hypot(nx,ny)
            angle=math.atan2(ny,nx)
            # P5.26: one connected water mass with an irregular eroded
            # shoreline-style contour instead of a perfect opaque disc.
            # Angular harmonics are authored from the fixed source seed, not
            # sampled random noise; the same mask is stable on every frame.
            boundary=(.93 + .050*math.sin(5*angle+phase)
                          + .028*math.cos(9*angle-.43*phase)
                          + .013*math.sin(17*angle+phase*.67))
            radial=r/boundary
            if radial>=1:
                continue
            # 24%-wide diffuse shore of the liquid volume. This lets
            # currents merge into already-painted deep ocean rather than
            # ending in an obvious hard circular presentation panel.
            q=max(0.,min(1.,(1-radial)/.24))
            edge=q*q*(3-2*q)
            core=math.exp(-(radial/.19)**2)
            body=math.exp(-((radial-.69)/.30)**2)
            striations=(math.sin(19*radial-4*angle+phase)*9
                        +math.sin(39*radial+7*angle+phase*.34)*4)
            fine=(max(0.,math.sin(35*radial-9*angle+phase*.81))**7
                  *14*(1-core))
            reflection=23*max(0.,-.72*nx-.5*ny)*(1-core)
            value=12*body-18*core+striations+fine+reflection
            px[x,y]=(
                _byte(tint[0]+value*.57),
                _byte(tint[1]+value),
                _byte(tint[2]+value*.85),
                _byte((107+45*body+29*(1-radial))*edge),
            )
    resized=source.resize((diameter,diameter),Image.Resampling.BICUBIC)
    # BICUBIC may introduce alpha=1..2 at the outermost image pixels,
    # even though the analytic fluid contour is fully inside its canvas.
    # Force the final 1px boundary transparent: no seam or optical-ghost
    # stripe when independently compositing this RGBA material at any Z.
    alpha=resized.getchannel("A")
    ImageDraw.Draw(alpha).rectangle(
        (0,0,diameter-1,diameter-1),outline=0,width=1)
    resized.putalpha(alpha)
    return resized


def vortex_frame(diameter: int, t: float, *,
                 palette: str = "ocean", seed: int = 385,
                 clockwise: bool = True) -> Image.Image:
    """Moving water filaments share a coherent orbit, not a spun flat image.

    Returned RGBA is independently authored at each timestamp and clipped
    to the source's exact alpha. Marker and teaching overlay are separate.
    """
    _validate(diameter,palette,seed)
    if (type(t) not in (int,float) or not math.isfinite(t)
            or not 0 <= t <= 180 or type(clockwise) is not bool):
        raise ValueError("Invalid original water animation clock")
    source=vortex_source(diameter,palette=palette,seed=seed)
    # Material volume itself evolves independently under the orbiting
    # streamlines. Clip each frame to the exact source, not a square card.
    shifting=moving_material(source.size,t,material="water",seed=seed)
    shifting.putalpha(ImageChops.multiply(
        shifting.getchannel("A"),source.getchannel("A")))
    source=Image.alpha_composite(source,shifting)
    overlay=Image.new("RGBA",source.size)
    draw=ImageDraw.Draw(overlay,"RGBA")
    center=(diameter-1)/2.
    radius=diameter*.475
    direction=1 if clockwise else -1
    # Nonidentical streamline spirals add material structure; paths remain
    # smoothly moving and bounded in source space for the whole 180s clip.
    for arm in range(12):
        phase=(arm*math.tau/12+direction*t*.24
               +.15*math.sin(arm*.7+seed*.01))
        points=[]
        for i in range(72):
            f=i/71
            radial=(.16+.71*f)*radius
            angle=phase+direction*(.20+f*2.4)
            angle+=.045*math.sin(f*13+arm)
            points.append((center+radial*math.cos(angle),
                           center+radial*math.sin(angle)*.93))
        shade=(119,211,233,85) if arm%3 else (208,245,254,122)
        dark=(16,56,102,52)
        draw.line([(x,y+max(1,diameter*.006)) for x,y in points],
                  fill=dark,width=max(2,round(diameter*.012)),joint="curve")
        draw.line(points,fill=shade,width=max(2,round(diameter*.006)),
                  joint="curve")
        if arm%2==0:
            tip=points[30+arm%6*5]
            r=max(2,round(diameter*.005))
            draw.ellipse((tip[0]-r,tip[1]-r,tip[0]+r,tip[1]+r),
                         fill=(226,249,255,172))
    # Additional fine liquid shear folds follow curved radial streamlines,
    # independently of the 12 primary gyre arms. No extra static icons.
    for filament in range(23):
        phase=(filament*math.tau/23
               +direction*t*(.18+.007*(filament%5))
               +.12*math.sin(filament*1.29+seed*.003))
        nodes=[]
        for j in range(42):
            u=j/41
            radius_fraction=.27+.55*u
            angle=phase+direction*(.21+u*2.9)
            angle+=.065*math.sin(u*11.1+filament*.79)
            rr=radius_fraction*radius
            nodes.append((center+rr*math.cos(angle),
                          center+rr*math.sin(angle)*.93))
        draw.line(nodes,fill=(145,219,238,40+filament%4*11),
                  width=max(1,round(diameter*.002)),joint="curve")
    # Clip all moving strokes to the very same original water silhouette.
    alpha=ImageChops.multiply(
        overlay.getchannel("A"),source.getchannel("A"))
    overlay.putalpha(alpha)
    return Image.alpha_composite(source,overlay)
