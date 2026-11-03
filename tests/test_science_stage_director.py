"""Cinematic science camera is continuous, crop-safe, content preserving."""
import unittest
from PIL import Image, ImageChops
from automate_ytb.science_stage_director import FRAME_SIZE, SHOTS, VERSION, pose, reframe


class ScienceDirectorTests(unittest.TestCase):
    def test_every_authored_shot_has_continuous_valid_crop(self):
        self.assertIn("science-director",VERSION)
        self.assertEqual(FRAME_SIZE,(1080,1380))
        for topic,beats in SHOTS.items():
            for beat in beats:
                with self.subTest(topic=topic,beat=beat):
                    previous=None
                    for frame in range(211):
                        t=frame/30
                        z,cx,cy=pose(topic,beat,t,7)
                        half_w,half_h=540/z,690/z
                        self.assertGreater(z,1.0)
                        self.assertGreaterEqual(cx-half_w,-1.e-6)
                        self.assertLessEqual(cx+half_w,1080+1.e-6)
                        self.assertGreaterEqual(cy-half_h,-1.e-6)
                        self.assertLessEqual(cy+half_h,1380+1.e-6)
                        if previous:
                            # Gentle travel, no jerky per-frame camera snap.
                            self.assertLess(abs(z-previous[0]),.009)
                            self.assertLess(abs(cx-previous[1]),4)
                            self.assertLess(abs(cy-previous[2]),8)
                        previous=z,cx,cy

    def test_deterministic_reframing_without_stretch_or_transparency(self):
        image=Image.new("RGBA",FRAME_SIZE,(20,30,50,255))
        d=__import__("PIL.ImageDraw",fromlist=["Draw"]).Draw(image)
        d.ellipse((355,400,555,600),fill=(220,90,34,255))
        first=reframe(image,"volcano","magma",0,7)
        again=reframe(image,"volcano","magma",0,7)
        last=reframe(image,"volcano","magma",7,7)
        self.assertEqual(first.size,FRAME_SIZE)
        self.assertEqual(first.getchannel("A").getextrema(),(255,255))
        self.assertEqual(first.tobytes(),again.tobytes())
        # Alpha remains 255: compare RGB, otherwise Pillow's getbbox() on
        # an RGBA difference incorrectly reports None (zero alpha difference).
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"),last.convert("RGB")).getbbox())
        self.assertEqual(first.getpixel((0,0))[3],255)

    def test_invalid_camera_inputs_fail_explicitly(self):
        stage=Image.new("RGBA",FRAME_SIZE)
        for topic,beat,t,dur in (
            ("unknown","magma",0,7),("volcano","unknown",0,7),
            ("aurora","curtains",-1,7),("aurora","curtains",8,7),
            ("volcano","magma",0,float("nan")),
            ("volcano","magma",0,0)):
            with self.assertRaises(ValueError):
                pose(topic,beat,t,dur)
        with self.assertRaises(ValueError):
            reframe(Image.new("RGB",FRAME_SIZE),"volcano","magma",0,7)
        with self.assertRaises(ValueError):
            reframe(Image.new("RGBA",(1080,930)),"volcano","magma",0,7)
