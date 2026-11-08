"""2.5D depth contract and real independently animated lightning plates."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.scene25d import Layer25D, Scene25D
from automate_ytb.science_lightning_fx import SIZE, environment_plates


class MultiZCompositorTests(unittest.TestCase):
    def _canvas(self, color=(0, 0, 0, 0)):
        return Image.new("RGBA", (48, 48), color)

    def test_occlusion_is_actual_alpha_compositing_at_each_depth(self):
        background = self._canvas((200, 25, 30, 255))
        actor = self._canvas()
        ImageDraw.Draw(actor).rectangle((8, 8, 32, 32),
                                        fill=(14, 42, 230, 255))
        foreground = self._canvas()
        ImageDraw.Draw(foreground).rectangle((16, 16, 24, 24),
                                             fill=(15, 238, 34, 255))
        scene = Scene25D((48, 48))
        scene.add(Layer25D("actor", 50, actor))
        scene.add(Layer25D("foreground", 90, foreground))
        scene.add(Layer25D("background", 0, background))
        result = scene.render()
        self.assertEqual(result.getpixel((3, 3)), (200, 25, 30, 255))
        self.assertEqual(result.getpixel((11, 11)), (14, 42, 230, 255))
        self.assertEqual(result.getpixel((20, 20)), (15, 238, 34, 255))
        self.assertEqual(scene.layer_names, ("background", "actor", "foreground"))

    def test_mask_controls_actual_visibility_and_preserves_source_alpha(self):
        original = self._canvas((240, 90, 30, 200))
        mask = Image.new("L", (48, 48), 0)
        ImageDraw.Draw(mask).rectangle((0, 0, 20, 47), fill=255)
        scene = Scene25D((48, 48))
        scene.add(Layer25D("background", 0, self._canvas((0, 0, 0, 255))))
        scene.add(Layer25D("masked", 10, original, mask=mask))
        result = scene.render()
        self.assertEqual(result.getpixel((40, 20)), (0, 0, 0, 255))
        self.assertNotEqual(result.getpixel((12, 20)), (0, 0, 0, 255))
        self.assertEqual(result.getpixel((12, 20))[3], 255)
        self.assertEqual(original.getpixel((12, 20))[3], 200)

    def test_independent_parallax_moves_only_near_layer(self):
        scene = Scene25D((48, 48))
        scene.add(Layer25D("sky", 0, self._canvas((9, 13, 17, 255))))
        near = self._canvas()
        ImageDraw.Draw(near).rectangle((10, 18, 14, 22),
                                      fill=(255, 100, 60, 255))
        scene.add(Layer25D("near", 10, near, parallax_x=1))
        first = scene.render(camera_x=0)
        second = scene.render(camera_x=9)
        self.assertEqual(first.getpixel((11, 20))[:3], (255, 100, 60))
        self.assertEqual(second.getpixel((11, 20))[:3], (9, 13, 17))
        self.assertEqual(second.getpixel((20, 20))[:3], (255, 100, 60))
        self.assertEqual(first.getpixel((0, 0)), second.getpixel((0, 0)))
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"), second.convert("RGB")).getbbox())

    def test_rejects_broken_masks_layers_and_unbounded_offsets(self):
        with self.assertRaises(ValueError):
            Scene25D((0, 100))
        scene = Scene25D((48, 48))
        with self.assertRaises(ValueError):
            scene.render()
        with self.assertRaises(ValueError):
            Layer25D("bad name", 2, self._canvas())
        with self.assertRaises(ValueError):
            Layer25D("bad-z", True, self._canvas())
        with self.assertRaises(ValueError):
            Layer25D("bad-mode", 2, Image.new("RGB", (48, 48)))
        with self.assertRaises(ValueError):
            Layer25D("bad-mask", 2, self._canvas(),
                     mask=Image.new("L", (32, 32)))
        with self.assertRaises(ValueError):
            Layer25D("bad-parallax", 2, self._canvas(),
                     parallax_x=float("nan"))
        scene.add(Layer25D("sky", 0, self._canvas()))
        with self.assertRaises(ValueError):
            scene.add(Layer25D("sky", 1, self._canvas()))
        with self.assertRaises(ValueError):
            scene.add(Layer25D("other", 0, self._canvas()))
        for shift in (float("nan"), float("inf"), 181):
            with self.subTest(shift=shift), self.assertRaises(ValueError):
                scene.render(camera_x=shift)


class RealLightningPlatesTests(unittest.TestCase):
    def test_six_distinct_authored_environment_planes(self):
        planes = environment_plates(1.1, "leader", 7.2)
        self.assertEqual(tuple(name for name, _ in planes),
                         ("sky", "clouds-far", "clouds-middle",
                          "clouds-near", "background-rain", "vignette"))
        self.assertTrue(all(plate.size == SIZE and plate.mode == "RGBA"
                            for _, plate in planes))
        self.assertEqual(planes[0][1].getpixel((0, 0))[3], 255)
        for name, layer in planes[1:]:
            with self.subTest(name=name):
                self.assertIsNotNone(layer.getchannel("A").getbbox())
                self.assertEqual(layer.getpixel((0, 0))[3], 0)

    def test_far_and_near_cloud_plates_move_independently(self):
        first = dict(environment_plates(.5, "leader", 7.2))
        later = dict(environment_plates(3.5, "leader", 7.2))
        for name in ("clouds-far", "clouds-near", "background-rain"):
            with self.subTest(layer=name):
                diff = ImageChops.difference(
                    first[name].convert("RGB"), later[name].convert("RGB"))
                self.assertIsNotNone(diff.getbbox())


if __name__ == "__main__":
    unittest.main()
