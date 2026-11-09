"""P5.6: truthful shared typography and real-scene mobile-safe regression."""
from __future__ import annotations

import unittest

from PIL import Image, ImageChops
from automate_ytb.editorial25d import (VERSION,paint_header,paint_caption,
                                        _atmospheric_scrim)
from automate_ytb.science_portrait import PortraitScienceScene


class OpenOriginal25DScienceEditorialTests(unittest.TestCase):
    def test_shared_open_overlay_preserves_world_outside_mobile_safe_zones(self):
        source=Image.new("RGBA",(1080,1920),(52,91,120,255))
        before=source.tobytes()
        paint_header(source,title=("Why Does Light Bend?",),font_size=43,
                     badge="LIGHT REFRACTION",compact=False)
        paint_caption(source,lines=("Sunlight changes direction.",),
                      font_size=40)
        self.assertIn("25d",VERSION)
        self.assertNotEqual(source.tobytes(),before)
        self.assertEqual(source.crop((0,600,1080,1450)).tobytes(),
                         Image.new("RGBA",(1080,850),(52,91,120,255)).tobytes())
        self.assertEqual(source.getpixel((540,1910)),(52,91,120,255))
        self.assertEqual(source.mode,"RGBA")
        self.assertEqual(source.getchannel("A").getextrema(),(255,255))
        # The accents are only on the left, not paired four-sided card rails.
        self.assertNotEqual(source.getpixel((90,235)),
                            source.getpixel((20,235)))
        self.assertNotEqual(source.getpixel((90,1555)),
                            source.getpixel((20,1555)))

    def test_overlay_is_reproducible_without_per_frame_randomness(self):
        def render():
            output=Image.new("RGBA",(1080,1920),(29,65,91,255))
            paint_header(output,title=("A curious storm",),font_size=44,
                         badge="CHARGE BUILDUP",compact=True)
            paint_caption(output,lines=("A field grows stronger.",),
                          font_size=38)
            return output
        self.assertEqual(render().tobytes(),render().tobytes())
        self.assertEqual(_atmospheric_scrim(70,330,138).getpixel((0,0))[3],0)
        self.assertEqual(_atmospheric_scrim(70,330,138).getpixel((0,329))[3],0)

    def test_all_story_domains_keep_exact_speech_cue_content(self):
        examples=(
            ("How do rainbows form?",
             "White sunlight contains several colors."),
            ("What makes a volcano erupt?",
             "Pressure builds as hot magma rises."),
            ("What if Earth stopped moving?",
             "Earth's rotation carries the oceans."),
        )
        for topic,narration in examples:
            with self.subTest(topic=topic):
                scene=PortraitScienceScene(topic=topic,narration=narration,
                                            scene_index=1)
                self.assertTrue(scene._title_layout)
                self.assertTrue(scene._caption_layouts=={})
                # Source-independent text layout; decoded video tests
                # independently check the actual encoding.
                active=scene.active_caption(.1,5.)
                self.assertEqual(active,narration)
                self.assertEqual(
                    "".join(scene._caption_layouts[active][0]).replace(" ",""),
                    "".join(narration.split()))

    def test_invalid_inputs_fail_before_image_mutation(self):
        frame=Image.new("RGBA",(1080,1920),(42,60,82,255))
        old=frame.tobytes()
        cases=(
            lambda:paint_header(frame,title=(),font_size=45,badge="SCIENCE"),
            lambda:paint_header(frame,title=("one",),font_size=12,badge="SCIENCE"),
            lambda:paint_header(frame,title=("one",),font_size=43,badge=""),
            lambda:paint_caption(frame,lines=(),font_size=40),
            lambda:paint_caption(Image.new("RGB",(1080,1920)),
                                 lines=("one",),font_size=40),
        )
        for operation in cases:
            with self.assertRaises(ValueError):
                operation()
        self.assertEqual(frame.tobytes(),old)


if __name__=="__main__":
    unittest.main()
