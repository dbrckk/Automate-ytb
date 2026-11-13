"""Source-noun original illustrated video: different silhouettes, honest fallback."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_subject_illustrations import (
    select_subject, subject_layers, subject_tracks, apply_original_subjects)
from automate_ytb.universal_vector_art import (
    validate_vector_layers, render_vector_layer, vector_sha256)
from automate_ytb.universal_art25d import (
    load_art_scenes, bind_actor_camera_world, render_art_stage)
from automate_ytb.universal_actor_rig import RiggedArtScene
from automate_ytb.universal_kinetic import read_story

TEXTS={
    "botanical":("The life of trees",
                 "The forest contains trees with many leaves and woody trunks. "
                 "A tiny seed can begin another plant.\n\n"
                 "Leaves move through the garden as the light changes over time."),
    "celestial":("The solar system",
                 "A planet travels along an orbit in outer space. "
                 "The moon reflects distant light.\n\n"
                 "Planets and moons have different paths around their neighbors."),
    "rail":("Railway transportation",
            "A locomotive moves on railway tracks between cities. "
            "A train passes the platform.\n\n"
            "The train approaches a station as its wheels continue turning."),
    "weather":("Weather and clouds",
               "Rain falls beneath clouds that drift over the hills. "
               "A storm appears far away.\n\n"
               "The clouds move across the sky while the rain continues."),
    "ocean":("How ocean waves work",
             "Ocean waves travel along a large surface of water. "
             "The tide changes on the shore.\n\n"
             "A wave rolls toward the coast as smaller ripples move around it."),
    "security":("Digital password security",
                "A login service checks a password and performs authentication. "
                "Encryption protects a message.\n\n"
                "The login gate may unlock when valid credentials are provided."),
}
RIGHTS="Original artwork generated locally by Automate-ytb"


class SourceAnchoredProceduralArtTests(unittest.TestCase):
    def test_explicit_words_produce_distinct_original_object_families(self):
        hashes=set()
        for family,(topic,script) in TEXTS.items():
            with self.subTest(family=family):
                output=compile_original_script(topic=topic,script=script,
                                               language="en")
                self.assertEqual(output["proceduralVisualFamily"],family)
                self.assertFalse(output["factualResearchPerformed"])
                self.assertTrue(output["originalTextOnly"])
                self.assertEqual(len(output["beats"]),2)
                layers=output["beats"][0]["visualVectors"]
                valid=validate_vector_layers(layers)
                self.assertEqual(len(valid),5)
                self.assertEqual({item["z"] for item in valid},
                                 {5,25,45,65,85})
                self.assertGreaterEqual(sum(len(x["shapes"]) for x in valid),45)
                self.assertTrue(all(x["rights"].startswith(RIGHTS)
                                    and x["rightsConfirmed"] for x in valid))
                self.assertEqual(layers,output["beats"][1]["visualVectors"])
                self.assertEqual(len(output["beats"][0]["actorTracks"]),4)
                self.assertEqual(len(output["beats"][1]["actorTracks"]),4)
                for before,after in zip(output["beats"][0]["actorTracks"],
                                        output["beats"][1]["actorTracks"]):
                    self.assertEqual(before["keys"][-1]["x"],
                                     after["keys"][0]["x"])
                    for axis in ("y","scale","angle"):
                        self.assertEqual(before["keys"][-1][axis],
                                         after["keys"][0][axis])
                hashes.add(vector_sha256(valid[2]))
        self.assertEqual(len(hashes),len(TEXTS))

    def test_unrelated_subjects_do_not_fabricate_concrete_visuals(self):
        script=("A mysterious mechanism repeats a pattern at regular times. "
                "The observer records what happens.\n\n"
                "The experiment continues and reaches a predictable endpoint.")
        result=compile_original_script(topic="An abstract process",
                                       script=script,language="en")
        self.assertIsNone(result["proceduralVisualFamily"])
        self.assertTrue(all("visualVectors" not in b and
                            "actorTracks" not in b for b in result["beats"]))
        self.assertIsNone(select_subject("Vehicles","No trains are present."))
        self.assertIsNone(select_subject("Digital","Nothing connects those ideas."))
        for topic,narration in ((12,"text"),("topic",None)):
            with self.assertRaises(ValueError):
                select_subject(topic,narration)
        with self.assertRaises(ValueError):
            subject_layers("made-up-family")
        with self.assertRaises(ValueError):
            subject_tracks(0,1)
        with self.assertRaises(ValueError):
            apply_original_subjects("Forest",[{"narration":"trees",
                                              "visualVectors":[]},
                                             {"narration":"leaves"}])

    def test_french_subjects_use_source_words_not_made_up_facts(self):
        cases=[
            ("Une forêt au printemps",
             "Les arbres grandissent dans la forêt. Les feuilles deviennent visibles.\n\n"
             "Une graine est déposée dans un jardin, puis les plantes évoluent.",
             "botanical"),
            ("Le voyage d'une planète",
             "La planète parcourt son orbite autour d'une étoile lointaine.\n\n"
             "La lune apparaît dans l'espace tandis que les étoiles sont visibles.",
             "celestial"),
            ("La circulation ferroviaire",
             "Un train traverse les voies ferrées pour rejoindre une gare.\n\n"
             "Une locomotive voyage dans un nouveau paysage avant le soir.",
             "rail"),
        ]
        for topic,text,family in cases:
            with self.subTest(family=family):
                story=compile_original_script(topic=topic,script=text,language="fr")
                self.assertEqual(story["proceduralVisualFamily"],family)
                self.assertTrue(story["originalTextOnly"])

    def test_generated_subject_provenance_cannot_be_spoofed_or_mutated(self):
        topic,script=TEXTS["botanical"]
        original=compile_original_script(topic=topic,script=script)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"approved.json"
            path.write_text(json.dumps(original),encoding="utf8")
            trusted=read_story(path)
            self.assertEqual(trusted["proceduralVisualFamily"],"botanical")
            forged=json.loads(json.dumps(original))
            forged["proceduralVisualFamily"]="celestial"
            path.write_text(json.dumps(forged),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"provenance"):
                read_story(path)
            forged=json.loads(json.dumps(original))
            forged["beats"][0]["visualVectors"][2]["shapes"][0]["fill"]="#000000"
            path.write_text(json.dumps(forged),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"altered"):
                read_story(path)
            forged=json.loads(json.dumps(original))
            forged["beats"][1]["actorTracks"][0]["keys"][1]["x"]+=.015
            path.write_text(json.dumps(forged),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"altered"):
                read_story(path)
            forged=json.loads(json.dumps(original))
            forged["proceduralVisualEngine"]="fake-remote-studio"
            path.write_text(json.dumps(forged),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"provenance"):
                read_story(path)

    def test_rasterized_original_world_is_real_transparent_and_continuous(self):
        for family in ("botanical","celestial","rail","ocean","weather","security"):
            with self.subTest(family=family),tempfile.TemporaryDirectory() as td:
                topic,script=TEXTS[family]
                original=compile_original_script(topic=topic,script=script)
                path=Path(td)/"story.json"
                path.write_text(json.dumps(original),encoding="utf8")
                parsed=read_story(path)
                scenes,provenance=load_art_scenes(parsed,path,360,640)
                self.assertEqual(len(scenes),2)
                self.assertEqual(len(provenance),10)
                self.assertIsInstance(scenes[0],RiggedArtScene)
                self.assertIsInstance(scenes[1],RiggedArtScene)
                for scene in scenes.values():
                    self.assertEqual(len(scene.crops),4)
                group=bind_actor_camera_world(parsed,scenes,[0,75,150])
                self.assertEqual(len(group),1)
                self.assertEqual(group[0]["cameraEndFrame"],150)
                a=render_art_stage(scenes[0],0,0,75)
                b=render_art_stage(scenes[0],40,0,75)
                c=render_art_stage(scenes[1],75,75,150)
                self.assertEqual(a.size,b.size)
                self.assertEqual(a.mode,"RGBA")
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertNotEqual(b.tobytes(),c.tobytes())
                self.assertEqual(b.tobytes(),
                                 render_art_stage(scenes[0],40,0,75).tobytes())


if __name__=="__main__":
    unittest.main()
