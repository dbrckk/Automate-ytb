"""True 9:16 science Shorts regression, original compositing and actual H.264."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import ImageChops

from automate_ytb.science_portrait import (
    PORTRAIT_SIZE, PORTRAIT_VERSION, PortraitScienceScene,
)
from automate_ytb.scene_plan import plan
from automate_ytb.episode import create_local_art, build_preview
from automate_ytb.production import render


class ScienceShortsTests(unittest.TestCase):
    def test_native_mobile_safe_portrait_and_determinism(self):
        self.assertIn("1080x1920", PORTRAIT_VERSION)
        common = dict(topic="Et si la Terre s'arrêtait ?", scene_index=2)
        for narration in (
            "La Terre continue sa rotation.",
            "Les océans génèrent des vagues.",
            "Le vent agite l'atmosphère.",
            "Le jour et la nuit alternent.",
        ):
            with self.subTest(narration=narration):
                scene = PortraitScienceScene(narration=narration, **common)
                first = scene.frame(.2, 1)
                later = scene.frame(.9, 1)
                self.assertEqual(first.size, PORTRAIT_SIZE)
                self.assertEqual(first.mode, "RGB")
                self.assertIsNotNone(ImageChops.difference(first, later).getbbox())
                self.assertEqual(first.tobytes(), scene.frame(.2, 1).tobytes())
                # Safe title/caption regions are original portrait compositions,
                # not a 16:9 crop or an empty pillarbox.
                self.assertNotEqual(first.getpixel((90, 235)),
                                    first.getpixel((20, 235)))
                self.assertNotEqual(first.getpixel((90, 1555)),
                                    first.getpixel((20, 1555)))
                self.assertTrue(all(0 <= v <= 255
                                    for v in first.getpixel((540, 1000))))

    def test_portrait_globe_is_demand_loaded_and_cache_is_bounded(self):
        scene = PortraitScienceScene(topic="Why Earth rotates",
                                     narration="Earth keeps rotating.",
                                     scene_index=1)
        self.assertEqual(len(scene._globes), 0)
        p0 = scene._planet_at(.0)
        p9 = scene._planet_at(9.0)
        self.assertIsNotNone(ImageChops.difference(
            p0.convert("RGB"), p9.convert("RGB")).getbbox())
        for t in (12, 13, 14, 15, 16, 17, 18, 19):
            scene._planet_at(float(t))
            self.assertLessEqual(len(scene._globes), 6)
        no_planet = PortraitScienceScene(
            topic="Earth's oceans", narration="Ocean waves are moving.",
            scene_index=1)
        no_planet.frame(.5, 1.0)
        self.assertFalse(no_planet._globes)

    def test_wrong_topics_and_unsafe_times_are_rejected(self):
        with self.assertRaises(ValueError):
            PortraitScienceScene(topic="Black hole",
                                 narration="Stars explode", scene_index=1)
        with self.assertRaises(ValueError):
            PortraitScienceScene(topic="Earth", narration="", scene_index=1)
        s = PortraitScienceScene(topic="Earth science",
                                 narration="The Earth moves", scene_index=1)
        for t, duration in ((-1,1), (2,1), (0,181),
                            (float("nan"),1), (float("inf"),1)):
            with self.subTest(t=t, duration=duration), self.assertRaises(ValueError):
                s.frame(t,duration)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Real FFmpeg required")
    def test_approved_original_science_short_is_encoded_at_exact_9_by_16(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / "plan.json"
            data = plan(
                topic="What if Earth's oceans changed?",
                script=("The oceans rise gently. The wind keeps moving."),
                duration=30, shot_seconds=15,
                character="Original Earth science graphics")
            # Short valid scene for the production route, not a fake movie.
            data["scenes"] = data["scenes"][:1]
            data["sceneCount"] = 1
            data["scenes"][0]["startMs"] = 0
            data["scenes"][0]["endMs"] = 300
            data["targetDurationSeconds"] = .3
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "science style"):
                build_preview(plan_path=p, output=root/"bad",
                              style="cartoon", resolution="shorts",
                              voice="none")
            art = create_local_art(p, style="science")
            self.assertEqual(art["characterRig"], "original-science-v1")
            result = render(plan_path=p, output=root/"short",
                            resolution="shorts", fps=30, transition="cut")
            video = Path(result["video"])
            self.assertGreater(video.stat().st_size, 3000)
            self.assertEqual(result["resolution"], "shorts")
            self.assertEqual(result["fps"], 30)
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,codec_name,avg_frame_rate",
                "-of", "json", str(video)],
                capture_output=True, text=True, check=True, timeout=40)
            stream = json.loads(probe.stdout)["streams"][0]
            self.assertEqual((stream["width"],stream["height"]), PORTRAIT_SIZE)
            self.assertEqual(stream["codec_name"], "h264")
            self.assertEqual(stream["avg_frame_rate"], "30/1")
            self.assertFalse(result["publicationApproved"])


if __name__ == "__main__":
    unittest.main()
