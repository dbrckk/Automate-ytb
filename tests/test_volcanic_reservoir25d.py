"""Verify coherent shared organic magma reservoir used by real video scenes."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageChops,ImageStat

from automate_ytb.volcanic_reservoir25d import (
    VERSION, SIZE, CENTER, BOUNDS, reservoir_contour,
    reservoir_mask, reservoir_rock_source, reservoir_molten_source,
)
from automate_ytb.science_volcano import _base
from automate_ytb.science_volcano_magma import (
    _chamber_mask, _molten_plate,draw_magma, BEATS,
)
from automate_ytb.science_portrait import PortraitScienceScene


class OriginalVolcanicReservoirTests(unittest.TestCase):
    def test_single_organic_contour_anchors_all_rock_liquid_and_pressure(self):
        boundary=reservoir_contour()
        self.assertIs(boundary,reservoir_contour())
        self.assertGreaterEqual(len(boundary),96)
        self.assertEqual(len(set(boundary)),len(boundary))
        self.assertGreater(max(x for x,y in boundary)-min(x for x,y in boundary),360)
        self.assertGreater(max(y for x,y in boundary)-min(y for x,y in boundary),180)
        self.assertEqual(SIZE,(1080,1380))
        self.assertEqual(CENTER,(542,1127))
        self.assertEqual(BOUNDS,(326,996,758,1257))
        self.assertTrue(VERSION.endswith("p517-v1"))
        # A true fixed irregular mineral contour, not a raster ellipse.
        scalars=[math.hypot((x-542)/202,(y-1127)/111) for x,y in boundary]
        self.assertGreater(max(scalars)-min(scalars),.075)

    def test_static_rock_source_mask_and_molten_material_are_reused(self):
        mask=reservoir_mask()
        self.assertIs(mask,reservoir_mask())
        self.assertIs(mask,_chamber_mask())
        self.assertEqual(mask.size,SIZE)
        self.assertEqual(mask.mode,"L")
        self.assertEqual(mask.getpixel((542,1120)),255)
        self.assertEqual(mask.getpixel((50,400)),0)
        rock=reservoir_rock_source()
        magma=reservoir_molten_source()
        self.assertIs(rock,reservoir_rock_source())
        self.assertIs(magma,reservoir_molten_source())
        self.assertEqual(rock.mode,"RGBA")
        self.assertEqual(magma.mode,"RGBA")
        self.assertEqual(rock.getpixel((0,0))[3],0)
        self.assertEqual(magma.getpixel((0,0))[3],0)
        self.assertGreater(rock.getpixel((542,1120))[3],200)
        self.assertGreater(magma.getpixel((542,1120))[3],80)

    def test_lively_source_animation_never_mutates_cached_reservoir(self):
        rockSignature=reservoir_rock_source().tobytes()
        moltenSignature=reservoir_molten_source().tobytes()
        a=_molten_plate(.45,6.8,"magma")
        b=_molten_plate(3.2,6.8,"magma")
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.tobytes(),_molten_plate(.45,6.8,"magma").tobytes())
        self.assertEqual(reservoir_rock_source().tobytes(),rockSignature)
        self.assertEqual(reservoir_molten_source().tobytes(),moltenSignature)
        self.assertEqual(_base(True).size,SIZE)

    def test_all_three_real_magma_storyboard_actions_preserve_motion(self):
        topic="How do volcanoes erupt?"
        scripts=(
            "Molten rock forms a chamber beneath the volcano.",
            "Trapped gas bubbles increase pressure inside the chamber.",
            "Rising magma pushes upward through the vent toward the summit.",
        )
        for expected,narration in zip(BEATS,scripts):
            with self.subTest(beat=expected):
                scene=PortraitScienceScene(topic=topic,narration=narration,
                                           scene_index=3)
                self.assertEqual(scene.volcano_beat,expected)
                early=scene.frame(.6,6.8)
                late=scene.frame(3.1,6.8)
                self.assertEqual(early.mode,"RGB")
                self.assertEqual(early.size,(1080,1920))
                self.assertNotEqual(early.crop((240,1190,850,1570)).tobytes(),
                                    late.crop((240,1190,850,1570)).tobytes())
                self.assertEqual(early.tobytes(),scene.frame(.6,6.8).tobytes())

    def test_reject_unsafe_scale_even_with_previous_cached_values(self):
        for scale in (True,False,0.,.19,1.09,-1,math.nan,math.inf,"1"):
            with self.assertRaises(ValueError):
                reservoir_contour(scale)
        self.assertEqual(reservoir_mask().getpixel(CENTER),255)


if __name__=="__main__":
    unittest.main()
