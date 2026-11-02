"""Aurora Shorts show original 5-beat motion rather than repeating lightning."""
import unittest
from PIL import Image, ImageChops

from automate_ytb.science_aurora import (
    BEATS, BADGES, classify, supports_topic, draw_aurora, STAGE_SIZE,
)
from automate_ytb.science_portrait import PortraitScienceScene

TOPIC="Why Do Northern Lights Dance?"
LINES=(
    "The Sun releases a stream of charged particles called the solar wind.",
    "Earth's magnetic field guides some of them toward the northern and southern polar skies.",
    "High above us, those particles collide with oxygen and nitrogen in the atmosphere.",
    "Excited gases release their energy as colored light, often green, sometimes red or violet.",
    "These glowing regions stretch into rippling curtains: the northern lights dancing across the sky.",
)


class OriginalAuroraTests(unittest.TestCase):
    def test_five_semantically_mapped_shots(self):
        self.assertEqual(len(BEATS),5)
        self.assertEqual(set(BEATS),set(BADGES))
        self.assertEqual(tuple(classify(TOPIC,x) for x in LINES),BEATS)
        self.assertTrue(supports_topic(TOPIC))
        self.assertFalse(supports_topic("How do rainbows form?"))
        self.assertFalse(supports_topic("How does lightning form?"))
        self.assertIsNone(classify(TOPIC,"Nothing much happens."))
        with self.assertRaises(ValueError):
            classify(None,LINES[0])

    def test_native_animated_portrait_has_no_old_planet_or_storm(self):
        signatures=[]
        for i,phrase in enumerate(LINES,1):
            shot=PortraitScienceScene(topic=TOPIC,narration=phrase,scene_index=i)
            self.assertEqual(shot.aurora_beat,BEATS[i-1])
            self.assertIsNone(shot.rainbow_beat)
            self.assertIsNone(shot.lightning_beat)
            self.assertTrue(shot.english)
            self.assertFalse(shot._globes)
            frame=shot.frame(.2,6)
            later=shot.frame(1.5,6)
            self.assertEqual(frame.size,(1080,1920))
            self.assertEqual(frame.mode,"RGB")
            self.assertEqual(frame.tobytes(),shot.frame(.2,6).tobytes())
            crop=frame.crop((90,490,995,1440))
            signatures.append(crop.tobytes())
            self.assertIsNotNone(ImageChops.difference(
                crop,later.crop((90,490,995,1440))).getbbox())
        self.assertEqual(len(set(signatures)),5)

    def test_invalid_times_and_source_frames_rejected(self):
        canvas=Image.new("RGBA",(1080,1920))
        with self.assertRaises(ValueError):
            draw_aurora(canvas,"invalid",0,6,True)
        with self.assertRaises(ValueError):
            draw_aurora(canvas,BEATS[0],-1,6,True)
        with self.assertRaises(ValueError):
            draw_aurora(Image.new("RGB",(1080,1920)),BEATS[0],0,6,True)
