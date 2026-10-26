"""Create a 4-biome visual-review contact sheet of actual rendered original art.

Run from the repository root:
    python scripts/render_visual_gallery.py --output out/premium-gallery.png

No third-party assets, model tokens or video uploads required. Each panel
uses the same approved artwork compositor as a production video.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from automate_ytb.animated_forest import render_character_poster as forest_poster
from automate_ytb.animated_owl import render_character_poster as owl_poster


EXAMPLES = (
    ("fox","forest","day","Le renard découvre un rayon de soleil dans la forêt."),
    ("rabbit","meadow","wind","Le lapin traverse une prairie ensoleillée."),
    ("cat","village","night","Le chat explore le village sous la lune."),
    ("owl","river","cloudy","La chouette observe une rivière paisible."),
)


def render_gallery(output: Path) -> None:
    if not isinstance(output, Path):
        raise ValueError("Output must be a file path")
    collage = Image.new("RGB", (2560, 1440), (15, 23, 42))
    with tempfile.TemporaryDirectory(prefix="storyboard-gallery-") as tmp:
        for index,(actor,biome,weather,narration) in enumerate(EXAMPLES):
            file=Path(tmp)/(actor+".png")
            direction={"action":"idle","emotion":"happy",
                       "weather":weather,"shot":"wide"}
            shared=dict(topic=f"Original {biome} — {actor}",
                        narration=narration, scene_index=index+1,
                        scene_count=len(EXAMPLES),style="cartoon",
                        destination=file,direction=direction,landscape=biome)
            if actor=="owl":
                owl_poster(**shared)
            else:
                forest_poster(kind=actor,**shared)
            with Image.open(file) as image:
                if image.size != (1280,720):
                    raise ValueError("Invalid production poster size")
                collage.paste(image.convert("RGB"),
                              (index%2*1280,index//2*720))
    output.parent.mkdir(parents=True,exist_ok=True)
    collage.save(output,"PNG",optimize=True)


def main() -> None:
    parser=argparse.ArgumentParser(description="Original cinematic art gallery")
    parser.add_argument("--output",default="out/visual-gallery.png")
    args=parser.parse_args()
    output=Path(args.output)
    render_gallery(output)
    print(f"Visual gallery: {output} ({output.stat().st_size} bytes)")


if __name__=="__main__":
    main()
