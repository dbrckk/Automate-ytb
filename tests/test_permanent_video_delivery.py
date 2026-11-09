"""No broken 'File not found' link can pass the public-release gate."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.verify_release_video import verify_release_video


class PermanentVideoDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.video = Path(self.tmp.name)/"short.mp4"
        self.report = Path(self.tmp.name)/"short.json"
        self.video.write_bytes(b"original-validated-video" * 10000)
        self.qa = {
            "videoSha256":hashlib.sha256(self.video.read_bytes()).hexdigest(),
            "voiceEngine":"kokoro-natural",
            "soundscape":{"clippedSamples":0},
            "size":[1080,1920],"fps":30,"frames":472,
            "publicationApproved":False,"durationSeconds":15.73
        }
        self.report.write_text(json.dumps(self.qa))
        self.probe = json.dumps({
            "format":{"duration":"15.73"},
            "streams":[
                {"codec_type":"video","codec_name":"h264",
                 "width":1080,"height":1920},
                {"codec_type":"audio","codec_name":"aac"}]})

    def test_good_video_requires_real_probe_and_full_decode(self):
        from subprocess import CompletedProcess
        with patch("scripts.verify_release_video.subprocess.run") as run:
            run.side_effect=[
                CompletedProcess([],0,stdout=self.probe),
                CompletedProcess([],0,stdout="")
            ]
            result=verify_release_video(self.video,self.report)
            self.assertTrue(result["releaseVerified"])
            self.assertEqual(run.call_count,2)
            self.assertIn("-xerror",run.call_args.args[0])

    def test_refuse_corrupt_checksum_before_any_ffmpeg_call(self):
        self.qa["videoSha256"]="0"*64
        self.report.write_text(json.dumps(self.qa))
        with patch("scripts.verify_release_video.subprocess.run") as run:
            with self.assertRaises(ValueError):
                verify_release_video(self.video,self.report)
            run.assert_not_called()

    def test_refuse_missing_video_and_missing_provenance(self):
        self.video.unlink()
        with self.assertRaises(ValueError):
            verify_release_video(self.video,self.report)

    def test_refuse_saturated_audio_or_wrong_publication_flag(self):
        for field,value in (("soundscape",{"clippedSamples":3}),
                            ("publicationApproved",True),
                            ("size",[1920,1080])):
            qa=dict(self.qa,**{field:value})
            self.report.write_text(json.dumps(qa))
            with self.assertRaises(ValueError):
                verify_release_video(self.video,self.report)

    def test_refuse_wrong_video_or_audio_codec(self):
        from subprocess import CompletedProcess
        for codec in ("hevc","vp9"):
            broken=self.probe.replace('"h264"',f'"{codec}"')
            with patch("scripts.verify_release_video.subprocess.run",
                       return_value=CompletedProcess([],0,stdout=broken)):
                with self.assertRaises(ValueError):
                    verify_release_video(self.video,self.report)


if __name__=="__main__":
    unittest.main()
