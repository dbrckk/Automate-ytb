"""Professional review: real QA evidence is interpreted without false aesthetic claims."""
import unittest

from automate_ytb.professional_review import assess


def evidence():
    return {
        "summary": {"status": "passed", "technicalPreviewReady": True},
        "visual": {
            "technicalVisualCheckPassed": True,
            "frames": [
                {"motion": {"changedPixelFraction": .21}, "meanLuminance": 87},
                {"motion": {"changedPixelFraction": .19}, "meanLuminance": 92},
                {"motion": {"changedPixelFraction": .25}, "meanLuminance": 101},
            ],
            "nearDuplicateNeighborCount": 0,
            "suspectedBandedPortraitSceneCount": 0,
            "nearBlackSceneCount": 0,
        },
        "media": {"status": "pass", "integratedLufs": -16.1,
                  "truePeakDbtp": -2.1, "targetLufs": -16},
    }


class ProfessionalReviewTests(unittest.TestCase):
    def test_healthy_encoded_video_still_requires_editorial_approval(self):
        e = evidence()
        r = assess(**e)
        self.assertEqual(r["status"], "editorial-review-required")
        self.assertFalse(r["publicationApproved"])
        self.assertEqual(r["priorities"], [])
        self.assertEqual(r["metrics"]["sampledScenes"], 3)

    def test_prioritizes_audio_and_visual_defects(self):
        e = evidence()
        e["visual"]["frames"][1]["motion"]["changedPixelFraction"] = .001
        e["visual"]["nearDuplicateNeighborCount"] = 1
        e["media"]["truePeakDbtp"] = -.1
        e["pacing"] = {"status": "failed"}
        r = assess(**e)
        p0 = {x["domain"] for x in r["priorities"] if x["priority"] == "P0"}
        self.assertTrue({"audio", "voice", "graphics", "animation"} <= p0)

    def test_invalid_or_unverified_reports_fail_closed(self):
        e = evidence()
        e["summary"]["technicalPreviewReady"] = False
        with self.assertRaises(ValueError):
            assess(**e)
        e = evidence()
        e["visual"]["frames"][0]["motion"]["changedPixelFraction"] = float("nan")
        with self.assertRaises(ValueError):
            assess(**e)

    def test_no_unsupported_premium_score(self):
        e = evidence()
        r = assess(**e)
        self.assertNotIn("professionalScore", r)
        self.assertNotIn("qualityRating", r)
        self.assertTrue(r["humanListeningRequired"])


if __name__ == "__main__":
    unittest.main()
