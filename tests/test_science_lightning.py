"""No reference-video repetition: five genuinely different lightning actions."""
from __future__ import annotations

import unittest
from PIL import Image, ImageChops

from automate_ytb.scene_plan import beats
from automate_ytb.science_lightning import (
    BEATS, BADGES, PATH, classify, supports_topic, draw_lightning,
    storm_background, STAGE_TOP, STAGE_BOTTOM,
)
from automate_ytb.science_portrait import PortraitScienceScene

TOPIC="Comment se forment les éclairs ?"
SCRIPT=(
    "Dans un nuage d'orage, les collisions entre gouttes et cristaux de glace contribuent à séparer les charges électriques.",
    "Quand le champ électrique devient suffisamment fort, un canal ionisé progresse par étapes vers le sol.",
    "Près du sol, des décharges ascendantes peuvent rejoindre ce canal et ouvrir un trajet conducteur.",
    "Un courant très intense remonte alors le canal : c'est l'éclair lumineux que nous observons.",
    "L'air se réchauffe brutalement et se dilate, créant une onde sonore : le tonnerre.",
)


class OriginalLightningEpisodeTests(unittest.TestCase):
    def test_exact_five_unique_narration_actions(self):
        self.assertEqual(len(BEATS),5)
        self.assertEqual(set(BEATS),set(BADGES))
        self.assertEqual(len(PATH),57)
        self.assertTrue(supports_topic(TOPIC))
        self.assertTrue(supports_topic("How does lightning form?"))
        self.assertFalse(supports_topic("Why does the Earth stop?"))
        self.assertFalse(supports_topic("Why is the ocean blue?"))
        self.assertFalse(supports_topic("How do rainbows form?"))
        self.assertEqual(
            tuple(classify(TOPIC,text) for text in SCRIPT),BEATS)
        self.assertEqual(len(beats(" ".join(SCRIPT))),5)
        self.assertIsNone(classify(TOPIC,"A mysterious shape appears."))
        self.assertIsNone(classify("Earth stopped",SCRIPT[1]))
        for bad in ((None,SCRIPT[0]),(TOPIC,None)):
            with self.assertRaises(ValueError):
                classify(*bad)

    def test_new_episode_has_no_globe_and_five_distinct_frames(self):
        signatures=[]
        for i,(beat,phrase) in enumerate(zip(BEATS,SCRIPT),1):
            with self.subTest(beat=beat):
                shot=PortraitScienceScene(
                    topic=TOPIC,narration=phrase,scene_index=i)
                self.assertEqual(shot.lightning_beat,beat)
                self.assertIsNone(shot.earth_stop_beat)
                self.assertIsNone(shot.rainbow_beat)
                self.assertIsNone(shot.beat)
                self.assertFalse(shot.english)
                self.assertFalse(shot._globes)
                start=shot.frame(.3,6.8)
                end=shot.frame(5.8,6.8)
                self.assertEqual(start.size,(1080,1920))
                self.assertEqual(start.mode,"RGB")
                self.assertEqual(start.tobytes(),shot.frame(.3,6.8).tobytes())
                hero=(70,610,1010,1490)
                crop=start.crop(hero)
                signatures.append(crop.tobytes())
                self.assertIsNotNone(ImageChops.difference(
                    crop,end.crop(hero)).getbbox())
                self.assertEqual(
                    start.crop((65,1522,1015,1722)).tobytes(),
                    end.crop((65,1522,1015,1722)).tobytes())
        self.assertEqual(len(set(signatures)),5)

    def test_storm_canvas_safe_text_and_no_earth_plate(self):
        base=storm_background()
        self.assertEqual(base.mode,"RGBA")
        self.assertEqual(base.size,(1080,1920))
        self.assertLess(base.getpixel((540,100))[2],100)
        for beat in BEATS:
            with self.subTest(beat=beat):
                frame=base.copy()
                draw_lightning(frame,beat,.4,6.8,False)
                self.assertEqual(frame.getchannel("A").getextrema(),(255,255))
                self.assertEqual(frame.crop((0,0,1080,STAGE_TOP)).tobytes(),
                                 base.crop((0,0,1080,STAGE_TOP)).tobytes())
                self.assertEqual(frame.crop((0,STAGE_BOTTOM,1080,1920)).tobytes(),
                                 base.crop((0,STAGE_BOTTOM,1080,1920)).tobytes())

    def test_reject_unsupported_scene_and_bad_clock(self):
        frame=storm_background().copy()
        for beat,t,dur in [
            ("planet",1.,6.8),("leader",-1.,6.8),
            ("charge",6.9,6.8),("return",1.,0),
            ("thunder",float("nan"),6.8),
        ]:
            with self.subTest(beat=beat,t=t),self.assertRaises(ValueError):
                draw_lightning(frame,beat,t,dur,False)
        with self.assertRaises(ValueError):
            draw_lightning(Image.new("RGB",(1080,1920)),
                           "leader",1.,6.8,False)
        with self.assertRaises(ValueError):
            PortraitScienceScene(topic=TOPIC,
                narration="A story without a physical mechanism",
                scene_index=1)


if __name__=="__main__":
    unittest.main()
