"""Delivery contract tests: verified previews only, no fake publication approval."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

from scripts.prepare_science_preview_delivery import prepare


class PreviewDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / "source"
        self.out = Path(self.temp.name) / "release"
        video = self.base / "video"
        video.mkdir(parents=True)
        self.movie = video / "preview.mp4"
        self.movie.write_bytes(b"synthetic-video" * 9_000)
        self.subtitle = video / "draft-captions.srt"
        self.subtitle.write_text("1\n00:00:01,000 --> 00:00:02,000\nOriginal speech\n")
        self.qa = {
            "status": "passed",
            "technicalPreviewReady": True,
            "humanEditorialReviewRequired": True,
            "publicationApproved": False,
            "errors": [],
            "checks": {
                "structural": "passed", "media": "pass",
                "frozenAnimatedScenes": 0, "nearBlackVisualSamples": 0,
                "reviewOrientation": "portrait",
                "mp4Width": 1080, "mp4Height": 1920,
                "contactSheetsVerified": True,
                "subtitleCues": 1, "mp4DurationSeconds": 30.1,
                "mp4Sha256": hashlib.sha256(self.movie.read_bytes()).hexdigest(),
                "srtSha256": hashlib.sha256(self.subtitle.read_bytes()).hexdigest(),
            },
        }
        self.qa_file = video / "qa-summary.json"
        self.save_qa()

    def save_qa(self):
        self.qa_file.write_text(json.dumps(self.qa), encoding="utf8")

    def fake_ffmpeg(self, args, **kwargs):
        if args[0] == "ffprobe":
            return subprocess.CompletedProcess(
                args, 0, stdout=json.dumps({
                    "format": {"duration": "30.1"},
                    "streams": [
                        {"codec_type":"video", "codec_name":"h264",
                         "width":1080,"height":1920,"r_frame_rate":"30/1"},
                        {"codec_type":"audio","codec_name":"aac"},
                    ],
                }))
        return subprocess.CompletedProcess(args,0,stdout="",stderr="")

    def test_full_verified_video_and_subtitles_are_delivered_unchanged(self):
        with patch("scripts.prepare_science_preview_delivery.subprocess.run",
                   side_effect=self.fake_ffmpeg) as stub:
            result = prepare(self.base,self.out,"rainbow-optics",1234567)
        self.assertEqual(stub.call_count,2)
        self.assertEqual(result["publicationApproved"],False)
        self.assertTrue(result["humanEditorialReviewRequired"])
        self.assertEqual(result["sourceRunId"],1234567)
        self.assertEqual(
            (self.out/"rainbow-optics.mp4").read_bytes(),self.movie.read_bytes())
        self.assertEqual(
            (self.out/"rainbow-optics.srt").read_bytes(),
            self.subtitle.read_bytes())
        self.assertTrue((self.out/"rainbow-optics-manifest.json").is_file())

    def test_fails_closed_on_corrupt_or_unapproved_artifacts(self):
        for name,value in (
            ("publicationApproved",True),
            ("status","failed"),
            ("technicalPreviewReady",False),
        ):
            with self.subTest(name=name):
                previous=self.qa[name]
                self.qa[name]=value
                self.save_qa()
                with self.assertRaises(ValueError):
                    prepare(self.base,self.out,"rainbow-optics",12345)
                self.qa[name]=previous
        self.qa["checks"]["frozenAnimatedScenes"]=1
        self.save_qa()
        with self.assertRaises(ValueError):
            prepare(self.base,self.out,"rainbow-optics",12345)
        self.qa["checks"]["frozenAnimatedScenes"]=0
        self.save_qa()
        self.movie.write_bytes(self.movie.read_bytes()+b"tampered")
        with self.assertRaisesRegex(ValueError,"digest"):
            prepare(self.base,self.out,"rainbow-optics",12345)
        self.assertFalse(self.out.exists())

    def test_rejects_unsafe_names_and_run_ids(self):
        with self.assertRaises(ValueError):
            prepare(self.base,self.out,"../../danger",12345)
        with self.assertRaises(ValueError):
            prepare(self.base,self.out,"science",0)


if __name__=="__main__":
    unittest.main()
