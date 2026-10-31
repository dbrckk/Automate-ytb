"""Audio-anchored 2D motion graphics in the actual Solar Storm FFmpeg pipeline."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageStat

from production.solar_storm.motion_graphics import (
    CUES, apply_motion_graphics, build_motion_graphics,
)


def narrated_scenes():
    return [{"start": i * 4.25, "end": i * 4.25 + 4.0,
             "text": CUES[i][1]} for i in range(6)]


def recognized_anchors():
    return [{"word": keyword, "start": i * 4.25 + 0.65,
             "end": i * 4.25 + 1.0, "recognized": True}
            for i, (keyword, _, _) in enumerate(CUES)]


class VoiceTimedMotionTests(unittest.TestCase):
    def test_all_six_scenes_render_original_timecoded_animated_events(self):
        events, report = build_motion_graphics(narrated_scenes(), recognized_anchors())
        self.assertEqual(report["spoken_cues"], 6)
        self.assertEqual(report["verified_word_cues"], 6)
        self.assertGreater(report["events"], 35)
        self.assertEqual(len(events), report["events"])
        self.assertTrue(all(line.startswith("Dialogue: ") for line in events))
        self.assertTrue(all("\\fad(" in line for line in events))
        self.assertTrue(any("\\move(" in x for x in events))
        self.assertTrue(any("\\p1" in x for x in events))
        self.assertFalse(report["editorial_approved"])
        self.assertEqual([cue["word"] for cue in report["cue_timeline"]],
                         [x[0] for x in CUES])
        self.assertTrue(all(cue["source"] == "verified_acoustic_word"
                            for cue in report["cue_timeline"]))

    def test_unrecognized_acoustic_words_are_reported_as_fallback(self):
        words = recognized_anchors()
        words[2]["recognized"] = False
        _, report = build_motion_graphics(narrated_scenes(), words)
        self.assertEqual(report["verified_word_cues"], 5)
        self.assertEqual(report["cue_timeline"][2]["source"],
                         "narration_scene_fallback")
        self.assertEqual(report["cue_timeline"][2]["word"], "plasma")

    def test_wrong_scene_count_and_bad_timeline_cannot_render(self):
        with self.assertRaisesRegex(ValueError, "exactly 6"):
            build_motion_graphics(narrated_scenes()[:5], recognized_anchors())
        scenes = narrated_scenes()
        scenes[3]["start"] = scenes[2]["start"]
        with self.assertRaisesRegex(ValueError, "spoken scene"):
            build_motion_graphics(scenes, recognized_anchors())

    def test_real_caption_context_does_not_duplicate_new_acoustic_hud(self):
        # A real decoded 35s 9:16 MP4 showed repeated EARTH'S MAGNETIC
        # SHIELD, NASA / SDO and AURORAS captions near the upper left.
        # The new Motion layer replaces those legacy context titles while
        # actual Voice subtitles and timestamps must survive unchanged.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.ass"
            original = (
                "[Script Info]\nPlayResX: 1080\nPlayResY: 1920\n"
                "[V4+ Styles]\nStyle: Context,DejaVu Sans,39\n"
                "[Events]\n"
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
                "MarginV, Effect, Text\n"
                "Dialogue: 1,0:00:18.35,0:00:21.40,Context,,0,0,0,,"
                "EARTH'S MAGNETIC SHIELD\n"
                "Dialogue: 4,0:00:18.50,0:00:19.50,Voice,,0,0,0,,"
                "our magnetic field\n"
                "Dialogue: 1,0:00:05.23,0:00:09.22,Context,,0,0,0,,"
                "EXTREME ULTRAVIOLET - NASA / SDO\n"
                "Dialogue: 1,0:00:25.00,0:00:27.00,Context,,0,0,0,,"
                "AURORAS - SPACE WEATHER\n"
            )
            path.write_text(original, encoding="utf-8")
            report = apply_motion_graphics(
                path, narrated_scenes(), recognized_anchors())
            composed = path.read_text(encoding="utf-8")
            self.assertEqual(report["suppressed_legacy_context_titles"], 3)
            self.assertEqual(composed.count("EARTH'S MAGNETIC SHIELD"), 1)
            self.assertEqual(composed.count("NASA / SDO"), 1)
            self.assertNotIn("Dialogue: 1,0:00:18.35", composed)
            self.assertNotIn("EXTREME ULTRAVIOLET -", composed)
            self.assertNotIn("AURORAS - SPACE WEATHER", composed)
            self.assertIn(
                "Dialogue: 4,0:00:18.50,0:00:19.50,Voice,,0,0,0,,"
                "our magnetic field", composed)
            self.assertEqual(composed.count("Style: Motion,"), 1)
            self.assertEqual(
                composed.count("Dialogue: "), report["events"] + 1)
            self.assertFalse(report["editorial_approved"])

    def test_ass_style_and_vector_effects_are_only_added_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.ass"
            path.write_text(
                "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
                "\n[V4+ Styles]\n"
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n"
                "Style: Voice,DejaVu Sans,48,&H00FFFFFF,&H00FFFFFF,&H00000000,"
                "&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,75,75,300,1\n"
                "\n[Events]\n"
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
                "MarginV, Effect, Text\n",
                encoding="utf-8")
            report = apply_motion_graphics(path, narrated_scenes(),
                                           recognized_anchors())
            composed = path.read_text(encoding="utf-8")
            self.assertEqual(composed.count("Style: Motion,"), 1)
            self.assertEqual(composed.count("[Events]"), 1)
            self.assertEqual(composed.count("Dialogue: "), report["events"])
            self.assertIn("CORONAL MASS EJECTION", composed)
            self.assertIn("SCHEMATIC FIELD RESPONSE", composed)
            self.assertNotIn("SCENE 1", composed)
            with self.assertRaisesRegex(ValueError, "already composited"):
                apply_motion_graphics(path, narrated_scenes(), recognized_anchors())

            # Validate actual libass interpretation on a real decoded frame.
            if shutil.which("ffmpeg") is None:
                return
            frame = Path(tmp) / "motion.png"
            cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                   "color=c=0x101820:s=1080x1920:r=30",
                   "-vf", f"ass=filename={path},select=gte(t\\,0.87)",
                   "-frames:v", "1", "-update", "1", str(frame)]
            subprocess.run(cmd, check=True, timeout=35)
            with Image.open(frame) as image:
                self.assertEqual(image.size, (1080, 1920))
                hud = image.convert("RGB").crop((65, 195, 550, 335))
                # This is the real burned-in animated HUD, not merely an
                # ASS file accepted syntactically by libass.
                self.assertGreater(max(x[1] for x in ImageStat.Stat(hud).extrema),
                                   120, "Acoustic graphics did not reach MP4 frame")


if __name__ == "__main__":
    unittest.main()
