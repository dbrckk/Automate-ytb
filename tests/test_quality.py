"""Regression checks for free Android workflow, exported media and soundtrack selection."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.episode import build_preview, main as episode_main
from automate_ytb.production import _write_json
from automate_ytb.quality import check, CUE, _verify_caption_timeline
from automate_ytb.scene_plan import plan
from automate_ytb.captions import subtitles_for_scenes, srt_time


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan_file = self.root / "scene-plan.json"
        data = plan(
            topic="Une chouette découvre une lumière originale",
            script="La chouette s'envole dans le jardin. "
                   "Elle découvre les étoiles. "
                   "La pluie arrive sur les plantes. "
                   "Elle visite la grande forêt. "
                   "Le soleil finit par apparaître.",
            duration=30, shot_seconds=6,
            character="Une petite chouette violette originale",
        )
        _write_json(self.plan_file, data)

    def tearDown(self):
        self.temp.cleanup()

    def test_quality_gate_detects_shifted_but_monotonic_caption_cues(self):
        scene = {
            "narration": (
                "The ocean waves begin to rise above the distant shoreline. "
                "The atmosphere pushes another current over the mountains. "
                "The planet continues to rotate while daylight changes."),
            "startMs": 0, "endMs": 12000,
        }
        srt, report = subtitles_for_scenes([scene])
        self.assertGreaterEqual(report["cueCount"], 3)
        original = list(CUE.finditer(srt))
        self.assertEqual(
            _verify_caption_timeline(
                original, [scene], "estimated-proportional-phrases"), [])
        # Shift BOTH sides of an internal boundary; SRT remains strictly
        # increasing and covers all twelve seconds, but the phrase no longer
        # starts when its approved timeline says it should.
        boundary = original[0]["b"]
        changed = srt.replace(boundary, srt_time(
            (int(boundary[:2])*3600+int(boundary[3:5])*60+
             int(boundary[6:8]))*1000+int(boundary[9:])+113))
        forged = list(CUE.finditer(changed))
        self.assertEqual(len(forged), len(original))
        self.assertLess(
            int(forged[0]["b"][-3:]), 1000)
        self.assertEqual(forged[0]["b"], forged[1]["a"])
        self.assertTrue(any(
            "Subtitle timeline differs" in msg
            for msg in _verify_caption_timeline(
                forged, [scene], "estimated-proportional-phrases")))

    def test_exact_audio_phrase_boundary_check_rejects_tampered_markers(self):
        scene = {
            "narration": "The Earth turns. The ocean moves.",
            "startMs": 2000, "endMs": 7000,
        }
        from automate_ytb.captions import caption_phrases
        phrases = caption_phrases(scene["narration"])
        self.assertGreaterEqual(len(phrases), 2)
        boundary = 4500
        scene["captionSegments"] = [
            {"text": phrases[0], "startMs": 2000, "endMs": boundary},
            {"text": phrases[1], "startMs": boundary, "endMs": 7000},
        ]
        srt, report = subtitles_for_scenes(
            [scene], use_audio_boundaries=True)
        self.assertEqual(
            _verify_caption_timeline(
                list(CUE.finditer(srt)), [scene], report["method"]), [])
        self.assertTrue(_verify_caption_timeline(
            list(CUE.finditer(srt)), [scene],
            "estimated-proportional-phrases"))
        broken = dict(scene)
        broken["captionSegments"] = [dict(c) for c in scene["captionSegments"]]
        broken["captionSegments"][0]["endMs"] += 42
        self.assertTrue(_verify_caption_timeline(
            list(CUE.finditer(srt)), [broken], report["method"]))
        self.assertTrue(_verify_caption_timeline(
            list(CUE.finditer(srt)), [scene], None))

    def test_cli_actually_forwards_music_choice_to_preview(self):
        stub = {
            "render": {"video": "fake-preview.mp4", "scenesRendered": 1},
            "voice": {"engine": "none"},
        }
        with patch("automate_ytb.episode.build_preview", return_value=stub) as called:
            rc = episode_main([
                "--plan", str(self.plan_file),
                "--output", str(self.root / "clip"),
                "--voice", "none",
                "--soundtrack", "ambient",
            ])
        self.assertEqual(rc, 0)
        self.assertEqual(called.call_args.kwargs["soundtrack"], "ambient")
        self.assertEqual(called.call_args.kwargs["voice"], "none")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg required to inspect exported MP4")
    def test_actual_video_music_caption_and_quality_report(self):
        folder = self.root / "render"
        rendered = build_preview(plan_path=self.plan_file, output=folder,
                                 style="documentary", voice="none",
                                 soundtrack="ambient", limit=1)
        self.assertTrue(rendered["render"]["hasBackgroundMusic"])
        report_path = folder / "quality-report.json"
        checked = check(plan=self.plan_file, output=folder,
                        expected_voice="none", expected_soundtrack="ambient",
                        report_path=report_path)
        self.assertEqual(checked["status"], "passed", checked["errors"])
        self.assertEqual(checked["checks"]["streams"].count("audio"), 1)
        self.assertEqual(checked["checks"]["sampledFramesDecoded"], 2)
        self.assertTrue(checked["checks"]["subtitleTimelineMatchesPlan"])
        self.assertTrue(report_path.is_file())
        self.assertFalse(json.loads(report_path.read_text())["publicationApproved"])

        # A UI selection is a contract; an unexpectedly silent or unmixed output
        # must fail the quality gate instead of being marked ready.
        mismatch = check(plan=self.plan_file, output=folder,
                         expected_voice="none", expected_soundtrack="none",
                         decode_frames=False)
        self.assertEqual(mismatch["status"], "failed")
        self.assertTrue(any("soundtrack" in m.lower() for m in mismatch["errors"]))

        srt = folder / "draft-captions.srt"
        srt.write_text(srt.read_text().replace("00:00:06,000", "00:00:09,000"))
        bad_subtitles = check(plan=self.plan_file, output=folder,
                              expected_voice="none", expected_soundtrack="ambient",
                              decode_frames=False)
        self.assertEqual(bad_subtitles["status"], "failed")
        self.assertTrue(any("subtitle" in m.lower() for m in bad_subtitles["errors"]))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "FFmpeg and eSpeak needed for a real narrated video")
    def test_narration_and_original_music_are_both_present(self):
        folder = self.root / "spoken"
        build_preview(plan_path=self.plan_file, output=folder,
                      style="documentary", voice="espeak",
                      soundtrack="ambient", limit=1)
        result = check(plan=self.plan_file, output=folder,
                       expected_voice="espeak", expected_soundtrack="ambient")
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["checks"]["streams"], ["video", "audio"])
        self.assertIn("approximate", " ".join(result["warnings"]).lower())


if __name__ == "__main__":
    unittest.main()
