"""Strict, reproducible source-verb contact events and genuine visual/audio links."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_subject_interaction import (
    VERSION, detect_contacts, contact_layers, contact_tracks_and_links)
from automate_ytb.universal_subject_composition import (
    composition_families, composition_tracks)
from automate_ytb.universal_kinetic import read_story, timeline_for
from automate_ytb.universal_actor_rig import (
    validate_cut_continuity, same_authored_actor_world, RiggedArtScene)
from automate_ytb.universal_vector_art import validate_vector_layers
from automate_ytb.universal_art25d import (
    load_art_scenes, bind_actor_camera_world, render_art_stage)

SCRIPT=(
    "Rain waters the forest tree and soaks its leaves while clouds gather nearby.\n\n"
    "The forest tree keeps growing while a rain cloud drifts over the garden.\n\n"
    "An ocean wave crashes into a train as the railway passes the shoreline.\n\n"
    "The train continues along the railway while an ocean wave rolls nearby."
)
PAIRS=[
    ["botanical","weather"],["botanical","weather"],
    ["rail","ocean"],["rail","ocean"],
]
EVENTS=[
    {"kind":"rain-waters-plant","at":.5},None,
    {"kind":"wave-hits-train","at":.5},None,
]


def checked(story):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/"story.json"
        path.write_text(json.dumps(story),encoding="utf8")
        return read_story(path)


class CausalOriginalActorTests(unittest.TestCase):
    def example(self):
        return compile_original_script(
            topic="Rain nourishes a forest; waves meet trains",
            script=SCRIPT,language="en")

    def test_two_explicit_contacts_are_source_grounded_and_real(self):
        story=self.example()
        self.assertEqual(story["proceduralVisualInteractionEngine"],VERSION)
        self.assertEqual(story["proceduralVisualCompositionFamilies"],PAIRS)
        self.assertEqual(story["proceduralVisualInteractions"],EVENTS)
        self.assertFalse(story["factualResearchPerformed"])
        self.assertTrue(story["originalTextOnly"])
        self.assertEqual([len(b.get("actorLinks",[])) for b in story["beats"]],
                         [1,0,1,0])
        parsed=checked(story)
        self.assertEqual(parsed["proceduralVisualInteractions"],EVENTS)
        self.assertEqual(validate_cut_continuity(parsed),2)
        for beat in parsed["beats"]:
            self.assertEqual(len(beat["visualVectors"]),6)
            self.assertEqual(len(beat["actorTracks"]),4)
            self.assertEqual(len(validate_vector_layers(beat["visualVectors"])),6)
        self.assertEqual(parsed["beats"][0]["actorLinks"],
                         [{"fromZ":70,"toZ":65,"at":.5}])
        self.assertEqual(parsed["beats"][2]["actorLinks"],
                         [{"fromZ":50,"toZ":45,"at":.5}])
        self.assertTrue(same_authored_actor_world(
            parsed["beats"][0],parsed["beats"][1]))
        self.assertTrue(same_authored_actor_world(
            parsed["beats"][2],parsed["beats"][3]))

    def test_contact_and_causal_foley_use_same_pcm_timeline(self):
        data=checked(self.example())
        bounds=[0,70,140,210,280]
        timeline=timeline_for(data,bounds)
        contacts=[cue for cue in timeline.audio_events()
                  if cue["family"]=="contact"]
        self.assertEqual(len(contacts),2)
        self.assertEqual([cue["atFrame"] for cue in contacts],[34,174])
        self.assertEqual(contacts[0]["atSample"],34*1600)
        self.assertEqual(contacts[1]["atSample"],174*1600)

    def test_persistent_growth_is_continuous_at_cut_and_distinct_from_v19(self):
        data=self.example()
        first={t["z"]:t for t in data["beats"][0]["actorTracks"]}
        second={t["z"]:t for t in data["beats"][1]["actorTracks"]}
        prior={t["z"]:t for t in composition_tracks(PAIRS[0],0,4)}
        self.assertGreater(first[65]["keys"][-1]["scale"],
                           prior[65]["keys"][-1]["scale"])
        self.assertAlmostEqual(first[65]["keys"][-1]["scale"]-
                               prior[65]["keys"][-1]["scale"],.07,places=6)
        self.assertEqual(first[65]["keys"][-1]["scale"],
                         second[65]["keys"][0]["scale"])
        self.assertEqual(first[70]["keys"][-1]["x"],
                         second[70]["keys"][0]["x"])
        middle=first[70]["keys"][2]
        self.assertLess(middle["x"],-.15)
        self.assertLess(middle["y"],-.15)

    def test_real_pixel_dynamics_deterministic_and_two_live_actors(self):
        story=self.example()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"story.json"
            path.write_text(json.dumps(story),encoding="utf8")
            parsed=read_story(path)
            scenes,manifest=load_art_scenes(parsed,path,360,640)
            self.assertEqual(len(manifest),24)
            self.assertEqual(len(scenes),4)
            self.assertTrue(all(isinstance(x,RiggedArtScene)
                                for x in scenes.values()))
            groups=bind_actor_camera_world(parsed,scenes,[0,70,140,210,280])
            self.assertEqual(len(groups),2)
            a=render_art_stage(scenes[0],8,0,70)
            contact=render_art_stage(scenes[0],35,0,70)
            aftermath=render_art_stage(scenes[0],60,0,70)
            collision=render_art_stage(scenes[2],175,140,210)
            self.assertEqual(a.mode,"RGBA")
            self.assertEqual(a.size,contact.size)
            self.assertNotEqual(a.tobytes(),contact.tobytes())
            self.assertNotEqual(contact.tobytes(),aftermath.tobytes())
            self.assertNotEqual(contact.tobytes(),collision.tobytes())
            self.assertEqual(contact.tobytes(),
                             render_art_stage(scenes[0],35,0,70).tobytes())

    def test_explicit_french_action_and_missing_verb_fallback(self):
        french=compile_original_script(
            topic="Pluie et vagues",language="fr",
            script=("La pluie arrose un arbre et nourrit les feuilles de la forêt.\n\n"
                    "Un arbre pousse près de la pluie, dans un jardin calme.\n\n"
                    "Une vague heurte un train près de la mer et de sa locomotive."))
        self.assertEqual(french["proceduralVisualInteractions"],[
            {"kind":"rain-waters-plant","at":.5},None,
            {"kind":"wave-hits-train","at":.5}])
        self.assertEqual(checked(french)["language"],"fr")
        unrelated=compile_original_script(
            topic="Forest and weather",script=(
                "Rain falls over the forest while a tree grows.\n\n"
                "The tree is tall and a rain cloud passes above the garden."))
        self.assertNotIn("proceduralVisualInteractionEngine",unrelated)
        self.assertIn("proceduralVisualCompositionEngine",unrelated)
        self.assertEqual(len(unrelated["beats"][0].get("actorLinks",[])),0)

    def test_negated_or_unsupported_claims_do_not_cause_false_contacts(self):
        for sample in (
            "Rain does not water the forest tree while leaves are falling.",
            "The ocean wave never hits the train travelling by the railway.",
            "The rain and the tree exist on opposite sides of the garden.",
            "A wave nears a train on the railway but never touches it.",
        ):
            self.assertIsNone(detect_contacts(
                [{"narration":sample},{"narration":sample}],
                composition_families(
                    [{"narration":sample},{"narration":sample}])))

    def test_saved_v19_dual_and_v18_chapter_stories_remain_readable(self):
        plain=compile_original_script(
            topic="Three scenes",script=(
                "A planet travels above a forest tree and its leaves.\n\n"
                "A tree grows while a planet moves across its orbit."))
        self.assertNotIn("proceduralVisualInteractionEngine",plain)
        self.assertEqual(checked(plain)["proceduralVisualCompositionFamilies"],
                         plain["proceduralVisualCompositionFamilies"])
        chapters=compile_original_script(
            topic="Different subjects",script=(
                "A forest tree grows near the garden each day.\n\n"
                "A planet travels around its moon across space."))
        self.assertNotIn("proceduralVisualInteractionEngine",chapters)
        self.assertEqual(checked(chapters)["proceduralVisualFamilies"],
                         ["botanical","celestial"])

    def test_forged_action_or_removed_provenance_fail_closed(self):
        good=self.example()
        tamper=[
            lambda x:x["proceduralVisualInteractions"].__setitem__(1,EVENTS[0]),
            lambda x:x["proceduralVisualInteractions"].__setitem__(0,None),
            lambda x:x.update(proceduralVisualInteractionEngine="fake"),
            lambda x:x.pop("proceduralVisualInteractionEngine"),
            lambda x:x.pop("proceduralVisualInteractions"),
            lambda x:x["beats"][0].__setitem__("actorLinks",[]),
            lambda x:x["beats"][0]["actorLinks"][0].__setitem__("at",.75),
            lambda x:x["beats"][0]["actorTracks"][0]["keys"][2].__setitem__(
                "x",.24),
            lambda x:x["beats"][1]["actorTracks"][2]["keys"][0].__setitem__(
                "scale",.70),
            lambda x:x["beats"][0]["visualVectors"][2]["shapes"][0].__setitem__(
                "fill","#000000"),
            lambda x:x["beats"][0].__setitem__(
                "narration","Rain and a forest tree appear next to a cloud."),
        ]
        for mutate in tamper:
            forged=deepcopy(good)
            mutate(forged)
            with self.subTest(tamper=str(mutate)),self.assertRaises(ValueError):
                checked(forged)
        all_removed=deepcopy(good)
        for field in list(all_removed):
            if field.startswith("procedural"):
                del all_removed[field]
        with self.assertRaisesRegex(ValueError,"provenance"):
            checked(all_removed)

    def test_missing_or_invalid_contact_timeline_rejected(self):
        seq=composition_families([
            {"narration":"Rain waters a tree in the forest."},
            {"narration":"The tree grows while rain falls."},
        ])
        self.assertEqual(seq,[["botanical","weather"],
                              ["botanical","weather"]])
        for bad in ([],[None],None,[{"kind":"unknown","at":.5},None],
                    [{"kind":"rain-waters-plant","at":.9},None]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                contact_tracks_and_links(seq[0],0,2,bad)
        for families in ([],["botanical","weather","ocean"]):
            with self.assertRaises(ValueError):
                contact_layers(families)


if __name__=="__main__":
    unittest.main()
