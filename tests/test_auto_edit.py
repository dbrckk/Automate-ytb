"""Real end-to-end multi-source video production and fail-closed guarantees."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
            assign_sources([499], [10000])

    def test_selection_prefers_distinct_optical_scene_when_candidates_exist(self):
        # All source windows are real chronological candidates. Simulate
        # already decoded optical measurements to isolate the scoring rule.
        calls=[]
        def measured(_source, start, _duration):
            calls.append(start)
            # Scene one is always a flat composition; on the next scene
            # the latest candidate has a different spatial composition.
            distinctive = start >= 7.0
            return {
                "sampledFrames":3,
                "meanLuminance":100,
                "contrastStdDev":25,
                "meanFrameChange":10,
                "technicalSelectionScore":.70 if not distinctive else .64,
                "requiresVisualReview":False,
                "spatialSignature":[190 if distinctive else 60]*48,
            }
        with patch("automate_ytb.auto_edit._sample_quality",side_effect=measured):
            selected=select_excerpts([Path("owned.mp4")],[4000,4000],
                                     [16000],(2,))
        self.assertEqual(len(selected),2)
        self.assertTrue(all(s["candidateCount"] >= 2 for s in selected))
        self.assertGreaterEqual(selected[1]["startSeconds"],7)
        self.assertFalse(selected[1]["technicalReview"]["adjacentOpticalComparison"]["nearDuplicateOpticalComposition"])
        self.assertLessEqual(selected[0]["startSeconds"]+4,selected[1]["startSeconds"])
        self.assertGreater(len(calls),2)

    def test_genres_are_explicit_not_llm_semantic_inference(self):
        self.assertIn("documentary", GENRES)
        self.assertIn("fitness", GENRES)
        self.assertIn("product", GENRES)
        self.assertIn("v2", VERSION)


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
        self.assertEqual(final["portraitFraming"]["requested"], "auto")
        self.assertEqual(final["portraitFraming"]["trackedScenes"], 0)
        self.assertEqual(final["portraitFraming"]["preservedScenes"], 5)
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
        args["portrait_framing"]="unsafe"
        args["video_paths"]=self.sources
        with self.assertRaisesRegex(ValueError,"Portrait framing"):
            auto_edit(**args)
        self.assertFalse(args["destination"].exists())
        args.pop("portrait_framing")
        args["video_paths"]=[self.sources[2]]
        with self.assertRaisesRegex(ValueError,"Not enough continuous"):
            auto_edit(**args)
        self.assertFalse(args["destination"].exists())

    @unittest.skipUnless(
        shutil.which("espeak-ng") or shutil.which("espeak"),
        "Real local eSpeak required for speech-to-video integration")
    def test_local_english_narration_is_audible_and_captions_use_pcm_times(self):
        request=self.kwargs()
        request["destination"]=self.root/"narrated-documentary"
        request.update(voice_engine="espeak",language="en",
                       narration_style="natural")
        final=auto_edit(**request)
        output=request["destination"]
        self.assertTrue(final["voiceGenerated"])
        self.assertEqual(final["narrationEngine"],"espeak-draft")
        self.assertEqual(final["narrationLanguage"],"en")
        self.assertEqual(final["subtitleTiming"],
                         "audio-derived-synthesized-phrases")
        self.assertFalse(final["hasUserProvidedNarration"])
        self.assertFalse(final["sourceAudioIncluded"])
        self.assertTrue((output/"narration.wav").is_file())
        voice=json.loads((output/"voice-report.json").read_text())
        self.assertEqual(voice["voice"],str(output/"narration.wav"))
        self.assertGreater(voice["captionPhraseCount"],0)
        scenes=load_plan(output/"scene-plan.json")["scenes"]
        self.assertTrue(all(s.get("captionSegments") for s in scenes))
        self.assertTrue(all(
            s["startMs"] <= cap["startMs"] < cap["endMs"] <= s["endMs"]
            for s in scenes for cap in s["captionSegments"]))
        movie=output/"render"/"preview.mp4"
        probe=json.loads(command(
            "ffprobe","-v","error","-show_entries",
            "stream=codec_type,codec_name:format=duration",
            "-of","json",str(movie)))
        self.assertIn("aac",[
            stream["codec_name"] for stream in probe["streams"]
            if stream["codec_type"]=="audio"])
        self.assertAlmostEqual(float(probe["format"]["duration"]),
                               scenes[-1]["endMs"]/1000,delta=.35)

    def test_interleaved_real_camera_clips_are_distinct_and_retain_no_source_audio(self):
        request=self.kwargs()
        request["destination"]=self.root/"interleaved-documentary"
        request["source_order"]="interleave"
        final=auto_edit(**request)
        shots=final["shots"]
        self.assertEqual(final["sceneCount"],5)
        self.assertEqual(final["sourcesUsed"],3)
        self.assertEqual(final["sourceOrderingStrategy"],"interleave")
        self.assertFalse(final["sourceOrderPreserved"])
        self.assertTrue(final["sourceChronologyPreserved"])
        self.assertTrue(final["sourceSegmentsNonoverlapping"])
        self.assertFalse(final["sourceAudioIncluded"])
        self.assertEqual(len(final["sourceSchedule"]),5)
        source_order=[shot["sourceName"] for shot in shots]
        self.assertGreaterEqual(
            sum(source_order[i]!=source_order[i-1]
                for i in range(1,len(shots))),3)
        for source in set(source_order):
            chosen=[s for s in shots if s["sourceName"]==source]
            self.assertTrue(all(
                a["startSeconds"] + a["durationSeconds"] <= b["startSeconds"]+.005
                for a,b in zip(chosen,chosen[1:])))
        output=request["destination"]/"render"/"preview.mp4"
        self.assertTrue(output.stat().st_size > 10000)
        command("ffmpeg","-nostdin","-v","error","-i",str(output),"-f","null","-",
                timeout=130)

    def test_narration_configuration_conflicts_fail_without_output(self):
        args=self.kwargs()
        args["voice_engine"]="espeak"
        args["audio"]=self.root/"user-voice.wav"
        with self.assertRaisesRegex(ValueError,"Choose supplied narration"):
            auto_edit(**args)
        self.assertFalse(args["destination"].exists())
        args.pop("audio")
        args["voice_engine"]="none"
        args["voice_name"]="af_bella"
        with self.assertRaisesRegex(ValueError,"named voice requires Kokoro"):
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
