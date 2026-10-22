"""Offline smoke contracts for honest exports, plans and content boundaries."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from automate_ytb.studio import (
    build, draft_scenes, distribute_duration, load_brief, slugify,
    video_id_from_reference, _srt_seconds,
)
from automate_ytb.youtube import discover_niches


class ProductionTests(unittest.TestCase):
    def test_reference_urls(self):
        self.assertEqual(video_id_from_reference(
            "https://www.youtube.com/watch?v=ABCDEFGHIjk"), "ABCDEFGHIjk")
        self.assertEqual(video_id_from_reference(
            "https://youtu.be/ABCDEFGHIjk"), "ABCDEFGHIjk")
        self.assertIsNone(video_id_from_reference(""))
        with self.assertRaises(ValueError):
            video_id_from_reference("http://youtu.be/ABCDEFGHIjk")
        with self.assertRaises(ValueError):
            video_id_from_reference("https://example.com/v/ABCDEFGHIjk")

    def test_script_has_no_competitor_reuse(self):
        brief = {"topic": "Apprendre le ciel", "angle": "Explication", "facts": []}
        scene = draft_scenes(brief)
        self.assertEqual(len(scene), 4)
        self.assertTrue(all(x["evidenceUrls"] == [] for x in scene))
        self.assertNotIn("100,000", " ".join(x["narration"] for x in scene))
        own = draft_scenes(brief, "Mon introduction.\n\nMon chapitre.\n\nConclusion.")
        self.assertEqual(len(own), 3)

    def test_duration(self):
        scenes = [{"narration": "one two"}, {"narration": "three four five"}]
        ds = distribute_duration(scenes, 60)
        self.assertEqual(round(sum(ds)), 60)
        self.assertTrue(all(x > 3 for x in ds))
        self.assertEqual(_srt_seconds(63.415), "00:01:03,415")

    def test_safety_rejects_untrusted_sources(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "brief.json"
            p.write_text(json.dumps({"facts": [
                {"claim": "A very plausible fact.", "source": "http://127.0.0.1/evil"}
            ]}), encoding="utf8")
            with self.assertRaises(ValueError):
                load_brief(p, "A topic", "")
            p.write_text(json.dumps({"facts": [
                {"claim": "A very plausible fact.", "source": "https://example.org/good"}
            ]}), encoding="utf8")
            self.assertEqual(len(load_brief(p, "A topic", "")["facts"]), 1)

    def test_plan_full_assets_and_metadata(self):
        with TemporaryDirectory() as td:
            result = build(
                "Comment apprendre l'astronomie ?", Path(td),
                reference="https://youtu.be/ABCDEFGHIjk",
                plan_only=True, duration=65, tts="off"
            )
            root, m = Path(result["folder"]), result["manifest"]
            self.assertTrue((root / "storyboard" / "scene-01.png").is_file())
            self.assertTrue((root / "thumbnails" / "thumbnail-3.png").is_file())
            self.assertTrue((root / "captions.srt").is_file())
            self.assertEqual(len(m["thumbnails"]), 3)
            self.assertEqual(round(m["plannedDurationSeconds"]), 65)
            self.assertTrue(m["manualReviewRequired"])
            self.assertFalse(m["youtubeUploaded"])
            self.assertFalse(m["reference"]["originalMediaDownloaded"])
            self.assertEqual(m["reference"]["youtubeVideoId"], "ABCDEFGHIjk")
            self.assertFalse((root / "video-draft.mp4").exists())
            yt = json.loads((root / "youtube-metadata.json").read_text())
            self.assertTrue(yt["manualPublishRequired"])
            self.assertEqual(yt["visibilityRecommended"], "private")

    def test_research_requires_key_and_no_revenue_claims(self):
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": ""}):
            with self.assertRaises(ValueError):
                discover_niches(["cartoon stories"])
        responses = iter([
            [{"id": {"videoId": "ABCDEFGHIjk"}}],
            [{"id": "ABCDEFGHIjk", "snippet": {
                "channelId": "channel123", "title": "A video",
                "publishedAt": "2026-10-20T09:00:00Z"},
                "statistics": {"viewCount": "500000"}}],
            [{"id": "channel123", "snippet": {"title": "Example channel"},
              "statistics": {"subscriberCount": "15000"}}],
        ])
        with patch("automate_ytb.youtube._get", side_effect=lambda *a, **k: next(responses)):
            data = discover_niches(["cartoon stories"], api_key="fake", min_views=100)
        self.assertEqual(len(data["results"]), 1)
        self.assertIsNone(data["results"][0]["revenueEstimate"])
        self.assertFalse(data["revenueVerified"])


if __name__ == "__main__":
    unittest.main()
