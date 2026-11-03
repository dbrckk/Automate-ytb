"""Original volcanic visual motion and full native portrait framing."""
import unittest
from PIL import Image,ImageChops
from automate_ytb.science_volcano import (
    BEATS,BADGES,SIZE,TOP,classify,supports_topic,draw_volcano
)
from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.science_stage_director import VERSION as DIRECTOR_VERSION

TOPIC="How Do Volcanoes Erupt?"
SCRIPT=(
    "Deep underground, hot rock partially melts, forming a glowing reservoir of magma beneath a volcano.",
    "Gas bubbles become trapped in thick magma, and pressure steadily grows inside the deep underground chamber.",
    "Rising pressure pushes magma steadily upward through cracks in the rock and a narrow vent toward the summit.",
    "When magma reaches the surface, expanding gases can blast ash and glowing fragments high into the sky.",
    "Escaping lava flows down the slopes, while ash settles and the volcano slowly cools.",
)

class OriginalVolcanoTests(unittest.TestCase):
    def test_camera_enabled_in_production_render(self):
        self.assertTrue(DIRECTOR_VERSION.startswith("original-science-director-v2-"))

    def test_five_semantic_actions(self):
        self.assertEqual(BEATS,tuple(classify(TOPIC,t) for t in SCRIPT))
        self.assertEqual(len(BEATS),len(BADGES))
        self.assertTrue(supports_topic(TOPIC))
        self.assertFalse(supports_topic("Why Do Northern Lights Dance?"))
        self.assertIsNone(classify(TOPIC,"A quiet evening passes."))
        with self.assertRaises(ValueError):
            classify(None,SCRIPT[0])

    def test_original_animated_scenes_stay_portrait(self):
        signatures=[]
        for i,phrase in enumerate(SCRIPT,1):
            scene=PortraitScienceScene(topic=TOPIC,narration=phrase,scene_index=i)
            self.assertEqual(scene.volcano_beat,BEATS[i-1])
            self.assertIsNone(scene.aurora_beat)
            self.assertIsNone(scene.lightning_beat)
            self.assertTrue(scene.english)
            self.assertFalse(scene._globes)
            first=scene.frame(.2,6.8)
            later=scene.frame(2.3,6.8)
            self.assertEqual(first.size,(1080,1920))
            self.assertEqual(first.mode,"RGB")
            self.assertEqual(first.tobytes(),scene.frame(.2,6.8).tobytes())
            box=(80,420,990,1470)
            a=first.crop(box)
            self.assertIsNotNone(ImageChops.difference(a,later.crop(box)).getbbox())
            signatures.append(a.tobytes())
        self.assertEqual(len(set(signatures)),5)
        self.assertEqual(SIZE,(1080,1380))
        self.assertEqual(TOP,330)

    def test_invalid_time_frames_rejected(self):
        canvas=Image.new("RGBA",(1080,1920))
        for beat,t,duration in (
                ("unknown",0,6),(BEATS[0],-1,6),(BEATS[0],0,0),
                (BEATS[0],7,6)):
            with self.assertRaises(ValueError):
                draw_volcano(canvas,beat,t,duration,True)
        with self.assertRaises(ValueError):
            draw_volcano(Image.new("RGB",(1080,1920)),BEATS[0],0,6,True)
