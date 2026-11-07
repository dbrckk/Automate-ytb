"""Deterministic actual 3D tracer timing and original path interpolation."""
from __future__ import annotations

import math
import unittest

from automate_ytb.aurora_tracer_motion import (
    TRACERS_PER_PATH, interpolate, progress,
)


class OriginalChargedTracerMotionTests(unittest.TestCase):
    def test_four_independent_particles_advance_on_solar_source_paths(self):
        self.assertEqual(TRACERS_PER_PATH,4)
        locations = []
        for slot in range(TRACERS_PER_PATH):
            t0, alpha0 = progress("solar_wind",0.,1,slot)
            t1, alpha1 = progress("solar_wind",.18,1,slot)
            self.assertTrue(0 <= t0 < 1 and 0 <= t1 < 1)
            self.assertGreater(alpha0,0)
            self.assertGreater(alpha1,0)
            self.assertAlmostEqual((t1-t0) % 1,1.04*.18)
            locations.append(t0)
        self.assertEqual(len(set(locations)),TRACERS_PER_PATH)

    def test_real_3d_path_changes_all_three_coordinates(self):
        knots=[(-4.,0.,1.),(-1.,2.,2.),(2.,-1.,4.),(4.,0.,5.)]
        for beat in ("solar_wind","magnetic_field"):
            t0,_=progress(beat,.02,0,0)
            t1,_=progress(beat,.17,0,0)
            start=interpolate(knots,t0)
            moved=interpolate(knots,t1)
            self.assertGreater(math.dist(start,moved),.3)
            self.assertNotEqual(start[0],moved[0])
            self.assertNotEqual(start[1],moved[1])
            self.assertNotEqual(start[2],moved[2])

    def test_wrap_is_hidden_by_geometric_visibility(self):
        # Glow disappears at the end of the path before it loops back.
        t,visibility=progress("solar_wind",0.,0,0)
        self.assertEqual(t,0.)
        self.assertLess(visibility,.01)
        self.assertEqual(interpolate([(0.,0.,0.),(2.,3.,5.)],0.),(0.,0.,0.))
        self.assertEqual(interpolate([(0.,0.,0.),(2.,3.,5.)],1.),(2.,3.,5.))

    def test_invalid_inputs_are_rejected_without_blender(self):
        for beat,q,i,j in (
            ("ocean",0.,0,0),("solar_wind",float("nan"),0,0),
            ("solar_wind",-1.,0,0),("solar_wind",1.1,0,0),
            ("solar_wind",.5,-1,0),("solar_wind",.5,0,4),
        ):
            with self.subTest(beat=beat,q=q,i=i,j=j):
                with self.assertRaises(ValueError):
                    progress(beat,q,i,j)
        for points,at in (
            ([(1.,2.,3.)],.5),
            ([(0,0,0),(1,2,3)],float("inf")),
            ([(0,0,0),(1,2,3)],2.),
            ([(1.,2.),(3.,4.)],.2),
            ([(0.,0.,0.),(float("nan"),1,2)],.5),
        ):
            with self.assertRaises(ValueError):
                interpolate(points,at)


if __name__ == "__main__":
    unittest.main()
