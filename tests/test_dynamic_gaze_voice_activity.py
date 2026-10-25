"""Real FFmpeg evidence for progressive object gaze and voice-activity mouth."""
from __future__ import annotations

from array import array
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import wave

from PIL import Image, ImageChops, ImageStat

from automate_ytb.scene_plan import plan
from automate_ytb.episode import build_preview
from automate_ytb.voice_activity import (
    activity_intervals, mouth_gate_expression, MOUTH_VERSION)
from automate_ytb.animated_forest import (
    render_motion_clip as forest_clip, render_layers as forest_layers)
from automate_ytb.animated_owl import render_motion_clip as owl_clip


def recorded_frame(path: Path, sec: float) -> Image.Image:
    output = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(sec),
         "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"], check=True, capture_output=True, timeout=90)
    with Image.open(io.BytesIO(output.stdout)) as src:
        return src.convert("RGB")


def delta(a: Image.Image, b: Image.Image, box: tuple) -> float:
    return sum(ImageStat.Stat(
        ImageChops.difference(a.crop(box), b.crop(box))).mean)


def make_test_wav(path: Path):
    """2.0s mono 16-bit voice-like signal with clear, controlled silences."""
    rate = 16000
    pcm = array("h")
    for n in range(rate * 2):
        t = n / rate
        # Speech-like bursts at 0.24-0.68s and 0.98-1.42s.
        active = .24 <= t < .68 or .98 <= t < 1.42
        pcm.append(int(9500 * __import__("math").sin(t * 900))
                   if active else 0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


class SpeechMouthTests(unittest.TestCase):
    def test_pcm_detects_measured_speech_and_actual_silence(self):
        self.assertIn("v1", MOUTH_VERSION)
        with tempfile.TemporaryDirectory() as folder:
            voice = Path(folder) / "speech.wav"
            make_test_wav(voice)
            windows = activity_intervals(
                voice, scene_start_ms=0, scene_end_ms=2000)
            self.assertIsNotNone(windows)
            self.assertEqual(len(windows), 2, windows)
            self.assertTrue(windows[0][0] <= .3 <= windows[0][1])
            self.assertTrue(windows[1][0] <= 1.15 <= windows[1][1])
            self.assertFalse(any(a <= .82 <= b for a, b in windows))
            self.assertEqual(activity_intervals(
                voice, scene_start_ms=1550, scene_end_ms=2000), [])
            self.assertIsNone(activity_intervals(
                None, scene_start_ms=0, scene_end_ms=2000))
            expr = mouth_gate_expression(windows)
            self.assertIn("between(t,", expr)
            self.assertIn("gt(", expr)
            self.assertNotIn(";", expr)
            self.assertEqual(mouth_gate_expression([]), "0")
            self.assertIsNone(mouth_gate_expression(None))

    def test_invalid_activity_is_rejected_and_external_formats_fall_back(self):
        with self.assertRaises(ValueError):
            mouth_gate_expression([(1.0, 0.5)])
        with self.assertRaises(ValueError):
            mouth_gate_expression([(0.2, 0.5), (0.1, 0.3)])
        with self.assertRaises(ValueError):
            mouth_gate_expression([(0.0, 0.5)] * 81)
        with tempfile.TemporaryDirectory() as folder:
            not_wav = Path(folder) / "external.mp3"
            not_wav.write_bytes(b"not a PCM WAV")
            self.assertIsNone(activity_intervals(
                not_wav, scene_start_ms=0, scene_end_ms=1000))
            with self.assertRaises(ValueError):
                activity_intervals(
                    not_wav, scene_start_ms=1000, scene_end_ms=0)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required")
    def test_cat_gaze_progressively_shifts_to_carried_apple(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = dict(kind="cat", topic="A unique woodland story",
                          narration="The cat takes a little walk.",
                          scene_index=2, scene_count=3,
                          style="cartoon", duration=1.5,
                          width=1280, height=720, fps=24,
                          direction={"weather": "day", "action": "idle",
                                     "emotion": "happy", "shot": "wide"})
            subject, neutral = root / "apple.mp4", root / "no-apple.mp4"
            forest_clip(destination=subject, held_prop="apple", **common)
            forest_clip(destination=neutral, **common)
            first = delta(recorded_frame(subject, .1),
                          recorded_frame(neutral, .1),
                          (255, 355, 480, 445))
            final = delta(recorded_frame(subject, 1.0),
                          recorded_frame(neutral, 1.0),
                          (255, 355, 480, 445))
            self.assertGreater(final, first + .5, (first, final))
            self.assertLess(first, 1.5, first)
            # Still-image poster retains its original final approved gaze.
            layers = forest_layers(
                root / "layers", kind="cat", topic=common["topic"],
                narration=common["narration"], scene_index=2,
                scene_count=3, style="cartoon", held_prop="apple")
            self.assertTrue(layers["neutral"].is_file())
            self.assertNotEqual(layers["neutral"].read_bytes(),
                                layers["body"].read_bytes())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required")
    def test_owl_gaze_transition_and_blink_are_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = dict(topic="Owl story", narration="The owl walks.",
                          scene_index=2, scene_count=3,
                          style="cartoon", duration=1.3,
                          width=1280, height=720, fps=24,
                          direction={"weather": "night", "action": "idle",
                                     "emotion": "neutral", "shot": "wide"})
            owl_clip(destination=root/"carried.mp4", held_prop="flower", **common)
            owl_clip(destination=root/"regular.mp4", **common)
            first = delta(recorded_frame(root/"carried.mp4", .1),
                          recorded_frame(root/"regular.mp4", .1),
                          (275, 305, 490, 410))
            last = delta(recorded_frame(root/"carried.mp4", .9),
                         recorded_frame(root/"regular.mp4", .9),
                         (275, 305, 490, 410))
            self.assertGreater(last, first + .5)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required")
    def test_voice_gated_mouth_closes_in_silence_in_rendered_fox(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / "voice.wav"
            make_test_wav(audio)
            intervals = activity_intervals(audio, scene_start_ms=0,
                                           scene_end_ms=2000)
            common = dict(kind="fox", topic="An original animal story",
                          narration="The little fox talks to the birds.",
                          scene_index=1, scene_count=3,
                          style="cartoon", duration=2,
                          width=1280, height=720, fps=24,
                          direction={"weather": "day", "action": "talk",
                                     "emotion": "happy", "shot": "wide"})
            gated, rhythmic = root/"gated.mp4", root/"rhythmic.mp4"
            forest_clip(destination=gated, mouth_intervals=intervals, **common)
            forest_clip(destination=rhythmic, **common)
            # At 0.10 seconds the rhythmic mouth would be open, while the
            # recorded audio is silent. At 0.32 speech is active.
            early = delta(recorded_frame(gated, .1),
                          recorded_frame(rhythmic, .1),
                          (337, 444, 424, 516))
            during = delta(recorded_frame(gated, .33),
                           recorded_frame(rhythmic, .33),
                           (337, 444, 424, 516))
            self.assertGreater(early, 1.5)
            self.assertLess(during, early / 2 + 0.5)


    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak-ng") or shutil.which("espeak")),
                         "Real offline voice + FFmpeg required")
    def test_one_click_voice_preview_reports_actual_mouth_activity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / "plan.json"
            scenes = plan(
                topic="Le renard original raconte une histoire",
                script=("Le renard raconte une histoire à ses amis. "
                        "Il parle calmement sous les étoiles. "
                        "Il explique pourquoi la forêt est belle. "
                        "Les animaux écoutent son récit passionnant. "
                        "Puis le renard rentre chez lui."),
                character="Un petit renard roux original",
                duration=30, shot_seconds=6)
            p.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            result = build_preview(
                plan_path=p, output=root / "preview",
                style="cartoon", voice="espeak", language="fr",
                caption_timing="audio", soundtrack="none",
                transition="cut", limit=1)
            report = result["render"]["speechMouth"]
            self.assertEqual(report["analyzedScenes"], 1)
            self.assertGreater(report["activeIntervals"], 0)
            self.assertEqual(report["fallbackScenes"], 0)
            self.assertEqual(report["audioTimelineShiftMs"], 0)
            self.assertTrue((root / "preview" / "preview.mp4").is_file())

if __name__ == "__main__":
    unittest.main()
