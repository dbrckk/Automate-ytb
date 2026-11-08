"""P4.3 original sculpted animal cheek silhouette and facial acting tests."""
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.animated_forest import COLORS
from automate_ytb.forest_head_sculpt25d import (
    VERSION, sculpt_head, EXPRESSIONS, SPECIES,
)
from automate_ytb.forest25d import character_plate
from automate_ytb.forest_contact25d import IMPACT_TIME
from automate_ytb.rig25d import GROUND


def sample(kind):
    art=Image.new("RGBA",(350,440))
    d=ImageDraw.Draw(art)
    d.ellipse((45,112,306,330),fill=COLORS[kind]["fur"])
    d.ellipse((97,185,137,239),fill=(22,28,42,255))
    d.ellipse((215,185,255,239),fill=(22,28,42,255))
    d.ellipse((166,245,191,265),fill=(52,30,55,255))
    d.arc((150,260,209,297),0,180,fill=(52,30,55,255),width=5)
    return art


class ForestSculptTests(unittest.TestCase):
    def test_all_original_species_and_five_expressions_painted(self):
        self.assertIn("p43", VERSION)
        for kind in SPECIES:
            source=sample(kind)
            untouched=source.tobytes()
            for emotion in EXPRESSIONS:
                with self.subTest(kind=kind,emotion=emotion):
                    actual=sculpt_head(source,kind=kind,expression=emotion)
                    self.assertEqual(actual.size,(350,440))
                    self.assertEqual(actual.mode,"RGBA")
                    self.assertLess(actual.getbbox()[0],source.getbbox()[0]-8)
                    self.assertGreater(actual.getbbox()[2],source.getbbox()[2]+8)
                    self.assertEqual(actual.getpixel((117,210)),
                                     source.getpixel((117,210)))
                    self.assertEqual(actual.getpixel((235,210)),
                                     source.getpixel((235,210)))
                    self.assertEqual(actual.getpixel((179,254)),
                                     source.getpixel((179,254)))
            self.assertEqual(source.tobytes(),untouched)

    def test_event_brows_are_actual_expression_specific_pixels(self):
        source=sample("fox")
        calm=sculpt_head(source,kind="fox",expression="body")
        startled=sculpt_head(source,kind="fox",expression="surprise")
        self.assertIsNotNone(ImageChops.difference(
            calm.convert("RGB"),startled.convert("RGB")).getbbox())
        self.assertEqual(startled.tobytes(),
                         sculpt_head(source,kind="fox",
                                     expression="surprise").tobytes())

    def test_physical_paws_are_never_modified_by_head_sculpt(self):
        for kind in SPECIES:
            actor,meta=character_plate(IMPACT_TIME+.21,
                                       kind=kind,interaction=True)
            self.assertEqual(actor.size,(1080,1920))
            self.assertEqual(meta["headSculpt"],VERSION)
            self.assertEqual(meta["expression"],"surprise")
            self.assertTrue(meta["right"].planted)
            self.assertEqual(meta["right"].foot[1],GROUND)

    def test_rejects_wrong_sizes_modes_species_and_emotions(self):
        for image,kind,emotion in (
            (Image.new("RGB",(350,440)),"fox","body"),
            (Image.new("RGBA",(120,440)),"fox","body"),
            (Image.new("RGBA",(350,440)),"owl","body"),
            (Image.new("RGBA",(350,440)),"fox","unknown"),
        ):
            with self.assertRaises(ValueError):
                sculpt_head(image,kind=kind,expression=emotion)


if __name__=="__main__":
    unittest.main()
