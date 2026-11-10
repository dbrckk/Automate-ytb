"""Cross-topic 2.5D light-field tests: real source alpha, depth and camera."""
import unittest

from PIL import Image,ImageDraw
from automate_ytb.lightfield25d import Light25D,illuminate
from automate_ytb.scene25d import Layer25D,Scene25D


class GenericLightFieldTests(unittest.TestCase):
    def _scene(self):
        scene=Scene25D((160,160))
        for index,z in enumerate((10,50,90)):
            image=Image.new("RGBA",(160,160))
            ImageDraw.Draw(image).ellipse(
                (24+index*13,35,110+index*12,125),
                fill=(48+index*25,71,109,185))
            scene.add(Layer25D(name="asset-%d"%index,z=z,image=image,
                               parallax_x=.2+index*.4,
                               material=("soft","mineral","metal")[index]))
        return scene

    def test_alpha_is_byte_for_byte_unchanged_and_no_new_geometry(self):
        source=Image.new("RGBA",(160,160))
        ImageDraw.Draw(source).ellipse((32,40,120,134),fill=(43,77,119,132))
        old=source.tobytes()
        result=illuminate(source,Light25D(85,70,100),z=60)
        self.assertEqual(result.getchannel("A").tobytes(),
                         source.getchannel("A").tobytes())
        self.assertEqual(source.tobytes(),old)
        self.assertEqual(result.getpixel((0,0))[3],0)
        self.assertNotEqual(result.getpixel((80,80))[:3],
                            source.getpixel((80,80))[:3])

    def test_depth_modulates_same_light_across_authored_plates(self):
        image=Image.new("RGBA",(160,160),(50,70,110,255))
        light=Light25D(80,80,105,strength=.95,ambient=1)
        near=illuminate(image,light,z=90)
        far=illuminate(image,light,z=10)
        self.assertGreater(near.getpixel((80,80))[0],
                           far.getpixel((80,80))[0])
        self.assertEqual(near.getpixel((0,0))[3],255)

    def test_shared_compositor_is_opt_in_deterministic_and_nonmutating(self):
        scene=self._scene()
        before=scene.render(camera_x=11,camera_y=5)
        light=Light25D(92,75,110,color=(255,185,92))
        a=scene.render(camera_x=11,camera_y=5,light=light)
        b=scene.render(camera_x=11,camera_y=5,light=light)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertNotEqual(a.tobytes(),before.tobytes())
        self.assertEqual(scene.render(camera_x=11,camera_y=5).tobytes(),
                         before.tobytes())
        self.assertIs(scene.quality_report()["publicationApproved"],False)

    def test_ambient_only_and_zero_light_are_safe(self):
        scene=self._scene()
        original=scene.render()
        neutral=scene.render(light=Light25D(80,80,90,strength=0,ambient=1))
        self.assertEqual(original.tobytes(),neutral.tobytes())
        dark=scene.render(light=Light25D(80,80,90,strength=0,ambient=.6))
        self.assertNotEqual(original.tobytes(),dark.tobytes())

    def test_bad_parameters_are_rejected(self):
        for args in (
            dict(x=float("nan"),y=80,radius=90),
            dict(x=80,y=80,radius=0),
            dict(x=80,y=80,radius=90,strength=3),
            dict(x=80,y=80,radius=90,color=(300,0,0)),
            dict(x=80,y=80,radius=90,ambient=.2),
        ):
            with self.assertRaises(ValueError):
                Light25D(**args)
        scene=self._scene()
        with self.assertRaises(ValueError):
            scene.render(light="fake-light")
        with self.assertRaises(ValueError):
            illuminate(Image.new("RGB",(160,160)),Light25D(50,50,90),z=20)


if __name__=="__main__":
    unittest.main()
