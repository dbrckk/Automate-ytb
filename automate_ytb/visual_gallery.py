"""Offline 1920×1080 review sheet made from *real* approved animal posters.

The sheet is deliberately for visual QA, not a fabricated cinematic preview.
Use it on mobile to inspect original species anatomy, color and composition
across four biomes and several director moods before publishing a video.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .animated_forest import render_character_poster as forest_poster
from .animated_owl import render_character_poster as owl_poster
from .studio import font

GALLERY_VERSION = "original-mobile-gallery-v1"
TILE_SIZE = (960, 540)
SHEETS = (
    ("Renard / forêt / soleil", "fox", "forest", "day", "happy",
     "Le renard sourit au soleil dans la forêt."),
    ("Lapin / prairie / soleil", "rabbit", "meadow", "day", "happy",
     "Le lapin joue dans la prairie."),
    ("Chat / village / nuit", "cat", "village", "night", "worried",
     "Le chat contemple le village pendant la nuit."),
    ("Chouette / rivière / soir", "owl", "river", "cloudy", "curious",
     "La chouette observe la rivière."),
)


def render_gallery(destination: Path) -> Path:
    if not isinstance(destination, Path):
        raise ValueError("Gallery output must be a local path")
    with tempfile.TemporaryDirectory(prefix="automate-ytb-gallery-") as tmp:
        root=Path(tmp)
        sheet=Image.new("RGB", (1920, 1080), (14, 23, 36))
        for i, (label, actor, setting, weather, emotion, narration) in enumerate(SHEETS):
            still=root/f"original-{i:02d}.png"
            args=dict(
                topic=label,narration=narration,scene_index=i+1,
                scene_count=4,style="cartoon",destination=still,
                landscape=setting,
                direction={"weather":weather,"action":"idle",
                           "emotion":emotion,"shot":"wide"})
            if actor=="owl":
                owl_poster(**args)
            else:
                forest_poster(kind=actor,**args)
            with Image.open(still) as original:
                tile=original.convert("RGB").resize(TILE_SIZE,Image.Resampling.LANCZOS)
            ox=(i%2)*TILE_SIZE[0]
            oy=(i//2)*TILE_SIZE[1]
            sheet.paste(tile,(ox,oy))
            # Small reserved label; no image search assets or imitation artwork.
            d=ImageDraw.Draw(sheet)
            d.rounded_rectangle((ox+18,oy+478,ox+470,oy+528),
                                radius=11,fill=(17,27,42))
            d.text((ox+30,oy+487),label,fill=(245,249,240),font=font(22))
        destination.parent.mkdir(parents=True,exist_ok=True)
        sheet.save(destination,format="PNG",optimize=True)
    return destination


def main() -> None:
    parser=argparse.ArgumentParser(description="Local mobile-ready original animal art review")
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=render_gallery(args.output)
    print(f"Original art review: {result} (1920x1080; four current renderers)")


if __name__=="__main__":
    main()
