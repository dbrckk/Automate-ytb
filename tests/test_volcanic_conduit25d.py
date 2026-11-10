"""Full causal agreement of shared 2.5D magma conduit source and animation."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageDraw,ImageChops

from automate_ytb.volcanic_conduit25d import (
    VERSION, VENT, BASE, INNER_WIDTH, conduit_center_x,
    conduit_mask, conduit_path, draw_rock_conduit, active_conduit_path,
)
from automate_ytb.science_volcano import _base
from automate_ytb.science_volcano_magma import _conduit_mask, draw_magma


class SharedMagmaConduitTests(unittest.TestCase):
    def test_single_original_path_remains_connected_to_actual_vent_and_chamber(self):
        path=conduit_path()
        self.assertIs(path,conduit_path())
        self.assertEqual(path[0],VENT)
        self.assertEqual(path[-1],BASE)
        self.assertGreater(len(path),70)
        self.assertTrue(all(a[1]<b[1] for a,b in zip(path,path[1:])))
        self.assertGreater(max(x for x,y in path)-min(x for x,y in path),8)
        self.assertEqual(round(conduit_center_x(VENT[1])),VENT[0])
        self.assertEqual(round(conduit_center_x(BASE[1])),BASE[0])
        self.assertTrue(VERSION.endswith("p516-v1"))

    def test_cached_alpha_mask_shared_with_magma_and_rock(self):
        m=conduit_mask()
        self.assertIs(m,conduit_mask())
        self.assertIs(m,_conduit_mask())
        self.assertEqual(m.mode,"L")
        self.assertEqual(m.size,(1080,1380))
        self.assertEqual(m.getpixel((542,690)),255)
        self.assertEqual(m.getpixel((400,690)),0)
        self.assertEqual(m.getpixel((540,660)),255)
        outer=conduit_mask(outer=True)
        self.assertGreaterEqual(outer.getbbox()[2]-outer.getbbox()[0],
                                m.getbbox()[2]-m.getbbox()[0])
        self.assertEqual(m.getpixel((15,300)),0)

    def test_magma_front_climbs_same_path_at_any_time(self):
        for y in (345,410,645,690,850,1028):
            with self.subTest(y=y):
                active=active_conduit_path(y)
                self.assertEqual(active[0][1],y)
                self.assertEqual(active[-1],BASE)
                self.assertAlmostEqual(active[0][0],conduit_center_x(y),delta=.6)
                self.assertTrue(all(a[1]<=b[1]
                                    for a,b in zip(active,active[1:])))
                self.assertEqual(conduit_mask().getpixel(active[0]),255)

    def test_actual_cutaway_and_ascending_lava_keep_existing_scene_contracts(self):
        rock=_base(True).copy()
        pen=ImageDraw.Draw(rock,"RGBA")
        draw_rock_conduit(pen)
        self.assertEqual(rock.size,(1080,1380))
        early=_base(True).copy()
        late=_base(True).copy()
        draw_magma(early,"ascent",.9,6.8)
        draw_magma(late,"ascent",5.6,6.8)
        self.assertNotEqual(early.tobytes(),late.tobytes())
        self.assertNotEqual(early.getpixel((540,690)),late.getpixel((540,690)))
        self.assertEqual(early.getpixel((20,55)),late.getpixel((20,55)))
        self.assertEqual(late.tobytes(),self._render_again(5.6))

    @staticmethod
    def _render_again(t):
        plate=_base(True).copy()
        draw_magma(plate,"ascent",t,6.8)
        return plate.tobytes()

    def test_magma_and_rock_geometry_reject_unsafe_clock_without_mutating_masks(self):
        before=conduit_mask().tobytes()
        for bad in (True,-1,344,1029,math.nan,math.inf,"700"):
            with self.assertRaises(ValueError):
                conduit_center_x(bad)
            with self.assertRaises(ValueError):
                active_conduit_path(bad)
        with self.assertRaises(ValueError):
            conduit_mask(outer=1)
        self.assertEqual(conduit_mask().tobytes(),before)


if __name__=="__main__":
    unittest.main()
