"""Regressions for truly dynamic and physically local P4.5 plant motion."""
import math
import unittest

from PIL import ImageChops

from automate_ytb.forest25d import ORIGIN_X, SPEED, TORSO_Y, frame
from automate_ytb.forest_contact25d import IMPACT_TIME, contact_at
from automate_ytb.forest_reactive_meadow25d import (
    VERSION, SIZE, ROOTS, blade_motion, meadow_plate,
)


def plate(t, *, interaction=True):
    return meadow_plate(t, origin_x=ORIGIN_X, speed=SPEED,
                        torso_y=TORSO_Y, interaction=interaction)


class PhysicallyReactiveMeadowTests(unittest.TestCase):
    def test_plants_have_rooted_geometry_and_real_between_frame_wind(self):
        self.assertIn("p45", VERSION)
        self.assertGreaterEqual(len(ROOTS), 60)
        a, b = plate(.40, interaction=False), plate(.40+1/30,
                                                      interaction=False)
        self.assertEqual(a.size, SIZE)
        self.assertEqual(a.mode, "RGBA")
        self.assertIsNotNone(a.getchannel("A").getbbox())
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB"), b.convert("RGB")).getbbox())
        # A valid roots' Earth attachment pixel stays in the same world spot.
        for root_x, root_y, _ in ROOTS[::10]:
            pixel=(round(root_x),round(root_y))
            self.assertGreater(a.getpixel(pixel)[3], 0)
            self.assertGreater(b.getpixel(pixel)[3], 0)
        # These effects are genuinely ground-level, not eye-level overlay FX.
        self.assertIsNone(a.crop((0,0,1080,1180)).getbbox())

    def test_paw_contact_propagates_at_finite_world_speed(self):
        hit=contact_at(IMPACT_TIME+.1,origin_x=ORIGIN_X,
                       speed=SPEED,torso_y=TORSO_Y)
        center=hit.x
        self.assertTrue(hit.planted)
        self.assertEqual(blade_motion(IMPACT_TIME-.05,center,
            impact_x=center, impact_time=IMPACT_TIME)[1],0)
        # A 0.2s-old event may affect its origin but not a plant 150px away
        # (finite propagation travel time 150/300=0.5s).
        near=blade_motion(IMPACT_TIME+.2,center,
                          impact_x=center,impact_time=IMPACT_TIME)[1]
        far=blade_motion(IMPACT_TIME+.2,center+150,
                         impact_x=center,impact_time=IMPACT_TIME)[1]
        self.assertGreater(near,10)
        self.assertEqual(far,0)
        self.assertNotEqual(blade_motion(IMPACT_TIME+1.,center+150,
                         impact_x=center,impact_time=IMPACT_TIME)[1],0)

    def test_contact_changes_render_only_after_the_actual_paw_landing(self):
        # Wind is always present. Contact waves must not be fabricated early.
        for t in (0.,IMPACT_TIME-.2,IMPACT_TIME):
            self.assertEqual(plate(t,interaction=True).tobytes(),
                             plate(t,interaction=False).tobytes())
        reaction=plate(IMPACT_TIME+.27,interaction=True)
        ordinary=plate(IMPACT_TIME+.27,interaction=False)
        self.assertIsNotNone(ImageChops.difference(
            reaction.convert("RGB"),ordinary.convert("RGB")).getbbox())
        self.assertEqual(reaction.tobytes(),
                         plate(IMPACT_TIME+.27,interaction=True).tobytes())

    def test_actual_story_compositor_stays_native_portrait(self):
        rendered=frame(IMPACT_TIME+.35,kind="fox",
                       interaction=True,story=True,show_story_titles=False)
        self.assertEqual(rendered.size,SIZE)
        self.assertEqual(rendered.mode,"RGB")

    def test_rejects_invalid_geometry_clocks_and_spoofed_flags(self):
        for t in (math.nan,math.inf,-1.,7.3,True):
            with self.assertRaises(ValueError):
                plate(t)
        for bad in (math.nan, -1., True):
            with self.assertRaises(ValueError):
                blade_motion(1.,bad)
        with self.assertRaises(ValueError):
            blade_motion(2.,300.,impact_x=400.)
        with self.assertRaises(ValueError):
            blade_motion(2.,300.,impact_x=math.inf,impact_time=1.)
        with self.assertRaises(ValueError):
            meadow_plate(2.,origin_x=ORIGIN_X,speed=SPEED,
                         torso_y=TORSO_Y,interaction=1)


if __name__=="__main__":
    unittest.main()
