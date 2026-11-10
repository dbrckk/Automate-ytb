"""Original shared material advection must work on genuine videos."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.dynamic_material25d import (
    VERSION, MATERIALS, PALETTES, _source_planes, moving_material,
)
from automate_ytb.flow_material25d import vortex_source, vortex_frame
from automate_ytb.science_volcano_magma import _molten_plate, _chamber_mask
from automate_ytb.volcanic_reservoir25d import reservoir_molten_source
from automate_ytb.science_portrait import PortraitScienceScene


class SharedAdvectedMaterialTests(unittest.TestCase):
    def test_source_cache_and_original_dynamic_material_keep_distinct_depth(self):
        for material in MATERIALS:
            with self.subTest(material=material):
                static=_source_planes((452,280),1701)
                self.assertIs(static,_source_planes((452,280),1701))
                self.assertEqual(len(static),3)
                self.assertTrue(all(plane.mode=="L" for plane in static))
                before=tuple(x.tobytes() for x in static)
                a=moving_material((452,280),.8,material=material)
                b=moving_material((452,280),3.7,material=material)
                self.assertEqual(a.size,(452,280))
                self.assertEqual(a.mode,"RGBA")
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),
                                 moving_material((452,280),.8,material=material).tobytes())
                self.assertEqual(before,tuple(x.tobytes() for x in static))
                self.assertLess(a.getchannel("A").getextrema()[0],255)
                self.assertGreater(max(ImageStat.Stat(a.convert("RGB")).stddev),11)
        self.assertEqual(set(MATERIALS),set(PALETTES))
        self.assertTrue(VERSION.endswith("p518-v1"))

    def test_invalid_inputs_are_rejected_before_source_cache(self):
        invalid=(
            ((True,280),1.,"magma",1),
            ((900,False),1.,"water",1),
            ((127,280),1.,"water",1),
            ((901,280),1.,"water",1),
            ([450,280],1.,"magma",1),
            ((450,280),True,"water",1),
            ((450,280),-1.,"magma",1),
            ((450,280),181.,"magma",1),
            ((450,280),math.nan,"magma",1),
            ((450,280),math.inf,"magma",1),
            ((450,280),1.,"invalid",1),
            ((450,280),1.,"water",False),
            ((450,280),1.,"water",1_000_001),
        )
        for size,t,kind,seed in invalid:
            with self.subTest(args=(size,t,kind,seed)):
                with self.assertRaises(ValueError):
                    moving_material(size,t,material=kind,seed=seed)

    def test_magma_overlay_never_mutates_original_source_or_leaks_from_mask(self):
        source=reservoir_molten_source()
        original=source.tobytes()
        a=_molten_plate(.8,6.8,"magma")
        b=_molten_plate(3.2,6.8,"magma")
        self.assertEqual(reservoir_molten_source().tobytes(),original)
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.tobytes(),_molten_plate(.8,6.8,"magma").tobytes())
        self.assertEqual(a.getpixel((20,40))[3],0)
        self.assertEqual(_chamber_mask().getpixel((542,1120)),255)

    def test_ocean_vortex_retains_transparent_rim_and_source_immutability(self):
        baseline=vortex_source(350,seed=385)
        data=baseline.tobytes()
        ocean=vortex_frame(350,2.,seed=385)
        ocean_later=vortex_frame(350,4.,seed=385)
        self.assertEqual(ocean.mode,"RGBA")
        self.assertEqual(ocean.getpixel((0,0))[3],0)
        self.assertEqual(ocean.getpixel((349,349))[3],0)
        self.assertNotEqual(ocean.tobytes(),ocean_later.tobytes())
        self.assertEqual(vortex_source(350,seed=385).tobytes(),data)

    def test_real_volcano_and_ocean_production_share_one_material_engine(self):
        volcanic=PortraitScienceScene(
            topic="How do volcanoes erupt?",
            narration="Trapped gas bubbles build pressure in the magma chamber.",
            scene_index=2)
        marine=PortraitScienceScene(
            topic="Why do ocean currents move?",
            narration="Earth rotation bends currents through the Coriolis effect.",
            scene_index=3)
        self.assertEqual(volcanic.volcano_beat,"pressure")
        self.assertEqual(marine.beat,"coriolis")
        for shot,box in ((volcanic,(300,1160,770,1560)),
                         (marine,(205,755,875,1425))):
            a=shot.frame(.7,6.8)
            b=shot.frame(2.9,6.8)
            self.assertEqual(a.size,(1080,1920))
            self.assertEqual(a.mode,"RGB")
            self.assertNotEqual(a.crop(box).tobytes(),b.crop(box).tobytes())
            self.assertEqual(a.tobytes(),shot.frame(.7,6.8).tobytes())


if __name__=="__main__":
    unittest.main()
