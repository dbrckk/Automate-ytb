"""High-quality FFmpeg export is selectable and verifiable from real encoded bytes."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.encoding_profiles import (
    PROFILES, VERSION, settings, video_args, audio_bitrate)
from automate_ytb.episode import build_preview
from automate_ytb.quality import check
from automate_ytb.scene_plan import plan


class VideoExportProfileTests(unittest.TestCase):
    def test_profiles_are_fixed_safe_and_separate(self):
        self.assertEqual(set(PROFILES), {"preview", "high"})
        self.assertIn("v1", VERSION)
        self.assertEqual(settings("high")["crf"], 18)
        self.assertEqual(settings("high")["preset"], "medium")
        self.assertEqual(audio_bitrate("high"), "256k")
        self.assertEqual(audio_bitrate("preview", music_only=True), "160k")
        self.assertEqual(video_args("high"), [
            "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p"])
        self.assertIn("20", video_args("preview", still=True))
        for invalid in ("high;movie=/secret", "lossless", "", None, True):
            with self.assertRaises(ValueError):
                video_args(invalid)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg encode and probe required")
    def test_high_profile_encodes_real_thirty_fps_video_and_quality_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/"plan.json"
            data = plan(topic="Histoire originale haute qualité",
                        script=" ".join([
                            "La lune éclaire le paysage.",
                            "Un voyageur arrive devant la maison.",
                            "Il observe une lumière lointaine.",
                            "Le ciel devient progressivement bleu.",
                            "Son aventure commence enfin.",
                        ]),
                        character="Original scenic narrator",
                        duration=30, shot_seconds=6)
            source.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
            output = root/"out"
            rendered = build_preview(
                plan_path=source, output=output, limit=1,
                style="documentary", voice="none", soundtrack="none",
                render_profile="high", resolution="720p", transition="cut")
            report = rendered["render"]
            self.assertEqual(report["fps"], 30)
            self.assertEqual(report["renderProfile"], "high")
            self.assertEqual(report["videoEncodingPreset"], "medium")
            self.assertEqual(report["videoEncodingCrf"], 18)
            self.assertEqual(rendered["renderProfile"], "high")
            inspected = check(plan=source,output=output,
                              expected_voice="none",expected_soundtrack="none",
                              expected_render_profile="high",decode_frames=False)
            self.assertEqual(inspected["status"], "passed", inspected["errors"])
            wrong = check(plan=source,output=output,
                          expected_voice="none",expected_soundtrack="none",
                          expected_render_profile="preview",decode_frames=False)
            self.assertEqual(wrong["status"], "failed")
            self.assertTrue(any("profile" in e.lower()
                                for e in wrong["errors"]))
            probe = subprocess.run([
                "ffprobe","-v","error","-select_streams","v:0",
                "-show_entries","stream=codec_name,r_frame_rate,width,height",
                "-of","json",str(output/"preview.mp4")],
                capture_output=True, text=True, timeout=60, check=True)
            video = json.loads(probe.stdout)["streams"][0]
            self.assertEqual(video["r_frame_rate"],"30/1")
            self.assertEqual(video["codec_name"],"h264")
            self.assertEqual((video["width"],video["height"]),(1280,720))
            self.assertFalse(rendered["publicationApproved"])


if __name__ == "__main__":
    unittest.main()
