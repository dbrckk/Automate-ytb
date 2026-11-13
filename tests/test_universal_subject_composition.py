"""Original multi-object scenes: real pixels, independently moving actors, provenance."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_subject_composition import (
    VERSION, composition_families, composition_layers, composition_tracks)
from automate_ytb.universal_kinetic import read_story
from automate_ytb.universal_vector_art import (
    validate_vector_layers, vector_sha256, render_vector_layer)
from automate_ytb.universal_actor_rig import (
    same_authored_actor_world, validate_cut_continuity, RiggedArtScene)
from automate_ytb.universal_art25d import (
    load_art_scenes, bind_actor_camera_world, render_art_stage)


STORY=(
    "A forest tree grows as a planet travels along its orbit.\n\n"
    "A tree inside the forest grows while a planet follows its orbit.\n\n"
    "An ocean wave swells while rain falls from a cloud during a storm.\n\n"
    "A conclusion follows from the previous argument without new objects."
)


def checked(data):
    with tempfile.TemporaryDirectory() as folder:
        file=Path(folder)/"story.json"
        file.write_text(json.dumps(data),encoding="utf8")
        return read_story(file)


class GroundedTwoSubjectSceneTests(unittest.TestCase):
    def test_source_text_two_actual_families_per_beat(self):
        data=compile_original_script(
            topic="Tree planet ocean and weather",script=STORY)
        self.assertEqual(data["proceduralVisualFamily"],None)
        self.assertNotIn("proceduralVisualChapterEngine",data)
        self.assertEqual(data["proceduralVisualCompositionEngine"],VERSION)
        self.assertEqual(data["proceduralVisualCompositionFamilies"],[
            ["botanical","celestial"],
            ["botanical","celestial"],
            ["weather","ocean"],[]])
        self.assertFalse(data["factualResearchPerformed"])
        data=checked(data)
        self.assertEqual(data["proceduralVisualCompositionEngine"],VERSION)
        for scene in data["beats"][:3]:
            self.assertEqual(len(scene["visualVectors"]),6)
            self.assertEqual(len(scene["actorTracks"]),4)
            self.assertEqual({track["z"] for track in scene["actorTracks"]},
                             {45,50,65,70})
            self.assertEqual(len(validate_vector_layers(
                scene["visualVectors"])),6)
        self.assertEqual(data["beats"][3]["visualVectors"],[])
        self.assertEqual(data["beats"][3]["actorTracks"],[])
        self.assertTrue(same_authored_actor_world(
            data["beats"][0],data["beats"][1]))
        self.assertFalse(same_authored_actor_world(
            data["beats"][1],data["beats"][2]))
        self.assertEqual(validate_cut_continuity(data),1)

    def test_all_six_families_can_supply_distinct_concrete_actors(self):
        pairs=[
            ["botanical","celestial"],["rail","weather"],
            ["ocean","security"],["security","botanical"]]
        ids=set()
        for pair in pairs:
            with self.subTest(pair=pair):
                layers=validate_vector_layers(composition_layers(pair))
                self.assertEqual(len(layers),6)
                self.assertEqual({l["z"] for l in layers},
                                 {5,25,45,50,65,70})
                self.assertGreaterEqual(sum(len(x["shapes"]) for x in layers),10)
                for item in layers:
                    self.assertTrue(item["rightsConfirmed"])
                    self.assertTrue(item["rights"].startswith(
                        "Original artwork generated locally"))
                hero_a=next(x for x in layers if x["z"]==45)
                hero_b=next(x for x in layers if x["z"]==50)
                self.assertNotEqual(hero_a["id"],hero_b["id"])
                self.assertNotEqual(vector_sha256(hero_a),
                                    vector_sha256(hero_b))
                ids.add((vector_sha256(hero_a),vector_sha256(hero_b)))
                for hero in (hero_a,hero_b):
                    canvas=render_vector_layer(hero,(360,640))
                    self.assertEqual(canvas.mode,"RGBA")
                    self.assertGreater(canvas.getbbox()[2],1)
                self.assertEqual(len(composition_tracks(pair,0,2)),4)
        self.assertEqual(len(ids),len(pairs))

    def test_genuine_independent_animated_2d_actors_and_camera_continuity(self):
        source=compile_original_script(topic="Two illustrated worlds",script=STORY)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"story.json"
            path.write_text(json.dumps(source),encoding="utf8")
            story=read_story(path)
            scenes,proof=load_art_scenes(story,path,360,640)
            self.assertEqual(set(scenes),{0,1,2})
            self.assertEqual(len(proof),18)
            self.assertTrue(all(isinstance(x,RiggedArtScene)
                                for x in scenes.values()))
            joins=bind_actor_camera_world(story,scenes,[0,45,90,135,180])
            self.assertEqual(len(joins),1)
            self.assertEqual((joins[0]["firstBeat"],joins[0]["lastBeat"]),
                             (0,1))
            a=render_art_stage(scenes[0],12,0,45)
            b=render_art_stage(scenes[0],37,0,45)
            c=render_art_stage(scenes[1],54,45,90)
            d=render_art_stage(scenes[2],100,90,135)
            self.assertEqual(a.mode,"RGBA")
            self.assertEqual(a.size,b.size)
            self.assertNotEqual(a.tobytes(),b.tobytes())
            self.assertNotEqual(b.tobytes(),c.tobytes())
            self.assertNotEqual(c.tobytes(),d.tobytes())
            self.assertEqual(a.tobytes(),
                             render_art_stage(scenes[0],12,0,45).tobytes())
            for x,y in zip(story["beats"][0]["actorTracks"],
                           story["beats"][1]["actorTracks"]):
                self.assertEqual(x["z"],y["z"])
                for axis in ("x","y","scale","angle"):
                    self.assertEqual(x["keys"][-1][axis],
                                     y["keys"][0][axis])

    def test_noun_negation_and_unknown_topics_never_fabricate_participants(self):
        script=(
            "No trains are present, but a tree grows in the forest beside a planet.\n\n"
            "The tree grows while the planet continues to move in space."
        )
        output=compile_original_script(topic="Trains and planets",script=script)
        self.assertEqual(output["proceduralVisualCompositionFamilies"],[
            ["botanical","celestial"],["celestial","botanical"]])
        self.assertEqual(checked(output)["proceduralVisualCompositionEngine"],
                         VERSION)
        three=[{"narration":"The forest tree, planet orbit, and ocean wave appear."},
               {"narration":"The discussion finishes without an object."}]
        self.assertIsNone(composition_families(three))
        plain=compile_original_script(
            topic="Abstract evidence",
            script="The argument starts with a possible answer.\n\n"
                   "This explanation follows the initial idea.")
        self.assertNotIn("proceduralVisualCompositionFamilies",plain)
        self.assertEqual(checked(plain)["beats"][0]["visualVectors"],[])

    def test_french_two_subjects_are_recognized_from_french_narration(self):
        data=compile_original_script(
            topic="Une comparaison",
            language="fr",
            script=("Un arbre pousse dans la forêt pendant que la planète suit son orbite.\n\n"
                    "La planète et la forêt restent visibles lorsque l'arbre grandit."))
        self.assertEqual(data["proceduralVisualCompositionFamilies"],[
            ["botanical","celestial"],["botanical","celestial"]])
        self.assertEqual(checked(data)["language"],"fr")

    def test_past_v17_and_v18_content_remains_unchanged(self):
        homogeneous=compile_original_script(
            topic="Ocean waves",
            script="An ocean wave moves across the sea.\n\n"
                   "A rising wave continues beyond the shore.")
        self.assertEqual(homogeneous["proceduralVisualFamily"],"ocean")
        self.assertNotIn("proceduralVisualCompositionEngine",homogeneous)
        self.assertEqual(checked(homogeneous)["proceduralVisualFamily"],"ocean")
        chapters=compile_original_script(
            topic="Different subjects",
            script="A tree grows in a forest every morning.\n\n"
                   "A planet orbits its distant moon in space.")
        self.assertEqual(chapters["proceduralVisualFamilies"],
                         ["botanical","celestial"])
        self.assertNotIn("proceduralVisualCompositionEngine",chapters)
        self.assertEqual(checked(chapters)["proceduralVisualFamilies"],
                         ["botanical","celestial"])

    def test_forged_sources_or_removed_provenance_rejected(self):
        original=compile_original_script(
            topic="Tree planet ocean weather",script=STORY)
        mutations=[
            lambda a:a["proceduralVisualCompositionFamilies"][1].reverse(),
            lambda a:a["proceduralVisualCompositionFamilies"][2].pop(),
            lambda a:a.update(proceduralVisualCompositionEngine="fake"),
            lambda a:a.pop("proceduralVisualCompositionEngine"),
            lambda a:a.pop("proceduralVisualCompositionFamilies"),
            lambda a:a.update(proceduralVisualFamily="botanical"),
            lambda a:a.update(proceduralMotionEngine="fake"),
            lambda a:a["beats"][0]["visualVectors"][2]["shapes"][0].__setitem__(
                "fill","#000000"),
            lambda a:a["beats"][0]["actorTracks"][0]["keys"][1].__setitem__(
                "x",.241),
            lambda a:a["beats"][3].__setitem__(
                "visualVectors",composition_layers(["security"])),
            lambda a:a["beats"][2].__setitem__(
                "narration","A conclusion follows from that original statement."),
        ]
        for mutate in mutations:
            altered=deepcopy(original)
            mutate(altered)
            with self.subTest(change=str(mutate)),self.assertRaises(ValueError):
                checked(altered)
        stripped=deepcopy(original)
        for field in list(stripped):
            if field.startswith("procedural"):
                stripped.pop(field)
        with self.assertRaisesRegex(ValueError,"provenance"):
            checked(stripped)

    def test_strict_budget_and_finite_selection(self):
        for invalid in ([],["botanical","botanical"],
                        ["botanical","celestial","ocean"],["unknown"],None):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                composition_layers(invalid)
        with self.assertRaises(ValueError):
            composition_tracks(["botanical","celestial"],1,1)
        with self.assertRaises(ValueError):
            composition_families([{"narration":"A tree."}])
        with self.assertRaises(ValueError):
            composition_families([{"narration":None},{"narration":"A planet."}])


if __name__=="__main__":
    unittest.main()
