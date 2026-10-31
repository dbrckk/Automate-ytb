"""Narration-to-action coverage for the actual Earth-stop 9:16 renderer."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.science_earth_stop import LABELS, classify, draw
from automate_ytb.science_portrait import PortraitScienceScene


TOPIC = "What If Earth Suddenly Stopped Spinning?"
STORY = {
    "stop": "What if Earth suddenly stopped spinning?",
    "inertia": "At the equator the ground has enormous speed and inertia.",
    "wind": "But the air keeps moving and strong winds sweep across the land.",
    "ocean": "The oceans would create waves and water could flood the coast.",
    "day": "A single day might last most of a year; months of daylight.",
    "poles": "Over time, oceans redistribute toward the poles.",
    "astronaut": "What advice could our astronauts give survivors?",
}


def _fake_globe(t, *, size=620):
    planet = Image.new("RGBA", (size, size))
    d = ImageDraw.Draw(planet)
    d.ellipse((3, 3, size-4, size-4), fill=(30, 151, 200, 255))
    x = size // 2 + round(90 * __import__("math").sin(t*.36))
    d.ellipse((x-45, 200, x+45, 280), fill=(40, 175, 104, 255))
    return planet


class EarthStopMotionTests(unittest.TestCase):
    def test_story_selects_action_from_actual_narration(self):
        for beat, text in STORY.items():
            with self.subTest(beat=beat):
                self.assertEqual(classify(TOPIC, text), beat)
                scene = PortraitScienceScene(topic=TOPIC, narration=text,
                                             scene_index=1)
                self.assertEqual(scene.earth_stop_beat, beat)
        self.assertIsNone(classify("Ocean Currents", "Strong wind"))
        self.assertEqual(classify(TOPIC, "Eventually the oceans shift toward the poles."), "poles")
        self.assertEqual(classify(TOPIC, "The oceans would create waves."), "ocean")
        self.assertIsNone(classify("Rainbows in the Sky", "Earth moves"))
        self.assertEqual(classify("Que se passe-t-il si la Terre arrête sa rotation?",
                                  "Les vents seront violents."), "wind")

    def test_each_of_six_beats_changes_actual_subject_pixels(self):
        for beat in LABELS:
            with self.subTest(beat=beat):
                a = Image.new("RGBA", (1080, 1920), (7, 20, 40, 255))
                b = a.copy()
                draw(a, beat, .1, 3.0, True, _fake_globe)
                draw(b, beat, 2.1, 3.0, True, _fake_globe)
                self.assertIsNotNone(
                    ImageChops.difference(
                        a.convert("RGB").crop((100, 650, 1000, 1450)),
                        b.convert("RGB").crop((100, 650, 1000, 1450)),
                    ).getbbox(), f"{beat} must animate within central scene")

    def test_stopped_earth_does_not_restart_spin_in_daylight_or_polar_story(self):
        samples = []
        def recording_globe(t, *, size=560):
            samples.append(t)
            return _fake_globe(t, size=size)
        for beat in ("poles", "day"):
            samples.clear()
            for moment in (.25, 2.0):
                pic = Image.new("RGBA", (1080, 1920))
                draw(pic, beat, moment, 3.0, True, recording_globe)
            self.assertEqual(samples, [0.0, 0.0],
                             "A stopped Earth must not rotate again in later scenes")

    def test_validates_frame_time_and_canvas(self):
        pic = Image.new("RGBA", (1080,1920))
        for t,duration in [(-.1, 3), (4., 3.), (0.,0.), (float("nan"),3.)]:
            with self.subTest(t=t,duration=duration), self.assertRaises(ValueError):
                draw(pic, "stop", t, duration, True, _fake_globe)
        with self.assertRaises(ValueError):
            draw(pic, "unrelated", 1., 3., True, _fake_globe)
        with self.assertRaises(ValueError):
            draw(Image.new("RGBA", (720,1280)),
                 "stop", 1., 3., True, _fake_globe)


if __name__ == "__main__":
    unittest.main()
