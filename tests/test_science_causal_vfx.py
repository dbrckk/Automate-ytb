"""Regression checks for causal ocean event trajectories and audio cue selection."""
from __future__ import annotations

import unittest
from PIL import Image, ImageDraw

from automate_ytb.science_causal_vfx import (
    BEATS, _trajectory, draw_interactions, event_phase,
)
from automate_ytb.science_audio_cues import audio_event_fraction


class OceanCausalMotionTests(unittest.TestCase):
    def test_event_trigger_is_bounded_and_responds_to_narration(self):
        self.assertEqual(event_phase(0, 6), 0)
        self.assertEqual(event_phase(6, 6), 1)
        self.assertEqual(event_phase(0.3, 6, 0.8), 0)
        self.assertGreater(event_phase(2.5, 6, 0.2),
                           event_phase(2.5, 6, 0.8))

    def test_all_actions_have_source_target_inside_storyboard(self):
        for beat in BEATS:
            with self.subTest(beat=beat):
                for fraction in (0, 0.05, 0.15, 0.3, 0.5, 0.75, 1):
                    x, y = _trajectory(beat, fraction)
                    self.assertTrue(110 <= x <= 960, (beat, fraction, x))
                    self.assertTrue(750 <= y <= 1450, (beat, fraction, y))

    def test_draw_is_reproducible_and_event_is_visible(self):
        def frame(t, event):
            picture = Image.new("RGBA", (1080, 1500), (0, 0, 0, 0))
            draw_interactions(ImageDraw.Draw(picture, "RGBA"), "sinking",
                              t=t, duration=6, event_progress=event)
            return picture
        self.assertEqual(frame(.2, .85).getbbox(), None)
        self.assertNotEqual(frame(3, .2).getbbox(), None)
        self.assertNotEqual(frame(3, .2).tobytes(), frame(4, .2).tobytes())
        self.assertEqual(frame(3, .2).tobytes(), frame(3, .2).tobytes())

    def test_invalid_timing_rejected(self):
        for event in (-0.1, 1.2, float("nan")):
            with self.assertRaises(ValueError):
                event_phase(1, 6, event)
        with self.assertRaises(ValueError):
            event_phase(7, 6)

    def test_all_five_ocean_scenes_accept_real_phrase_boundaries(self):
        cases = {
            "solar": "Sunlight heats tropical water.",
            "wind": "Winds push the upper layer.",
            "coriolis": "Earth's rotation bends the current.",
            "sinking": "Cold salty water sinks.",
            "heat": "The ocean transports heat.",
        }
        for beat, text in cases.items():
            with self.subTest(beat=beat):
                cue = audio_event_fraction("ocean", beat, [
                    {"text": text, "startMs": 3000, "endMs": 5000},
                    {"text": "Another authored phrase.", "startMs": 5000,
                     "endMs": 7000},
                ], 3000)
                self.assertAlmostEqual(cue, .25, places=6)
                self.assertIsNone(audio_event_fraction("ocean", beat, None, 3000))


if __name__ == "__main__":
    unittest.main()
