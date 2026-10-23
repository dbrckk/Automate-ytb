"""Regression: storyboard weather/action cues drive real MP4 visuals and safe cache."""
from __future__ import annotations

from pathlib import Path
import io
import json
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageChops, ImageStat

from automate_ytb.director import (direction_for, direct_scenes, validate_direction)
from automate_ytb.scene_plan import plan
from automate_ytb.episode import build_preview, create_local_art
from automate_ytb.production import load_plan, render, audit
from automate_ytb.animated_owl import render_motion_clip


def grab_frame(path: Path, time_sec: float) -> Image.Image:
    proc = subprocess.run(["ffmpeg", "-nostdin", "-v", "error",
                           "-ss", str(time_sec), "-i", str(path),
                           "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                          capture_output=True, check=True)
    with Image.open(io.BytesIO(proc.stdout)) as image:
        return image.convert("RGB")


def frame_difference(first: Image.Image, second: Image.Image, bounds: tuple):
    a, b = first.crop(bounds), second.crop(bounds)
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean)


class DirectionTests(unittest.TestCase):
    def test_weather_persists_until_author_explicitly_changes_it(self):
        scenes = [{"narration": "La chouette observe la pluie dans le jardin.",
                   "camera": "wide establishing"},
                  {"narration": "Elle cherche une fleur et sourit.",
                   "camera": "close-up"},
                  {"narration": "Au matin, le soleil apparaît.",
                   "camera": "medium"},
                  {"narration": "Le vent souffle soudain !",
                   "camera": "low-angle"}]
        actual = direct_scenes(scenes)
        self.assertEqual([s["weather"] for s in actual], ["rain","rain","day","wind"])
        self.assertEqual([s["shot"] for s in actual],
                         ["wide","closeup","medium","low"])
        self.assertEqual(actual[1]["emotion"], "happy")
        self.assertEqual(actual[3]["action"], "surprise")
        self.assertEqual(scenes[1]["narration"], "Elle cherche une fleur et sourit.")

    def test_rejects_invalid_direction_and_does_not_invent_weather(self):
        self.assertEqual(direction_for("Une chouette médite.")["weather"], "day")
        self.assertEqual(direction_for("The owl flies." )["action"], "fly")
        self.assertEqual(direction_for("La lune éclaire la forêt.")["weather"], "night")
        with self.assertRaisesRegex(ValueError,"direction"):
            validate_direction({"weather": "http://bad", "action":"idle"})
        with self.assertRaisesRegex(ValueError,"camera"):
            direction_for("Test",camera="evil injection")

    def test_original_narration_unchanged_and_timecodes_contiguous(self):
        original = " ".join([
            "Le vent souffle sur la colline.",
            "La chouette vole dans le ciel.",
            "Une pluie légère commence.",
            "Elle retourne vers son arbre.",
            "Au matin le soleil revient.",
        ])
        data = plan(topic="Une aventure originale",script=original,duration=30,
                    shot_seconds=6,character="Original purple owl with yellow scarf")
        self.assertEqual(" ".join(s["narration"] for s in data["scenes"]),original)
        self.assertEqual(data["sceneCount"],5)
        for before, after in zip(data["scenes"],data["scenes"][1:]):
            self.assertEqual(before["endMs"], after["startMs"])
        self.assertEqual([s["direction"]["weather"] for s in data["scenes"]],
                         ["wind","wind","rain","rain","day"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/ffprobe needed for frame verification")
    def test_weather_rain_is_animated_but_night_sky_is_static(self):
        with tempfile.TemporaryDirectory(prefix="director-scenes-") as tmp:
            root=Path(tmp)
            rain = root/"rain.mp4"
            night=root/"night.mp4"
            base=dict(topic="Une histoire originale",scene_count=2,
                      style="cartoon",duration=2,width=1280,height=720,fps=24)
            render_motion_clip(narration="La chouette vole sous la pluie.",
                               scene_index=1,destination=rain,
                               direction=direction_for("La chouette vole sous la pluie.",
                                                       camera="wide establishing"),**base)
            render_motion_clip(narration="La chouette contemple la lune.",
                               scene_index=2,destination=night,
                               direction=direction_for("La chouette contemple la lune.",
                                                       camera="wide establishing"),**base)
            rainy_1,rainy_2=grab_frame(rain,.25),grab_frame(rain,1.25)
            dark_1,dark_2=grab_frame(night,.25),grab_frame(night,1.25)
            sky=(980,60,1200,85)
            self.assertGreater(frame_difference(rainy_1,rainy_2,sky),.4)
            self.assertLess(frame_difference(dark_1,dark_2,sky),.6)
            self.assertGreater(frame_difference(rainy_1,dark_1,(700,120,840,210)),10)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/ffprobe needed for render")
    def test_directed_scene_is_rendered_and_reused_safely(self):
        with tempfile.TemporaryDirectory(prefix="director-preview-") as tmp:
            root=Path(tmp)
            scene_plan=root/"plan.json"
            script=" ".join([
                "La chouette vole sous la pluie.",
                "Elle trouve une fleur curieuse.",
                "Une rafale de vent la surprend.",
                "Pendant la nuit, elle observe les étoiles.",
                "Au matin, elle revient chez elle.",
            ])
            data=plan(topic="Voyage d'une chouette originale",script=script,
                      duration=30,character="A brand new original owl",shot_seconds=6)
            scene_plan.write_text(json.dumps(data,ensure_ascii=False))
            output=root/"out"
            first=build_preview(plan_path=scene_plan,output=output,
                                style="cartoon",voice="none",limit=1)
            self.assertEqual(first["render"]["animatedOwlScenes"],1)
            self.assertEqual(first["render"]["director"]["counts"]["weather"],
                             {"rain": 1})
            self.assertEqual(first["render"]["director"]["directedScenes"],1)
            self.assertEqual(first["art"]["created"],1)
            self.assertEqual(audit(scene_plan,limit=1)["counts"]["ready"],1)
            second=build_preview(plan_path=scene_plan,output=output,
                                 style="cartoon",voice="none",limit=1)
            self.assertEqual(second["art"]["reused"],1)
            self.assertEqual(first["render"]["videoSha256"],
                             second["render"]["videoSha256"])
            altered=load_plan(scene_plan)
            altered["scenes"][0]["direction"]["weather"]="night"
            scene_plan.write_text(json.dumps(altered,ensure_ascii=False))
            with self.assertRaisesRegex(ValueError,"another story/character"):
                create_local_art(scene_plan,style="cartoon",limit=1)
            with self.assertRaisesRegex(ValueError,"brief changed"):
                render(plan_path=scene_plan,output=root/"unsafe",limit=1)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg/ffprobe needed for legacy render")
    def test_legacy_scene_plan_without_direction_still_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"plan.json"
            data=plan(topic="Le voyage de la chouette",
                      script="Un. Deux. Trois. Quatre. Cinq.",
                      duration=30,character="An original purple owl",shot_seconds=6)
            for scene in data["scenes"]:
                scene.pop("direction")
            source.write_text(json.dumps(data))
            summary=build_preview(plan_path=source,output=root/"video",
                                  voice="none",limit=1)
            self.assertEqual(summary["render"]["animatedOwlScenes"],1)
            self.assertFalse(summary["publicationApproved"])


if __name__ == "__main__":
    unittest.main()
