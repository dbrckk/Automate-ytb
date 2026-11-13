"""Real pixel tests for reusable world-first moving portrait and local Foley glints."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops

from automate_ytb.universal_cinematic_portrait import (
    composite_authored_world, shot_title_alpha)
from automate_ytb.universal_contact_glints import paint_contact_glints
from automate_ytb.universal_kinetic import frame_image, read_story, timeline_for


class CinematicCompositionTests(unittest.TestCase):
    def test_real_original_world_fill_is_aspect_correct_and_matted(self):
        for width in (360,720):
            with self.subTest(width=width):
                base=Image.new("RGB",(width,width*16//9),(12,25,41))
                art=Image.new("RGBA",(295,327),(227,140,89,255))
                before=base.tobytes()
                image=composite_authored_world(base,art)
                self.assertEqual(base.tobytes(),before)
                self.assertEqual(image.mode,"RGB")
                self.assertEqual(image.size,base.size)
                self.assertEqual(image.getpixel((width//2,round(image.height*.45))),
                                 (227,140,89))
                self.assertEqual(image.getpixel((width//2,5)),(12,25,41))
                self.assertEqual(image.getpixel((width//2,image.height-10)),
                                 (12,25,41))
                # Full portrait width is real source color, not a small box.
                self.assertEqual(image.getpixel((2,round(image.height*.45))),
                                 (227,140,89))
                self.assertEqual(image.getpixel((width-3,round(image.height*.45))),
                                 (227,140,89))
                # At the matte edge we preserve the base; no harsh horizontal seam.
                y=round(image.height*.15)
                edge=image.getpixel((width//2,y))
                self.assertNotEqual(edge,(227,140,89))
                self.assertNotEqual(edge,(12,25,41))

    def test_narrow_artwork_keeps_its_original_silhouette(self):
        base=Image.new("RGB",(360,640),(4,9,14))
        picture=Image.new("RGBA",(128,500),(220,121,52,255))
        output=composite_authored_world(base,picture)
        centre=output.getpixel((180,320))
        margin=output.getpixel((10,320))
        self.assertEqual(centre,(220,121,52))
        self.assertEqual(margin,(4,9,14))

    def test_title_is_temporarily_visible_then_fades_without_resets(self):
        self.assertEqual(shot_title_alpha(0,0,180),255)
        self.assertEqual(shot_title_alpha(30,0,180),255)
        self.assertTrue(0<shot_title_alpha(47,0,180)<255)
        self.assertEqual(shot_title_alpha(90,0,180),0)
        self.assertEqual(shot_title_alpha(100,90,180),255)
        self.assertEqual(shot_title_alpha(179,90,180),0)
        for bad in ((-1,0,100),(100,0,100),(0,1,1),(0,20,10)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                shot_title_alpha(*bad)

    def test_rejects_unapproved_frame_types_and_dimensions(self):
        canvas=Image.new("RGB",(360,640))
        artwork=Image.new("RGBA",(296,327))
        for changed,scene in (
            (Image.new("RGB",(360,600)),artwork),
            (canvas,Image.new("RGB",(296,327))),
            (canvas,Image.new("RGBA",(20,20))),
            (Image.new("RGBA",(360,640)),artwork),
        ):
            with self.assertRaises(ValueError):
                composite_authored_world(changed,scene)


class ContactGlintTests(unittest.TestCase):
    def test_distant_actors_never_receive_an_artificial_connector_line(self):
        image=Image.new("RGBA",(620,410))
        paint_contact_glints(image,(100,205),(510,205),.9,stage_width=600)
        self.assertEqual(image.getpixel((305,205))[3],0)
        self.assertGreater(image.getpixel((100,205))[3],0)
        self.assertGreater(image.getpixel((510,205))[3],0)
        again=Image.new("RGBA",image.size)
        paint_contact_glints(again,(100,205),(510,205),.9,stage_width=600)
        self.assertEqual(image.tobytes(),again.tobytes())

    def test_nearby_actors_glint_only_where_they_meet(self):
        image=Image.new("RGBA",(620,410))
        paint_contact_glints(image,(250,205),(310,205),1.,stage_width=600)
        self.assertGreater(image.getpixel((280,205))[3],0)
        self.assertEqual(image.getpixel((100,205))[3],0)
        blank=Image.new("RGBA",(620,410))
        paint_contact_glints(blank,(250,205),(310,205),0,stage_width=600)
        self.assertIsNone(blank.getbbox())
        paint_contact_glints(blank,(-9,-9),(1,1),1,stage_width=600)
        self.assertIsNotNone(blank.getbbox())

    def test_rejects_unsafe_event_parameters(self):
        for intensity in (True,-1,1.1,float("nan"),float("inf"),None):
            with self.subTest(intensity=intensity),self.assertRaises(ValueError):
                paint_contact_glints(Image.new("RGBA",(400,400)),
                    (60,90),(90,90),intensity,stage_width=360)
        for point in (None,12,(1,),("invalid",3),(float("nan"),2)):
            with self.subTest(point=point),self.assertRaises(ValueError):
                paint_contact_glints(Image.new("RGBA",(400,400)),
                    point,(80,90),.5,stage_width=360)


if __name__=="__main__":
    unittest.main()
