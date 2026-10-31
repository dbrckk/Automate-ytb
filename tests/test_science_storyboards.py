"""Real pixel-level regressions for five distinct free science Shorts storyboards."""
from __future__ import annotations

import hashlib
import math
import unittest

from PIL import Image, ImageChops

from automate_ytb.science_storyboards import BEATS, classify, draw_storyboard
from automate_ytb.science_portrait import PortraitScienceScene, PORTRAIT_SIZE


class TopicStoryboardTests(unittest.TestCase):
    topic = "Why Do Ocean Currents Move?"
    examples = (
        ("solar", "Sunlight heats tropical oceans more than polar waters, creating contrasts."),
        ("wind", "Global winds push surface waters, driving powerful currents between continents."),
        ("coriolis", "Earth rotation bends currents through the Coriolis effect into rotating gyres."),
        ("sinking", "Near the poles, cold salty ocean water sinks into the deep circulation."),
        ("heat", "Connected currents redistribute heat around Earth and influence climate."),
    )

    def test_five_distinct_semantic_storyboards_from_real_release_narration(self):
        self.assertEqual(len(BEATS), 5)
        self.assertEqual(tuple(classify(self.topic, text) for _, text in self.examples),
                         tuple(beat for beat, _ in self.examples))
        self.assertIsNone(classify(self.topic, "Fish swim below the waves."))
        self.assertIsNone(classify("Earth's ocean atmosphere", self.examples[0][1]))
        self.assertIsNone(classify("Black holes", self.examples[2][1]))
        self.assertEqual(
            classify("Pourquoi les courants océaniques bougent-ils ?",
                     "Le vent entraîne les eaux de surface."), "wind")
        for a, b in ((None, "wind"), ("ocean currents", None)):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                classify(a, b)

    def test_every_beat_renders_distinct_original_frames_at_native_resolution(self):
        signatures = []
        for beat, narration in self.examples:
            with self.subTest(beat=beat):
                scene = PortraitScienceScene(
                    topic=self.topic, narration=narration, scene_index=1)
                self.assertEqual(scene.beat, beat)
                self.assertTrue(scene.english, "English science needs English labels")
                initial = scene.frame(0., 1.)
                later = scene.frame(.4, 1.)
                self.assertEqual(initial.size, PORTRAIT_SIZE)
                self.assertEqual(initial.mode, "RGB")
                # The actual hero artwork changes over time, not just captions.
                hero_start = initial.crop((95, 730, 985, 1460))
                hero_end = later.crop((95, 730, 985, 1460))
                self.assertIsNotNone(ImageChops.difference(hero_start, hero_end).getbbox())
                self.assertEqual(initial.tobytes(), scene.frame(0., 1.).tobytes())
                self.assertFalse(scene._globes, "Story diagrams must not allocate expensive globe poses")
                # Native source UI-safe title and caption areas remain present.
                self.assertNotEqual(initial.getpixel((90,235)), initial.getpixel((20,235)))
                self.assertNotEqual(initial.getpixel((90,1555)), initial.getpixel((20,1555)))
                signatures.append(hashlib.sha256(hero_start.tobytes()).hexdigest())
        self.assertEqual(len(set(signatures)), 5)

    def test_existing_non_story_topics_keep_the_generic_animation(self):
        shot = PortraitScienceScene(topic="How Earth rotates",
                                    narration="The Earth moves from daylight to night.", scene_index=1)
        self.assertIsNone(shot.beat)
        self.assertEqual(shot.mode, "daylight")
        shot.frame(.2, 1.)
        self.assertTrue(shot._globes)

    def test_storyboard_rejects_invalid_animation_arguments(self):
        canvas = Image.new("RGBA", PORTRAIT_SIZE)
        from PIL import ImageDraw
        pen = ImageDraw.Draw(canvas, "RGBA")
        for beat, t, english in (("unknown", 0, True), ("solar", -1, True),
                                  ("wind", math.nan, True), ("heat", 0, "yes")):
            with self.subTest(beat=beat, t=t, english=english), self.assertRaises(ValueError):
                draw_storyboard(pen, beat, t, english)


if __name__ == "__main__":
    unittest.main()
