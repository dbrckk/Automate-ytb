"""Regression on real original PCM and an encoded final AAC with continuous score."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave
from array import array

from automate_ytb.episode import build_preview
from automate_ytb.production import _write_json
from automate_ytb.quality import check
from automate_ytb.scene_plan import plan
from automate_ytb.score_composer import create_score, RATE, VERSION


def make_plan(destination: Path, *, one_scene: bool = False) -> Path:
    data = plan(
        topic="An original ocean-current science explainer",
        script=("A current begins beneath the warm surface. "
                "The temperature changes at the deep boundary. "
                "A narrow current starts to move across the ocean. "
                "The flow becomes visible in the water. "
                "The current slowly reaches equilibrium."),
        duration=30, shot_seconds=6, character="An original violet owl with turquoise eyes and a golden scarf",
    )
    if one_scene:
        data["scenes"] = data["scenes"][:1]
        data["sceneCount"] = 1
        data["scenes"][0]["endMs"] = 12000
    else:
        for i, scene in enumerate(data["scenes"]):
            scene["startMs"], scene["endMs"] = i*2400, (i+1)*2400
    data["targetDurationSeconds"] = 12
    _write_json(destination, data)
    return destination


class ContinuousScoreTests(unittest.TestCase):
    def test_deterministic_global_stereo_score_no_scene_reset(self):
        with tempfile.TemporaryDirectory(prefix="score-original-") as temporary:
            root = Path(temporary)
            story = make_plan(root / "scene-plan.json")
            first = root / "a" / "background-original.wav"
            second = root / "b" / "background-original.wav"
            a = create_score(plan_path=story, output=first)
            b = create_score(plan_path=story, output=second)
            self.assertEqual(a["engine"], VERSION)
            self.assertEqual(a["wavSha256"], b["wavSha256"])
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), a["wavSha256"])
            self.assertEqual(a["sampleRateHz"], RATE)
            self.assertEqual(a["channels"], 2)
            self.assertEqual(a["sceneBoundaryResets"], 0)
            self.assertFalse(a["containsThirdPartyMusic"])
            self.assertEqual(a["externalApiCalls"], 0)
            self.assertFalse(a["humanReviewed"])
            with wave.open(str(first), "rb") as wav:
                self.assertEqual(wav.getnframes(), 12*RATE)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getnchannels(), 2)
                # Check audio on both sides of every boundary. Old soundtrack
                # intentionally faded to silence at every scene transition.
                for boundary in (2.4, 4.8, 7.2, 9.6):
                    wav.setpos(int((boundary-.04)*RATE))
                    raw = wav.readframes(int(.025*RATE))
                    pcm = array("h")
                    pcm.frombytes(raw)
                    self.assertGreater(sum(abs(x) for x in pcm)/len(pcm), 40)
                    wav.setpos(int((boundary+.015)*RATE))
                    pcm = array("h")
                    pcm.frombytes(wav.readframes(int(.025*RATE)))
                    self.assertGreater(sum(abs(x) for x in pcm)/len(pcm), 40)
                wav.setpos(2*RATE)
                pcm = array("h")
                pcm.frombytes(wav.readframes(2048))
                self.assertTrue(any(pcm[i] != pcm[i+1] for i in range(0, len(pcm), 2)))

    def test_opt_in_source_locked_reveal_event_marker(self):
        with tempfile.TemporaryDirectory(prefix="score-visual-") as temporary:
            root = Path(temporary)
            story = make_plan(root / "scene-plan.json")
            data = json.loads(story.read_text())
            data["masterTimeline"] = {
                "schemaVersion": 1,
                "cameraId": "camera-one",
                "visibleActors": ["ocean-current"],
                "objects": [
                    {"id": "camera-one", "properties": {"x": 0., "zoom": 1.}},
                    {"id": "ocean-current", "properties": {
                        "x": .2, "y": .5, "scale": 1., "opacity": 1.}}
                ],
                "events": [{"id": "ocean-reveal", "objectId": "ocean-current",
                            "field": "scale",
                            "start": {"sceneId": "scene-002", "fraction": .5},
                            "end": {"sceneId": "scene-002", "fraction": .8},
                            "from": 1., "to": 1.4}],
                "soundCues": [{"id": "reveal-chime",
                               "sourceEventId": "ocean-reveal",
                               "family": "reveal"}]
            }
            _write_json(story, data)
            report = create_score(plan_path=story, output=root / "score.wav")
            self.assertEqual(report["musicArc"]["pivotSource"], "authored-visual-reveal")
            self.assertEqual(report["authoredEventAccents"][0]["sourceEventId"],
                             "ocean-reveal")
            self.assertEqual(report["authoredEventAccents"][0]["atSample"],
                             round(3.6 * RATE))

    def test_invalid_inputs_rejected_without_output(self):
        with tempfile.TemporaryDirectory(prefix="score-invalid-") as temporary:
            root = Path(temporary)
            story = make_plan(root / "scene-plan.json")
            with self.assertRaisesRegex(ValueError, "mode"):
                create_score(plan_path=story, output=root / "bad.wav",
                             mode="use-copyrighted-track")
            data = json.loads(story.read_text())
            data["targetDurationSeconds"] = 190
            data["scenes"][-1]["endMs"] = 190000
            _write_json(story, data)
            with self.assertRaisesRegex(ValueError, "12–180"):
                create_score(plan_path=story, output=root / "bad.wav")
            self.assertFalse((root / "bad.wav").exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg and FFprobe required")
    def test_real_12_second_video_with_final_aac_and_fail_closed_integrity(self):
        with tempfile.TemporaryDirectory(prefix="score-encoded-") as temporary:
            root = Path(temporary)
            story = make_plan(root / "scene-plan.json", one_scene=True)
            out = root / "out"
            result = build_preview(
                plan_path=story, output=out, voice="none", soundtrack="score",
                style="cartoon", resolution="720p", transition="cut",
            )
            self.assertEqual(result["soundtrack"]["engine"], VERSION)
            self.assertTrue(result["render"]["hasBackgroundMusic"])
            self.assertEqual(result["render"]["audioMixMode"], "original-bed-only")
            self.assertFalse(result["render"]["hasCausalFoley"])
            video = Path(result["render"]["video"])
            streams = json.loads(subprocess.check_output([
                "ffprobe", "-v", "error", "-of", "json",
                "-show_entries", "stream=codec_type,codec_name,sample_rate,channels",
                str(video)], text=True))["streams"]
            audio = [s for s in streams if s["codec_type"] == "audio"]
            self.assertEqual(len(audio), 1)
            self.assertEqual(audio[0]["codec_name"], "aac")
            self.assertEqual(audio[0]["sample_rate"], "48000")
            self.assertEqual(audio[0]["channels"], 2)
            before = check(plan=story, output=out, expected_voice="none",
                           expected_soundtrack="score")
            self.assertNotIn("Continuous score provenance or PCM timing mismatch",
                             before["errors"])
            # Authenticating the original WAV and the report matters even when
            # the already encoded AAC/MP4 has not been changed.
            stem = out / "background-original.wav"
            with stem.open("ab") as stream:
                stream.write(b"tamper")
            after = check(plan=story, output=out, expected_voice="none",
                          expected_soundtrack="score")
            self.assertIn("Continuous score provenance or PCM timing mismatch",
                          after["errors"])
            self.assertEqual(after["status"], "failed")


if __name__ == "__main__":
    unittest.main()
