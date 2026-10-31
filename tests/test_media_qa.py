"""Technical QA for an actual rendered MP4 and portable WebVTT subtitles."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

from automate_ytb.media_qa import generate_vtt, assess
from automate_ytb.scene_plan import plan
from automate_ytb.episode import build_preview


class MediaQualityTests(unittest.TestCase):
    def test_webvtt_validates_and_converts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            srt=root/"draft.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:03,000\nBonjour.\n\n"
                           "2\n00:00:03,000 --> 00:00:05,250\nAu revoir.\n",encoding="utf8")
            result=generate_vtt(srt,root/"out.vtt",max_duration_ms=5250)
            self.assertEqual(result["cues"],2)
            self.assertEqual(result["lastCueMs"],5250)
            self.assertIn("WEBVTT\n", (root/"out.vtt").read_text())
            self.assertIn("00:00:03.000 --> 00:00:05.250", (root/"out.vtt").read_text())
            with self.assertRaisesRegex(ValueError,"duration"):
                generate_vtt(srt,root/"wrong.vtt",max_duration_ms=1000)

    def test_overlap_and_empty_cue_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bad.srt"
            p.write_text("1\n00:00:00,000 --> 00:00:03,000\nOK\n\n"
                         "2\n00:00:02,000 --> 00:00:04,000\nOverlap\n")
            with self.assertRaisesRegex(ValueError,"Overlapping"):
                generate_vtt(p,Path(tmp)/"out.vtt")
            p.write_text("1\n00:00:00,000 --> 00:00:00,000\nInvalid\n")
            with self.assertRaises(ValueError):
                generate_vtt(p,Path(tmp)/"out.vtt")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe required")
    def test_actual_native_1080x1920_h264_short_has_no_false_ratio_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "portrait.mp4"
            subprocess.run(
                ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                 "-y", "-f", "lavfi",
                 "-i", "color=c=navy:s=1080x1920:r=2:d=0.5",
                 "-frames:v", "1", "-an", "-c:v", "libx264",
                 "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(video)],
                check=True, capture_output=True, text=True, timeout=30)
            report = assess(video=video)
            self.assertEqual((report["media"]["width"], report["media"]["height"]),
                             (1080, 1920))
            self.assertEqual(report["status"], "pass", report["warnings"])
            self.assertEqual(report["warnings"], [])
            self.assertFalse(report["publicationApproved"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg required")
    def test_real_render_passes_mp4_qa_and_exports_webvtt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            story=" ".join(["Une chouette observe les étoiles.",
                            "Elle découvre une luciole.",
                            "Puis elle vole vers une clairière.",
                            "La lune éclaire les arbres.",
                            "Au matin, elle raconte son aventure."])
            draft=plan(topic="Une aventure de chouette",script=story,
                       duration=30,character="Chouette violette originale",
                       shot_seconds=6)
            planpath=root/"plan.json"
            planpath.write_text(json.dumps(draft),encoding="utf8")
            preview=build_preview(plan_path=planpath,output=root/"render",
                                  voice="none",limit=1)
            v=root/"render"/"preview.mp4"
            s=root/"render"/"draft-captions.srt"
            report=assess(video=v,captions=s,expected_duration=6,
                          destination=root/"quality.json")
            self.assertEqual(report["status"],"pass")
            self.assertFalse(report["publicationApproved"])
            self.assertEqual(report["subtitleCues"],1)
            self.assertFalse(report["media"]["hasAudio"])
            self.assertTrue((root/"quality.json").is_file())
            report_missing=assess(video=v,captions=s,require_audio=True)
            self.assertEqual(report_missing["status"],"fail")
            self.assertIn("Narration audio is missing",report_missing["errors"])
            generate_vtt(s,root/"render"/"captions.vtt",
                         max_duration_ms=6000)
            self.assertTrue((root/"render"/"captions.vtt").is_file())

if __name__=="__main__":
    unittest.main()
