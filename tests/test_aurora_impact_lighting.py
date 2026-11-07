"""Regression coverage for genuinely reaction-driven Blender POINT lights."""
from __future__ import annotations

import math
import unittest

from automate_ytb.aurora_impact_lighting import (
    PEAK_ENERGY, VERSION, impact_light_color, impact_light_energy,
)


class AuroraImpactLightingTests(unittest.TestCase):
    def test_all_ten_original_impacts_produce_timed_light_not_constant_glow(self):
        self.assertIn("impact-lighting", VERSION)
        for beat in ("collisions", "emission"):
            for index in range(10):
                hit=.27+.048*(index%9)
                with self.subTest(beat=beat,index=index):
                    self.assertEqual(impact_light_energy(beat,0.,hit),0.)
                    self.assertEqual(impact_light_energy(beat,hit-.001,hit),0.)
                    self.assertAlmostEqual(
                        impact_light_energy(beat,hit,hit),PEAK_ENERGY[beat])
                    self.assertLess(
                        impact_light_energy(beat,hit+.25,hit),
                        PEAK_ENERGY[beat]*.15)
                    self.assertLess(
                        impact_light_energy(beat,1.0,hit),
                        PEAK_ENERGY[beat])
                    color=impact_light_color(beat,index)
                    self.assertEqual(len(color),3)
                    self.assertTrue(all(0<=x<=1 for x in color))
                    self.assertGreater(max(color),.75)

    def test_flash_energy_monotonically_decays_after_impact(self):
        for beat in ("collisions", "emission"):
            hit=.36
            values=[impact_light_energy(beat,hit+d,hit)
                    for d in (0., .025, .065, .10, .20, .30)]
            self.assertEqual(values,sorted(values,reverse=True))
            self.assertGreater(values[0],180)
            self.assertLess(values[-1],.15*values[0])

    def test_different_atmospheric_events_have_distinct_lights(self):
        collisions={impact_light_color("collisions",i) for i in range(10)}
        emission={impact_light_color("emission",i) for i in range(10)}
        self.assertEqual(len(collisions),2)
        self.assertEqual(len(emission),3)
        self.assertNotEqual(collisions,emission)
        self.assertGreater(PEAK_ENERGY["emission"],PEAK_ENERGY["collisions"])

    def test_invalid_or_non_finite_impacts_fail_closed(self):
        for beat,q,hit in (
            ("curtains",.3,.27),("emission",-1.,.27),
            ("collisions",1.1,.27),("collisions",float("nan"),.27),
            ("collisions",.3,float("inf")),("collisions",.3,0.),
            ("emission",.2,1.),("emission",.2,-.2),
            ("collisions",True,.27),("collisions",.25,True),
        ):
            with self.subTest(beat=beat,q=q,hit=hit):
                with self.assertRaises(ValueError):
                    impact_light_energy(beat,q,hit)
        for beat,index in (
            ("solar_wind",2),("collisions",-1),("emission",10),
            ("emission",True),("emission",1.2),
        ):
            with self.assertRaises(ValueError):
                impact_light_color(beat,index)


if __name__=="__main__":
    unittest.main()
