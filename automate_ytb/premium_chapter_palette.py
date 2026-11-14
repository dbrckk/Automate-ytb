"""Original per-chapter color direction for all authored 2.5D scene packs.

Unlike a fixed topic hash, the wardrobe, atmosphere and reflection tones
change with *narrated chapter*. Stable actor geometry, rights information,
source facts and timeline positions are preserved. This is a lightweight,
CPU-only grade prepared ONCE per rasterized vector layer, not per video frame.

Palette names are editorial styles; colors never assert a physical property.
"""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageChops, ImageOps

VERSION = "chapter-art-directed-color-grading-v1"


@dataclass(frozen=True)
class ChapterPalette:
    name: str
    dark: tuple[int,int,int]
    tint: tuple[int,int,int]
    accent: tuple[int,int,int]
    secondary: tuple[int,int,int]
    reflection: tuple[int,int,int]

    def backdrop(self):
        return self.dark, self.tint, self.accent, self.secondary


STYLES = {
    "copper": ChapterPalette(
        "copper", (20,14,32), (79,37,48),
        (255,184,118), (253,226,164), (238,142,109)),
    "cobalt": ChapterPalette(
        "cobalt", (10,19,44), (28,68,103),
        (119,207,255), (214,240,255), (104,167,245)),
    "violet": ChapterPalette(
        "violet", (24,12,48), (82,40,108),
        (216,148,255), (141,222,255), (186,125,242)),
    "emerald": ChapterPalette(
        "emerald", (10,27,28), (25,75,63),
        (144,255,191), (227,246,176), (94,211,167)),
    "rose": ChapterPalette(
        "rose", (31,13,35), (90,33,65),
        (255,155,193), (255,210,139), (232,110,161)),
    "amber": ChapterPalette(
        "amber", (35,21,18), (104,62,37),
        (255,215,111), (255,239,185), (247,161,104)),
}

# The storytelling stage matters more than an episode-wide primary hue.
# These are deliberate, contrasting editorial looks across causal chapters.
MAGLEV_CUES = {
    "gap":"copper", "wheels":"amber", "levitation":"violet",
    "propulsion":"cobalt", "airflow":"rose", "glide":"emerald",
}

# Other source-grounded stories receive distinct but reproducible per-beat
# lighting without misidentifying a noun as a concrete illustration.
SEQUENCES = {
    "botanical":("emerald","amber","copper","violet","cobalt","rose"),
    "celestial":("cobalt","violet","rose","amber","emerald","copper"),
    "rail":("copper","cobalt","amber","violet","rose","emerald"),
    "weather":("violet","cobalt","emerald","rose","amber","copper"),
    "ocean":("cobalt","emerald","violet","rose","amber","copper"),
    "security":("violet","emerald","cobalt","amber","rose","copper"),
}


def scene_palette(family: str, narration: str, index: int) -> ChapterPalette:
    if (type(family) is not str or type(narration) is not str
            or type(index) is not int or not 0 <= index <= 11):
        raise ValueError("Invalid chapter palette input")
    if family=="maglev":
        from .premium_story_cues import cue_for_narration
        cue=cue_for_narration(narration)
        if cue is None:
            raise ValueError("Maglev chapter has no grounded visual action")
        return STYLES[MAGLEV_CUES[cue]]
    if family not in SEQUENCES:
        raise ValueError("No source-grounded palette for this visual family")
    return STYLES[SEQUENCES[family][index%len(SEQUENCES[family])]]


def palette_for_beat(story: dict, index: int) -> ChapterPalette | None:
    if (type(story) is not dict or type(index) is not int
            or type(story.get("beats")) is not list
            or not 0 <= index < len(story["beats"])):
        raise ValueError("Invalid original color story")
    if not story.get("proceduralVisualFinishEngine"):
        return None
    beat=story["beats"][index]
    if type(beat) is not dict or type(beat.get("narration")) is not str:
        raise ValueError("Missing original color chapter narration")
    family=story.get("proceduralVisualFamily")
    if family is None:
        # Multi-family chapter artwork takes its color from that chapter's
        # explicit original family; otherwise preserve the legacy palette.
        families=story.get("proceduralVisualFamilies")
        if type(families) is list and len(families)==len(story["beats"]):
            family=families[index]
    if family is None:
        return None
    return scene_palette(family,beat["narration"],index)


def tint_authored_layer(source: Image.Image, style: ChapterPalette,
                       depth: int) -> Image.Image:
    """Color-direction once per cached scene layer without flattening shading."""
    if (not isinstance(source,Image.Image) or source.mode!="RGBA"
            or not isinstance(style,ChapterPalette) or type(depth) is not int
            or not 0 <= depth <= 100):
        raise ValueError("Invalid original vector color grade")
    art=source.copy()
    visible=art.getchannel("A")
    # The atmosphere and ground should visibly change the mood, but preserve
    # geometry. Subject highlights receive far subtler color bounced light.
    if depth<=10:
        color,opacity=style.tint,92
    elif depth<=25:
        color,opacity=style.dark,60
    else:
        color,opacity=style.reflection,82
    plate=Image.new("RGBA",art.size,(*color,255))
    if depth<=25:
        mask=visible.point(lambda a:round(a*opacity/255))
    else:
        # Bright metallic reflections catch the tint, while dark windows
        # retain their original luminance and silhouette.
        light=ImageOps.grayscale(art.convert("RGB"))
        mask=light.point(
            lambda l:min(opacity,max(0,round((l-58)*opacity/160))))
        mask=ImageChops.multiply(mask,visible)
    plate.putalpha(mask)
    return Image.alpha_composite(art,plate)


__all__=("VERSION","STYLES","MAGLEV_CUES","ChapterPalette",
         "scene_palette","palette_for_beat","tint_authored_layer")
