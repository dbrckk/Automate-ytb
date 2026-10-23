"""Actual 9:16 FFmpeg render, audio preservation and subtitle clipping."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.shorts import clip_srt, export_short, probe


class ShortsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_subtitle_retiming_preserves_text_and_intervals(self):
        captions = self.root / "original.srt"
        captions.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nUn premier exemple.\n\n"
            "2\n00:00:02,000 --> 00:00:05,000\nUne seconde phrase.\n\n"
            "3\n00:00:05,000 --> 00:00:08,000\nLa dernière phrase.\n",
            encoding="utf-8")
        output = self.root / "vertical.srt"
        count = clip_srt(captions, output, start_ms=3000, end_ms=6500)
        self.assertEqual(count, 2)
        result = output.read_text(encoding="utf-8")
        self.assertIn("00:00:00,000 --> 00:00:02,000", result)
        self.assertIn("00:00:02,000 --> 00:00:03,500", result)
        self.assertNotIn("premier", result)
        self.assertIn("dernière phrase", result)

    def test_rejects_malformed_subtitle(self):
        source = self.root / "bad.srt"
        source.write_text("1\ninvalid --> 00:00:03,000\nX\n")
        with self.assertRaisesRegex(ValueError, "timestamp"):
            clip_srt(source, self.root / "out.srt", start_ms=0, end_ms=1000)

    def test_missing_source_fails_early(self):
        with self.assertRaises(FileNotFoundError):
            export_short(video=self.root / "missing.mp4",
                         output=self.root / "out")
        with self.assertRaisesRegex(ValueError, "vertical resolution"):
            export_short(video=self.root / "missing.mp4",
                         output=self.root / "out", width=1024)
        with self.assertRaisesRegex(ValueError, "start/seconds"):
            export_short(video=self.root / "missing.mp4",
                         output=self.root / "out", start=-1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Needs FFmpeg/ffprobe for actual video")
    def test_video_with_audio_has_vertical_dimensions_and_preserved_audio(self):
        source = self.root / "sample.mp4"
        subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", "-c:a", "aac", source
        ], check=True, capture_output=True)
        subtitle = self.root / "captions.srt"
        subtitle.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nBonjour.\n\n"
            "2\n00:00:02,000 --> 00:00:03,000\nFin.\n",
            encoding="utf-8")
        record = export_short(video=source, output=self.root / "short",
                              captions=subtitle, start=1, seconds=1.5)
        self.assertTrue(Path(record["video"]).exists())
        self.assertEqual(record["aspectRatio"], "9:16")
        self.assertTrue(record["audioPresent"])
        self.assertFalse(record["publicationApproved"])
        self.assertEqual(record["captionBlocks"], 2)
        info = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height:format=duration",
            "-of", "json", record["video"]],
            capture_output=True, text=True, check=True)
        data = json.loads(info.stdout)
        video = next(x for x in data["streams"] if x["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"]), (720, 1280))
        self.assertIn("audio", {x["codec_type"] for x in data["streams"]})
        self.assertAlmostEqual(float(data["format"]["duration"]), 1.5, delta=.3)
        self.assertTrue((self.root / "short" / "short-report.json").exists())


if __name__ == "__main__":
    unittest.main()
