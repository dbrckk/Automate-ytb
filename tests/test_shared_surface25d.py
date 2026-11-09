"""Cross-domain original 2.5D surface-relief contracts."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.scene25d import Layer25D, Scene25D
from automate_ytb.surface25d import MATERIALS, relight_surface


class Shared2p5DMaterialTests(unittest.TestCase):
    def make_asset(self):
        frame=Image.new("RGBA",(96,96))
        d=ImageDraw.Draw(frame)
        d.polygon([(28,17),(65,23),(76,63),(37,77),(17,53)],
                  fill=(114,143,171,227))
        d.line((31,34,54,48),fill=(230,194,125,255),width=4)
        return frame

    def test_materials_modify_real_silhouette_without_changing_alpha(self):
        original=self.make_asset()
        for name in MATERIALS:
            with self.subTest(material=name):
                result=relight_surface(original,name)
                self.assertEqual(result.mode,"RGBA")
                self.assertEqual(result.size,original.size)
                self.assertEqual(result.getchannel("A").tobytes(),
                                 original.getchannel("A").tobytes())
                self.assertEqual(result.getpixel((1,1))[3],0)
                self.assertEqual(original.getpixel((1,1))[3],0)
                if name=="none":
                    self.assertIs(result,original)
                else:
                    self.assertIsNotNone(ImageChops.difference(
                        result.convert("RGB"),original.convert("RGB")).getbbox())
                    self.assertEqual(result.tobytes(),
                                     relight_surface(original,name).tobytes())
        self.assertEqual(original.getpixel((40,49))[3],227)

    def test_material_lighting_is_also_in_generic_z_order_compositor(self):
        source=self.make_asset()
        base=Image.new("RGBA",(96,96),(17,24,31,255))
        for material in ("metal","soft","mineral","water","fabric","foliage"):
            with self.subTest(material=material):
                normal=Scene25D((96,96))
                normal.add(Layer25D("sky",0,base))
                normal.add(Layer25D("actor",50,source))
                relief=Scene25D((96,96))
                relief.add(Layer25D("sky",0,base))
                relief.add(Layer25D("actor",50,source,material=material))
                plain=normal.render()
                shaded=relief.render()
                self.assertEqual(shaded.getpixel((1,1)),
                                 plain.getpixel((1,1)))
                self.assertIsNotNone(ImageChops.difference(
                    plain.convert("RGB"),shaded.convert("RGB")).getbbox())
                self.assertEqual(shaded.tobytes(),relief.render().tobytes())
        self.assertEqual(source.getpixel((1,1))[3],0)

    def test_invalid_material_fails_closed_and_base_contract_is_preserved(self):
        source=self.make_asset()
        with self.assertRaises(ValueError):
            Layer25D("actor",10,source,material="blender")
        with self.assertRaises(ValueError):
            relight_surface(source,"3d")
        with self.assertRaises(ValueError):
            relight_surface(Image.new("RGB",(96,96)),"metal")
        none=relight_surface(source,"none")
        self.assertIs(none,source)
        opaque=Image.new("RGBA",(96,96),(10,40,60,255))
        self.assertIs(relight_surface(opaque,"metal"),opaque)


if __name__=="__main__":
    unittest.main()
