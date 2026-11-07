"""M2 optical shot review: reproducible real decoded pixels and no semantic claims."""
import unittest

from automate_ytb.shot_diversity import (
    PIXELS, UPPER_PIXELS, _signature, _temporal_pixel_change,
    analyze_frames, compare_signatures,
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

    def test_temporal_audit_flags_frozen_content_and_measures_motion(self):
        still=bytes([90])*PIXELS
        early=bytes([60 if i%96 < 48 else 200 for i in range(PIXELS)])
        middle=bytes([200 if i%96 < 48 else 60 for i in range(PIXELS)])
        result=analyze_frames(
            [still,middle],source_names=["still.mp4","moving.mp4"],
            temporal_frames=[(still,still),(early,early)],
        )
        self.assertTrue(result["temporalMotionAudited"])
        self.assertEqual(result["temporalSamplesPerScene"],3)
        self.assertEqual(result["temporalAuditedSceneCount"],2)
        self.assertEqual(result["nearStaticSceneCount"],1)
        self.assertTrue(result["scenes"][0]["temporalPixelActivity"]["nearStaticOpticalActivity"])
        self.assertFalse(result["scenes"][1]["temporalPixelActivity"]["nearStaticOpticalActivity"])
        self.assertGreater(result["scenes"][1]["temporalPixelActivity"]["meanPixelDelta"],100)
        self.assertTrue(any("near-static" in w for w in result["warnings"]))

    def test_pixel_motion_ignores_bottom_caption_region(self):
        first=bytes([80])*PIXELS
        last=bytearray(first)
        last[UPPER_PIXELS:]=bytes([250])*(PIXELS-UPPER_PIXELS)
        self.assertEqual(_temporal_pixel_change(first,bytes(last)),0)
        with self.assertRaises(ValueError):
            _temporal_pixel_change(bytes(PIXELS-1),first)

    def test_temporal_samples_must_match_scene_count_and_dimensions(self):
        frame=bytes([90])*PIXELS
        with self.assertRaisesRegex(ValueError,"align"):
            analyze_frames(
                [frame,frame],source_names=["a.mp4","b.mp4"],
                temporal_frames=[(frame,frame)],
            )
        with self.assertRaisesRegex(ValueError,"dimensions"):
            analyze_frames(
                [frame,frame],source_names=["a.mp4","b.mp4"],
                temporal_frames=[(frame,bytes(PIXELS-1)),(frame,frame)],
            )

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
