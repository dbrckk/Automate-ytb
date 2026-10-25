"""Scene dissolves must change real MP4 pixels without changing scene timing."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.episode import build_preview
from automate_ytb.production import load_plan
from automate_ytb.quality import check
from automate_ytb.scene_plan import plan
from automate_ytb.transitions import transition_clips


def _frame(path: Path, t: float) -> tuple[int, int, int]:
    result = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(t),
         "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "-"],
        capture_output=True, timeout=90, check=True)
    with Image.open(io.BytesIO(result.stdout)) as frame:
        return frame.convert("RGB").getpixel((frame.width // 2, frame.height // 2))


def _duration(path: Path) -> float:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, timeout=30, check=True)
    return float(p.stdout)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Real FFmpeg and ffprobe required")
class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="transition-test-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _solid_clip(self, color: str, name: str, duration: float) -> Path:
        result = self.root / name
        subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
             f"color=c={color}:s=320x180:r=24:d={duration}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-y", str(result)],
            check=True, capture_output=True, timeout=30)
        return result

    def test_dissolve_is_visible_and_preserves_exact_frame_count(self):
        red = self._solid_clip("red", "red.mp4", 1.0)
        blue = self._solid_clip("blue", "blue.mp4", 2.0)
        files, report = transition_clips(
            [red, blue], cache=self.root / "cache", fps=24,
            durations=[1.0, 2.0], mode="dissolve")
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["timelineShiftMs"], 0)
        self.assertEqual(_duration(files[1]), 2.0)
        before = _frame(files[1], 0.0)
        during = _frame(files[1], 0.18)
        after = _frame(files[1], 0.70)
        self.assertGreater(before[0], before[2] + 50, before)
        self.assertGreater(after[2], after[0] + 50, after)
        self.assertGreater(during[0], after[0] + 10, during)
        self.assertGreater(during[2], before[2] + 10, during)
        original = files[1].read_bytes()
        second, report2 = transition_clips(
            [red, blue], cache=self.root / "cache", fps=24,
            durations=[1.0, 2.0], mode="dissolve")
        self.assertEqual(second, files)
        self.assertEqual(second[1].read_bytes(), original)
        self.assertEqual(report2, report)

    def test_cut_keeps_original_clips_and_rejects_invalid_inputs(self):
        red = self._solid_clip("red", "red.mp4", 1.0)
        blue = self._solid_clip("blue", "blue.mp4", 1.0)
        clips, report = transition_clips(
            [red, blue], cache=self.root / "cache", fps=24,
            durations=[1.0, 1.0], mode="cut")
        self.assertEqual(clips, [red, blue])
        self.assertEqual(report["count"], 0)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            transition_clips([red], cache=self.root, fps=24,
                             durations=[1], mode="wipe;unsafe")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            transition_clips([red, blue], cache=self.root, fps=24,
                             durations=[1], mode="dissolve")

    def test_two_scene_preview_keeps_srt_scene_timecodes_and_quality(self):
        scene_plan = self.root / "scene-plan.json"
        script = " ".join([
            "La forêt s'éveille au lever du soleil.",
            "Un renard découvre une nouvelle clairière.",
            "Les fleurs dansent dans le vent.",
            "Un papillon s'envole dans le ciel.",
            "Le renard retourne chez lui le soir."
        ])
        data = plan(topic="Une aventure forestière originale",
                    script=script, character="A red original fox with golden scarf",
                    duration=30, shot_seconds=6)
        scene_plan.write_text(json.dumps(data), encoding="utf-8")
        out = self.root / "preview"
        response = build_preview(plan_path=scene_plan, output=out, limit=2,
                                 style="documentary", voice="none",
                                 transition="dissolve")
        report = response["render"]["transitions"]
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["timelineShiftMs"], 0)
        planned = load_plan(scene_plan)["scenes"][:2]
        self.assertAlmostEqual(_duration(Path(response["render"]["video"])),
                               planned[-1]["endMs"] / 1000, delta=.10)
        srt = (out / "draft-captions.srt").read_text(encoding="utf-8")
        boundary = planned[0]["endMs"]
        from automate_ytb.captions import srt_time
        self.assertIn(srt_time(boundary), srt)
        qa = check(plan=scene_plan, output=out,
                   expected_voice="none", expected_soundtrack="none")
        self.assertEqual(qa["status"], "passed", qa["errors"])


if __name__ == "__main__":
    unittest.main()
