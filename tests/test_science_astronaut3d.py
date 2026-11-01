"""Deterministic original astronaut world-space rig and native 9:16 film tests."""
from __future__ import annotations

import math
import unittest
from PIL import Image, ImageChops

from automate_ytb.science_astronaut3d import (
    astronaut_pose, camera_pose, draw_astronaut3d,
)
from automate_ytb.science_city3d import SCENE_TOP, SCENE_BOTTOM


class EVAScene3DTests(unittest.TestCase):
    def setUp(self):
        self.blank=Image.new("RGBA",(1080,1920),(8,22,45,255))

    def test_all_human_joints_share_world_space_motion_and_camera(self):
        old=astronaut_pose(.2,6)
        later=astronaut_pose(4.2,6)
        for joint in ("hip","head","shoulder_l","shoulder_r","elbow_l",
                      "elbow_r","hand_l","hand_r","knee_l","knee_r",
                      "foot_l","foot_r","tether"):
            with self.subTest(joint=joint):
                xyz=old[joint]
                self.assertEqual(len(xyz),3)
                self.assertTrue(all(math.isfinite(v) for v in xyz))
                self.assertIsNotNone(camera_pose(.2,6).project(xyz))
        self.assertNotEqual(old["head"],later["head"])
        self.assertNotEqual(old["foot_r"],later["foot_r"])
        self.assertNotEqual(old["tether"],later["tether"])
        self.assertNotEqual(camera_pose(.2,6).eye,camera_pose(4.2,6).eye)
        self.assertLess(camera_pose(.2,6).project(old["head"])[1],
                        camera_pose(.2,6).project(old["foot_r"])[1])

    def test_eva_is_fully_drawn_in_scenic_area_deterministically(self):
        first=self.blank.copy()
        last=self.blank.copy()
        again=self.blank.copy()
        draw_astronaut3d(first,.2,6)
        draw_astronaut3d(last,4.7,6)
        draw_astronaut3d(again,.2,6)
        self.assertEqual(first.tobytes(),again.tobytes())
        self.assertEqual(first.getchannel("A").getextrema(),(255,255))
        self.assertEqual(last.getchannel("A").getextrema(),(255,255))
        for bbox in ((0,0,1080,SCENE_TOP),(0,SCENE_BOTTOM,1080,1920)):
            with self.subTest(bbox=bbox):
                self.assertEqual(first.crop(bbox).tobytes(),
                                 self.blank.crop(bbox).tobytes())
        center=(130,730,990,1400)
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB").crop(center),
            self.blank.convert("RGB").crop(center)).getbbox())
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB").crop(center),
            last.convert("RGB").crop(center)).getbbox())
        # Large original suit subject must not shrink to an invisible icon.
        changed=ImageChops.difference(first.convert("RGB"),
                                     self.blank.convert("RGB"))
        bbox=changed.getbbox()
        self.assertIsNotNone(bbox)
        self.assertGreater(bbox[2]-bbox[0],220)
        self.assertGreater(bbox[3]-bbox[1],250)

    def test_reject_invalid_clock_and_dimensions_before_modifying(self):
        for t,dur in ((-1,6),(7,6),(0,0),
                      (1,float("nan")),(float("inf"),6)):
            with self.subTest(t=t,duration=dur),self.assertRaises(ValueError):
                draw_astronaut3d(self.blank,t,dur)
        with self.assertRaises(ValueError):
            draw_astronaut3d(Image.new("RGB",(1080,1920)),1,6)
        with self.assertRaises(ValueError):
            draw_astronaut3d(Image.new("RGBA",(720,1280)),1,6)
        self.assertEqual(self.blank.getpixel((500,1000)),(8,22,45,255))


if __name__=="__main__":
    unittest.main()
