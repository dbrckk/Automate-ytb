"""Cross-topic and cross-language safety tests for the plain-script entry point."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_kinetic import read_story, timeline_for, frame_image


class UniversalScriptTests(unittest.TestCase):
    def test_unrelated_topics_share_one_visual_engine(self):
        stories = [
            ("History of a railway",
             "A railway connects towns and industrial districts. Trains change how goods and travelers move.\n\n"
             "First workers survey the route; then engineers prepare a rail bed; finally the service opens.",
             "en"),
            ("La vie d'une forêt",
             "Les arbres absorbent de la lumière et grandissent au fil des saisons.\n\n"
             "D'abord une graine germe; puis des feuilles apparaissent; enfin les racines se développent.",
             "fr"),
            ("How computer security checks work",
             "A login service checks a password and a second factor. This process can protect an account.\n\n"
             "First a client requests access; then the service validates credentials; finally access can be granted.",
             "en"),
            ("An original recipe",
             "A fresh recipe starts with careful preparation of ingredients. Heat gradually changes the texture.\n\n"
             "First wash the vegetables; then warm the pan; finally combine the cooked ingredients.",
             "en"),
        ]
        for topic, script, language in stories:
            with self.subTest(topic=topic):
                compiled=compile_original_script(topic=topic,script=script,
                                                 language=language)
                with tempfile.TemporaryDirectory() as td:
                    source=Path(td)/"story.json"
                    source.write_text(json.dumps(compiled),encoding="utf8")
                    data=read_story(source)
                self.assertEqual(data["language"],language)
                self.assertGreaterEqual(len(data["beats"]),2)
                self.assertTrue(all(b["kind"] in ("concept","sequence")
                                    for b in data["beats"]))
                self.assertTrue(all(not b["sources"] for b in data["beats"]))
                boundaries=[i*60 for i in range(len(data["beats"])+1)]
                track=timeline_for(data,boundaries)
                frame=frame_image(data,track,boundaries,30,360,640)
                self.assertEqual(frame.size,(360,640))

    def test_every_visual_label_is_derived_from_original_text(self):
        story=compile_original_script(
            topic="Digital transactions",
            script="A client asks a service for information about the transaction.\n\n"
                   "First check the ledger; then verify the value; finally report the result.",
            language="en")
        available=(story["topic"]+" "+
                   " ".join(b["narration"] for b in story["beats"])).casefold()
        for beat in story["beats"]:
            labels=beat.get("nodes",beat.get("steps",[]))
            for label in labels:
                self.assertIn(label.casefold(),available)
        self.assertFalse(story["factualResearchPerformed"])
        self.assertTrue(story["originalTextOnly"])
        self.assertTrue(all("value" not in b and "leftValue" not in b
                            for b in story["beats"]))

    def test_one_paragraph_splits_into_real_sentences(self):
        data=compile_original_script(
            topic="Why weather changes",
            script="The air becomes warmer as the sun rises. Clouds form over the hills. Wind carries moisture to the coast.",
            language="en")
        self.assertEqual(len(data["beats"]),3)
        self.assertTrue(data["beats"][1]["narration"].startswith("Clouds"))

    def test_invalid_input_does_not_fabricate_beats(self):
        for script in ("Hello.", "One short original sentence only.",
                       "Something unsafe.\x00Second sentence."):
            with self.subTest(script=script), self.assertRaises(ValueError):
                compile_original_script(topic="Any subject",script=script)
        with self.assertRaises(ValueError):
            compile_original_script(topic="Any subject",
                                    script="Some original narrative. Another complete sentence.",
                                    language="xx")


if __name__=="__main__":
    unittest.main()
