"""P4.9: real mobile composition, one-shot lightning hook and strict safe bands."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops

from automate_ytb.lightning_editorial25d import (
    VERSION, _intro_plate, _chapter_plate, render_lightning_editorial,
)
from automate_ytb.science_lightning import BEATS
from automate_ytb.science_portrait import PortraitScienceScene


TITLE = ("Can Lightning Travel Upward", "From a Tower?")
TOPIC = "Can Lightning Travel Upward From a Tower?"


def overlay(beat: str, index: int, t: float, duration: float = 6.):
    base = Image.new("RGBA", (1080, 1920), (7, 18, 38, 255))
    render_lightning_editorial(
        base, beat=beat, scene_index=index, t=t,
        duration=duration, english=True,
        title_lines=TITLE, title_size=47)
    return base


class LightningEditorialTests(unittest.TestCase):
    def test_full_episode_hook_only_in_opening_not_each_scene(self):
        self.assertIn("p49",VERSION)
        opening=overlay("charge",1,.4)
        chapter=overlay("charge",1,3.)
        next_shot=overlay("leader",2,3.)
        late_next_shot=overlay("leader",2,5.)
        band=(65,105,1020,305)
        self.assertNotEqual(opening.crop(band).tobytes(),
                            chapter.crop(band).tobytes())
        self.assertNotEqual(chapter.crop(band).tobytes(),
                            next_shot.crop(band).tobytes())
        # Persistent chapter heading does not bounce or re-render differently
        # inside an action. Camera moves, NOT the typography in the top band.
        self.assertEqual(next_shot.crop(band).tobytes(),
                         late_next_shot.crop(band).tobytes())
        self.assertEqual(overlay("leader",2,3.).tobytes(),
                         next_shot.tobytes())

    def test_cinematic_hook_is_smooth_and_ends_without_frozen_card(self):
        base=Image.new("RGBA",(1080,1920),(7,18,38,255))
        at_start=overlay("charge",1,0.)
        intro=overlay("charge",1,.30)
        before_crossfade=overlay("charge",1,1.54)
        crossfade=overlay("charge",1,1.92)
        after=overlay("charge",1,2.40)
        self.assertEqual(at_start.tobytes(),base.tobytes())
        self.assertNotEqual(intro.tobytes(),base.tobytes())
        self.assertNotEqual(before_crossfade.tobytes(),crossfade.tobytes())
        self.assertNotEqual(crossfade.tobytes(),after.tobytes())
        self.assertEqual(after.tobytes(),overlay("charge",1,5.).tobytes())

    def test_real_world_and_subtitle_bands_are_byte_identical(self):
        for beat,idx,t in (("charge",1,.5),("leader",2,2.),
                           ("connection",3,3.),("return",4,1.)):
            base=Image.new("RGBA",(1080,1920),(5,16,35,255))
            edited=base.copy()
            render_lightning_editorial(
                edited,beat=beat,scene_index=idx,t=t,duration=6.,
                english=True,title_lines=TITLE,title_size=47)
            # The upper hook is the only altered band: no alpha overlays
            # cover the moving lightning, viewer controls or measured captions.
            self.assertEqual(edited.crop((0,335,1080,1920)).tobytes(),
                             base.crop((0,335,1080,1920)).tobytes())
            self.assertEqual(edited.getchannel("A").getextrema(),(255,255))

    def test_cached_plates_never_mutate_during_alpha_fades(self):
        intro=_intro_plate(TITLE,47)
        chapter=_chapter_plate("charge",True)
        original_intro=intro.tobytes()
        original_chapter=chapter.tobytes()
        for t in (.02,.26,.7,1.57,1.91,2.0,3.):
            overlay("charge",1,t)
        self.assertEqual(_intro_plate(TITLE,47).tobytes(),original_intro)
        self.assertEqual(_chapter_plate("charge",True).tobytes(),
                         original_chapter)

    def test_all_five_chapters_distinct_and_french_labels_supported(self):
        signature=set()
        for beat in BEATS:
            label=_chapter_plate(beat,True)
            signature.add(label.tobytes())
            self.assertEqual(label.size,(1080,335))
            french=_chapter_plate(beat,False)
            self.assertNotEqual(french.tobytes(),label.tobytes())
        self.assertEqual(len(signature),5)

    def test_production_portrait_still_places_real_video_and_subtitles(self):
        scene=PortraitScienceScene(
            topic=TOPIC,
            narration="From the tower tip, upward streamers rise and connect.",
            scene_index=3)
        a=scene.frame(.4,6.)
        b=scene.frame(2.8,6.)
        self.assertEqual(a.size,(1080,1920))
        self.assertEqual(a.mode,"RGB")
        self.assertIsNotNone(ImageChops.difference(a,b).getbbox())
        # Regression against accidentally replacing the scene dispatcher:
        # moving lightning geometry inside the physical stage must change,
        # independently of the top title or lower narration captions.
        hero=(40,350,1040,1530)
        self.assertIsNotNone(
            ImageChops.difference(a.crop(hero),b.crop(hero)).getbbox())
        self.assertEqual(a.crop((0,80,1080,330)).size,(1080,250))

    def test_invalid_editorial_state_fails_closed(self):
        for canvas,beat,index,t,dur,english,title,size in (
            (Image.new("RGB",(1080,1920)),"charge",1,1.,6.,True,TITLE,47),
            (Image.new("RGBA",(720,1280)),"charge",1,1.,6.,True,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"unknown",1,1.,6.,True,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"charge",0,1.,6.,True,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"charge",1,math.nan,6.,True,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"charge",1,1.,0.,True,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"charge",1,7.,6.,True,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"charge",1,1.,6.,1,TITLE,47),
            (Image.new("RGBA",(1080,1920)),"charge",1,1.,6.,True,(),47),
            (Image.new("RGBA",(1080,1920)),"charge",1,1.,6.,True,TITLE,13),
        ):
            with self.assertRaises(ValueError):
                render_lightning_editorial(canvas,beat=beat,scene_index=index,
                                           t=t,duration=dur,english=english,
                                           title_lines=title,title_size=size)


if __name__=="__main__":
    unittest.main()
