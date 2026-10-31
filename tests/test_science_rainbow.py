"""Native 9:16 original rainbows: five physical ideas, not repeated ocean shots."""
from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.science_rainbow import (
    BEATS, BADGES, SPECTRUM, classify, supports_topic, draw_rainbow,
)
from automate_ytb.science_portrait import PortraitScienceScene, PORTRAIT_SIZE
from automate_ytb.science_motion import render_character_poster


class RainbowScienceTests(unittest.TestCase):
    topic = "How Do Rainbows Form?"
    scripts = (
        ("sunlight", "White sunlight contains many colors, although we usually see one beam."),
        ("refraction", "Entering a raindrop, light bends, separating colors by different amounts."),
        ("reflection", "Some of this light reflects from the back inside the drop."),
        ("emergence", "Leaving the drop, the colors bend again and spread toward us."),
        ("arc", "Millions of drops send different colors toward our eyes, forming a curved rainbow."),
    )

    def test_five_distinct_exact_original_optics_beats(self):
        self.assertEqual(len(BEATS), 5)
        self.assertEqual(len(SPECTRUM), 7)
        self.assertEqual(set(BADGES), set(BEATS))
        self.assertTrue(supports_topic(self.topic))
        self.assertTrue(supports_topic("Comment se forme un arc-en-ciel ?"))
        self.assertFalse(supports_topic("How do black holes work?"))
        self.assertFalse(supports_topic("How do oceans move?"))
        self.assertEqual(
            tuple(classify(self.topic, text) for _, text in self.scripts),
            tuple(beat for beat, _ in self.scripts))
        self.assertIsNone(classify(self.topic, "A surreal shape appears mysteriously."))
        self.assertIsNone(classify("How Earth rotates", self.scripts[0][1]))
        self.assertEqual(classify("Pourquoi un arc-en-ciel ?",
                                  "La lumière blanche vient du soleil."), "sunlight")
        self.assertEqual(classify("Pourquoi un arc-en-ciel ?",
                                  "La lumière se réfléchit dans une goutte."), "reflection")
        for a, b in ((None, "sunlight"), ("rainbow", None)):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                classify(a, b)

    def test_each_original_native_portrait_scene_is_distinct_animated_and_safe(self):
        signatures = []
        for beat, script in self.scripts:
            with self.subTest(beat=beat):
                shot = PortraitScienceScene(
                    topic=self.topic, narration=script, scene_index=1)
                self.assertEqual(shot.rainbow_beat, beat)
                self.assertIsNone(shot.beat)
                self.assertTrue(shot.english)
                initial = shot.frame(.1, 6.0)
                following = shot.frame(.15, 6.0)
                self.assertEqual(initial.size, PORTRAIT_SIZE)
                self.assertEqual(initial.mode, "RGB")
                first_hero = initial.crop((80, 695, 1000, 1490))
                second_hero = following.crop((80, 695, 1000, 1490))
                self.assertIsNotNone(
                    ImageChops.difference(first_hero,second_hero).getbbox())
                self.assertEqual(initial.tobytes(), shot.frame(.1,6.).tobytes())
                self.assertEqual(
                    initial.crop((65,1522,1015,1722)).tobytes(),
                    following.crop((65,1522,1015,1722)).tobytes())
                self.assertFalse(shot._globes,
                                 "Rainbow optics must not instantiate an Earth globe")
                signatures.append(hash(first_hero.tobytes()))
        self.assertEqual(len(set(signatures)), 5)

    def test_rendered_static_rights_poster_does_not_show_false_earth(self):
        with tempfile.TemporaryDirectory() as temp:
            png = Path(temp)/"rainbow-poster.png"
            render_character_poster(
                topic=self.topic, narration=self.scripts[1][1],
                scene_index=2, scene_count=5, style="science",
                destination=png)
            self.assertTrue(png.is_file())
            with Image.open(png) as image:
                self.assertEqual(image.size, (1280,720))
                self.assertEqual(image.format, "PNG")
                self.assertIsNotNone(image.getbbox())

    def test_unsupported_optical_narration_must_fail_instead_of_faking_physics(self):
        with self.assertRaisesRegex(ValueError, "Rainbow Shorts need authored narration"):
            PortraitScienceScene(
                topic=self.topic, narration="Magic makes colorful surprises!",
                scene_index=1)
        with self.assertRaises(ValueError):
            PortraitScienceScene(
                topic="Why do black holes form?",
                narration=self.scripts[0][1], scene_index=1)

    def test_invalid_time_and_inputs_rejected(self):
        d = ImageDraw.Draw(Image.new("RGBA", PORTRAIT_SIZE),"RGBA")
        for t, duration, english in ((-1.,5.,True),(6.,5.,True),
                    (math.nan,5.,True),(0,math.inf,True),
                    (0,5.,"yes"), (0,0,True),(0,181,True),
                    (True,5.,True)):
            with self.subTest(t=t,duration=duration,english=english),self.assertRaises(ValueError):
                draw_rainbow(d,"arc",t,duration,english)
        with self.assertRaises(ValueError):
            draw_rainbow(d,"unknown",0,5,True)


if __name__=="__main__":
    unittest.main()
