"""Shared Extreme 2.5D: tests independent of any one video subject."""
from __future__ import annotations

import random
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.finish25d import (
    VERSION, LOOKS, Look25D, artwork_diagnostics, finish_world,
    science_look, frame_layout_diagnostics,
)


class Universal2p5DQualityTests(unittest.TestCase):
    def _frame(self):
        scene=Image.new("RGBA",(192,320),(24,46,68,255))
        d=ImageDraw.Draw(scene,"RGBA")
        for i in range(50):
            x=17+i*3
            d.line((x,85,x+15,204),fill=(
                72+i%6*11,115+i%4*17,146+i%3*17,210),width=2)
        d.ellipse((54,109,157,208),fill=(183,97,49,255))
        d.rectangle((22,278,176,304),fill=(247,241,235,255))
        return scene

    def test_one_renderer_works_for_every_supported_science_and_forest_look(self):
        self.assertIn("25d",VERSION)
        self.assertEqual(set(LOOKS),
                         {"storm","volcano","aurora","ocean",
                          "rainbow","daylight","forest","neutral"})
        base=self._frame()
        for look in LOOKS:
            with self.subTest(look=look):
                finished=base.copy()
                finish_world(finished,bounds=(16,66,176,242),
                             look=look,t=1.25,duration=6.)
                self.assertEqual(finished.size,base.size)
                self.assertEqual(finished.mode,"RGBA")
                self.assertEqual(finished.getchannel("A").tobytes(),
                                 base.getchannel("A").tobytes())
                self.assertEqual(finished.crop((0,0,192,66)).tobytes(),
                                 base.crop((0,0,192,66)).tobytes())
                self.assertEqual(finished.crop((0,242,192,320)).tobytes(),
                                 base.crop((0,242,192,320)).tobytes())
                self.assertEqual(finished.getpixel((60,291)),
                                 base.getpixel((60,291)))
                changed=ImageChops.difference(
                    finished.crop((16,66,176,242)).convert("RGB"),
                    base.crop((16,66,176,242)).convert("RGB"))
                self.assertIsNotNone(changed.getbbox())

    def test_deterministic_temporal_finishing_no_random_flicker(self):
        first,second=self._frame(),self._frame()
        finish_world(first,bounds=(16,66,176,242),
                     look="storm",t=1.2,duration=6.)
        finish_world(second,bounds=(16,66,176,242),
                     look="storm",t=1.2,duration=6.)
        self.assertEqual(first.tobytes(),second.tobytes())
        third=self._frame()
        finish_world(third,bounds=(16,66,176,242),
                     look="storm",t=3.7,duration=6.)
        # Lighting follows source events, never a synthetic uncorrelated
        # noise pattern that jumps whenever absolute frame time changes.
        self.assertEqual(first.tobytes(),third.tobytes())

    def test_named_art_direction_uses_existing_science_classification(self):
        self.assertEqual(science_look(lightning=True),"storm")
        self.assertEqual(science_look(volcano=True),"volcano")
        self.assertEqual(science_look(aurora=True),"aurora")
        self.assertEqual(science_look(rainbow=True),"rainbow")
        self.assertEqual(science_look(mode="ocean"),"ocean")
        self.assertEqual(science_look(),"daylight")

    def test_synthetic_flat_assets_raise_advisory_not_fake_approval(self):
        flat=Image.new("RGB",(192,320),(31,42,59))
        record=artwork_diagnostics(flat,bounds=(16,66,176,242))
        self.assertFalse(record["editorialApproval"])
        self.assertIn("flat-color-geometry",record["reviewSignals"])
        self.assertIn("low-fine-detail",record["reviewSignals"])
        rng=random.Random(84)
        varied=Image.frombytes("RGB",(192,320),
                               rng.randbytes(192*320*3))
        report=artwork_diagnostics(varied,bounds=(16,66,176,242))
        self.assertGreater(report["edgeDetail"],record["edgeDetail"])
        self.assertGreater(report["paletteFamilies"],record["paletteFamilies"])
        self.assertFalse(report["editorialApproval"])

    def test_large_slide_panel_is_detected_but_no_false_quality_approval(self):
        import PIL.ImageDraw
        framed=Image.new("RGB",(192,320),(12,32,49))
        d=PIL.ImageDraw.Draw(framed)
        d.rectangle((12,72,180,224),outline=(211,223,235),width=3)
        metrics=frame_layout_diagnostics(framed)
        self.assertTrue(metrics["suspectedDominantRectangularFrame"])
        self.assertTrue(metrics["humanReviewRequired"])
        scenery=Image.new("RGB",(192,320),(32,77,104))
        self.assertFalse(frame_layout_diagnostics(scenery)[
            "suspectedDominantRectangularFrame"])
        with self.assertRaises(ValueError):
            frame_layout_diagnostics(Image.new("RGB",(32,32)))

    def test_no_effect_is_ever_allowed_to_damage_unsafe_inputs(self):
        picture=self._frame()
        cases=[
            (dict(bounds=(0,0,192,320),look="3d",t=1.,duration=6.)),
            (dict(bounds=(-1,60,180,230),look="storm",t=1.,duration=6.)),
            (dict(bounds=(16,66,176,242),look="storm",
                  t=float("nan"),duration=6.)),
            (dict(bounds=(16,66,176,242),look="storm",t=9.,duration=6.)),
            (dict(bounds=(16,66,176,242),look="storm",t=1.,duration=181.)),
        ]
        original=picture.tobytes()
        for options in cases:
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    finish_world(picture,**options)
                self.assertEqual(picture.tobytes(),original)
        with self.assertRaises(ValueError):
            Look25D(1.5,1.3,200,(0,255,0),.7)
        with self.assertRaises(ValueError):
            artwork_diagnostics(picture,bounds=(0,0,500,320))


if __name__=="__main__":
    unittest.main()
