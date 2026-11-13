"""Cinematic 9:16 PCM caption overlay: all original words, real pixels, safe area."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops

from automate_ytb.captions import caption_phrases
from automate_ytb.universal_caption_overlay import (
    caption_layout, paint_phrase_caption, phrase_opacity)


class PhraseSafeSubtitleTests(unittest.TestCase):
    def test_original_words_are_preserved_with_real_font_measurements(self):
        scripts=(
            "A strange bird unfolds its feathers as the morning light returns.",
            "Les particules lumineuses rebondissent dans la profondeur des océans.",
            "A hydrogen atom contains one proton, and may also contain a neutron.",
            "This short narration mentions a long scientific observation; without skipping a word.",
        )
        for width in (360,720,1080):
            height=width*16//9
            for sentence in scripts:
                for phrase in caption_phrases(sentence):
                    with self.subTest(width=width,phrase=phrase):
                        layout=caption_layout(phrase,width=width,height=height)
                        self.assertEqual(" ".join(layout["lines"])," ".join(phrase.split()))
                        self.assertTrue(1<=len(layout["lines"])<=3)
                        self.assertGreaterEqual(layout["x"],round(width*.08))
                        self.assertLessEqual(layout["x"]+layout["panelWidth"],
                                             width-round(width*.08))
                        self.assertGreaterEqual(layout["y"],round(height*.69))
                        self.assertLessEqual(layout["y"]+layout["panelHeight"],
                                             round(height*.89))
                        self.assertEqual(
                            layout,caption_layout(phrase,width=width,height=height))

    def test_real_in_image_caption_is_local_not_fullscreen(self):
        width=360
        original=Image.new("RGB",(width,640),(42,61,81))
        before=original.tobytes()
        phrase="A floating illustration continues to move behind this caption."
        layout=caption_layout(phrase,width=360,height=640)
        image=paint_phrase_caption(
            original,phrase,frame=42,start=0,end=90,layout=layout)
        self.assertIs(image,original)
        self.assertNotEqual(before,image.tobytes())
        self.assertEqual(image.getpixel((20,50)),(42,61,81))
        self.assertEqual(image.getpixel((20,600)),(42,61,81))
        x=layout["x"]+layout["panelWidth"]//2
        y=layout["y"]+layout["panelHeight"]//2
        self.assertNotEqual(image.getpixel((x,y)),(42,61,81))
        second=Image.new("RGB",(360,640),(42,61,81))
        paint_phrase_caption(second,phrase,frame=42,start=0,end=90,
                             layout=layout)
        self.assertEqual(image.tobytes(),second.tobytes())

    def test_caption_phrase_fades_follow_exact_speech_frame_bounds(self):
        self.assertLess(phrase_opacity(0,0,90),120)
        self.assertEqual(phrase_opacity(6,0,90),255)
        self.assertLess(phrase_opacity(89,0,90),120)
        self.assertLess(phrase_opacity(10,10,44),255)
        self.assertEqual(phrase_opacity(20,10,44),255)
        for frame,start,stop in ((-1,0,90),(0,0,0),(90,0,90),
                                 (0,1,90),(1,True,90),
                                 (1,1,2.0)):
            with self.subTest(input=(frame,start,stop)),self.assertRaises(ValueError):
                phrase_opacity(frame,start,stop)

    def test_layout_cache_cannot_corrupt_the_source_text(self):
        phrase="Original scientific words are never silently removed."
        first=caption_layout(phrase,width=720,height=1280)
        first["lines"].clear()
        first["fontSize"]=1000
        second=caption_layout(phrase,width=720,height=1280)
        self.assertEqual(" ".join(second["lines"]),phrase)
        self.assertLess(second["fontSize"],100)
        frame=Image.new("RGB",(720,1280),(18,19,22))
        with self.assertRaisesRegex(ValueError,"stale"):
            paint_phrase_caption(frame,phrase,frame=10,start=0,end=30,
                                 layout=first)

    def test_unrenderable_long_tokens_fail_closed_without_ellipsis(self):
        for bad in ("W"*200,"a"*800, "\0 unsafe"):
            with self.subTest(value=bad[:10]),self.assertRaises(ValueError):
                caption_layout(bad,width=360,height=640)
        with self.assertRaises(ValueError):
            caption_layout("Empty geometry",width=True,height=640)
        with self.assertRaises(ValueError):
            caption_layout("Landscape frame",width=720,height=720)
        with self.assertRaises(ValueError):
            paint_phrase_caption(
                Image.new("RGB",(300,600)),
                "Cannot write landscape output",frame=0,start=0,end=30)


if __name__=="__main__":
    unittest.main()
