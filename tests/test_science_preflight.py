"""Fail-fast original science storyboarding, no TTS/MP4 required."""
import unittest
from automate_ytb.scene_plan import plan
from automate_ytb.science_preflight import inspect

def make(topic,script):
    return plan(topic=topic,script=script,duration=30,character="Original animated geological visual",shot_seconds=6)

class SciencePreflightTests(unittest.TestCase):
    def test_complete_original_volcano_story_passes(self):
        script=("Hot rock melts into magma. Gas bubbles become trapped under pressure. "
                "Magma rises through cracks and a vent. Eruptions blast ash into the sky. "
                "Lava flows down the slopes.")
        result=inspect(make("How Do Volcanoes Erupt?",script))
        self.assertEqual(result["status"],"passed")
        self.assertEqual(result["domain"],"volcano")
        self.assertEqual(len({x["beat"] for x in result["classifiedScenes"]}),5)

    def test_unsupported_action_fails_before_speech(self):
        script=("Hot rock melts into magma. Gas bubbles create pressure. "
                "A sleepy owl watches the stars. Eruptions blast ash. "
                "Lava flows down the slopes.")
        result=inspect(make("How Do Volcanoes Erupt?",script))
        self.assertEqual(result["status"],"failed")
        self.assertEqual(result["errors"],["Scene scene-003 lacks a supported volcano action"])

    def test_repeated_beats_are_review_only(self):
        script=("Magma melts deep below. Molten rock creates magma. "
                "Gas pressure grows. Eruptions blast ash. Lava flows down.")
        result=inspect(make("How Do Volcanoes Erupt?",script))
        self.assertEqual(result["status"],"passed")
        self.assertEqual(len(result["warnings"]),1)

    def test_non_science_does_not_require_science_classifiers(self):
        result=inspect(make("The Purple Owl",
            "She flies. She lands. She listens. She dances. She sleeps."),
            style="cartoon",resolution="720p")
        self.assertEqual(result["status"],"not-applicable")

    def test_ambiguous_domain_rejected(self):
        script="Magma melts. Gas pressure rises. Ash erupts. Lava flows. Rock cools."
        with self.assertRaisesRegex(ValueError,"Ambiguous"):
            inspect(make("Volcano and aurora science",script))

    def test_duplicate_identifiers_are_rejected(self):
        script="Magma melts. Gas pressure rises. Ash erupts. Lava flows. Rock cools."
        p=make("How Do Volcanoes Erupt?",script)
        p["scenes"][1]["id"]=p["scenes"][0]["id"]
        with self.assertRaisesRegex(ValueError,"duplicate"):
            inspect(p)
