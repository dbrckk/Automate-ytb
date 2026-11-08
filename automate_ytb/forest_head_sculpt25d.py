"""Original additive, expression-aware cheek silhouette and face relief.

The existing painted eyes, mouth, scarf and world-locked IK joints are
preserved. All supersampled geometry is authored locally with Pillow.
"""
from __future__ import annotations

from PIL import Image, ImageDraw

from .animated_forest import COLORS

VERSION = "original-p43-authored-cheek-silhouette-expression-relief-v1"
SIZE = (350, 440)
SPECIES = ("fox", "rabbit", "cat")
EXPRESSIONS = ("body", "blink", "look-down", "surprise", "follow")
_SCALE = 3


def _mix(first: tuple[int, ...], second: tuple[int, ...], q: float,
         *, alpha: int = 255) -> tuple[int, int, int, int]:
    return (*tuple(round(first[i] * (1-q) + second[i] * q)
                   for i in range(3)), alpha)


def sculpt_head(sprite: Image.Image, *, kind: str,
                expression: str) -> Image.Image:
    """Paint a distinctive cheek outline behind the unaltered face sprites."""
    if (not isinstance(sprite, Image.Image) or sprite.size != SIZE
            or sprite.mode != "RGBA" or kind not in SPECIES
            or expression not in EXPRESSIONS):
        raise ValueError("Invalid original 2.5D head sculpture")
    colors = COLORS[kind]
    fur, dark, belly = colors["fur"], colors["dark"], colors["belly"]
    rim = _mix(fur, dark, .71)
    shaded = _mix(fur, dark, .32)
    warm = _mix(fur, belly, .37)

    underlay = Image.new("RGBA", (SIZE[0]*_SCALE, SIZE[1]*_SCALE))
    d = ImageDraw.Draw(underlay)

    def polygon(points, fill):
        d.polygon([(round(x*_SCALE), round(y*_SCALE))
                   for x, y in points], fill=fill)

    # Three uneven cheek-fluff steps on each side interrupt the round head.
    # Lower tufts end above the IK hip attachments and the animated scarf.
    left = [(94,232), (56,236), (35,250), (47,264),
            (25,276), (49,286), (34,299), (70,311),
            (93,318), (116,294), (119,257)]
    inside = [(92,241), (59,244), (47,252), (61,267),
              (43,275), (64,285), (51,296), (76,304),
              (96,305), (106,291), (108,261)]
    for mirror in (False, True):
        convert = lambda points: [(SIZE[0]-x if mirror else x,y)
                                  for x,y in points]
        polygon(convert(left), rim)
        polygon(convert(inside), fur)
        polygon(convert([(55,267),(34,269),(58,278),(76,276)]), shaded)
        polygon(convert([(61,296),(45,297),(74,307),(87,302)]), warm)

    # Crown tuft breaks the circular forehead without touching separate ears.
    polygon([(141,144),(152,113),(168,126),(182,106),
             (197,131),(211,142),(187,154)], rim)
    polygon([(150,139),(158,119),(170,135),(183,114),
             (192,137),(198,145),(179,150)], fur)
    underlay = underlay.resize(SIZE, Image.Resampling.LANCZOS)
    sculpted = Image.alpha_composite(underlay, sprite)

    # Expression-specific brows sit above the pupils, never over gaze/eyeballs.
    accent = Image.new("RGBA", (SIZE[0]*_SCALE, SIZE[1]*_SCALE))
    a = ImageDraw.Draw(accent)
    brow_shift = {"body":0, "blink":6, "look-down":8,
                  "surprise":-11, "follow":-2}[expression]
    for center in (117,235):
        y = 171 + brow_shift
        a.arc(((center-38)*_SCALE,(y-13)*_SCALE,
               (center+36)*_SCALE,(y+22)*_SCALE),
              start=202,end=337,fill=shaded,width=4*_SCALE)
        a.arc(((center-32)*_SCALE,(y-14)*_SCALE,
               (center+31)*_SCALE,(y+15)*_SCALE),
              start=204,end=336,fill=warm,width=2*_SCALE)
    # Translucent cheek volume below the eyes, away from nose and smile.
    muzzle = _mix(fur, belly, .64, alpha=86)
    for bounds in ((126,244,166,269), (186,244,226,269)):
        a.ellipse(tuple(round(v*_SCALE) for v in bounds), fill=muzzle)
    for mirror in (False, True):
        pts = [(67,251),(79,261),(83,275)]
        if mirror:
            pts = [(SIZE[0]-x,y) for x,y in pts]
        a.line([(round(x*_SCALE),round(y*_SCALE)) for x,y in pts],
               fill=warm,width=4*_SCALE,joint="curve")
    accent = accent.resize(SIZE, Image.Resampling.LANCZOS)
    return Image.alpha_composite(sculpted,accent)
