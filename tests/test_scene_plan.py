"""Regression checks for multi-scene original audiovisual planning."""
import unittest

from automate_ytb.scene_plan import plan


class ScenePlanTests(unittest.TestCase):
    def test_150_scenes_15_minutes(self):
        script = " ".join(f"Original narration beat {i} explains a new step." for i in range(150))
        result = plan(topic="Why do eggs have two yolks?", script=script, duration=900,
                      character="An original cheerful orange chick with green boots")
        self.assertEqual(result["sceneCount"], 150)
        self.assertEqual(result["scenes"][-1]["endMs"], 900_000)
        self.assertEqual(result["scenes"][0]["startMs"], 0)
        self.assertTrue(all(not s["assetApproved"] for s in result["scenes"]))
        self.assertFalse(result["publicationApproved"])
        self.assertEqual(len({x["imageAsset"] for x in result["scenes"]}), 150)

    def test_cannot_make_up_script_beats(self):
        with self.assertRaisesRegex(ValueError, "Need 150"):
            plan(topic="Eggs", script="A single statement.", duration=900,
                 character="An original orange chick with green boots")

    def test_merge_keeps_every_word(self):
        script = " ".join(f"Original statement {i} explains a new fact." for i in range(30))
        data = plan(topic="Eggs", script=script, duration=60,
                    character="An original orange chick with green boots")
        self.assertEqual(data["sceneCount"], 10)
        self.assertEqual(" ".join(s["narration"] for s in data["scenes"]), script)

    def test_timing_is_contiguous(self):
        script = " ".join(f"Original statement {i} explains a new detail." for i in range(17))
        data = plan(topic="Eggs", script=script, duration=90,
                    character="An original orange chick with green boots")
        for a,b in zip(data["scenes"], data["scenes"][1:]):
            self.assertEqual(a["endMs"],b["startMs"])


if __name__ == "__main__":
    unittest.main()
