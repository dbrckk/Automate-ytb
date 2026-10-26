"""Premium-looking original fur and plumage detail remains alpha-safe."""
import unittest
from PIL import Image, ImageChops
from automate_ytb.animal_microtexture import paint_microtexture


class MicrotextureTests(unittest.TestCase):
    def test_texture_changes_color_not_silhouette(self):
        for kind,part,size in (("fox","body",(350,440)),
                               ("rabbit","tail",(230,240)),
                               ("cat","ear",(150,240)),
                               ("owl","body",(322,430)),
                               ("owl","wing",(164,212))):
            with self.subTest(kind=kind,part=part):
                im=Image.new("RGBA",size)
                from PIL import ImageDraw
                d=ImageDraw.Draw(im)
                d.ellipse((12,12,size[0]-12,size[1]-12),fill=(115,95,155,255))
                original=im.copy()
                paint_microtexture(im,kind=kind,part=part)
                self.assertEqual(im.getchannel("A").tobytes(),
                                 original.getchannel("A").tobytes())
                self.assertIsNotNone(ImageChops.difference(im,original).getbbox())
                repeat=original.copy()
                paint_microtexture(repeat,kind=kind,part=part)
                self.assertEqual(im.tobytes(),repeat.tobytes())

    def test_unsupported_plates_are_rejected(self):
        with self.assertRaises(ValueError):
            paint_microtexture(Image.new("RGB",(100,100)),kind="fox",part="body")
        with self.assertRaises(ValueError):
            paint_microtexture(Image.new("RGBA",(100,100)),kind="owl",part="ear")
