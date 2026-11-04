"""Real end-to-end multi-source video production and fail-closed guarantees."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from automate_ytb.auto_edit import (
    GENRES, VERSION, assign_sources, auto_edit, select_excerpts,
)
from automate_ytb.production import audit, load_plan

FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
RIGHTS = "I filmed and own every supplied original video and its editing rights."


def command(*args, timeout=100) -> bytes:
    proc = subprocess.run(
        list(args),capture_output=True,timeout=timeout,check=False)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf8","replace")[-1500:])
    return proc.stdout


class SourceAllocationTests(unittest.TestCase):
    def test_chronological_diverse_allocation_without_repeated_footage(self):
        self.assertEqual(
            assign_sources([6000]*5,[12500,12500,6500]),
            (2,2,1))
        self.assertEqual(
            assign_sources([6000]*3,[6000,6000,6000]),
            (1,1,1))
        self.assertEqual(
            assign_sources([6000]*4,[25000]),
            (4,))
        with self.assertRaisesRegex(ValueError,"Not enough continuous"):
            assign_sources([6000]*4,[7000,7000])
        with self.assertRaises(ValueError):
            assign_sources([500], [10000])

    def test_genres_are_explicit_not_llm_semantic_inference(self):
        self.assertIn("documentary", GENRES)
        self.assertIn("fitness", GENRES)
        self.assertIn("product", GENRES)
        self.assertIn("v1", VERSION)


@unittest.skipUnless(FFMPEG_AVAILABLE, "Real local FFmpeg required")
class EndToEndAutoEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.script = self.root/"authored-script.txt"
        self.script.write_text(" ".join(
            f"Original documentary segment number {i} discusses authentic "
            f"footage from the project."
            for i in range(1,6)),encoding="utf8")
        self.sources=[]
        # 2+2+1 six-second scenes. A real audio stream exists in sources
        # specifically to prove that it cannot leak into the final export.
        for i, duration in enumerate((12.5,12.5,6.5),1):
            source=self.root/f"original-{i}.mp4"
            command(
                "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i",
                f"testsrc2=size=320x256:rate=12",
                "-f","lavfi","-i",
                f"sine=frequency={220+i*110}:sample_rate=48000",
                "-t",str(duration),"-c:v","libx264","-preset","ultrafast",
                "-threads","1","-pix_fmt","yuv420p",
                "-c:a","aac","-shortest",str(source))
            self.sources.append(source)

    def tearDown(self):
        self.temp.cleanup()

    def kwargs(self):
        return {
            "video_paths":self.sources,
            "destination":self.root/"complete-documentary",
            "script_path":self.script,
            "topic":"Original creator-owned documentary",
            "duration":30,
            "shot_seconds":6,
            "genre":"documentary",
            "rights_note":RIGHTS,
            "rights_confirmed":True,
            "resolution":"720p",
            "fps":24,
            "transition":"cut",
        }

    def test_single_command_delivers_five_real_moving_clips_and_final_mp4(self):
        request=self.kwargs()
        final=auto_edit(**request)
        destination=request["destination"]
        movie=destination/"render"/"preview.mp4"
        self.assertEqual(final["status"],"rendered-for-human-review")
        self.assertEqual(final["sceneCount"],5)
        self.assertEqual(final["sourcesUsed"],3)
        self.assertEqual(final["sourceAllocationCounts"],[2,2,1])
        self.assertEqual(final["outputVideo"],str(movie))
        self.assertFalse(final["publicationApproved"])
        self.assertFalse(final["semanticMatchingPerformed"])
        self.assertFalse(final["voiceGenerated"])
        self.assertFalse(final["sourceAudioIncluded"])
        self.assertEqual(audit(destination/"scene-plan.json")["counts"]["ready"],5)
        persisted=json.loads((destination/"auto-edit-report.json").read_text())
        self.assertEqual(persisted["shots"],final["shots"])
        self.assertTrue(all(len(shot["sourceSHA256"])==64
                            for shot in final["shots"]))
        self.assertTrue(all(shot["normalizedVideoSHA256"] and
                            shot["technicalReview"]["sampledFrames"]>=1
                            for shot in final["shots"]))
        self.assertEqual(
            [shot["sourceName"] for shot in final["shots"]],
            ["original-1.mp4"]*2+["original-2.mp4"]*2+["original-3.mp4"])
        for previous,current in zip(final["shots"],final["shots"][1:]):
            if previous["sourceName"]==current["sourceName"]:
                self.assertLessEqual(
                    previous["startSeconds"]+previous["durationSeconds"],
                    current["startSeconds"]+.005)
        metadata=json.loads(command(
            "ffprobe","-v","error",
            "-show_entries","stream=codec_type,codec_name,width,height:"
                            "format=duration",
            "-of","json",str(movie)))
        tracks=metadata["streams"]
        frame=next(x for x in tracks if x["codec_type"]=="video")
        self.assertEqual(frame["codec_name"],"h264")
        self.assertEqual((frame["width"],frame["height"]),(1280,720))
        self.assertFalse(any(x["codec_type"]=="audio" for x in tracks))
        self.assertAlmostEqual(float(metadata["format"]["duration"]),30,delta=.35)
        self.assertTrue((destination/"render"/"draft-captions.srt").is_file())
        self.assertTrue((destination/"render"/"visual-preflight.json").is_file())
        self.assertEqual(load_plan(destination/"scene-plan.json")["sceneCount"],5)
        with self.assertRaisesRegex(ValueError,"already exists"):
            auto_edit(**request)

    def test_rights_duplicate_sources_and_capacity_fail_without_artifacts(self):
        args=self.kwargs()
        args["rights_confirmed"]=False
        with self.assertRaisesRegex(ValueError,"confirm-rights"):
            auto_edit(**args)
        self.assertFalse(args["destination"].exists())
        args["rights_confirmed"]=True
        args["video_paths"]=[self.sources[0],self.sources[0]]
        with self.assertRaisesRegex(ValueError,"Duplicate source"):
            auto_edit(**args)
        self.assertFalse(args["destination"].exists())
        args["video_paths"]=[self.sources[2]]
        with self.assertRaisesRegex(ValueError,"Not enough continuous"):
            auto_edit(**args)
        self.assertFalse(args["destination"].exists())

    def test_real_short_samples_have_exposure_and_motion_diagnostics(self):
        source=self.sources[0]
        excerpts=select_excerpts([source],[6000],[12500],(1,))
        self.assertEqual(len(excerpts),1)
        self.assertGreaterEqual(excerpts[0]["startSeconds"],0)
        self.assertLessEqual(excerpts[0]["startSeconds"]+6,12.5)
        info=excerpts[0]["technicalReview"]
        self.assertGreater(info["sampledFrames"],0)
        self.assertGreater(info["contrastStdDev"],0)
        self.assertGreater(info["meanLuminance"],0)
        self.assertIn("meanFrameChange",info)
        self.assertGreaterEqual(excerpts[0]["candidateCount"],2)


if __name__=="__main__":
    unittest.main()
