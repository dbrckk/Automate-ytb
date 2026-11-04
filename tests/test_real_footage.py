"""Prove mixed still and real moving footage works in actual encoded H.264."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.production import (
    audit, ingest, ingest_video, load_plan, render,
)
from automate_ytb.scene_plan import plan

TOOLS = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def run(*args):
    return subprocess.run(
        list(args), capture_output=True, check=True, timeout=100)


@unittest.skipUnless(TOOLS, "Free local FFmpeg + FFprobe required")
class RealFootageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan_path = self.root / "scene-plan.json"
        script = " ".join(f"This is original footage scene {i}." for i in range(5))
        data = plan(
            topic="Original documentary montage", script=script,
            character="Original filmmaker and camera footage",
            duration=30, shot_seconds=6)
        self.plan_path.write_text(json.dumps(data),encoding="utf8")
        self.video=self.root/"owned.mp4"
        run("ffmpeg","-nostdin","-hide_banner","-v","error","-y",
            "-f","lavfi","-i","testsrc2=size=480x320:rate=24",
            "-f","lavfi","-i","sine=frequency=440:sample_rate=48000",
            "-t","6.5","-c:v","libx264","-preset","ultrafast",
            "-threads","1","-pix_fmt","yuv420p",
            "-c:a","aac","-shortest",str(self.video))
        self.rights="I own the original footage and all rights necessary for editing."

    def tearDown(self):
        self.temp.cleanup()

    def attach(self, **overrides):
        args=dict(plan_path=self.plan_path, scene_id="scene-001",
                  video_path=self.video, provider="original-camera",
                  rights_note=self.rights, cost_usd="0",
                  rights_confirmed=True)
        args.update(overrides)
        return ingest_video(**args)

    def test_real_footage_not_a_still_and_source_audio_is_removed(self):
        recorded=self.attach()
        self.assertFalse(recorded["sourceAudioIncluded"])
        self.assertEqual(recorded["videoDetails"]["normalizedFps"],30)
        saved=load_plan(self.plan_path)
        self.assertEqual(saved["scenes"][0]["videoAsset"],"assets/scene-001.mp4")
        self.assertTrue((self.root/"assets/scene-001.png").is_file())
        self.assertTrue((self.root/"assets/scene-001.mp4").is_file())
        self.assertEqual(audit(self.plan_path,limit=1)["counts"]["ready"],1)
        report=render(plan_path=self.plan_path,
                      output=self.root/"preview",limit=1,
                      fps=24,resolution="720p",transition="cut")
        self.assertEqual(report["realFootageSceneCount"],1)
        self.assertFalse(report["realFootageSourceAudioIncluded"])
        final=self.root/"preview/preview.mp4"
        self.assertTrue(final.is_file())
        metadata=json.loads(run(
            "ffprobe","-v","error","-show_entries",
            "stream=codec_name,codec_type,width,height:format=duration",
            "-of","json",str(final)).stdout)
        video_streams=[s for s in metadata["streams"]
                       if s.get("codec_type")=="video"]
        self.assertEqual(len(video_streams),1)
        self.assertEqual(video_streams[0]["codec_name"],"h264")
        self.assertEqual(video_streams[0]["width"],1280)
        self.assertEqual(video_streams[0]["height"],720)
        self.assertFalse(any(s.get("codec_type")=="audio"
                             for s in metadata["streams"]))
        self.assertAlmostEqual(float(metadata["format"]["duration"]),6,delta=.2)
        frames=run(
            "ffmpeg","-nostdin","-hide_banner","-v","error",
            "-ss","0.4","-i",str(final),"-t","1.5",
            "-vf","fps=2,scale=96:54,format=gray",
            "-f","rawvideo","-pix_fmt","gray","pipe:1")
        # Real moving source must produce different encoded pixels over time.
        raw=frames.stdout.encode("latin1") if isinstance(frames.stdout,str) else frames.stdout
        pixels=96*54
        self.assertGreaterEqual(len(raw),3*pixels)
        self.assertNotEqual(raw[:pixels],raw[-pixels:])

    def test_tampered_video_rejects_render_and_stale_stills_can_replace(self):
        self.attach()
        movie=self.root/"assets/scene-001.mp4"
        movie.write_bytes(movie.read_bytes()+b"not-original")
        self.assertEqual(audit(self.plan_path,limit=1)["counts"]["changed"],1)
        with self.assertRaisesRegex(ValueError,"not ready"):
            render(plan_path=self.plan_path,output=self.root/"preview",limit=1)
        still=self.root/"owned-still.png"
        Image.new("RGB",(640,360),(40,120,170)).save(still)
        ingest(plan_path=self.plan_path,scene_id="scene-001",
               image_path=still,provider="human-original",
               rights_note=self.rights,cost_usd="0",
               rights_confirmed=True,replace=True)
        self.assertNotIn("videoAsset",load_plan(self.plan_path)["scenes"][0])
        self.assertFalse(movie.exists())
        self.assertEqual(audit(self.plan_path,limit=1)["counts"]["ready"],1)

    def test_reject_unapproved_video_unsafe_path_and_short_clip(self):
        with self.assertRaisesRegex(ValueError,"confirm-rights"):
            self.attach(rights_confirmed=False)
        with self.assertRaisesRegex(ValueError,"exists"):
            self.attach()
            self.attach()
        doc=load_plan(self.plan_path)
        doc["scenes"][0]["videoAsset"]="../../unsafe.mp4"
        self.plan_path.write_text(json.dumps(doc),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"Unsafe video path"):
            load_plan(self.plan_path)
        doc["scenes"][0]["videoAsset"]="assets/scene-001.mp4"
        self.plan_path.write_text(json.dumps(doc),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"trim|duration"):
            self.attach(clip_start_seconds=4,replace=True)
        self.assertEqual(audit(self.plan_path,limit=1)["counts"]["ready"],1)


if __name__=="__main__":
    unittest.main()
