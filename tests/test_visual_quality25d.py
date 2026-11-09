"""P5.5 generic visual quality diagnostics; no storm-specific assumptions."""
import random
import unittest

from PIL import Image, ImageDraw
from automate_ytb.scene25d import Layer25D, Scene25D
from automate_ytb.visual_quality25d import analyze_layer, analyze_scene, VERSION


class Generic25DQualityTests(unittest.TestCase):
    def test_flat_primitives_are_flagged_without_false_approval(self):
        image=Image.new("RGBA",(320,320))
        ImageDraw.Draw(image).rectangle((70,70,250,250),fill=(50,70,90,255))
        result=analyze_layer(image,name="plain-building")
        self.assertEqual(result["name"],"plain-building")
        self.assertGreater(result["alphaCoverage"],.2)
        self.assertTrue(any("material detail" in w for w in result["warnings"]))

    def test_rich_original_asset_has_measurable_detail(self):
        rng=random.Random(119)
        image=Image.new("RGBA",(320,320))
        pixels=image.load()
        for y in range(30,280):
            for x in range(35,285):
                n=rng.randrange(150)
                pixels[x,y]=(60+n,20+n//3,80+n//2,255)
        detailed=analyze_layer(image)
        flat=Image.new("RGBA",(320,320))
        ImageDraw.Draw(flat).rectangle((35,30,284,279),
                                        fill=(100,100,100,255))
        simple=analyze_layer(flat)
        self.assertGreater(detailed["detailEnergy"],simple["detailEnergy"]+5)
        self.assertGreater(detailed["chromaVariation"],simple["chromaVariation"])

    def test_scene_report_is_generic_deterministic_and_nonmutating(self):
        scene=Scene25D((320,320))
        for index,dx in enumerate((.15,.55,1.2)):
            image=Image.new("RGBA",(320,320))
            ImageDraw.Draw(image).ellipse(
                (35+index*22,70,230+index*18,235),
                fill=(60+index*40,80+index*15,150,175))
            scene.add(Layer25D(name="layer-%d"%index,z=10+index*20,
                               image=image,parallax_x=dx,parallax_y=dx*.25))
        original=scene.render().tobytes()
        report=scene.quality_report()
        self.assertEqual(report,analyze_scene(scene))
        self.assertIn("p55",VERSION)
        self.assertEqual(report["layerCount"],3)
        self.assertEqual(report["depthPlanes"],3)
        self.assertEqual(report["independentMotionProfiles"],3)
        self.assertGreater(report["visibleCameraDifference"],.1)
        self.assertIs(report["publicationApproved"],False)
        self.assertEqual(scene.render().tobytes(),original)

    def test_single_flat_layer_requires_review(self):
        scene=Scene25D((160,160))
        scene.add(Layer25D(name="background",z=1,
                           image=Image.new("RGBA",(160,160),(25,25,25,255))))
        report=scene.quality_report()
        self.assertEqual(report["status"],"review")
        self.assertTrue(any("depth" in w for w in report["warnings"]))

    def test_bad_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            analyze_layer(Image.new("RGB",(64,64)))
        with self.assertRaises(ValueError):
            analyze_scene(None)
        scene=Scene25D((64,64))
        with self.assertRaises(ValueError):
            scene.quality_report()
        scene.add(Layer25D(name="layer-a",z=1,
                           image=Image.new("RGBA",(64,64))))
        for invalid in (float("nan"),float("inf"),181):
            with self.assertRaises(ValueError):
                scene.quality_report(camera_x=invalid)


    def test_generic_materials_and_masks_remain_compatible(self):
        scene=Scene25D((320,320))
        for index,material in enumerate(("foliage","metal","water")):
            image=Image.new("RGBA",(320,320))
            ImageDraw.Draw(image).ellipse((20,40,300,270),
                    fill=(55+index*44,110,170,200))
            opacity=(Image.new("L",(320,320),0) if index==2 else None)
            scene.add(Layer25D(name="world-%d"%index,
                z=10+index*20,image=image,material=material,
                parallax_x=.12+index*.4,mask=opacity))
        report=scene.quality_report()
        self.assertEqual([item["material"] for item in report["layers"]],
                         ["foliage","metal","water"])
        self.assertEqual(report["layers"][2]["alphaCoverage"],0.0)
        self.assertEqual(report["depthPlanes"],3)
        self.assertIs(report["publicationApproved"],False)

    def test_translucent_atmosphere_keeps_its_real_visible_texture(self):
        rng=random.Random(921)
        textured=Image.new("RGBA",(320,320))
        pixels=textured.load()
        for y in range(35,285):
            for x in range(35,285):
                n=rng.randrange(120)
                pixels[x,y]=(64+n,92+n//3,137+n//2,138)
        plain=Image.new("RGBA",(320,320))
        ImageDraw.Draw(plain).rectangle((35,35,284,284),
                                        fill=(110,115,160,138))
        detailed=analyze_layer(textured)["detailEnergy"]
        base=analyze_layer(plain)["detailEnergy"]
        self.assertGreater(detailed,base+3)

    def test_material_microtexture_is_not_faked_by_plain_edge(self):
        rng=random.Random(445)
        rich=Image.new("RGBA",(320,320))
        solid=Image.new("RGBA",(320,320))
        ImageDraw.Draw(solid).rectangle((50,50,270,270),
                                         fill=(110,110,110,255))
        pixels=rich.load()
        for y in range(50,271):
            for x in range(50,271):
                variation=rng.randint(-35,35)
                pixels[x,y]=(110+variation,110+variation,110+variation,255)
        signal=analyze_layer(rich)["detailEnergy"]
        primitive=analyze_layer(solid)["detailEnergy"]
        self.assertGreater(signal,primitive+5)

if __name__=="__main__":
    unittest.main()
