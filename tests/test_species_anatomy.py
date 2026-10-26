"""Species-specific muzzle/forehead shapes remain present across expressions."""
import tempfile
from pathlib import Path
import unittest
from PIL import Image, ImageChops

from automate_ytb.species_anatomy import (
    FACE_ANATOMY_VERSION, paint_anatomy_base, paint_anatomy_accents)
from automate_ytb.sprite_supersampling import sprite_canvas, resolve_sprite
from automate_ytb.animated_forest import _sprite_body, COLORS


class OriginalAnimalAnatomyTests(unittest.TestCase):
    def test_fox_rabbit_cat_have_distinct_shape_motifs(self):
        self.assertIn("v1",FACE_ANATOMY_VERSION)
        rendered = {}
        for kind in ("fox", "rabbit", "cat"):
            image,brush=sprite_canvas((350,440))
            colors=COLORS[kind]
            paint_anatomy_base(brush,kind=kind,**{
                color:colors[color] for color in ("fur","dark","belly","ear")})
            paint_anatomy_accents(brush,kind=kind,dark=colors["dark"],
                                  ear=colors["ear"])
            rendered[kind]=resolve_sprite(image,(350,440))
        # The feline forehead pattern is a genuine new painted feature, not
        # merely a relabeled fur color or an added post-processing glow.
        self.assertGreater(rendered["cat"].getpixel((178,145))[3],160)
        self.assertEqual(rendered["rabbit"].getpixel((178,145))[3],0)
        self.assertEqual(rendered["fox"].getpixel((178,145))[3],0)
        self.assertIsNotNone(ImageChops.difference(
            rendered["fox"],rendered["rabbit"]).getbbox())
        with self.assertRaises(ValueError):
            paint_anatomy_base(brush,kind="wolf",
                               **{color:COLORS["fox"][color]
                                  for color in ("fur","dark","belly","ear")})

    def test_pupils_blink_and_mouth_stay_in_original_sprite_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for kind in ("fox","rabbit","cat"):
                normal=root/(kind+"-gaze.png")
                blink=root/(kind+"-blink.png")
                _sprite_body(normal,kind=kind,blink=False,
                             emotion="happy",gaze="right",include_ears=False)
                _sprite_body(blink,kind=kind,blink=True,
                             emotion="happy",gaze="right",include_ears=False)
                with Image.open(normal) as src,Image.open(blink) as eyelid:
                    self.assertEqual(src.size,(350,440))
                    self.assertEqual(src.mode,"RGBA")
                    self.assertIsNotNone(ImageChops.difference(
                        src.convert("RGB"),eyelid.convert("RGB")).getbbox())


if __name__=="__main__":
    unittest.main()
