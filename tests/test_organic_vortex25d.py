"""P5.26: original non-circular source art, not another generic video filter."""
from __future__ import annotations

import math
import unittest

from PIL import Image

from automate_ytb.flow_material25d import (
    VERSION, PALETTES, vortex_source, vortex_frame,
)
from automate_ytb.science_portrait import PortraitScienceScene


class OrganicGyreSourceTests(unittest.TestCase):
    def test_real_material_source_has_irregular_connected_feathered_border(self):
        self.assertIn("p526",VERSION)
        for palette in PALETTES:
            with self.subTest(palette=palette):
                source=vortex_source(670,palette=palette,seed=377)
                self.assertIs(source,vortex_source(670,palette=palette,seed=377))
                self.assertEqual(source.mode,"RGBA")
                self.assertEqual(source.getpixel((0,0))[3],0)
                self.assertGreater(source.getpixel((335,335))[3],100)
                # A perfect circular slide panel would have the same alpha
                # around a given radius. Organic geometry has both present
                # and absent material along this near-edge ring.
                ring=[]
                for deg in range(0,360,3):
                    theta=math.radians(deg)
                    x=round(334.5+670*.455*math.cos(theta))
                    y=round(334.5+670*.455*math.sin(theta))
                    ring.append(source.getpixel((x,y))[3])
                self.assertGreater(sum(alpha==0 for alpha in ring),20)
                self.assertGreater(sum(alpha>=20 for alpha in ring),8)
                self.assertLess(max(ring),75)
                # The liquid has a broad soft fade, not a sharp cropped disc.
                alpha=source.getchannel("A")
                mids=[alpha.getpixel((round(335+335*r),335))
                      for r in (.67,.79,.88,.97)]
                self.assertGreater(mids[0],mids[-1])
                self.assertEqual(mids[-1],0)

    def test_distinct_materials_and_motion_are_real_and_deterministic(self):
        signatures=[]
        for palette in PALETTES:
            a=vortex_frame(410,1.25,palette=palette,seed=91)
            b=vortex_frame(410,2.25,palette=palette,seed=91)
            self.assertEqual(a.tobytes(),
                             vortex_frame(410,1.25,palette=palette,seed=91).tobytes())
            self.assertNotEqual(a.tobytes(),b.tobytes())
            self.assertEqual(a.getpixel((0,0))[3],0)
            signatures.append(a.tobytes())
        self.assertEqual(len(set(signatures)),3)

    def test_invalid_argument_protection_preserved(self):
        for value in (-1,True,float("nan"),181):
            with self.assertRaises(ValueError):
                vortex_frame(410,value,palette="ocean")
        with self.assertRaises(ValueError):
            vortex_source(670,palette="untrusted")

    def test_real_1080x1920_coriolis_video_still_moves_and_keeps_text(self):
        scene=PortraitScienceScene(
            topic="Why Do Ocean Currents Move?",
            narration="Earth rotation bends currents through the Coriolis effect.",
            scene_index=3)
        a=scene.frame(1.2,6.0)
        b=scene.frame(3.1,6.0)
        self.assertEqual(a.size,(1080,1920))
        self.assertEqual(a.mode,"RGB")
        self.assertNotEqual(a.crop((205,755,875,1425)).tobytes(),
                            b.crop((205,755,875,1425)).tobytes())
        self.assertEqual(a.tobytes(),scene.frame(1.2,6.0).tobytes())


if __name__=="__main__":
    unittest.main()
