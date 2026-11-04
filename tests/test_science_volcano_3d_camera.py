"""The eruption rock geometry is genuinely reprojected in 3D per frame."""
import math
import unittest

from PIL import Image, ImageChops

from automate_ytb.science_volcano_3d_camera import (
    VERSION, SIZE, camera_yaw, world_to_screen,
    render_orbit_terrain, _geometry,
)
from automate_ytb.science_volcano import draw_volcano


class VolcanicCamera3DTests(unittest.TestCase):
    def test_camera_moves_world_geometry_not_flat_image(self):
        self.assertIn("worldspace-camera",VERSION)
        self.assertEqual(SIZE,(1080,1380))
        self.assertGreater(len(_geometry()),2000)
        self.assertAlmostEqual(camera_yaw(0,7),-.17)
        self.assertAlmostEqual(camera_yaw(7,7),.17)
        self.assertAlmostEqual(camera_yaw(3.5,7),0)
        for t in (0,.5,2,3.5,6,7):
            y=camera_yaw(t,7)
            summit=world_to_screen(0,0,685,y)
            self.assertAlmostEqual(summit[0],540)
            self.assertAlmostEqual(summit[1],1050-685*1.03)
        flank=(320,-130,200)
        start=world_to_screen(*flank,camera_yaw(0,7))
        finish=world_to_screen(*flank,camera_yaw(7,7))
        self.assertGreater(abs(start[0]-finish[0]),5)
        self.assertGreater(abs(start[1]-finish[1]),1)

    def test_rendered_faces_change_with_camera_and_keep_safe_mask(self):
        start=render_orbit_terrain(.3,6.8)
        finish=render_orbit_terrain(6.5,6.8)
        self.assertEqual(start.mode,"RGBA")
        self.assertEqual(start.size,SIZE)
        self.assertEqual(start.getpixel((1,100))[3],0)
        self.assertEqual(finish.getpixel((540,1180))[3],0)
        self.assertGreater(start.getpixel((540,620))[3],100)
        self.assertIsNotNone(ImageChops.difference(
            start.convert("RGB"),finish.convert("RGB")).getbbox())
        self.assertEqual(start.tobytes(),render_orbit_terrain(.3,6.8).tobytes())

    def test_full_eruption_uses_real_3d_stage_without_changing_output_size(self):
        image=Image.new("RGBA",(1080,1920),(9,20,39,255))
        before=image.copy()
        draw_volcano(image,"eruption",1.1,6.8,True)
        self.assertEqual(image.size,(1080,1920))
        self.assertEqual(image.getchannel("A").getextrema(),(255,255))
        self.assertEqual(image.getpixel((20,1860)),before.getpixel((20,1860)))
        self.assertNotEqual(image.tobytes(),before.tobytes())

    def test_untrusted_clocks_and_world_inputs_are_rejected(self):
        for value in (-1,7.1,float("inf"),float("nan"),"1",True):
            with self.assertRaises(ValueError):
                camera_yaw(value,7)
        for duration in (0,-1,181,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                render_orbit_terrain(1,duration)
        for bad in (float("nan"),float("inf"),True):
            with self.assertRaises(ValueError):
                world_to_screen(bad,0,0,0)
        with self.assertRaises(ValueError):
            world_to_screen(0,0,0,5)
