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

    def test_phone_subtitles_use_large_legible_type_without_overflow(self):
        from PIL import ImageDraw
        from automate_ytb.science_motion import _font
        for beat, narration in self.examples:
            with self.subTest(beat=beat):
                scene = PortraitScienceScene(
                    topic=self.topic, narration=narration, scene_index=1)
                preview = scene.frame(.25, 1.0)
                self.assertEqual(preview.size, PORTRAIT_SIZE)
                active = scene.active_caption(.25, 1.0)
                lines, fontsize = scene._caption_layouts[active]
                # 40px native type displays at roughly 13px on a 360px phone.
                self.assertGreaterEqual(fontsize, 38)
                self.assertLessEqual(len(lines), 3)
                self.assertLessEqual(1551 + 46*(len(lines)-1) + fontsize, 1722)
                probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                for line in lines:
                    self.assertLessEqual(
                        probe.textbbox((0, 0), line,
                                       font=_font(fontsize, True))[2], 842)

    def test_cause_process_effect_progresses_without_overwriting_subtitles(self):
        from automate_ytb.science_storyboards import PROGRESSION
        self.assertEqual(set(PROGRESSION), set(BEATS))
        for beat, narration in self.examples:
            with self.subTest(beat=beat):
                scene = PortraitScienceScene(
                    topic=self.topic, narration=narration, scene_index=1)
                timeline = [scene.frame(t, 6.0) for t in (.7, 2.7, 4.7)]
                # A real timeline has three independent chapter states and a
                # continuously moving fill; it is not a static stage badge.
                bands = [f.crop((80, 548, 1000, 595)).tobytes()
                         for f in timeline]
                self.assertEqual(len(set(bands)), 3)
                self.assertEqual(len(PROGRESSION[beat][0]), 3)
                self.assertEqual(len(PROGRESSION[beat][1]), 3)
                captions = [f.crop((65, 1522, 1015, 1722)).tobytes()
                            for f in timeline]
                self.assertEqual(len(set(captions)), 1)
                # Original frame resolution and the actual animated hero
                # remain unchanged; no slower compositing or globe projection.
                self.assertTrue(all(f.size == PORTRAIT_SIZE for f in timeline))
                self.assertFalse(scene._globes)

    def test_heat_reservoir_names_are_readable_against_colored_cards(self):
        scene = PortraitScienceScene(
            topic=self.topic,
            narration="Currents redistribute heat around Earth and influence climate.",
            scene_index=5)
        frame = scene.frame(2.5, 6.0)
        self.assertEqual(scene.beat, "heat")
        # Previously the WARM/COOL glyphs used identical foreground and
        # background hues; on the real encoded MP4 both words vanished.
        for x in (208, 733):
            with self.subTest(x=x):
                pixels = frame.crop((x, 981, x+146, 1032)).getdata()
                self.assertGreater(sum(1 for r, g, b in pixels
                                       if r >= 225 and g >= 235 and b >= 235), 15)

    def test_causal_timeline_rejects_invalid_durations(self):
        from PIL import ImageDraw
        from automate_ytb.science_storyboards import PROGRESSION
        pen = ImageDraw.Draw(Image.new("RGBA", PORTRAIT_SIZE), "RGBA")
        self.assertEqual(len(PROGRESSION), 5)
        for duration in (0, -1, float("nan"), float("inf"), 181, True):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                draw_storyboard(pen, "heat", .1, True, duration=duration)
        with self.assertRaises(ValueError):
            draw_storyboard(pen, "heat", 5.01, True, duration=5.0)
        with self.assertRaises(ValueError):
            draw_storyboard(pen, "wind", float("nan"), True, duration=6.0)

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
