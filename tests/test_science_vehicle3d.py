"""Original world-space 3D vehicle geometry must move with the same camera as city."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops

from automate_ytb.science_city3d import camera_pose
from automate_ytb.science_vehicle3d import vehicle_pose, draw_vehicle3d


class ScienceVehicle3DTests(unittest.TestCase):
    def setUp(self):
        self.blank=Image.new("RGBA",(1080,1920),(9,25,45,255))

    def test_car_is_projected_from_world_space_and_wheels_track_distance(self):
        a,b,c=[vehicle_pose(t,6) for t in (0,3,6)]
        self.assertLess(a["x"],b["x"])
        self.assertLess(b["x"],c["x"])
        self.assertGreater(c["wheel_angle"],b["wheel_angle"])
        self.assertAlmostEqual(
            (b["x"]-a["x"])/.30,
            b["wheel_angle"]-a["wheel_angle"],places=6)
        cam=camera_pose(0,6,"inertia")
        near=cam.project((a["x"],.8,a["z"]))
        later=camera_pose(6,6,"inertia").project((c["x"],.8,c["z"]))
        self.assertIsNotNone(near)
        self.assertIsNotNone(later)
        self.assertGreater(later[0],near[0])

    def test_3d_vehicles_move_without_changing_title_or_caption_areas(self):
        first=self.blank.copy()
        second=self.blank.copy()
        same=self.blank.copy()
        draw_vehicle3d(first,.2,6)
        draw_vehicle3d(second,4.6,6)
        draw_vehicle3d(same,.2,6)
        self.assertEqual(first.tobytes(),same.tobytes())
        self.assertEqual(first.getchannel("A").getextrema(),(255,255))
        self.assertEqual(second.getchannel("A").getextrema(),(255,255))
        for crop in ((0,0,1080,570),(0,1455,1080,1920)):
            self.assertEqual(first.crop(crop).tobytes(),
                             self.blank.crop(crop).tobytes())
        scenic=(5,700,1070,1410)
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB").crop(scenic),
            second.convert("RGB").crop(scenic)).getbbox())
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB").crop(scenic),
            self.blank.convert("RGB").crop(scenic)).getbbox())

    def test_invalid_clock_and_canvas_are_rejected(self):
        for t,dur in ((-1,6),(6.1,6),(0,0),(1,float("nan")),
                      (float("inf"),6)):
            with self.subTest(t=t,duration=dur),self.assertRaises(ValueError):
                draw_vehicle3d(self.blank,t,dur)
        with self.assertRaises(ValueError):
            draw_vehicle3d(Image.new("RGB",(1080,1920)),1,6)


if __name__=="__main__":
    unittest.main()
