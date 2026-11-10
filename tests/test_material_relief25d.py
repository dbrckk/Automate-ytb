"""Global original visual material graph across ocean, rock and aurora."""
from __future__ import annotations

import math
import unittest
from PIL import Image,ImageDraw,ImageChops,ImageStat
from automate_ytb.material_relief25d import (
    VERSION,MATERIALS,sculpt_authored_material,
)
from automate_ytb.finish25d import LOOKS, finish_world
from automate_ytb.science_portrait import PortraitScienceScene


class SharedSourceMaterialReliefTests(unittest.TestCase):
    def test_all_original_scene_palette_contracts(self):
        self.assertIn("p524-v1",VERSION)
        self.assertEqual(set(MATERIALS),set(LOOKS))

    def test_flat_color_and_precise_optics_never_gain_fake_detail(self):
        source=Image.new("RGB",(320,320),(65,115,170))
        for look in MATERIALS:
            with self.subTest(look=look):
                result=sculpt_authored_material(source,look=look)
                self.assertEqual(result.tobytes(),source.tobytes())
        for look in ("rainbow","daylight","neutral"):
            self.assertIs(sculpt_authored_material(source,look=look),source)

    def test_authored_color_gradients_produce_depth_without_mutating_source(self):
        source=Image.new("RGB",(320,320),(27,40,61))
        d=ImageDraw.Draw(source)
        for i in range(13):
            d.ellipse((40+i*6,45+i*2,240-i*3,244-i*4),
                      fill=(85+i*9,51+i*5,98+i*6))
        source_bytes=source.tobytes()
        for look in ("ocean","volcano","aurora","storm","forest"):
            with self.subTest(look=look):
                shade=sculpt_authored_material(source,look=look)
                self.assertEqual(shade.mode,"RGB")
                self.assertEqual(shade.size,source.size)
                self.assertNotEqual(shade.tobytes(),source_bytes)
                self.assertEqual(
                    shade.tobytes(),
                    sculpt_authored_material(source,look=look).tobytes())
                self.assertEqual(shade.getpixel((8,8)),source.getpixel((8,8)))
        self.assertEqual(source.tobytes(),source_bytes)

    def test_material_shading_never_wraps_opposite_world_edges(self):
        """No synthetic rim where a flat source touches a crop boundary."""
        for edge in ("left", "right", "top", "bottom"):
            with self.subTest(edge=edge):
                source=Image.new("RGB",(320,256),(35,35,35))
                d=ImageDraw.Draw(source)
                bright={
                    "left":(0,0,55,255),
                    "right":(265,0,319,255),
                    "top":(0,0,319,55),
                    "bottom":(0,200,319,255),
                }[edge]
                d.rectangle(bright,fill=(225,225,225))
                target={
                    "left":(0,128),
                    "right":(319,128),
                    "top":(160,0),
                    "bottom":(160,255),
                }[edge]
                shaded=sculpt_authored_material(source,look="volcano")
                self.assertEqual(shaded.getpixel(target),
                                 source.getpixel(target))
                # Relief must still react to genuine internal boundaries.
                self.assertNotEqual(
                    shaded.crop((50,55,270,200)).tobytes(),
                    source.crop((50,55,270,200)).tobytes())

    def test_global_finish_never_changes_titles_subtitles_or_alpha(self):
        source=Image.new("RGBA",(460,540),(16,39,60,255))
        d=ImageDraw.Draw(source)
        for i in range(15):
            d.ellipse((45+i*8,143+i*3,315+i*3,409-i*4),
                      fill=(81+i*7,101+i*5,152+i*5,185))
        for look in ("volcano","ocean","aurora","storm","forest","rainbow"):
            with self.subTest(look=look):
                options=dict(bounds=(30,115,430,440),look=look,
                             t=2.2,duration=6.8)
                a=source.copy()
                b=source.copy()
                finish_world(a,**options)
                finish_world(b,**options)
                self.assertEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.getchannel("A").tobytes(),
                                 source.getchannel("A").tobytes())
                for area in ((0,0,460,110),(0,445,460,540)):
                    self.assertEqual(a.crop(area).tobytes(),
                                     source.crop(area).tobytes())
                for p in ((30,250),(429,250),(150,115),(150,439)):
                    self.assertEqual(a.getpixel(p),source.getpixel(p))

    def test_invalid_formats_and_look_names_rejected(self):
        valid=Image.new("RGB",(160,160))
        for image,look in (
            (valid.convert("RGBA"),"ocean"),
            (Image.new("RGB",(31,160)),"ocean"),
            (valid,"unknown"),(valid,True),(None,"volcano"),
        ):
            with self.assertRaises(ValueError):
                sculpt_authored_material(image,look=look)

    def test_three_actual_native_9_16_video_subjects_share_source_material(self):
        examples=(
            ("Why do ocean currents move?",
             "Earth rotation bends ocean currents through the Coriolis effect."),
            ("How do volcanoes erupt?",
             "Rising magma pushes upward through the volcanic vent."),
            ("Why do auroras glow?",
             "Excited gas atoms emit light as colorful curtains."),
        )
        for topic,narration in examples:
            with self.subTest(topic=topic):
                shot=PortraitScienceScene(topic=topic,narration=narration,
                                          scene_index=2)
                a=shot.frame(1.1,6.8)
                b=shot.frame(3.5,6.8)
                self.assertEqual(a.size,(1080,1920))
                self.assertEqual(a.mode,"RGB")
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),shot.frame(1.1,6.8).tobytes())


if __name__=="__main__":
    unittest.main()
