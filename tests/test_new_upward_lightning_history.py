"""Contract for unique upward-lightning film and real GitHub video history."""
import unittest
from pathlib import Path

from automate_ytb.science_lightning import classify, supports_topic
from scripts.update_video_history import catalog_from_releases

ROOT=Path(__file__).resolve().parents[1]


class NewOriginalShortTests(unittest.TestCase):
    def test_five_unique_physical_actions_have_correct_semantic_animations(self):
        topic="Can Lightning Travel Upward From a Tower?"
        self.assertTrue(supports_topic(topic))
        lines=(
            "Inside a storm cloud, collisions separate electric charges and build a powerful voltage.",
            "As the electric field intensifies, a branching leader can descend toward a tall tower.",
            "From the tower tip, upward streamers rise and may connect with the approaching channel.",
            "Once connected, an intense return stroke produces the brilliant lightning flash we see.",
            "The rapid heating of air launches a shock wave that reaches our ears as thunder.",
        )
        self.assertEqual(
            [classify(topic,line) for line in lines],
            ["charge","leader","connection","return","thunder"])

    def test_new_video_workflow_keeps_real_media_quality_and_voice(self):
        wf=(ROOT/".github/workflows/upward-lightning-original-short.yml").read_text()
        self.assertIn("Can Lightning Travel Upward From a Tower?",wf)
        self.assertIn("uses: ./.github/workflows/one-click-preview.yml",wf)
        for expected in ("voice: kokoro","voice_name: af_heart",
                         "resolution: shorts","render_profile: high",
                         "caption_timing: audio","needs: render-and-verify"):
            self.assertIn(expected,wf)

    def test_history_contains_only_actual_uploaded_mp4_releases(self):
        releases=[
            {"tag_name":"science-preview-upward-lightning-12345",
             "published_at":"2026-11-09T12:00:00Z",
             "html_url":"https://github.com/example/repo/releases/tag/abc",
             "assets":[{"name":"upward-lightning.mp4","state":"uploaded",
                        "browser_download_url":"https://github.com/example/repo/releases/download/abc/upward-lightning.mp4",
                        "size":1000000,"digest":"sha256:abc"},
                       {"name":"upward-lightning.srt","state":"uploaded",
                        "browser_download_url":"https://example.org/subtitle"}]},
            {"tag_name":"science-preview-upward-lightning-12345",
             "published_at":"2026-11-09T12:00:00Z","assets":[]},
            {"tag_name":"failed-render","assets":[{"name":"broken.mp4",
                                                  "state":"starter",
                                                  "browser_download_url":"https://example.org/broken"}]},
        ]
        catalog=catalog_from_releases(releases)
        self.assertEqual(catalog["count"],1)
        entry=catalog["videos"][0]
        self.assertEqual(entry["topic"],"upward-lightning")
        self.assertEqual(entry["category"],"science")
        self.assertEqual(entry["sha256"],"sha256:abc")
        self.assertFalse(catalog["publicationApproved"])


if __name__=="__main__":
    unittest.main()
