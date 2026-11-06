"""M2 optical shot review: reproducible real decoded pixels and no semantic claims."""
import unittest

from automate_ytb.shot_diversity import (
    PIXELS, _signature, analyze_frames, compare_signatures,
)


class DiversityTests(unittest.TestCase):
    def test_near_duplicate_adjacent_shots_flagged(self):
        frames=[bytes([100])*PIXELS,bytes([100])*PIXELS,bytes([215])*PIXELS]
        result=analyze_frames(frames,source_names=["a.mp4","a.mp4","b.mp4"])
        self.assertEqual(result["sceneCount"],3)
        self.assertEqual(result["distinctSourceFiles"],2)
        self.assertEqual(result["adjacentNearDuplicateCount"],1)
        self.assertEqual(result["adjacentSourceChangeCount"],1)
        self.assertFalse(result["semanticMatchingPerformed"])
        self.assertFalse(result["publicationApproved"])
        self.assertTrue(result["editorialReviewRequired"])

    def test_spatial_change_detected_even_with_same_global_mean(self):
        first=bytes([60 if x%96<48 else 200 for x in range(PIXELS)])
        second=bytes([200 if x%96<48 else 60 for x in range(PIXELS)])
        a,b=_signature(first),_signature(second)
        self.assertAlmostEqual(a["meanLuminance"],b["meanLuminance"])
        self.assertFalse(compare_signatures(a,b)["nearDuplicateOpticalComposition"])

    def test_rejects_misaligned_sources_and_bad_frame_dimensions(self):
        with self.assertRaises(ValueError):
            analyze_frames([bytes(PIXELS)]*2,source_names=["one"])
        with self.assertRaises(ValueError):
            analyze_frames([bytes(PIXELS)],source_names=["one"])
        with self.assertRaises(ValueError):
            _signature(bytes(PIXELS-1))

    def test_near_black_scene_warns_instead_of_claiming_semantic_failure(self):
        result=analyze_frames(
            [bytes([0])*PIXELS,bytes([80])*PIXELS],
            source_names=["sourceA","sourceB"],
        )
        self.assertTrue(any("near-black" in w for w in result["warnings"]))
        self.assertIn("No speech-to-image semantic alignment is inferred.",
                      result["limitations"])


if __name__=="__main__":
    unittest.main()
