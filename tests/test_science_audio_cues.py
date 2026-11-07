"""Source-bound, bounded, deterministic phrase-synchronized visual cues."""
import unittest
from automate_ytb.science_audio_cues import audio_event_fraction, PATTERNS
from automate_ytb.science_portrait import PortraitScienceScene

class ScienceAudioCueTests(unittest.TestCase):
    def test_eruption_uses_actual_second_phrase_time_not_guessed_scene_middle(self):
        segments=[
            {"text":"Deep hot magma rises beneath the rock.","startMs":1000,"endMs":3900},
            {"text":"Then the eruption blasts ash.","startMs":3900,"endMs":6000},
        ]
        actual=audio_event_fraction("volcano","eruption",segments,1000)
        self.assertAlmostEqual(actual, (4950-1000)/5000)
        self.assertNotEqual(actual,.46)
        scene=PortraitScienceScene(topic="How Do Volcanoes Erupt?",
            narration="Deep hot magma rises beneath the rock. Then the eruption blasts ash.",
            scene_index=4,scene_start_ms=1000,caption_segments=segments)
        self.assertAlmostEqual(scene._narrated_event_fraction,actual)

    def test_aurora_collisions_follow_narrated_phrase(self):
        seg=[
            {"text":"Solar wind travels toward Earth.","startMs":0,"endMs":1850},
            {"text":"The particles collide with oxygen.","startMs":1850,"endMs":5700},
        ]
        self.assertAlmostEqual(audio_event_fraction(
            "aurora","collisions",seg,0),(1850+5700)/2/5700)

    def test_lightning_action_uses_real_narration_phrase_midpoint(self):
        from automate_ytb.science_lightning import _narrated_action_clock
        segments=[
            {"text":"The storm grows dark.","startMs":1000,"endMs":2800},
            {"text":"A branching stepped leader begins descending.","startMs":2800,"endMs":6200},
        ]
        event=audio_event_fraction("lightning","leader",segments,1000)
        self.assertAlmostEqual(event,(2800+6200-2000)/2/5200)
        scene=PortraitScienceScene(
            topic="The Secret Life of a Lightning Bolt",
            narration="The storm grows dark. A branching stepped leader begins descending.",
            scene_index=2,scene_start_ms=1000,caption_segments=segments)
        self.assertAlmostEqual(scene._narrated_event_fraction,event)
        duration=7.2
        self.assertAlmostEqual(_narrated_action_clock(0,duration,event),0)
        self.assertAlmostEqual(_narrated_action_clock(duration,duration,event),duration)
        self.assertAlmostEqual(_narrated_action_clock(duration*event,duration,event),duration/2)
        self.assertAlmostEqual(_narrated_action_clock(3.1,duration,None),3.1)
        samples=[_narrated_action_clock(duration*i/100,duration,event)
                 for i in range(101)]
        self.assertTrue(all(a<=b for a,b in zip(samples,samples[1:])))
        with self.assertRaises(ValueError):
            _narrated_action_clock(1,duration,float("nan"))

    def test_missing_phrase_keeps_authored_camera_and_missing_audio_is_safe(self):
        self.assertIsNone(audio_event_fraction("volcano","eruption",None,0))
        self.assertIsNone(audio_event_fraction("volcano","eruption",[
            {"text":"A quiet valley in sunlight.","startMs":0,"endMs":4200}],0))
        self.assertEqual(set(PATTERNS["volcano"]),
            {"magma","pressure","ascent","eruption","lava"})

    def test_corrupt_timing_is_not_silently_used(self):
        good={"text":"Magma erupts.","startMs":0,"endMs":2000}
        for bad in (
            [],[{"text":"Magma erupts.","startMs":100,"endMs":2000}],
            [{"text":"Magma erupts.","startMs":0,"endMs":0}],
            [{"text":"Magma erupts.","startMs":0,"endMs":2000},
             {"text":"Magma erupts.","startMs":2500,"endMs":3000}],
            [{"text":"","startMs":0,"endMs":2000}]):
            with self.assertRaises(ValueError):
                audio_event_fraction("volcano","eruption",bad,0)
        with self.assertRaises(ValueError):
            audio_event_fraction("volcano","eruption",[good],True)
        with self.assertRaises(ValueError):
            audio_event_fraction("none","eruption",[good],0)
