"""Chapter color-direction checks using real vector layers, no screenshots or mocks."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.premium_chapter_palette import (
    VERSION, MAGLEV_CUES, STYLES, palette_for_beat,scene_palette,
    cinematic_chapter_backdrop,tint_authored_layer)
from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_kinetic import read_story,_backdrop
from automate_ytb.universal_art25d import load_art_scenes,render_art_stage

ROOT=Path(__file__).resolve().parents[1]


class CinematicChapterColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        req=json.loads((ROOT/"video_requests"/
            "maglev-floating-train-20261114-original.json").read_text())
        cls.story=compile_original_script(
            topic=req["topic"],script=req["script"],language=req["language"])

    def test_real_five_chapter_story_has_five_distinct_premium_moods(self):
        palettes=[palette_for_beat(self.story,i)
                  for i in range(len(self.story["beats"]))]
        self.assertEqual([p.name for p in palettes],
                         ["copper","amber","violet","cobalt","rose"])
        self.assertEqual(len({p.dark for p in palettes}),5)
        self.assertEqual(len({p.accent for p in palettes}),5)
        self.assertTrue(all(p.backdrop()!=palettes[0].backdrop()
                            for p in palettes[1:]))
        self.assertTrue(VERSION.startswith("chapter-"))
        self.assertEqual(len(MAGLEV_CUES),6)

    def test_backdrops_show_visible_color_changes_not_just_labels(self):
        palettes=[palette_for_beat(self.story,i) for i in range(5)]
        backgrounds=[cinematic_chapter_backdrop(360,640,style) for style in palettes]
        colors=[image.getpixel((180,300)) for image in backgrounds]
        self.assertEqual(len(set(colors)),5)
        # Palette richness is variation across RGB channels, not just
        # the peak channel brightness: amber/cobalt may have equally
        # bright highlights while looking completely different.
        differences=[sum(abs(a-b) for a,b in zip(left,right))
                     for left in colors for right in colors]
        self.assertGreater(max(differences),90)

    def test_cached_source_art_has_distinct_reflections_and_same_alpha(self):
        art=Image.new("RGBA",(180,200))
        draw=ImageDraw.Draw(art)
        draw.rounded_rectangle((18,40,169,145),radius=20,
                               fill=(192,222,215,255))
        draw.rectangle((35,69,138,96),fill=(31,48,69,255))
        for depth in (5,25,45,65,85):
            tones=[tint_authored_layer(art,style,depth)
                   for style in (STYLES["copper"],STYLES["cobalt"],STYLES["rose"])]
            self.assertEqual(len({x.tobytes() for x in tones}),3)
            self.assertEqual(tones[0].getchannel("A").tobytes(),
                             art.getchannel("A").tobytes())
            self.assertEqual(tint_authored_layer(art,STYLES["copper"],depth).tobytes(),
                             tones[0].tobytes())
            self.assertEqual(tones[0].getpixel((0,0)),(0,0,0,0))

    def test_actual_cinematic_source_layers_rasterize_in_distinct_chapters(self):
        with tempfile.TemporaryDirectory() as temp:
            story_path=Path(temp)/"story.json"
            story_path.write_text(
                json.dumps(self.story,separators=(",",":")),encoding="utf-8")
            parsed=read_story(story_path)
            scenes,manifest=load_art_scenes(parsed,story_path,360,640)
            self.assertEqual(len(scenes),5)
            self.assertEqual(len(manifest),25)
            first=render_art_stage(scenes[0],4,0,60)
            second=render_art_stage(scenes[1],64,60,120)
            self.assertEqual(first.size,second.size)
            self.assertIsNotNone(
                ImageChops.difference(first.convert("RGB"),
                                      second.convert("RGB")).getbbox())

    def test_legacy_generated_stories_preserve_old_color_selection(self):
        story=json.loads(json.dumps(self.story))
        story.pop("proceduralVisualFinishEngine")
        self.assertIsNone(palette_for_beat(story,0))
        with self.assertRaises(ValueError):
            scene_palette("unknown","The subject appears.",0)
        with self.assertRaises(ValueError):
            tint_authored_layer(Image.new("RGB",(160,160)),
                               STYLES["cobalt"],45)


if __name__=="__main__":
    unittest.main()
