"""Original science infographic drawings and end-to-end MP4 regression."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops

from automate_ytb.science_motion import (
    SCIENCE_VERSION, ScienceScene, scene_mode, art_brief_sha256,
    render_motion_clip, FULL_HD)


class ScienceMotionTests(unittest.TestCase):
    def test_story_controls_distinct_original_modes_and_real_motion(self):
        self.assertIn("science-motion-v4", SCIENCE_VERSION)
        cues = {
            "La planète continue sa rotation.": "orbital",
            "L'air et le vent continuent leur déplacement.": "atmosphere",
            "Les océans génèrent de gigantesques vagues.": "ocean",
            "Le jour et la nuit changent.": "daylight",
        }
        for script, mode in cues.items():
            with self.subTest(mode=mode):
                self.assertEqual(scene_mode(script),mode)
                shot=ScienceScene(topic="Et si la Terre cessait de tourner ?",
                                  narration=script,scene_index=1)
                frame=shot.frame(.1,2)
                moved=shot.frame(.9,2)
                self.assertEqual(frame.size,(1280,720))
                self.assertIsNotNone(ImageChops.difference(frame,moved).getbbox())
                self.assertEqual(frame.tobytes(),shot.frame(.1,2).tobytes())
        with self.assertRaises(ValueError):
            scene_mode(None)
        with self.assertRaises(ValueError):
            ScienceScene(topic="A",narration="",scene_index=1)
        with self.assertRaisesRegex(ValueError,"Earth/ocean"):
            ScienceScene(topic="A story about a purple owl",
                         narration="The owl goes to sleep.",scene_index=1)

    def test_long_shot_globe_keeps_rotating_after_previous_five_second_limit(self):
        shot = ScienceScene(
            topic="Why Earth keeps rotating",
            narration="The Earth rotates under the stars.",
            scene_index=1)
        self.assertEqual(len(shot._globes), 0)
        first = shot._globe_at(4.9)
        later = shot._globe_at(6.5)
        self.assertIsNotNone(ImageChops.difference(first.convert('RGB'), later.convert('RGB')).getbbox())
        self.assertEqual(shot._globe_at(6.5).tobytes(), later.tobytes())
        self.assertIn(int(6.5 * 2.5), shot._globes)
        self.assertNotIn(11, shot._globes)
        # The scene continues to change through 6 seconds, not just the
        # moving stars or animated camera while the planet is frozen.
        for instant in (7.1, 8.1, 9.1, 10.1, 11.1, 12.1,
                        13.1, 14.1, 15.1, 16.1):
            shot._globe_at(instant)
            self.assertLessEqual(len(shot._globes), 8)
        self.assertEqual(shot.frame(6.1, 7).size, (1280, 720))

    def test_ocean_atmosphere_do_not_allocate_globes(self):
        common = dict(topic="What if Earth's oceans changed?", scene_index=2)
        with patch("automate_ytb.science_motion._planet",
                   side_effect=AssertionError("Unneeded sphere render")):
            for narration in (
                "The oceans begin to move.",
                "The wind and atmosphere keep moving."):
                scene = ScienceScene(narration=narration, **common)
                self.assertEqual(scene._globes, {})
                self.assertEqual(scene.frame(.4, 1).size, (1280, 720))
                self.assertEqual(scene._globes, {})

    def test_full_hd_is_drawn_directly_not_enlarged_from_hd(self):
        # Native coordinates, line thickness, text and planet diameter are
        # rasterized at 1920x1080, without enlarging pre-rendered 720p pixels.
        kwargs = dict(
            topic="Why Earth rotates",
            narration="The Earth spins under the bright stars.",
            scene_index=2)
        hd = ScienceScene(**kwargs)
        high = ScienceScene(**kwargs, size=FULL_HD)
        hd_image = hd.frame(.4, 1)
        high_image = high.frame(.4, 1)
        self.assertEqual(hd_image.size, (1280, 720))
        self.assertEqual(high_image.size, (1920, 1080))
        self.assertEqual(high.base.size, FULL_HD)
        self.assertEqual(high._globe_at(.4).size,
                         (round(408*1.5)+2*round(28*1.5),)*2)
        resized = hd_image.resize(FULL_HD, Image.Resampling.LANCZOS)
        self.assertIsNotNone(
            ImageChops.difference(high_image, resized).getbbox())
        self.assertEqual(high.frame(.4, 1).tobytes(), high_image.tobytes())
        with self.assertRaises(ValueError):
            ScienceScene(**kwargs, size=(1024, 768))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Native full-HD requires actual FFmpeg")
    def test_full_hd_encoder_receives_1920_source_frames(self):
        with tempfile.TemporaryDirectory() as temp:
            mp4 = Path(temp) / "science1080.mp4"
            render_motion_clip(
                topic="Why Earth rotates",
                narration="The Earth moves.", scene_index=1, scene_count=1,
                style="science", duration=.25, width=1920, height=1080,
                fps=24, destination=mp4)
            self.assertGreater(mp4.stat().st_size, 2000)
            detail = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=codec_name,width,height",
                 "-of", "json", str(mp4)], check=True,
                capture_output=True, text=True, timeout=40)
            stream=json.loads(detail.stdout)["streams"][0]
            self.assertEqual((stream["width"], stream["height"]),
                             (1920, 1080))
            self.assertEqual(stream["codec_name"], "h264")

    def test_art_fingerprint_is_bound_to_the_authored_scene(self):
        common=dict(topic="Why Earth rotates",narration="The Earth spins.",
                    scene_id="scene-001",character="Original graphic astronomy",
                    style="science")
        a=art_brief_sha256(**common)
        self.assertNotEqual(a,art_brief_sha256(**{**common,
                            "narration":"The ocean moves."}))
        with self.assertRaises(ValueError):
            art_brief_sha256(**{**common,"style":"cartoon"})

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "Actual MP4 encoding requires FFmpeg")
    def test_real_reviewed_science_style_renders_30fps_video(self):
        from automate_ytb.scene_plan import plan
        from automate_ytb.episode import create_local_art
        from automate_ytb.production import render
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            data=plan(topic="What if Earth stopped rotating?",
                      script=("The atmosphere would keep moving. "
                              "The oceans would continue moving."),
                      duration=30,shot_seconds=15,
                      character="Original astronomy graphics")
            # A short but schema-valid single scene exercises the entire
            # rights -> original PNG -> animated MP4 path in a cheap CI test.
            data["scenes"]=data["scenes"][:1]
            data["sceneCount"]=1
            data["scenes"][0]["startMs"]=0
            data["scenes"][0]["endMs"]=1000
            data["targetDurationSeconds"]=1.0
            path=root/"scene-plan.json"
            path.write_text(json.dumps(data),encoding="utf-8")
            art=create_local_art(path,style="science")
            self.assertEqual(art["characterRig"],"original-science-v1")
            report=render(plan_path=path,output=root/"output",
                          resolution="720p",fps=30,
                          transition="cut")
            video=Path(report["video"])
            self.assertGreater(video.stat().st_size,2500)
            details=subprocess.run(
                ["ffprobe","-v","error","-select_streams","v:0",
                 "-show_entries","stream=codec_name,width,height,avg_frame_rate",
                 "-of","json",str(video)],
                check=True,capture_output=True,text=True,timeout=40)
            stream=json.loads(details.stdout)["streams"][0]
            self.assertEqual(stream["codec_name"],"h264")
            self.assertEqual((stream["width"],stream["height"]),(1280,720))
            self.assertEqual(stream["avg_frame_rate"],"30/1")


if __name__ == "__main__":
    unittest.main()
