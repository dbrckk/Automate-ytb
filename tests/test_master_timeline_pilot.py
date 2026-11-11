"""A true audiovisual cross-scene continuity proof, not a mocked demo."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/render_master_timeline_pilot.py"
spec = importlib.util.spec_from_file_location("render_master_timeline_pilot", SOURCE)
assert spec is not None and spec.loader is not None
PILOT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PILOT)


class TimelinePilotTests(unittest.TestCase):
    def test_physical_value_is_persistent_when_editorial_chapter_changes(self):
        t = PILOT.build_timeline()
        self.assertEqual([x.id for x in t.beats], ["growth", "follow", "reveal"])
        self.assertEqual(t.state_at(59)["beatId"], "growth")
        self.assertEqual(t.state_at(60)["beatId"], "follow")
        self.assertEqual(t.state_at(119)["beatId"], "follow")
        self.assertEqual(t.state_at(120)["beatId"], "reveal")
        for boundary in (60, 120):
            left = t.state_at(boundary-1)
            right = t.state_at(boundary)
            for name in ("signal", "camera"):
                for key in left["objects"][name]:
                    self.assertLess(abs(right["objects"][name][key] -
                                        left["objects"][name][key]), 2,
                                    msg=f"{boundary}:{name}:{key}")
        self.assertEqual(t.state_at(179)["objects"]["signal"]["value"] , 64)

    def test_actual_timeline_event_anchors_are_sample_aligned(self):
        t = PILOT.build_timeline()
        cues = t.audio_events()
        self.assertEqual(len(cues), 4)
        self.assertEqual([cue["atFrame"] for cue in cues],
                         [16, 63, 96, 135])
        for cue in cues:
            self.assertEqual(cue["atSample"], cue["atFrame"] * 1600)
            self.assertGreaterEqual(cue["atSample"], 0)
            self.assertLess(cue["atSample"], 6 * 48000)

    def test_render_rejects_wrong_portrait_format_before_encoding(self):
        with tempfile.TemporaryDirectory() as root:
            for width, height in ((360, 480), (361, 640), (1081, 1920)):
                with self.subTest(width=width), self.assertRaises(ValueError):
                    PILOT.produce(Path(root) / "invalid.mp4", width=width, height=height)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg/H264/AAC required")
    def test_encoded_real_h264_aac_with_nonresetting_visual_state(self):
        with tempfile.TemporaryDirectory(prefix="original-master-timeline-test-") as root:
            output = Path(root) / "original-six-second-pilot.mp4"
            report = PILOT.produce(output, width=288, height=512)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 15_000)
            self.assertEqual(report["frames"], 180)
            self.assertTrue(report["technicalPilotOnly"])
            self.assertFalse(report["publicationApproved"])
            self.assertFalse(report["narrationIncluded"])
            self.assertEqual(report["audio"]["cueCount"], 4)
            self.assertEqual(report["audio"]["audioSampleRateHz"], 48000)
            self.assertTrue(output.with_suffix(".json").exists())
            metadata = json.loads(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration:stream=codec_type,codec_name,width,height,sample_rate",
                 "-of", "json", str(output)], capture_output=True, check=True,
                timeout=25, text=True).stdout)
            self.assertAlmostEqual(float(metadata["format"]["duration"]), 6., delta=.15)
            video = [x for x in metadata["streams"] if x["codec_type"] == "video"]
            audio = [x for x in metadata["streams"] if x["codec_type"] == "audio"]
            self.assertEqual((video[0]["codec_name"], video[0]["width"],
                              video[0]["height"]), ("h264", 288, 512))
            self.assertEqual(audio[0]["codec_name"], "aac")
            self.assertEqual(audio[0]["sample_rate"], "48000")
            def frame_rgb(position: str) -> bytes:
                return subprocess.run([
                    "ffmpeg", "-nostdin", "-v", "error", "-ss", position,
                    "-i", str(output), "-frames:v", "1", "-f", "rawvideo",
                    "-pix_fmt", "rgb24", "-"], check=True, capture_output=True,
                    timeout=25).stdout
            first, middle, ending = (frame_rgb(i) for i in ("0.4", "2.8", "5.5"))
            self.assertEqual(len(first), 288*512*3)
            self.assertNotEqual(first, middle)
            self.assertNotEqual(middle, ending)
            samples = subprocess.run([
                "ffmpeg", "-nostdin", "-v", "error", "-i", str(output),
                "-map", "0:a:0", "-ar", "48000", "-ac", "1",
                "-f", "s16le", "-"], check=True, capture_output=True,
                timeout=25).stdout
            self.assertGreater(len(samples), 200000)
            def peak(start_frame: int, end_frame: int) -> int:
                data = samples[start_frame*2:end_frame*2]
                return max(abs(x[0]) for x in struct.iter_unpack("<h", data))
            # Audio is silent before the first event; onset after frame 16.
            self.assertLess(peak(0, 8000), 16)
            self.assertGreater(peak(28000, 41000), 100)
            self.assertGreater(peak(156000, 166000), 100)


if __name__ == "__main__":
    unittest.main()
