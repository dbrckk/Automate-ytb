"""Portrait layout diagnostics flag old 16:9 strip without blocking art."""
from __future__ import annotations

import unittest
from PIL import Image, ImageDraw
from automate_ytb.review_board import _portrait_band_metrics


class PortraitBandCompositionTests(unittest.TestCase):
    def test_blurred_filler_and_sharp_horizontal_strip_requires_editorial_review(self):
        image=Image.new("RGB",(360,640),(11,28,47))
        draw=ImageDraw.Draw(image)
        # A colorful but low-detail atmospheric filler at both ends.
        draw.ellipse((-120,-80,470,260), fill=(24,70,123))
        draw.ellipse((-170,430,440,760), fill=(27,58,92))
        # Original horizontal edit embedded as a crisply detailed 16:9 strip.
        for x in range(0,360,9):
            for y in range(234,407,9):
                draw.rectangle((x,y,x+4,y+4),
                               fill=(240,211,141) if (x+y)//9%2 else (32,101,168))
        metrics=_portrait_band_metrics(image)
        self.assertTrue(metrics["suspectedBandedComposition"])
        self.assertGreater(metrics["centerDetail"],metrics["topDetail"]*6)

    def test_real_portrait_design_can_have_high_quality_detail_across_frame(self):
        image=Image.new("RGB",(360,640),(12,26,50))
        draw=ImageDraw.Draw(image)
        for x in range(20,340,20):
            for y in (78,112,305,462,565):
                draw.rectangle((x,y,x+7,y+8),fill=(200,235,246))
        metrics=_portrait_band_metrics(image)
        self.assertFalse(metrics["suspectedBandedComposition"])
        self.assertIn("bottomDetail",metrics)

    def test_landscape_cannot_be_misreported_as_portrait(self):
        with self.assertRaises(ValueError):
            _portrait_band_metrics(Image.new("RGB",(640,360)))


if __name__=="__main__":
    unittest.main()
