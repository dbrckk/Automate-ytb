import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageChops
from automate_ytb.science_explainer import poster, render_mp4


class ScienceExplainerTests(unittest.TestCase):
    def test_original_poster_is_deterministic_and_1080p(self):
        with tempfile.TemporaryDirectory() as temp:
            a,b,c=(Path(temp)/x for x in ("a.jpg","b.jpg","c.jpg"))
            poster(a,topic="What if Earth stopped spinning?")
            poster(b,topic="What if Earth stopped spinning?")
            poster(c,topic="What if Earth stopped spinning?",phase=1.1)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with Image.open(a) as im:
                self.assertEqual(im.size,(1920,1080))
            self.assertNotEqual(a.read_bytes(),c.read_bytes())

    def test_rejects_invalid_topic_and_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                poster(Path(temp)/"a.jpg",topic="")
            with self.assertRaises(ValueError):
                render_mp4(Path(temp)/"a.mp4",topic="Earth",seconds=-1)
