"""Numeric explanatory Shorts: strict source claims and continuous world motion."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_scale_journey import (
    VERSION, derive_scale_journey, eased_progress, render_scale_frame,
    scale_coordinate)
from automate_ytb.universal_kinetic import frame_image, read_story, timeline_for


SOURCE=Path(__file__).resolve().parents[1]/(
    "examples/universal_scale_journey_story.en.txt")


def checked(data):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/"story.json"
        path.write_text(json.dumps(data),encoding="utf8")
        return read_story(path)


class OriginalContinuousScaleTests(unittest.TestCase):
    def story(self):
        return compile_original_script(
            topic="What if a glowing thread kept growing?",
            script=SOURCE.read_text(encoding="utf8"),language="en")

    def test_six_explicit_magnitudes_produce_one_original_world(self):
        story=self.story()
        self.assertEqual(story["proceduralScaleJourneyEngine"],VERSION)
        self.assertIsNone(story["proceduralVisualEngine"])
        self.assertFalse(story["factualResearchPerformed"])
        points=story["proceduralScaleJourney"]["points"]
        self.assertEqual([p["sourceSpan"] for p in points],
                         ["1 mm","1 cm","1 m","100 m","1 km","100 km"])
        self.assertEqual([p["metres"] for p in points],
                         ["0.001","0.01","1","100","1000","100000"])
        self.assertEqual([p["illustration"] for p in points],
                         ["ruler","human","tree","tower","mountain","earth"])
        self.assertTrue(all(not b.get("visualVectors") and
                            not b.get("actorTracks") for b in story["beats"]))
        parsed=checked(story)
        self.assertEqual(parsed["proceduralScaleJourney"],
                         story["proceduralScaleJourney"])
        self.assertEqual(parsed["proceduralScaleJourneyEngine"],VERSION)
        self.assertEqual(len(parsed["beats"]),6)

    def test_source_units_are_physically_comparable_without_hallucinated_facts(self):
        beats=[
            {"title":"one","narration":"The object has a length of 1 mm today."},
            {"title":"two","narration":"It expands to exactly 10 cm now."},
            {"title":"three","narration":"Its length reaches 2 m at the end."},
            {"title":"four","narration":"The length finally reaches 3 km."},
        ]
        chart=derive_scale_journey(beats)
        self.assertEqual([p["metres"] for p in chart["points"]],
                         ["0.001","0.10","2","3000"])
        self.assertEqual(chart["baseUnit"],"m")
        astronomical=[
            {"title":"one","narration":"The first distance is 1 km."},
            {"title":"two","narration":"The second distance is 1 light-year."},
            {"title":"three","narration":"The third distance is 2 light-years."},
        ]
        self.assertEqual([p["metres"] for p in
                          derive_scale_journey(astronomical)["points"]],
                         ["1000","9460730472580800",
                          "18921460945161600"])

    def test_unsupported_or_contradictory_inputs_do_not_invent_sequences(self):
        sample=[
            {"title":"one","narration":"A starting 1 mm length is marked."},
            {"title":"two","narration":"The length grows to 10 cm."},
            {"title":"three","narration":"The length reaches 3 m."},
        ]
        mutations=[
            sample[:2],
            [*sample[:2],{"title":"no fact","narration":"It grows a lot."}],
            [*sample[:2],{"title":"two facts",
                        "narration":"It grows to 2 m and then 3 m."}],
            [*sample[:2],{"title":"wrong order",
                        "narration":"It goes back to 0.1 mm."}],
            [*sample[:2],{"title":"not finite",
                        "narration":"It now measures 9e999 m."}],
            [*sample[:2],{"title":"out of range",
                        "narration":"It grows to 999999999999 km."},
                         {"title":"goes back","narration":"Now it is 2 km."}],
        ]
        for bad in mutations:
            with self.subTest(bad=bad):
                self.assertIsNone(derive_scale_journey(bad))
        legacy=compile_original_script(
            topic="Two independent subjects",
            script=("A forest tree grows next to an orbiting planet.\n\n"
                    "The moon glows while an ocean wave crashes into rocks."))
        self.assertNotIn("proceduralScaleJourneyEngine",legacy)
        self.assertTrue(checked(legacy)["beats"][0]["visualVectors"])

    def test_global_log_positions_never_reset_at_editorial_boundaries(self):
        journey=self.story()["proceduralScaleJourney"]
        values=[scale_coordinate(journey,Decimal(p["metres"]))
                for p in journey["points"]]
        self.assertTrue(all(a < b for a,b in zip(values,values[1:])))
        self.assertGreater(values[0],0)
        self.assertLess(values[-1],1)
        for index in range(1,len(values)):
            self.assertAlmostEqual(eased_progress(journey,index-1,1.0),
                                   eased_progress(journey,index,0.0),
                                   places=12)
        for index in range(len(values)):
            self.assertLessEqual(eased_progress(journey,index,0),
                                 eased_progress(journey,index,.5))
            self.assertLess(eased_progress(journey,index,.5),
                            eased_progress(journey,index,1))
        with self.assertRaises(ValueError):
            eased_progress(journey,len(values),.2)

    def test_real_painted_frames_are_deterministic_and_animated(self):
        story=checked(self.story())
        bounds=[0,45,90,135,180,225,270]
        timeline=timeline_for(story,bounds)
        a=frame_image(story,timeline,bounds,12,360,640)
        b=frame_image(story,timeline,bounds,31,360,640)
        c=frame_image(story,timeline,bounds,52,360,640)
        final=frame_image(story,timeline,bounds,255,360,640)
        self.assertEqual((a.mode,a.size),("RGB",(360,640)))
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertNotEqual(b.tobytes(),c.tobytes())
        self.assertNotEqual(c.tobytes(),final.tobytes())
        self.assertEqual(b.tobytes(),
                         frame_image(story,timeline,bounds,31,360,640).tobytes())
        with self.assertRaises(ValueError):
            render_scale_frame(story["proceduralScaleJourney"],story["topic"],
                               frame=46,boundaries=bounds,position=0,
                               width=360,height=640)

    def test_tampering_scale_values_geometry_or_provenance_is_rejected(self):
        good=self.story()
        attacks=[
            lambda x: x["proceduralScaleJourney"]["points"][0].__setitem__(
                "metres","0.1"),
            lambda x: x["proceduralScaleJourney"]["points"][3].__setitem__(
                "sourceSpan","100 km"),
            lambda x: x["proceduralScaleJourney"]["points"][4].__setitem__(
                "illustration","earth"),
            lambda x: x.update(proceduralScaleJourneyEngine="fake"),
            lambda x: x.pop("proceduralScaleJourneyEngine"),
            lambda x: x.pop("proceduralScaleJourney"),
            lambda x: x.update(proceduralVisualEngine="forged"),
            lambda x: x["beats"][2].__setitem__("narration",
                "The object no longer has an explicitly stated measurement."),
            lambda x: x["beats"][0].__setitem__(
                "visualVectors",[{"fake":"outside storyboard"}]),
        ]
        for attack in attacks:
            forged=deepcopy(good)
            attack(forged)
            with self.subTest(attack=str(attack)),self.assertRaises(ValueError):
                checked(forged)


if __name__=="__main__":
    unittest.main()
