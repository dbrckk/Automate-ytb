"""Causal original subject animations: continuous time, real frames, safe provenance.

The full 2.5D renderer is reused; no frame-wise asset generation or network
image service is introduced. Tests exercise all six subject families and
stored version-15 original JSON for backwards compatibility.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_subject_motion import (
    ACTOR_DEPTHS, FAMILIES, VERSION, subject_pose, subject_motion_tracks)
from automate_ytb.universal_subject_illustrations import (
    subject_layers, subject_tracks)
from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_kinetic import read_story
from automate_ytb.universal_actor_rig import (
    validate_actor_rig, validate_cut_continuity)
from automate_ytb.universal_art25d import (
    load_art_scenes, bind_actor_camera_world, render_art_stage)
from automate_ytb.universal_vector_art import validate_vector_layers


EXAMPLES={
    "botanical":("Tree growth",
                 "A seed grows into a tree while its leaves unfold.\n\n"
                 "The tree stretches upward and leaves move in the wind."),
    "celestial":("Moon and planet",
                 "The moon moves around a planet along a stylized orbit.\n\n"
                 "The planet continues rotating while its moon travels farther."),
    "rail":("A moving train",
            "A locomotive travels along the rails past the railway station.\n\n"
            "The train proceeds toward the next platform with a trail of smoke."),
    "weather":("Rain in clouds",
               "Clouds drift while rain begins to fall.\n\n"
               "Wind moves the cloud and raindrops descend toward the ground."),
    "ocean":("Ocean wave",
             "A wave rises above the ocean surface before falling.\n\n"
             "Waves keep rolling toward the shore and their foam rises."),
    "security":("Password protection",
                "Password security protects an account during login.\n\n"
                "Authentication can help users control access to their account."),
}


class SubjectSpecificMotionTests(unittest.TestCase):
    def test_all_families_produce_distinct_bounded_dynamic_actions(self):
        trajectories=set()
        for family in FAMILIES:
            with self.subTest(family=family):
                frames=[]
                for index in range(4):
                    tracks=subject_motion_tracks(family,index,4)
                    self.assertEqual({t["z"] for t in tracks},set(ACTOR_DEPTHS))
                    for track in tracks:
                        self.assertEqual([k["at"] for k in track["keys"]],
                                         [0.,.25,.5,.75,1.])
                        self.assertTrue(any(
                            abs(k[p]-track["keys"][0][p])>.0001
                            for k in track["keys"][1:]
                            for p in ("x","y","scale","angle")))
                        self.assertGreaterEqual(
                            min(k["scale"] for k in track["keys"]),.45)
                        self.assertLessEqual(
                            max(abs(k["angle"]) for k in track["keys"]),65)
                    if index:
                        prior=subject_motion_tracks(family,index-1,4)
                        for left,right in zip(prior,tracks):
                            self.assertEqual(left["keys"][-1], {
                                **right["keys"][0], "at":1.
                            } | {"at":1.})
                    frames.append(tracks)
                trajectories.add(tuple(
                    (t["z"],tuple((k["x"],k["y"],k["scale"],k["angle"])
                                  for k in t["keys"]))
                    for t in frames[0]))
        self.assertEqual(len(trajectories),6)

    def test_causes_are_specific_and_not_recolored_generic_sines(self):
        plant_first=subject_pose("botanical",45,0)
        plant_final=subject_pose("botanical",45,1)
        self.assertGreater(plant_final["scale"]-plant_first["scale"],.45)
        self.assertGreater(plant_first["y"]-plant_final["y"],.10)

        rail_first=subject_pose("rail",45,0)
        rail_final=subject_pose("rail",45,1)
        self.assertGreater(rail_final["x"]-rail_first["x"],.32)
        for t in (0., .25, .5, .75, 1.):
            # These two physical layers must travel in the same direction
            # because the second carries windows/working machinery.
            self.assertEqual(subject_pose("rail",45,t)["x"],
                             subject_pose("rail",65,t)["x"])

        orbit_start=subject_pose("celestial",65,0)
        orbit_end=subject_pose("celestial",65,1)
        self.assertGreater(orbit_end["angle"]-orbit_start["angle"],100)
        self.assertNotEqual(subject_pose("celestial",65,.25)["y"],
                            subject_pose("celestial",65,.75)["y"])

        rain_start=subject_pose("weather",65,0)
        rain_final=subject_pose("weather",65,1)
        self.assertGreater(rain_final["y"]-rain_start["y"],.15)
        sea=subject_pose("ocean",45,.5)
        self.assertGreater(sea["scale"],subject_pose("ocean",45,0)["scale"])
        self.assertLess(sea["y"],subject_pose("ocean",45,0)["y"])
        self.assertNotEqual(subject_pose("security",85,.25),
                            subject_pose("security",85,.5))

    def test_every_track_validates_with_existing_approved_2d_rig(self):
        for family in FAMILIES:
            layers=validate_vector_layers(subject_layers(family))
            for index in range(3):
                tracks=subject_motion_tracks(family,index,3)
                valid,links=validate_actor_rig(tracks,[],layers)
                self.assertEqual(len(valid),4)
                self.assertEqual(links,[])

    def test_source_provenance_cannot_substitute_motion_or_topic(self):
        for family,(topic,script) in EXAMPLES.items():
            with self.subTest(family=family),tempfile.TemporaryDirectory() as td:
                folder=Path(td)
                story=compile_original_script(
                    topic=topic,script=script,language="en")
                self.assertEqual(story["proceduralMotionEngine"],VERSION)
                self.assertEqual(story["proceduralVisualFamily"],family)
                path=folder/"original.json"
                path.write_text(json.dumps(story),encoding="utf8")
                approved=read_story(path)
                self.assertEqual(approved["proceduralMotionEngine"],VERSION)
                self.assertEqual(validate_cut_continuity(approved),1)
                forged=deepcopy(story)
                forged["proceduralMotionEngine"]="another-motor"
                path.write_text(json.dumps(forged),encoding="utf8")
                with self.assertRaisesRegex(ValueError,"motion provenance"):
                    read_story(path)
                forged=deepcopy(story)
                forged["beats"][0]["actorTracks"][2]["keys"][1]["scale"]+=.015
                path.write_text(json.dumps(forged),encoding="utf8")
                with self.assertRaisesRegex(ValueError,"altered"):
                    read_story(path)
                forged=deepcopy(story)
                forged["beats"][1]["narration"]="These words have no matching subject."
                path.write_text(json.dumps(forged),encoding="utf8")
                with self.assertRaises(ValueError):
                    read_story(path)

    def test_old_generated_v15_json_is_still_valid(self):
        topic,script=EXAMPLES["celestial"]
        fresh=compile_original_script(topic=topic,script=script)
        legacy=deepcopy(fresh)
        legacy.pop("proceduralMotionEngine")
        for index,beat in enumerate(legacy["beats"]):
            beat["actorTracks"]=subject_tracks(index,len(legacy["beats"]))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"old-v15-story.json"
            path.write_text(json.dumps(legacy),encoding="utf8")
            parsed=read_story(path)
            self.assertEqual(parsed["proceduralVisualFamily"],"celestial")
            self.assertIsNone(parsed["proceduralMotionEngine"])
            self.assertEqual(validate_cut_continuity(parsed),1)

    def test_actual_25d_pixels_move_with_subject_specific_actions(self):
        # Rendering sampled frames exercises the actual existing actor path,
        # not a chart or a mocked motion preview.
        for family in ("botanical","celestial","rail","weather","ocean","security"):
            with self.subTest(family=family),tempfile.TemporaryDirectory() as td:
                topic,script=EXAMPLES[family]
                story=compile_original_script(topic=topic,script=script)
                path=Path(td)/"scene.json"
                path.write_text(json.dumps(story),encoding="utf8")
                parsed=read_story(path)
                scenes,records=load_art_scenes(parsed,path,360,640)
                self.assertEqual(len(records),10)
                bound=bind_actor_camera_world(parsed,scenes,[0,75,150])
                self.assertEqual(len(bound),1)
                first=render_art_stage(scenes[0],5,0,75)
                next_frame=render_art_stage(scenes[0],50,0,75)
                last=render_art_stage(scenes[1],125,75,150)
                self.assertEqual(first.mode,"RGBA")
                self.assertEqual(first.size,(295,326))
                self.assertNotEqual(first.tobytes(),next_frame.tobytes())
                self.assertNotEqual(next_frame.tobytes(),last.tobytes())
                self.assertEqual(
                    next_frame.tobytes(),
                    render_art_stage(scenes[0],50,0,75).tobytes())

    def test_invalid_parameters_do_not_become_video_keyframes(self):
        for family,z,moment in (
                ("unlisted",45,.4),("ocean",True,.2),
                ("rail",10,.7),("weather",45,float("nan")),
                ("botanical",65,1.1),("security",85,True),
        ):
            with self.subTest(case=(family,z,moment)),self.assertRaises(ValueError):
                subject_pose(family,z,moment)
        for family,index,total in (
                ("unknown",0,2),("rail",True,3),("weather",0,1),
                ("ocean",3,3),("security",0,13),
        ):
            with self.assertRaises(ValueError):
                subject_motion_tracks(family,index,total)


if __name__=="__main__":
    unittest.main()
