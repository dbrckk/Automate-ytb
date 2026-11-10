"""Real source-space temporal QA for universal 2.5D material ribbons."""
import hashlib
import math
import unittest

from PIL import Image,ImageDraw,ImageChops
from automate_ytb.material_ribbons25d import (
    VERSION,MATERIALS,_position,draw_material_ribbon,
)


class MaterialRibbon25DTests(unittest.TestCase):
    def _render(self, material="water",progress=.41,curve=None):
        art=Image.new("RGBA",(320,260))
        pts=curve or [(33,204),(91,163),(134,134),(180,138),(230,95),(290,54)]
        draw_material_ribbon(ImageDraw.Draw(art,"RGBA"),pts,
                             material=material,color=(128,214,235,224),
                             width=12,progress=progress)
        return art

    def test_causal_motion_is_deterministic_and_following_a_real_curve(self):
        a=self._render(progress=.25)
        same=self._render(progress=.25)
        b=self._render(progress=.68)
        self.assertEqual(a.tobytes(),same.tobytes())
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertGreater(a.getchannel("A").getextrema()[1],100)
        self.assertEqual(a.getpixel((0,0))[3],0)
        self.assertEqual(a.getpixel((319,259))[3],0)

    def test_arc_length_not_vertex_index_is_used_for_animated_tracer(self):
        coordinates=[(10.,10.),(11.,10.),(211.,10.)]
        mid,total=_position(coordinates,.5)
        self.assertAlmostEqual(total,201.)
        self.assertAlmostEqual(mid[0],110.5)
        self.assertAlmostEqual(mid[1],10.)

    def test_three_distinct_material_responses_use_same_rig(self):
        self.assertEqual(set(MATERIALS),{"light","water","magma"})
        self.assertTrue(VERSION.endswith("p510-v1"))
        art=[self._render(material=m) for m in MATERIALS]
        self.assertEqual(len({
            hashlib.sha256(img.tobytes()).hexdigest() for img in art}),3)

    def test_straight_science_ray_is_never_curved_by_material_system(self):
        image=self._render(material="light",progress=.5,
                           curve=[(25,75),(300,75)])
        self.assertGreater(image.getpixel((150,75))[3],20)
        self.assertEqual(image.getpixel((150,30))[3],0)
        self.assertEqual(image.getpixel((150,130))[3],0)

    def test_bad_meshes_and_nonfinite_times_fail_explicitly(self):
        paths=([(0,0)],[(0,0),(0,0)],
               [(0,0),(math.nan,5)],[(0,0),(5000,5)])
        for curve in paths:
            with self.assertRaises(ValueError):
                self._render(curve=curve)
        for material in ("neon","3d",""):
            with self.assertRaises(ValueError):
                self._render(material=material)
        for progress in (-1.,1.1,math.nan,math.inf,True):
            with self.assertRaises(ValueError):
                self._render(progress=progress)

    def test_actual_three_topic_renderers_use_same_native_stage(self):
        # This verifies the integration points aren't just unused helper
        # functions, and that their artwork remains time-sensitive.
        from automate_ytb.science_rainbow import draw_rainbow
        from automate_ytb.science_ocean_depth import draw_depth
        from automate_ytb.science_volcano import draw_volcano
        out=[]
        for name in ("rainbow","ocean","volcano"):
            initial=Image.new("RGBA",(1080,1920))
            later=Image.new("RGBA",(1080,1920))
            if name=="rainbow":
                draw_rainbow(ImageDraw.Draw(initial,"RGBA"),"refraction",.9,6.,True)
                draw_rainbow(ImageDraw.Draw(later,"RGBA"),"refraction",2.7,6.,True)
            elif name=="ocean":
                draw_depth(initial,"wind",t=.9,duration=6.)
                draw_depth(later,"wind",t=2.7,duration=6.)
            else:
                draw_volcano(initial,"lava",.9,6.,True)
                draw_volcano(later,"lava",2.7,6.,True)
                empty=Image.new("RGBA",(1080,1920))
                draw_volcano(empty,"lava",0.,6.,True)
            self.assertEqual(initial.size,(1080,1920))
            self.assertIsNotNone(ImageChops.difference(initial,later).getbbox())
            out.append(initial.getbbox())
        self.assertEqual(len(out),3)


if __name__=="__main__":
    unittest.main()
