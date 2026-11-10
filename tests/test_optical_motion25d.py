"""General original 2.5D optical animation and true subpixel compositing."""
from __future__ import annotations

import math
import unittest

from PIL import Image,ImageDraw,ImageChops

from automate_ytb.optical_motion25d import (
    VERSION,PRESETS,MESH_STEP,refract_source,translate_subpixel,
)
from automate_ytb.finish25d import finish_world,science_look
from automate_ytb.scene25d import Layer25D,Scene25D
from automate_ytb.science_portrait import PortraitScienceScene


class SharedSourceOpticalMotionTests(unittest.TestCase):
    def _authored_scene(self,size=(320,320)):
        art=Image.new("RGB",size,(23,42,61))
        d=ImageDraw.Draw(art)
        d.ellipse((60,28,size[0]-60,size[1]-57),
                  fill=(195,94,43))
        for j in range(5):
            path=[(x,round(100+j*20+12*math.sin(x*.037+j*.51)))
                  for x in range(15,size[0]-15,5)]
            d.line(path,fill=(125+j*9,204,232),width=4)
        return art

    def test_refracts_only_existing_source_and_motion_is_temporally_smooth(self):
        base=self._authored_scene()
        signature=base.tobytes()
        self.assertTrue(VERSION.endswith("p523-v1"))
        self.assertEqual(MESH_STEP,64)
        self.assertEqual(set(PRESETS),{
            "storm","volcano","aurora","ocean","forest","rainbow",
            "daylight","neutral"})
        for look in ("ocean","volcano","aurora","storm","forest"):
            with self.subTest(material=look):
                a=refract_source(base,look=look,t=1.,duration=6.8)
                b=refract_source(base,look=look,t=1.1,duration=6.8)
                c=refract_source(base,look=look,t=3.8,duration=6.8)
                self.assertEqual(a.size,base.size)
                self.assertEqual(a.mode,"RGB")
                self.assertNotEqual(a.tobytes(),c.tobytes())
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertEqual(a.tobytes(),
                                 refract_source(base,look=look,
                                                t=1.,duration=6.8).tobytes())
                self.assertEqual(a.getpixel((0,0)),base.getpixel((0,0)))
                self.assertEqual(a.getpixel((319,319)),
                                 base.getpixel((319,319)))
                near=ImageChops.difference(a,b)
                far=ImageChops.difference(a,c)
                self.assertLess(sum(near.getbbox() is None for _ in (0,)),1)
                # Smaller timeline steps should be visibly less disruptive.
                self.assertLess(sum(near.convert("L").getdata()),
                                sum(far.convert("L").getdata()))
        self.assertEqual(base.tobytes(),signature)

    def test_precise_optics_and_flat_materials_do_not_invent_detail(self):
        source=self._authored_scene()
        for look in ("rainbow","daylight","neutral"):
            self.assertIs(refract_source(source,look=look,t=3.,duration=6.),
                          source)
        simple=Image.new("RGB",(320,320),(74,109,151))
        for look in ("volcano","ocean","aurora"):
            self.assertEqual(
                refract_source(simple,look=look,t=2.7,duration=6.8).tobytes(),
                simple.tobytes())

    def test_original_alpha_edges_remain_bright_when_sampling_subpixel(self):
        source=Image.new("RGBA",(128,128))
        d=ImageDraw.Draw(source,"RGBA")
        d.ellipse((24,24,104,104),fill=(255,67,15,255))
        input_sig=source.tobytes()
        result=translate_subpixel(source,.5,.375)
        self.assertEqual(result.mode,"RGBA")
        self.assertEqual(result.size,source.size)
        self.assertNotEqual(result.tobytes(),source.tobytes())
        self.assertEqual(source.tobytes(),input_sig)
        self.assertEqual(result.getpixel((0,0))[3],0)
        half=[result.getpixel((x,y))
              for y in range(21,108) for x in range(21,108)
              if 12<result.getpixel((x,y))[3]<240]
        self.assertGreater(len(half),20)
        self.assertGreater(min(v[0] for v in half),240)
        self.assertEqual(result.tobytes(),
                         translate_subpixel(source,.5,.375).tobytes())
        self.assertIs(translate_subpixel(source,0.,0.),source)

    def test_camera_motion_has_genuine_fractional_progress_in_any_scene(self):
        scene=Scene25D((160,160))
        scene.add(Layer25D(name="sky",z=0,
                           image=Image.new("RGBA",(160,160),
                                           (9,19,36,255))))
        cloud=Image.new("RGBA",(160,160))
        ImageDraw.Draw(cloud).ellipse((40,48,120,113),fill=(229,176,121,255))
        scene.add(Layer25D(name="cloud",z=70,image=cloud,
                           parallax_x=.9,parallax_y=.4,material="soft"))
        at_zero=scene.render(camera_x=0.,camera_y=0.)
        at_quarter=scene.render(camera_x=.27,camera_y=.18)
        at_half=scene.render(camera_x=.65,camera_y=.46)
        self.assertNotEqual(at_zero.tobytes(),at_quarter.tobytes())
        self.assertNotEqual(at_quarter.tobytes(),at_half.tobytes())
        self.assertEqual(scene.render(camera_x=.65,camera_y=.46).tobytes(),
                         at_half.tobytes())
        self.assertEqual(at_half.getpixel((0,0)),at_zero.getpixel((0,0)))
        self.assertEqual(cloud.getpixel((40,70)),(229,176,121,255))

    def test_common_finish_is_text_safe_alpha_safe_and_repeatable(self):
        original=Image.new("RGBA",(450,500),(24,47,68,255))
        d=ImageDraw.Draw(original)
        for x in range(32,414,8):
            d.ellipse((x,155,x+48,350),fill=(75+(x%100),139,198,180))
        for look in ("ocean","aurora","volcano","storm","rainbow"):
            with self.subTest(look=look):
                copy=original.copy()
                other=original.copy()
                args=dict(bounds=(35,135,415,375),look=look,t=2.1,
                          duration=6.8)
                finish_world(copy,**args)
                finish_world(other,**args)
                self.assertEqual(copy.tobytes(),other.tobytes())
                self.assertEqual(copy.getchannel("A").tobytes(),
                                 original.getchannel("A").tobytes())
                self.assertEqual(copy.crop((0,0,450,120)).tobytes(),
                                 original.crop((0,0,450,120)).tobytes())
                self.assertEqual(copy.crop((0,400,450,500)).tobytes(),
                                 original.crop((0,400,450,500)).tobytes())
                for p in ((35,200),(414,200),(150,135),(150,374)):
                    self.assertEqual(copy.getpixel(p),original.getpixel(p))

    def test_input_validation_guards_all_real_renderers(self):
        image=self._authored_scene()
        for t,duration in ((True,6.8),(-1,6.8),(math.inf,6.8),
                           (7,6.8),(1,math.nan),(1,181)):
            with self.assertRaises(ValueError):
                refract_source(image,look="ocean",t=t,duration=duration)
        for bad in ("bad",None,22):
            with self.assertRaises(ValueError):
                refract_source(image,look=bad,t=1.,duration=6.)
        with self.assertRaises(ValueError):
            refract_source(image.convert("RGBA"),look="ocean",
                           t=1.,duration=6.)
        rgba=Image.new("RGBA",(64,64))
        for dx,dy in ((True,1),(.5,math.nan),(math.inf,.5),
                      (401,0),(0,-401)):
            with self.assertRaises(ValueError):
                translate_subpixel(rgba,dx,dy)

    def test_real_1080x1920_generators_share_optical_engine(self):
        examples=(
            ("Why do ocean currents move?",
             "Earth rotation bends ocean currents through the Coriolis effect.",
             "ocean"),
            ("How do volcanoes erupt?",
             "Rising magma pushes upward through the volcanic vent.",
             "volcano"),
            ("Why do auroras glow?",
             "Excited gas atoms emit light as colorful curtains.",
             "aurora"),
        )
        for title,narration,look in examples:
            with self.subTest(topic=title):
                scene=PortraitScienceScene(
                    topic=title,narration=narration,scene_index=2)
                self.assertEqual(
                    science_look(aurora=look=="aurora",
                                 volcano=look=="volcano",
                                 mode=look if look=="ocean" else "orbital"),
                    look)
                a=scene.frame(1.7,6.8)
                b=scene.frame(3.1,6.8)
                self.assertEqual(a.size,(1080,1920))
                self.assertEqual(a.mode,"RGB")
                self.assertNotEqual(a.tobytes(),b.tobytes())


if __name__=="__main__":
    unittest.main()
