"""Check real spoken-phrase subtitle timing and decoded mobile ASS burn-in."""
from __future__ import annotations

import copy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.short_captions import (
    caption_fragments, export_caption_assets, verify_measured_beats,
)


def two_beats():
    return [
        {"index": 1, "text": "The ocean is alive. It moves.",
         "startMs": 180, "endMs": 2900,
         "captionSegments": [
             {"text": "The ocean is alive.", "startMs": 180, "endMs": 1550},
             {"text": "It moves.", "startMs": 1620, "endMs": 2900},
         ]},
        {"index": 2,
         "text": "A jellyfish carries its own light. A signal in the dark.",
         "startMs": 3150, "endMs": 7750,
         "captionSegments": [
             {"text": "A jellyfish carries its own light.",
              "startMs": 3150, "endMs": 5180},
             {"text": "A signal in the dark.",
              "startMs": 5240, "endMs": 7750},
         ]},
    ]


class NaturalShortCaptionTests(unittest.TestCase):
    def test_preserves_real_documentary_script_and_readability(self):
        script = (Path(__file__).resolve().parents[1] /
                  "examples/deep-ocean-jellyfish-short.en.txt")
        beats = [line.strip() for line in script.read_text(
            encoding="utf8").splitlines() if line.strip()]
        self.assertEqual(len(beats), 4)
        all_parts = [caption_fragments(line) for line in beats]
        self.assertGreaterEqual(sum(map(len, all_parts)), 7)
        for full, parts in zip(beats, all_parts):
            self.assertEqual(" ".join(parts), " ".join(full.split()))
            self.assertTrue(all(len(part) <= 44 for part in parts))
            self.assertTrue(all(len(part.split()) <= 8 for part in parts))

    def test_refuses_unsupported_ass_markup_and_long_words(self):
        for value in ["hello {\\move(0,0,900,900)} world",
                      "hello \\N world", "x" * 52, "  "]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    caption_fragments(value)

    def test_rejects_tampered_transcripts_and_overlapping_cues(self):
        original = two_beats()
        self.assertEqual(len(verify_measured_beats(
            original, duration_ms=8000)), 4)
        changed = copy.deepcopy(original)
        changed[1]["captionSegments"][1]["text"] = "A different sentence."
        with self.assertRaises(ValueError):
            verify_measured_beats(changed, duration_ms=8000)
        bad_start = copy.deepcopy(original)
        bad_start[1]["captionSegments"][0]["startMs"] = 1400
        with self.assertRaises(ValueError):
            verify_measured_beats(bad_start, duration_ms=8000)
        crossed = copy.deepcopy(original)
        crossed[0]["captionSegments"][1]["endMs"] = 3300
        with self.assertRaises(ValueError):
            verify_measured_beats(crossed, duration_ms=8000)
        with self.assertRaises(ValueError):
            verify_measured_beats(original, duration_ms=7000)

    def test_writes_srt_and_shot_local_ass(self):
        with tempfile.TemporaryDirectory(prefix="caption-assets-") as td:
            assets = export_caption_assets(two_beats(), duration_ms=8000,
                                           directory=Path(td))
            self.assertEqual(assets["captionCount"], 4)
            self.assertFalse(assets["wordLevelAligned"])
            self.assertEqual(len(assets["assPaths"]), 2)
            srt = Path(assets["srtPath"]).read_text(encoding="utf8")
            self.assertIn("00:00:00,180 --> 00:00:01,550", srt)
            self.assertIn("A signal in the dark.", srt)
            first = Path(assets["assPaths"][0]).read_text(encoding="utf8")
            second = Path(assets["assPaths"][1]).read_text(encoding="utf8")
            self.assertIn(r"{\fad(85,100)}The ocean is alive.", first)
            self.assertIn("0:00:00.00", second)  # second scene local start
            self.assertNotIn("The ocean is alive.", second)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg is required for burn-in integration")
    def test_real_h264_video_contains_spoken_caption_overlay(self):
        with tempfile.TemporaryDirectory(prefix="caption-render-") as td:
            work = Path(td)
            assets = export_caption_assets(two_beats(), duration_ms=8000,
                                           directory=work)
            ass_name = Path(assets["assPaths"][0]).name
            render = work / "burned-captions.mp4"
            result = subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y",
                "-f", "lavfi", "-i",
                "color=c=black:s=270x480:r=12:d=3",
                "-vf", f"ass=filename={ass_name},format=yuv420p",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-crf", "24", "-an", str(render),
            ], cwd=work, capture_output=True, timeout=90)
            self.assertEqual(result.returncode, 0,
                             result.stderr.decode("utf8", "replace")[-800:])
            def frame(at):
                raw = subprocess.run([
                    "ffmpeg", "-nostdin", "-v", "error",
                    "-ss", str(at), "-i", str(render),
                    "-frames:v", "1", "-f", "rawvideo",
                    "-pix_fmt", "gray", "pipe:1",
                ], capture_output=True, timeout=30, check=True).stdout
                self.assertEqual(len(raw), 270 * 480)
                return raw
            before = frame(0.0)
            during = frame(0.9)
            self.assertLess(max(before), 24)
            self.assertGreater(max(during), 100)
            self.assertGreater(
                sum(p > 60 for p in during),
                sum(p > 60 for p in before) + 60,
            )
            subprocess.run([
                "ffmpeg", "-nostdin", "-v", "error", "-i", str(render),
                "-f", "null", "-",
            ], check=True, timeout=60)


if __name__ == "__main__":
    unittest.main()
