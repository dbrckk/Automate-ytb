"""Regression for actual colored rectangular seams in common 2.5D video finish."""
import hashlib
import unittest

from PIL import Image,ImageDraw

from automate_ytb.finish25d import _seamless_world_mask,finish_world


class SeamlessSharedWorldTests(unittest.TestCase):
    def _canvas(self):
        image=Image.new("RGBA",(320,320),(32,59,88,255))
        d=ImageDraw.Draw(image)
        for y in range(320):
            d.line((0,y,319,y),fill=(25+y//8,66+y//11,99+y//9,255))
        d.ellipse((75,64,235,250),fill=(201,112,49,220))
        for x in range(30,290,9):
            d.line((x,80,x+23,220),fill=(125,205,221,110),width=2)
        return image

    def test_exact_source_edges_and_adjacent_outside_pixels_are_preserved(self):
        before=self._canvas()
        after=before.copy()
        bounds=(48,52,280,264)
        finish_world(after,bounds=bounds,look="volcano",t=2,duration=6)
        # No sudden color-step at the four edges of the post-processing crop.
        for x,y in ((48,145),(279,145),(140,52),(140,263),
                    (47,145),(280,145),(140,51),(140,264)):
            self.assertEqual(after.getpixel((x,y)),before.getpixel((x,y)))
        self.assertNotEqual(after.getpixel((160,145)),
                            before.getpixel((160,145)))
        self.assertEqual(after.getchannel("A").tobytes(),
                         before.getchannel("A").tobytes())

    def test_smooth_gradient_instead_of_full_strength_one_pixel_rail(self):
        w,h=232,212
        mask=_seamless_world_mask(w,h)
        self.assertIs(mask,_seamless_world_mask(w,h))
        self.assertEqual(mask.getpixel((0,h//2)),0)
        self.assertEqual(mask.getpixel((w-1,h//2)),0)
        self.assertEqual(mask.getpixel((w//2,0)),0)
        self.assertEqual(mask.getpixel((w//2,h-1)),0)
        left=[mask.getpixel((x,h//2)) for x in (0,3,9,18,36,76)]
        self.assertEqual(left,sorted(left))
        self.assertGreater(len(set(left)),4)
        self.assertEqual(mask.getpixel((w//2,h//2)),255)

    def test_authored_event_pulse_cannot_reintroduce_frame_border(self):
        original=self._canvas()
        a=original.copy()
        b=original.copy()
        options=dict(bounds=(48,52,280,264),look="ocean",
                     duration=6,event_fraction=.5)
        finish_world(a,t=3,**options)
        finish_world(b,t=3,**options)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertEqual(a.getpixel((48,150)),original.getpixel((48,150)))
        self.assertEqual(a.getpixel((165,52)),original.getpixel((165,52)))
        self.assertNotEqual(a.getpixel((170,160)),original.getpixel((170,160)))
        self.assertEqual(a.getchannel("A").tobytes(),
                         original.getchannel("A").tobytes())

    def test_outside_region_and_caption_area_are_untouched(self):
        canvas=self._canvas()
        before=hashlib.sha256(canvas.crop((0,270,320,320)).tobytes()).hexdigest()
        finish_world(canvas,bounds=(48,52,280,264),
                     look="rainbow",t=.9,duration=5.)
        self.assertEqual(
            hashlib.sha256(canvas.crop((0,270,320,320)).tobytes()).hexdigest(),
            before)


if __name__=="__main__":
    unittest.main()
