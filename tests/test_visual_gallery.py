"""Mobile-friendly genuine 4-up storyboard quality review."""
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageChops
from automate_ytb.visual_gallery import GALLERY_VERSION, render_gallery, SHEETS


class CharacterGalleryTests(unittest.TestCase):
    def test_real_original_art_for_four_independent_species(self):
        self.assertEqual(len(SHEETS),4)
        self.assertIn("v1",GALLERY_VERSION)
        self.assertEqual({row[1] for row in SHEETS},{"fox","rabbit","cat","owl"})
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/"qa.png"
            render_gallery(dest)
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size,12000)
            with Image.open(dest) as img:
                self.assertEqual(img.mode,"RGB")
                self.assertEqual(img.size,(1920,1080))
                quadrants=[]
                for row in range(2):
                    for col in range(2):
                        x,y=col*960,row*540
                        quadrants.append(img.crop((x+160,y+150,x+470,y+415)))
                for a,b in zip(quadrants,quadrants[1:]):
                    self.assertIsNotNone(ImageChops.difference(a,b).getbbox())

    def test_output_path_validation(self):
        with self.assertRaises(ValueError):
            render_gallery("not-a-Path")
