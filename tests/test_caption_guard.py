"""Regression coverage for script-to-caption fidelity in Android previews."""
import unittest

from automate_ytb.caption_guard import audit_caption_text
from automate_ytb.captions import subtitles_for_scenes


class CaptionGuardTests(unittest.TestCase):
    def setUp(self):
        self.scenes = [
            {"startMs": 0, "endMs": 5000,
             "narration": "La chouette explore la forêt. Puis elle rencontre une luciole."},
            {"startMs": 5000, "endMs": 10000,
             "narration": "Elle revient chez elle, heureuse !"},
        ]
        self.captions, _ = subtitles_for_scenes(self.scenes)

    def test_original_multi_cue_script_passes(self):
        result = audit_caption_text(self.captions, self.scenes)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["scenesVerified"], 2)
        self.assertGreater(result["cueCount"], 1)

    def test_subtitles_cannot_silently_change_a_word(self):
        tampered = self.captions.replace("chouette", "renard", 1)
        result = audit_caption_text(tampered, self.scenes)
        self.assertFalse(result["passed"])
        self.assertTrue(any("text differs" in e for e in result["errors"]))

    def test_missing_final_cue_is_rejected(self):
        blocks = self.captions.strip().split("\n\n")
        result = audit_caption_text("\n\n".join(blocks[:-1]), self.scenes)
        self.assertFalse(result["passed"])
        self.assertTrue(result["errors"])

    def test_cue_crossing_scene_boundary_is_rejected(self):
        tampered = self.captions.replace(
            "00:00:05,000", "00:00:05,200", 1)
        result = audit_caption_text(tampered, self.scenes)
        self.assertFalse(result["passed"])
        self.assertTrue(result["errors"])

    def test_unknown_extra_cue_is_rejected(self):
        extra = (self.captions.strip()
                 + "\n\n99\n00:00:10,000 --> 00:00:11,000\nExtra.\n")
        result = audit_caption_text(extra, self.scenes)
        self.assertFalse(result["passed"])

    def test_malformed_timestamp_and_empty_srt_are_rejected(self):
        damaged = self.captions.replace("00:00:00,000", "00:99:00,000", 1)
        self.assertFalse(audit_caption_text(damaged, self.scenes)["passed"])
        self.assertFalse(audit_caption_text("", self.scenes)["passed"])

    def test_valid_utf8_and_whitespace_are_preserved(self):
        scenes = [
            {"startMs": 0, "endMs": 2000,
             "narration": "L'été arrive : « bientôt » !"}
        ]
        srt, _ = subtitles_for_scenes(scenes)
        self.assertTrue(audit_caption_text(srt, scenes)["passed"])


if __name__ == "__main__":
    unittest.main()
