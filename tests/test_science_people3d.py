"""3D joint projection and deterministic wind-performer render regressions."""
from __future__ import annotations

import unittest
from PIL import Image, ImageChops
from automate_ytb.science_city3d import camera_pose
from automate_ytb.science_people3d import actor_pose, draw_wind_actors3d


class WorldSpaceActorTests(unittest.TestCase):
    def setUp(self):
        self.blank=Image.new("RGBA",(1080,1920),(9,26,47,255))

    def test_gust_drives_articulations_while_feet_remain_grounded(self):
        for index in (0,1):
            first=actor_pose(0,6,index)
            last=actor_pose(6,6,index)
            self.assertGreater(last["gust"],first["gust"])
            self.assertGreater(last["lean"],first["lean"])
            self.assertEqual(first["foot_l"],last["foot_l"])
            self.assertEqual(first["foot_r"],last["foot_r"])
            self.assertNotEqual(first["shoulder"],last["shoulder"])
            self.assertNotEqual(first["head"],last["head"])
            cam=camera_pose(2,6,"wind")
            head=cam.project(actor_pose(2,6,index)["head"])
            foot=cam.project(actor_pose(2,6,index)["foot_l"])
            self.assertIsNotNone(head)
            self.assertIsNotNone(foot)
            self.assertLess(head[1],foot[1])

    def test_two_world_space_actors_have_real_depth_parallax(self):
        cam=camera_pose(.5,6,"wind")
        near=actor_pose(.5,6,0)
        far=actor_pose(.5,6,1)
        near_size=abs(cam.project(near["head"])[1]-cam.project(near["foot_l"])[1])
        far_size=abs(cam.project(far["head"])[1]-cam.project(far["foot_l"])[1])
        self.assertGreater(near_size,far_size)
        self.assertGreater(near_size,55)

    def test_full_character_and_umbrella_drawn_inside_safe_stage(self):
        a,b,c=self.blank.copy(),self.blank.copy(),self.blank.copy()
        draw_wind_actors3d(a,.2,6)
        draw_wind_actors3d(b,5.5,6)
        draw_wind_actors3d(c,.2,6)
        self.assertEqual(a.tobytes(),c.tobytes())
        self.assertEqual(a.getchannel("A").getextrema(),(255,255))
        self.assertEqual(b.getchannel("A").getextrema(),(255,255))
        for bbox in ((0,0,1080,570),(0,1455,1080,1920)):
            self.assertEqual(a.crop(bbox).tobytes(),self.blank.crop(bbox).tobytes())
        area=(10,760,1070,1430)
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB").crop(area),
            self.blank.convert("RGB").crop(area)).getbbox())
        self.assertIsNotNone(ImageChops.difference(
            a.convert("RGB").crop(area),
            b.convert("RGB").crop(area)).getbbox())

    def test_invalid_values_and_canvas_are_rejected(self):
        for t,dur in ((-1,6),(7,6),(0,0),(1,float("nan")),
                      (float("inf"),6)):
            with self.subTest(t=t,duration=dur),self.assertRaises(ValueError):
                draw_wind_actors3d(self.blank,t,dur)
        for index in (-1,2,22):
            with self.subTest(index=index),self.assertRaises(ValueError):
                actor_pose(1,6,index)
        with self.assertRaises(ValueError):
            draw_wind_actors3d(Image.new("RGB",(1080,1920)),1,6)


if __name__=="__main__":
    unittest.main()
