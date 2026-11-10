"""Non-mocked source geometry QA across three different future video genres."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from PIL import Image, ImageChops

from automate_ytb.semantic_geometry25d import (
    MATERIALS, VERSION, render_material_sheet,
)
from automate_ytb.science_portrait import PortraitScienceScene


class SemanticSourceGeometryTests(unittest.TestCase):
    def test_every_material_is_authored_translucent_and_reproducible(self):
        self.assertIn("p525", VERSION)
        self.assertEqual(set(MATERIALS), {"plasma", "water", "ash"})
        for material in MATERIALS:
            with self.subTest(material=material):
                options=dict(size=(320,250),material=material,seed=457,
                             color=(89,190,213),t=1.7,duration=6.,
                             baseline=51,thickness=121,opacity=102)
                a=render_material_sheet(**options)
                b=render_material_sheet(**options)
                later=render_material_sheet(**{**options,"t":3.1})
                self.assertEqual(a.size,(320,250))
                self.assertEqual(a.mode,"RGBA")
                self.assertEqual(a.tobytes(),b.tobytes())
                self.assertNotEqual(a.tobytes(),later.tobytes())
                alpha=a.getchannel("A")
                self.assertGreater(alpha.getextrema()[1],25)
                self.assertEqual(alpha.getextrema()[0],0)
                # Different x-samples must reveal organic, non-flat contour.
                highs=[]
                for x in (25,80,145,215,285):
                    ys=[y for y in range(250) if alpha.getpixel((x,y))>15]
                    self.assertGreater(len(ys),17)
                    highs.append(min(ys))
                self.assertGreater(max(highs)-min(highs),3)

    def test_invalid_assets_and_nonfinite_clock_are_rejected(self):
        defaults=dict(size=(320,250),material="water",
                      color=(89,190,213),seed=457,t=1.7,
                      duration=6.,baseline=51,thickness=121,opacity=102)
        cases=(
            {"material":"unknown"},{"color":(11,22,999)},
            {"seed":True},{"t":float("nan")},{"duration":0},
            {"t":7.},{"baseline":250},{"thickness":12},
            {"opacity":231},{"size":(0,250)},
        )
        for edit in cases:
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                render_material_sheet(**{**defaults,**edit})

    def test_three_independent_native_science_sources_use_common_geometry(self):
        # Real 9:16 frames, same timestamp/voice/text; only the original
        # geometry generator is disabled for each control reference.
        families=(
            ("aurora", "Why do auroras glow?",
             "These glowing curtains of aurora ripple across the sky.",
             "automate_ytb.science_aurora.render_material_sheet"),
            ("water", "Why Do Ocean Currents Move?",
             "Global winds push surface waters, driving powerful currents.",
             "automate_ytb.science_ocean_depth.render_material_sheet"),
            ("ash", "How do volcanoes erupt?",
             "An eruption sends an ash plume above the volcano.",
             "automate_ytb.science_volcano.render_material_sheet"),
        )
        for material,topic,narration,module in families:
            with self.subTest(material=material):
                scene=PortraitScienceScene(topic=topic,narration=narration,
                                           scene_index=2)
                with patch(module,
                           side_effect=lambda size,**kw: Image.new("RGBA",size)):
                    control=scene.frame(2.3,6.4)
                rich=scene.frame(2.3,6.4)
                self.assertEqual(rich.mode,"RGB")
                self.assertEqual(rich.size,(1080,1920))
                self.assertNotEqual(
                    control.crop((85,495,995,1465)).tobytes(),
                    rich.crop((85,495,995,1465)).tobytes())
                self.assertEqual(control.crop((0,0,1080,320)).tobytes(),
                                 rich.crop((0,0,1080,320)).tobytes())
                self.assertEqual(control.crop((0,1510,1080,1920)).tobytes(),
                                 rich.crop((0,1510,1080,1920)).tobytes())
                self.assertEqual(rich.tobytes(),scene.frame(2.3,6.4).tobytes())


if __name__ == "__main__":
    unittest.main()
