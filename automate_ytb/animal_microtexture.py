"""Deterministic alpha-clipped fine fur and feather grain for original 2D rigs.

The effect adds material complexity within silhouettes, never synthetic
photorealism, external assets or new opaque pixels outside the original mask.
"""
from __future__ import annotations
import hashlib
import random
from PIL import Image, ImageDraw, ImageChops

MICROTEXTURE_VERSION = "authored-animal-fibers-v1"
_PARTS = {"body", "wing", "tail", "ear"}
_KINDS = {"fox", "rabbit", "cat", "owl"}


def paint_microtexture(sprite: Image.Image, *, kind: str, part: str) -> None:
    if kind not in _KINDS or part not in _PARTS:
        raise ValueError("Unsupported original material")
    if sprite.mode != "RGBA" or sprite.width > 500 or sprite.height > 500:
        raise ValueError("Expected original RGBA character plate")
    if kind == "owl" and part not in {"body", "wing"}:
        raise ValueError("Unsupported owl material")
    if kind != "owl" and part == "wing":
        raise ValueError("Unsupported animal wing material")
    alpha = sprite.getchannel("A")
    if alpha.getbbox() is None:
        return
    w,h=sprite.size
    seed=int(hashlib.sha256(f"{kind}:{part}:{w}:{h}".encode()).hexdigest()[:16],16)
    rng=random.Random(seed)
    pigment=Image.new("RGBA",sprite.size)
    brush=ImageDraw.Draw(pigment,"RGBA")
    # Restrained low-alpha directional lines; the existing silhouette is
    # preserved exactly by alpha clipping after drawing.
    count=max(80,round(w*h/145))
    for _ in range(count):
        x=rng.randrange(w)
        y=rng.randrange(h)
        if alpha.getpixel((x,y)) < 200:
            continue
        if kind == "owl":
            span=rng.randint(4,10)
            color=(252,228,255,rng.randint(16,38))
            brush.arc((x-span,y-span//2,x+span,y+span),15,135,fill=color,width=1)
        else:
            span=rng.randint(3,9)
            slant=rng.choice((-3,-2,1,2))
            color=((255,243,224,rng.randint(18,40)) if part!="tail"
                   else (255,218,183,rng.randint(16,34)))
            brush.line((x,y,x+slant,y+span),fill=color,width=1)
    mask=ImageChops.multiply(pigment.getchannel("A"),alpha)
    pigment.putalpha(mask)
    sprite.alpha_composite(pigment)
    sprite.putalpha(alpha)
