"""Multi-chapter source-text visual routing, no invented scenes, old playback."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_subject_illustrations import (
    CHAPTER_VERSION, subject_chapter_families, subject_layers,
    subject_tracks, apply_chapter_subjects)
from automate_ytb.universal_subject_motion import VERSION as MOTION_VERSION
from automate_ytb.universal_kinetic import read_story
from automate_ytb.universal_art25d import (
    load_art_scenes, bind_actor_camera_world, render_art_stage)
from automate_ytb.universal_actor_rig import (
    validate_cut_continuity, same_authored_actor_world)


MIXED=(
    "A seed grows into a tree and leaves unfold inside the forest.\n\n"
    "The tree keeps growing as new leaves move in the garden.\n\n"
    "A planet travels around its moon along a beautiful orbit in space.\n\n"
    "A transition follows the story without naming another visible subject.\n\n"
    "An ocean wave rises toward the shore while the tide changes."
)


def read(data):
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/"story.json"
        path.write_text(json.dumps(data),encoding="utf8")
        return read_story(path)


class OriginalChapterArtTests(unittest.TestCase):
    def test_each_beat_uses_only_its_own_explicit_subject(self):
        story=compile_original_script(topic="Changing worlds",
                                      script=MIXED,language="en")
        self.assertEqual(story["proceduralVisualFamily"],None)
        self.assertEqual(
            story["proceduralVisualFamilies"],
            ["botanical","botanical","celestial",None,"ocean"])
        self.assertEqual(story["proceduralVisualChapterEngine"],CHAPTER_VERSION)
        self.assertEqual(story["proceduralMotionEngine"],MOTION_VERSION)
        self.assertFalse(story["factualResearchPerformed"])
        self.assertTrue(story["originalTextOnly"])
        parsed=read(story)
        self.assertEqual(parsed["proceduralVisualFamilies"],
                         story["proceduralVisualFamilies"])
        for index,family in enumerate(story["proceduralVisualFamilies"]):
            beat=parsed["beats"][index]
            if family is None:
                self.assertFalse(beat["visualVectors"])
                self.assertFalse(beat["actorTracks"])
            else:
                self.assertEqual(len(beat["visualVectors"]),5)
                self.assertEqual(len(beat["actorTracks"]),4)
                self.assertEqual(beat["visualVectors"][2]["id"],family+"-hero")
        self.assertEqual(validate_cut_continuity(parsed),1)
        self.assertTrue(same_authored_actor_world(parsed["beats"][0],
                                                  parsed["beats"][1]))
        self.assertFalse(same_authored_actor_world(parsed["beats"][1],
                                                   parsed["beats"][2]))

    def test_local_source_selection_overrides_title_without_hallucination(self):
        script=(
            "The clouds bring rain across the valley, and wind moves the storm.\n\n"
            "No trains are present, but the clouds continue to release rain.\n\n"
            "A planet and its moon travel through space in separate orbits."
        )
        result=compile_original_script(
            topic="Why trains and locomotives are fast",
            script=script)
        self.assertEqual(result["proceduralVisualFamilies"],
                         ["weather","weather","celestial"])
        self.assertEqual(read(result)["proceduralVisualFamilies"],
                         result["proceduralVisualFamilies"])
        for beat in result["beats"][:2]:
            self.assertNotIn("rail",beat["visualVectors"][2]["id"])

    def test_french_mixed_topics_are_source_grounded(self):
        script=(
            "Les feuilles d'un arbre s'ouvrent dans une forêt au matin.\n\n"
            "La planète avance dans son orbite et une lune reste visible.\n\n"
            "Un train circule le long du chemin de fer puis la locomotive avance."
        )
        story=compile_original_script(topic="Un voyage",script=script,
                                      language="fr")
        self.assertEqual(story["proceduralVisualFamilies"],
                         ["botanical","celestial","rail"])
        self.assertEqual(read(story)["language"],"fr")

    def test_single_subject_and_unknown_scripts_keep_previous_engines(self):
        homogeneous=compile_original_script(
            topic="Ocean waves",
            script="A wave rises over the ocean.\n\n"
                   "Another wave rolls across the sea.")
        self.assertEqual(homogeneous["proceduralVisualFamily"],"ocean")
        self.assertNotIn("proceduralVisualFamilies",homogeneous)
        self.assertNotIn("proceduralVisualChapterEngine",homogeneous)
        self.assertEqual(len(read(homogeneous)["beats"][0]["actorTracks"]),4)
        unknown=compile_original_script(
            topic="A theoretical principle",
            script="The sequence begins with an abstract proposition.\n\n"
                   "Its conclusion follows the earlier reasoning.")
        self.assertIsNone(unknown["proceduralVisualFamily"])
        self.assertNotIn("proceduralVisualFamilies",unknown)
        self.assertFalse(read(unknown)["beats"][0]["visualVectors"])

    def test_per_beat_motion_uses_global_timeline_and_real_2d_pixels(self):
        story=compile_original_script(topic="Changing worlds",script=MIXED)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"story.json"
            path.write_text(json.dumps(story),encoding="utf8")
            data=read_story(path)
            scenes,records=load_art_scenes(data,path,360,640)
            self.assertEqual(set(scenes),{0,1,2,4})
            self.assertEqual(len(records),20)
            groups=bind_actor_camera_world(data,scenes,[0,60,120,180,240,300])
            self.assertEqual(len(groups),1)
            self.assertEqual(groups[0]["firstBeat"],0)
            self.assertEqual(groups[0]["lastBeat"],1)
            one=render_art_stage(scenes[0],30,0,60)
            two=render_art_stage(scenes[1],90,60,120)
            space=render_art_stage(scenes[2],145,120,180)
            self.assertEqual(one.mode,"RGBA")
            self.assertEqual(one.size,(296,326))
            self.assertNotEqual(one.tobytes(),two.tobytes())
            self.assertNotEqual(two.tobytes(),space.tobytes())
            self.assertEqual(one.tobytes(),
                             render_art_stage(scenes[0],30,0,60).tobytes())
            first=story["beats"][0]["actorTracks"]
            second=story["beats"][1]["actorTracks"]
            for left,right in zip(first,second):
                for prop in ("x","y","scale","angle"):
                    self.assertEqual(left["keys"][-1][prop],
                                     right["keys"][0][prop])

    def test_inconsistent_families_and_artwork_are_rejected(self):
        good=compile_original_script(topic="Changing worlds",script=MIXED)
        for modify in (
            lambda s:s["proceduralVisualFamilies"].__setitem__(2,"rail"),
            lambda s:s["proceduralVisualFamilies"].__setitem__(3,"ocean"),
            lambda s:s.update(proceduralVisualFamily="botanical"),
            lambda s:s.update(proceduralVisualChapterEngine="made-up"),
            lambda s:s.pop("proceduralVisualChapterEngine"),
            lambda s:s.pop("proceduralVisualFamilies"),
            lambda s:s.update(proceduralMotionEngine="unsupported-motion"),
            lambda s:s["beats"][3].__setitem__(
                "visualVectors",subject_layers("security")),
            lambda s:s["beats"][2].__setitem__(
                "visualVectors",subject_layers("botanical")),
            lambda s:s["beats"][2]["actorTracks"][1]["keys"][2].__setitem__(
                "x",.211),
            lambda s:s["beats"][2].__setitem__(
                "narration","The conclusion continues toward another outcome."),
        ):
            tampered=deepcopy(good)
            modify(tampered)
            with self.subTest(modify=modify),self.assertRaises(ValueError):
                read(tampered)

    def test_unsupported_visual_sequences_fail_closed(self):
        beats=[{"narration":"The tree grows in the forest."},
               {"narration":"The planet follows an orbit."}]
        original=subject_chapter_families(beats)
        self.assertEqual(original,["botanical","celestial"])
        for bad in (["botanical","rail"],["botanical"],[],None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                apply_chapter_subjects(deepcopy(beats),bad)
        for bad in ([],[{"narration":"forest"}],[{"narration":None},
                                                {"narration":"planet"}]):
            with self.assertRaises(ValueError):
                subject_chapter_families(bad)
        ambiguous=[{"narration":"The tree grows in the forest."},
                   {"narration":"The leaves move in the garden."}]
        self.assertIsNone(subject_chapter_families(ambiguous))


if __name__=="__main__":
    unittest.main()
