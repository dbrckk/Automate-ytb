"""Real paw-to-environment 2.5D causal interaction regression tests."""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
import unittest
import wave

from PIL import ImageChops

from automate_ytb.forest_contact25d import (
    IMPACT_TIME, SIZE, VERSION, contact_at, flower_plates,
)
from automate_ytb.forest25d import (
    KINDS, ORIGIN_X, SPEED, TORSO_Y, frame, character_plate,
)
from automate_ytb.rig25d import GROUND, walking_leg


def state(t: float):
    return contact_at(t, origin_x=ORIGIN_X, speed=SPEED, torso_y=TORSO_Y)


def plates(t: float):
    return flower_plates(t, origin_x=ORIGIN_X,
                         speed=SPEED, torso_y=TORSO_Y)


class PhysicalFlowerContactTests(unittest.TestCase):
    def test_flower_contact_matches_actual_ik_planted_right_paw(self):
        paw=walking_leg(IMPACT_TIME+.0001,side="right",
                        origin_x=ORIGIN_X,speed=SPEED,torso_y=TORSO_Y)
        hit=state(IMPACT_TIME+.03)
        self.assertTrue(paw.planted)
        self.assertTrue(hit.planted)
        self.assertAlmostEqual(hit.x,paw.foot[0],places=6)
        self.assertEqual(hit.y,GROUND)
        self.assertEqual(hit.time,IMPACT_TIME)
        for other in (IMPACT_TIME+.05,IMPACT_TIME+.18,IMPACT_TIME+.45):
            with self.subTest(t=other):
                self.assertAlmostEqual(state(other).x,hit.x,places=6)
        self.assertIn("world-paw-grounded",VERSION)

    def test_no_spring_response_or_particles_before_paw_landing(self):
        for t in (0.,1.,IMPACT_TIME-.1,IMPACT_TIME):
            with self.subTest(t=t):
                hit=state(t)
                self.assertFalse(hit.planted)
                self.assertEqual(hit.deformation,0.)
                self.assertEqual(hit.particle_count,0)
        back,front=plates(IMPACT_TIME-.25)
        self.assertEqual(back.size,SIZE)
        self.assertIsNotNone(back.getchannel("A").getbbox())
        self.assertIsNone(front.getchannel("A").getbbox())

    def test_physical_contact_compresses_flower_and_releases_petals(self):
        untouched,p0=plates(IMPACT_TIME-.15)
        impacted,p1=plates(IMPACT_TIME+.30)
        later,p2=plates(IMPACT_TIME+1.1)
        self.assertGreater(state(IMPACT_TIME+.30).deformation,0)
        self.assertGreater(state(IMPACT_TIME+.30).particle_count,0)
        self.assertIsNone(p0.getchannel("A").getbbox())
        self.assertIsNotNone(p1.getchannel("A").getbbox())
        self.assertIsNotNone(ImageChops.difference(
            untouched.convert("RGB"),impacted.convert("RGB")).getbbox())
        self.assertIsNotNone(ImageChops.difference(
            p1.convert("RGB"),p2.convert("RGB")).getbbox())
        self.assertEqual(state(IMPACT_TIME+4).particle_count,0)
        self.assertLess(state(IMPACT_TIME+4).deformation,.01)

    def test_all_original_animals_react_at_same_grounded_foot_contact(self):
        t=IMPACT_TIME+.18
        for kind in KINDS:
            with self.subTest(kind=kind):
                normal,_=character_plate(t,kind=kind)
                reacted,_=character_plate(t,kind=kind,interaction=True)
                self.assertIsNotNone(ImageChops.difference(
                    normal.convert("RGB"),reacted.convert("RGB")).getbbox())
        normal=frame(IMPACT_TIME+.31,kind="rabbit")
        interacting=frame(IMPACT_TIME+.31,kind="rabbit",interaction=True)
        self.assertEqual(interacting.size,SIZE)
        self.assertEqual(interacting.mode,"RGB")
        self.assertIsNotNone(ImageChops.difference(
            normal,interacting).getbbox())

    def test_original_pcm_impact_chime_starts_only_after_actual_foot_contact(self):
        from scripts.render_25d_character_pilot import score
        with tempfile.TemporaryDirectory() as root:
            plain=Path(root)/"base.wav"
            active=Path(root)/"contact.wav"
            score(plain,interaction=False)
            score(active,interaction=True)
            with wave.open(str(plain),"rb") as a, wave.open(str(active),"rb") as b:
                self.assertEqual(a.getparams(),b.getparams())
                self.assertEqual(a.getframerate(),48000)
                first=round((IMPACT_TIME-.015)*48000)
                a.setpos(0)
                b.setpos(0)
                self.assertEqual(a.readframes(first),b.readframes(first))
                a.setpos(round((IMPACT_TIME+.03)*48000))
                b.setpos(round((IMPACT_TIME+.03)*48000))
                self.assertNotEqual(a.readframes(1000),b.readframes(1000))

    def test_rejects_unsafe_contact_and_unexpected_interaction_types(self):
        for t in (float("nan"),float("inf"),-1.,21.):
            with self.subTest(t=t),self.assertRaises(ValueError):
                state(t)
        with self.assertRaises(ValueError):
            contact_at(1.,origin_x=float("nan"),
                       speed=SPEED,torso_y=TORSO_Y)
        with self.assertRaises(ValueError):
            contact_at(1.,origin_x=ORIGIN_X,
                       speed=0.,torso_y=TORSO_Y)
        with self.assertRaises(ValueError):
            frame(1.0,kind="cat",interaction=1)
        with self.assertRaises(ValueError):
            character_plate(1.0,kind="fox",interaction="true")


if __name__=="__main__":
    unittest.main()
