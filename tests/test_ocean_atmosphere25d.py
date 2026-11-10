"""Verify continuous original undersea plates never reuse space starfields."""
from __future__ import annotations

import unittest

from PIL import Image,ImageChops

from automate_ytb.ocean_atmosphere25d import (
    underwater_background, SIZE, VERSION,
)
from automate_ytb.science_portrait import PortraitScienceScene, _sky


class UnderseaAtmosphereTests(unittest.TestCase):
    def test_cached_star_free_source_is_valid_opaque_portrait(self):
        seed=271818
        ocean=underwater_background(seed)
        self.assertEqual(ocean.size,SIZE)
        self.assertEqual(ocean.mode,"RGBA")
        self.assertIs(ocean,underwater_background(seed))
        self.assertEqual(ocean.getchannel("A").getextrema(),(255,255))
        self.assertNotEqual(ocean.tobytes(),_sky(seed).tobytes())
        self.assertNotEqual(ocean.tobytes(),underwater_background(seed+13).tobytes())
        # The mobile title area has no bright stars or stray high-intensity
        # point sources; it is a genuine continuously blue shaded medium.
        for x,y in ((27,150),(240,220),(600,330),(900,380)):
            r,g,b,a=ocean.getpixel((x,y))
            self.assertLess(r,80)
            self.assertLess(g,125)
            self.assertLess(b,155)
        self.assertTrue(VERSION.endswith("p514-v2"))

    def test_all_ocean_storyboards_receive_star_free_environment(self):
        topic="Why do ocean currents move?"
        for scene_index,narration in enumerate((
            "The sun heats the surface ocean unevenly.",
            "Winds drive surface currents across the sea.",
            "Earth rotation bends currents through Coriolis effect.",
            "Cold salty polar water sinks into deep circulation.",
            "Ocean currents transport heat around the planet.",
        ),start=1):
            with self.subTest(scene_index=scene_index):
                scene=PortraitScienceScene(topic=topic,
                    narration=narration,scene_index=scene_index)
                self.assertIsNotNone(scene.beat)
                self.assertEqual(scene.base.mode,"RGBA")
                self.assertEqual(scene.base.size,SIZE)
                self.assertLess(scene.base.getpixel((240,220))[0],80)
                self.assertEqual(scene.frame(.25,6.).size,SIZE)

    def test_earth_space_videos_keep_their_original_space_environment(self):
        shot=PortraitScienceScene(topic="How does the Earth rotate?",
                                 narration="The Earth spins through day and night.",
                                 scene_index=1)
        self.assertIsNone(shot.beat)
        self.assertIsNone(shot.rainbow_beat)
        # Original dark space palette with point stars is deliberately
        # preserved for space-oriented videos, not for oceanography.
        self.assertEqual(shot.base.tobytes(),_sky(
            int.from_bytes(__import__("hashlib").sha256(
                b"How does the Earth rotate?|1|portrait").digest()[:8],"big")
        ).tobytes())

    def test_bounded_seed_contract(self):
        for invalid in (-1,False,2**64+1,4.2):
            with self.assertRaises(ValueError):
                underwater_background(invalid)


if __name__=="__main__":
    unittest.main()
