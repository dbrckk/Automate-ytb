"""Real 3D-world perspective, mesh surfaces and camera motion regressions."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops

from automate_ytb.science_city3d import (
    BEATS, Camera3D, camera_pose, city_blocks, draw_city_mesh,
)


class CityMesh3DTests(unittest.TestCase):
    def setUp(self):
        self.blank=Image.new("RGBA",(1080,1920),(9,26,47,255))

    def test_pinhole_projection_has_actual_perspective_and_depth(self):
        eye=Camera3D((0.,6.,-10.),(0.,2.,18.))
        near=eye.project((2.,3.,5.))
        far=eye.project((2.,3.,35.))
        self.assertIsNotNone(near)
        self.assertIsNotNone(far)
        self.assertLess(near[2],far[2])
        self.assertGreater(abs(near[0]-540),abs(far[0]-540))
        self.assertNotEqual(
            eye.project((2.,3.,5.))[:2],eye.project((2.,7.,5.))[:2])
        self.assertEqual(eye.project((1.,1.,-50.)),None)
        self.assertGreaterEqual(len(tuple(city_blocks())),12)
        self.assertGreater(len({b[5] for b in city_blocks()}),4)

    def test_true_camera_translation_changes_projection(self):
        first=camera_pose(0,6,"inertia")
        last=camera_pose(6,6,"inertia")
        self.assertNotEqual(first.eye,last.eye)
        self.assertNotEqual(first.target,last.target)
        self.assertNotEqual(first.project((4.,6.,20.)),
                            last.project((4.,6.,20.)))
        self.assertGreater(last.eye[2],first.eye[2])
        self.assertNotEqual(camera_pose(0,6,"wind").eye[2],
                            camera_pose(6,6,"wind").eye[2])

    def test_city_is_in_native_portrait_and_preserves_editorial_zones(self):
        for beat in BEATS:
            with self.subTest(beat=beat):
                a,b=self.blank.copy(),self.blank.copy()
                draw_city_mesh(a,beat,.2,6)
                draw_city_mesh(b,beat,5.3,6)
                top=(0,0,1080,570)
                bottom=(0,1455,1080,1920)
                for bounds in (top,bottom):
                    self.assertEqual(a.crop(bounds).tobytes(),
                                     self.blank.crop(bounds).tobytes())
                scenic=(35,700,1045,1400)
                self.assertIsNotNone(ImageChops.difference(
                    a.convert("RGB").crop(scenic),
                    b.convert("RGB").crop(scenic)).getbbox())
                self.assertIsNotNone(ImageChops.difference(
                    a.convert("RGB").crop(scenic),
                    self.blank.convert("RGB").crop(scenic)).getbbox())
                identical=self.blank.copy()
                draw_city_mesh(identical,beat,.2,6)
                self.assertEqual(a.tobytes(),identical.tobytes())

    def test_invalid_projection_rejected_before_drawing(self):
        for bad in (
            ("inertia",float("nan"),6),
            ("inertia",-1,6),
            ("ocean",7,6),
            ("wind",0,0),
            ("not-a-beat",1,6),
        ):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                draw_city_mesh(self.blank,*bad)
        with self.assertRaises(ValueError):
            draw_city_mesh(Image.new("RGB",(1080,1920)),"wind",1,6)
        with self.assertRaises(ValueError):
            Camera3D((0.,0.,0.),(0.,0.,0.))
        with self.assertRaises(ValueError):
            Camera3D((0.,1.,0.),(1.,1.,2.),float("inf"))
        with self.assertRaises(ValueError):
            Camera3D((0.,2.,-10.),(0.,2.,20.)).project(
                (float("nan"),1,5))


if __name__ == "__main__":
    unittest.main()
