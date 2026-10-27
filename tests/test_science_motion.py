"""Original science infographic drawings and end-to-end MP4 regression."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import ImageChops

from automate_ytb.science_motion import (
    SCIENCE_VERSION, ScienceScene, scene_mode, art_brief_sha256)


class ScienceMotionTests(unittest.TestCase):
    def test_story_controls_distinct_original_modes_and_real_motion(self):
        self.assertIn("science-motion-v1", SCIENCE_VERSION)
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
