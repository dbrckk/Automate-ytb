"""Eruption and lava emit localized light onto 3D rock, not empty sky."""
import unittest
from PIL import Image, ImageChops
from automate_ytb.science_volcano_lighting import (
    VERSION,_terrain_mask,illuminate_rock
)

class VolcanicLightingTests(unittest.TestCase):
    def test_static_terrain_mask_and_deterministic_emission(self):
        self.assertIn("rock-masked-light",VERSION)
        self.assertIs(_terrain_mask(),_terrain_mask())
        image=Image.new("RGBA",(1080,1380),(10,17,31,255))
        other=image.copy()
        sources=[(540,345,330,1.0)]
        illuminate_rock(image,sources)
        illuminate_rock(other,sources)
        self.assertEqual(image.tobytes(),other.tobytes())
        self.assertEqual(image.getpixel((0,0)),(10,17,31,255))
        self.assertEqual(image.getpixel((540,65)),(10,17,31,255))
        self.assertNotEqual(image.getpixel((540,540)),(10,17,31,255))
        self.assertIsNotNone(ImageChops.difference(
            image,Image.new("RGBA",image.size,(10,17,31,255))).getbbox())

    def test_light_power_and_coordinates_change_render(self):
        a=Image.new("RGBA",(1080,1380),(10,17,31,255))
        b=a.copy()
        illuminate_rock(a,[(540,345,330,1)])
        illuminate_rock(b,[(540,345,330,.2)])
        self.assertNotEqual(a.tobytes(),b.tobytes())

    def test_unsafe_inputs_refused(self):
        for src in ([(-1,2,-3,.5)],[(540,345,200,1.1)],
                    [(540,345,200,float("nan"))],
                    [(540,345,200,.5)]*25):
            with self.assertRaises(ValueError):
                illuminate_rock(Image.new("RGBA",(1080,1380)),src)
        with self.assertRaises(ValueError):
            illuminate_rock(Image.new("RGB",(1080,1380)),[])
