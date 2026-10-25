"""Action phases use true synthesized *phrase* starts, never fake word timing."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.action_timeline import action_phases, choreograph, timeline_report
from automate_ytb.animated_forest import render_motion_clip
from automate_ytb.episode import build_preview
from automate_ytb.scene_plan import plan
from automate_ytb.production import load_plan
from automate_ytb.captions import caption_phrases
from automate_ytb.choreography import body_position
from automate_ytb.director import direction_for


SCRIPT = (
    "The fox walks toward the quiet tall trees beside the road. "
    "Then the fox jumps over a stone near the river bank. "
    "Afterwards the fox talks about the whole wonderful journey."
)


def _synthetic_measured_phrases(text: str, *, first_ms: int = 3200):
    """Exact caption text with plausible externally measured, variable spans."""
    pieces = caption_phrases(text)
    elapsed = first_ms
    segments = []
    for i, phrase in enumerate(pieces):
        duration_ms = 790 + i * 310
        segments.append({"text": phrase, "startMs": elapsed,
                         "endMs": elapsed + duration_ms})
        elapsed += duration_ms
    return segments, (elapsed - first_ms)/1000


def _frame(file: Path, t: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error",
         "-ss", str(t), "-i", str(file), "-frames:v", "1",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, timeout=90, check=True)
    with Image.open(io.BytesIO(result.stdout)) as img:
        return img.convert("RGB")


class AudioAnchoredGestureTests(unittest.TestCase):
    def test_audio_phrases_override_only_measured_multi_action_boundaries(self):
        cues, duration = _synthetic_measured_phrases(SCRIPT)
        phases = action_phases(
            SCRIPT, duration=duration, fallback_action="walk",
            caption_segments=cues, scene_start_ms=3200)
        self.assertEqual([p["action"] for p in phases],
                         ["walk", "jump", "talk"])
        self.assertEqual(phases[0]["start"], 0)
        self.assertEqual(phases[-1]["end"], duration)
        phrase_actions = [direction_for(p["text"])["action"] for p in cues]
        first_jump = phrase_actions.index("jump")
        first_talk = phrase_actions.index("talk")
        self.assertEqual(phases[1]["start"],
                         round((cues[first_jump]["startMs"]-3200)/1000, 4))
        self.assertEqual(phases[2]["start"],
                         round((cues[first_talk]["startMs"]-3200)/1000, 4))
        report = timeline_report(
            SCRIPT, duration, "walk", caption_segments=cues,
            scene_start_ms=3200)
        self.assertTrue(report["audioAnchored"])
        self.assertEqual(report["audioTimelineShiftMs"], 0)
        self.assertIn("phrase-onsets", report["timingMethod"])
        legacy = timeline_report(SCRIPT, duration, "walk")
        self.assertFalse(legacy["audioAnchored"])
        self.assertNotEqual(legacy["phases"], phases)

    def test_one_phrase_cannot_claim_word_level_audio_alignment(self):
        script = "The fox walks, then jumps."
        segments = [{"text": script, "startMs": 5000, "endMs": 10000}]
        result = timeline_report(
            script, 5, "walk", caption_segments=segments,
            scene_start_ms=5000)
        self.assertFalse(result["audioAnchored"])
        self.assertIn("relative-script", result["timingMethod"])

    def test_invalid_audio_cue_is_rejected_instead_of_silent_retiming(self):
        cues, duration = _synthetic_measured_phrases(SCRIPT)
        bad_text = [dict(x) for x in cues]
        bad_text[0]["text"] = "An invented unrelated narration."
        with self.assertRaisesRegex(ValueError, "differs"):
            action_phases(SCRIPT, duration=duration, fallback_action="walk",
                          caption_segments=bad_text, scene_start_ms=3200)
        wrong_time = [dict(x) for x in cues]
        wrong_time[1]["startMs"] += 12
        with self.assertRaisesRegex(ValueError, "timestamps"):
            action_phases(SCRIPT, duration=duration, fallback_action="walk",
                          caption_segments=wrong_time, scene_start_ms=3200)
        wrong_end = [dict(x) for x in cues]
        wrong_end[-1]["endMs"] -= 2
        with self.assertRaisesRegex(ValueError, "scene end"):
            action_phases(SCRIPT, duration=duration, fallback_action="walk",
                          caption_segments=wrong_end, scene_start_ms=3200)

    def test_single_action_phrases_keep_exact_legacy_animation(self):
        text = "The fox walks beside the flowers."
        pieces = caption_phrases(text)
        self.assertEqual(len(pieces), 1)
        cues = [{"text": pieces[0], "startMs": 0, "endMs": 4000}]
        result = choreograph(
            text, duration=4, fallback_action="walk",
            caption_segments=cues, scene_start_ms=0,
            pose=lambda action: body_position(action, x=180, y=184))
        self.assertEqual(result, body_position("walk", x=180, y=184))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual FFmpeg required for animated output comparison")
    def test_real_fox_video_moves_according_to_audio_phrase_cues(self):
        cues, duration = _synthetic_measured_phrases(SCRIPT, first_ms=0)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = dict(
                kind="fox", topic="Original narrated action",
                narration=SCRIPT, scene_index=1, scene_count=3,
                style="cartoon", duration=duration,
                width=1280, height=720, fps=24,
                direction={"weather": "day", "action": "walk",
                           "emotion": "happy", "shot": "wide"})
            measured = root/"audio-anchored.mp4"
            estimated = root/"legacy-positions.mp4"
            render_motion_clip(destination=measured,
                               caption_segments=cues, scene_start_ms=0,
                               **common)
            render_motion_clip(destination=estimated, **common)
            self.assertGreater(measured.stat().st_size, 1000)
            self.assertGreater(estimated.stat().st_size, 1000)
            first_jump = next(c["startMs"]/1000 for c in cues
                              if direction_for(c["text"])["action"] == "jump")
            view = min(duration - .3, first_jump + .35)
            a, b = _frame(measured, view), _frame(estimated, view)
            self.assertEqual(a.size, (1280, 720))
            diff = ImageChops.difference(
                a.crop((185, 245, 555, 620)),
                b.crop((185, 245, 555, 620)))
            self.assertGreater(sum(ImageStat.Stat(diff).mean), .5)


    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak-ng") or shutil.which("espeak")),
                         "Real offline TTS and FFmpeg required")
    def test_full_offline_synthesized_audio_anchors_real_preview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan_path = root / "scene-plan.json"
            data = plan(
                topic="Original illustrated story of a fox",
                script=(SCRIPT + " ") * 4,
                duration=30, shot_seconds=6,
                character="An original red fox in a golden scarf")
            # Preserve the exact long scene narration so eSpeak synthesizes
            # enough distinct caption phrases to anchor three actions.
            data["scenes"][0]["narration"] = SCRIPT
            plan_path.write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8")
            preview = build_preview(
                plan_path=plan_path, output=root / "preview",
                limit=1, style="cartoon", language="en",
                voice="espeak", caption_timing="audio",
                soundtrack="none", transition="cut")
            saved = load_plan(plan_path)["scenes"][0]
            self.assertGreaterEqual(len(saved["captionSegments"]), 3)
            report = preview["render"]["actionTimeline"]
            self.assertEqual(report["audioAnchoredScenes"], 1)
            self.assertTrue(report["scenes"][0]["audioAnchored"])
            self.assertEqual(
                [p["action"] for p in report["scenes"][0]["phases"]],
                ["walk", "jump", "talk"])
            self.assertEqual(report["scenes"][0]["audioTimelineShiftMs"], 0)
            self.assertEqual(
                preview["render"]["captionCueAlignment"],
                "audio-derived-synthesized-phrases")
            self.assertTrue((root / "preview" / "preview.mp4").is_file())


if __name__ == "__main__":
    unittest.main()
