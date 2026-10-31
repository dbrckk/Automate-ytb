"""True 9:16 science Shorts regression, original compositing and actual H.264."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageChops

from automate_ytb.captions import (
    caption_phrases, timed_cues_for_scene,
    subtitles_for_scenes, srt_time,
)
from automate_ytb.science_portrait import (
    PORTRAIT_SIZE, PORTRAIT_VERSION, PortraitScienceScene, _fit_lines, _ocean_currents,
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

    def test_burned_text_uses_exact_audio_derived_srt_cues(self):
        narration = (
            "The ocean expands toward the coast. "
            "Winds begin to circle the planet. "
            "New waves move across the water.")
        phrases = caption_phrases(narration)
        self.assertGreaterEqual(len(phrases), 2)
        start, length = 12000, 6000
        step = length // len(phrases)
        markers = [
            {"text": phrase,
             "startMs": start + i*step,
             "endMs": start + (i+1)*step if i+1<len(phrases)
                       else start+length}
            for i, phrase in enumerate(phrases)
        ]
        scene = {
            "narration": narration, "startMs": start,
            "endMs": start + length, "captionSegments": markers,
        }
        srt, report = subtitles_for_scenes(
            [scene], use_audio_boundaries=True)
        self.assertEqual(report["cueCount"], len(phrases))
        shot = PortraitScienceScene(
            topic="What if Earth's oceans changed?", narration=narration,
            scene_index=3, scene_start_ms=start,
            caption_segments=markers)
        crops = []
        for i, phrase in enumerate(phrases):
            t = (markers[i]["startMs"]-start+100)/1000
            self.assertEqual(' '.join(shot.active_caption(t, length/1000).split()), phrase)
            stamp = srt_time(markers[i]["startMs"])
            self.assertIn(stamp, srt)
            if i < 2:
                crops.append(
                    shot.frame(t, length/1000).crop((65,1522,1015,1722)))
        self.assertIsNotNone(ImageChops.difference(
            crops[0], crops[1]).getbbox())
        self.assertEqual(' '.join(shot.active_caption(6, 6).split()), phrases[-1])

    def test_estimated_short_text_matches_srt_without_pretending_word_alignment(self):
        narration = (
            "The first wave arrives. "
            "The second wave moves faster. "
            "The third wave crosses the ocean.")
        scene = {"narration": narration, "startMs": 2000, "endMs": 8000}
        cues = timed_cues_for_scene(scene)
        srt, report = subtitles_for_scenes([scene])
        self.assertEqual(report["method"], "estimated-proportional-phrases")
        self.assertFalse(report["wordLevelAligned"])
        self.assertGreaterEqual(len(cues), 2)
        shot = PortraitScienceScene(
            topic="Earth ocean currents", narration=narration,
            scene_index=4, scene_start_ms=2000)
        for cue in cues:
            local_time = (cue["startMs"]-2000+.1)/1000
            self.assertEqual(
                shot.active_caption(local_time, 6), cue["text"])
            self.assertIn(
                srt_time(cue["startMs"])+" --> "+srt_time(cue["endMs"]),
                srt)
        invalid = PortraitScienceScene(
            topic="Earth ocean currents", narration=narration,
            scene_index=4, scene_start_ms=2000,
            caption_segments=[{"text": "wrong", "startMs":2000,
                               "endMs":8000}])
        with self.assertRaises(ValueError):
            invalid.active_caption(0, 6)
        with self.assertRaises(ValueError):
            PortraitScienceScene(
                topic="Earth ocean currents", narration=narration,
                scene_index=4, scene_start_ms=True)

    def test_original_mobile_text_never_loses_words_or_characters(self):
        self.assertIn("lossless-text", PORTRAIT_VERSION)
        # Long natural language, including technical identifiers, must be
        # displayed completely rather than silently shortened with ellipses.
        title = "What if the Earth and its oceans changed direction unexpectedly?"
        rows, font_size = _fit_lines(
            title, size=47, width=860, maximum=2, minimum=22)
        self.assertGreaterEqual(font_size, 22)
        self.assertLessEqual(len(rows), 2)
        self.assertEqual(
            "".join(rows).replace(" ", ""),
            "".join(title.split()))
        technical = "AtmosphericSpectroscopyMeasurements" * 2
        rows, font_size = _fit_lines(
            technical, size=31, width=360, maximum=3, minimum=22)
        self.assertGreaterEqual(font_size, 22)
        self.assertEqual("".join(rows).replace(" ", ""), technical)
        # The layout is cached but its output is deterministic.
        self.assertEqual((rows, font_size), _fit_lines(
            technical, size=31, width=360, maximum=3, minimum=22))

    def test_unreadable_text_rejected_without_silent_truncation(self):
        with self.assertRaisesRegex(ValueError, "cannot fit safely"):
            _fit_lines("W"*700, size=31, width=842,
                       maximum=3, minimum=22)
        with self.assertRaisesRegex(ValueError, "cannot fit safely"):
            PortraitScienceScene(
                topic="Earth " + "W"*170,
                narration="The ocean moves.", scene_index=1)
        with self.assertRaisesRegex(ValueError, "cannot fit safely"):
            scene = PortraitScienceScene(
                topic="The Earth changes", narration="W"*700,
                scene_index=1)
            scene.active_caption(0, 1)

    def test_portrait_text_layout_matches_actual_mobile_safe_band(self):
        scene = PortraitScienceScene(
            topic="Why Earth's oceans are moving in very different directions",
            narration="The ocean slowly moves across the entire planet.",
            scene_index=1)
        frame = scene.frame(.1, 1)
        self.assertEqual(frame.size, PORTRAIT_SIZE)
        for rows, font_size, maximum_width in (
                (*scene._title_layout, 860),
                (*scene._caption_layouts[scene.active_caption(.1,1)], 842)):
            self.assertLessEqual(len(rows), 3)
            probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            from automate_ytb.science_motion import _font
            for row in rows:
                self.assertLessEqual(
                    probe.textbbox((0, 0), row,
                                   font=_font(font_size, True))[2],
                    maximum_width)

    def test_ocean_currents_have_multiple_visible_continuous_flow_lanes(self):
        self.assertIn("ocean-flow", PORTRAIT_VERSION)
        def flow(time):
            canvas = Image.new("RGBA", PORTRAIT_SIZE, (8, 28, 49, 255))
            pen = ImageDraw.Draw(canvas, "RGBA")
            _ocean_currents(pen, time)
            return canvas.crop((40, 930, 1035, 1470))
        frame0 = flow(0.0)
        frame1 = flow(1/30)
        frame2 = flow(2/30)
        self.assertEqual(frame0.size, (995, 540))
        self.assertEqual(frame1.tobytes(), flow(1/30).tobytes())
        self.assertIsNotNone(ImageChops.difference(frame0, frame1).getbbox())
        self.assertIsNotNone(ImageChops.difference(frame1, frame2).getbbox())
        # Different flow streams have independent animated particles and
        # displaced loop elements, not a static pictorial background.
        for y in (1033, 1197, 1361):
            row = frame1.crop((20, y-930-25, 970, y-930+25))
            background = Image.new("RGBA", row.size, (8, 28, 49, 255))
            self.assertIsNotNone(ImageChops.difference(
                row, background).getbbox())

    def test_ocean_scene_remains_native_portrait_with_safe_overlay_bands(self):
        scene = PortraitScienceScene(
            topic="What if Earth's ocean currents changed?",
            narration="The ocean currents move across the water.",
            scene_index=5)
        before = scene.frame(0, 1)
        after = scene.frame(1/30, 1)
        self.assertEqual(before.size, (1080, 1920))
        self.assertFalse(scene._globes)
        self.assertIsNotNone(ImageChops.difference(
            before.crop((90, 990, 990, 1420)),
            after.crop((90, 990, 990, 1420))).getbbox())
        self.assertEqual(
            before.crop((65, 1522, 1015, 1722)).tobytes(),
            after.crop((65, 1522, 1015, 1722)).tobytes())

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

    def test_fluid_globe_changes_on_every_intermediate_frame_with_bounded_cache(self):
        self.assertIn("fluid-planet", PORTRAIT_VERSION)
        self.assertIn("lossless-text", PORTRAIT_VERSION)
        scene = PortraitScienceScene(
            topic="Why the Earth rotates",
            narration="The Earth keeps moving.", scene_index=1)
        first = scene._planet_at(0, size=72)
        halfway = scene._planet_at(.2, size=72)
        second = scene._planet_at(.4, size=72)
        self.assertEqual(len(scene._globes), 2)
        self.assertIn((0, 72), scene._globes)
        self.assertIn((1, 72), scene._globes)
        self.assertEqual(
            halfway.tobytes(), Image.blend(first, second, .5).tobytes())
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"), halfway.convert("RGB")).getbbox())
        self.assertIsNotNone(ImageChops.difference(
            halfway.convert("RGB"), second.convert("RGB")).getbbox())
        self.assertEqual(
            halfway.tobytes(), scene._planet_at(.2, size=72).tobytes())
        other_size = scene._planet_at(0, size=73)
        self.assertNotEqual(other_size.size, first.size)
        self.assertIn((0, 73), scene._globes)
        self.assertEqual(len(scene._globes), 3)
        # The third cache entry remains legitimate when the first twelve
        # interpolated video frames are rendered; no extra pose projection.
        for n in range(1, 12):
            scene._planet_at(n/30, size=72)
        self.assertEqual(len(scene._globes), 3)
        for second in (5, 13, 29, 42, 60):
            scene._planet_at(second, size=72)
            self.assertLessEqual(len(scene._globes), 6)

    def test_globe_interpolation_rejects_unsafe_input(self):
        shot = PortraitScienceScene(
            topic="Earth in motion",
            narration="Earth continues rotating.", scene_index=1)
        for t in (-1, float("nan"), float("inf")):
            with self.subTest(t=t), self.assertRaises(ValueError):
                shot._planet_at(t, size=72)
        for size in (0, 15, 1081, True):
            with self.subTest(size=size), self.assertRaises(ValueError):
                shot._planet_at(.1, size=size)

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
            data["scenes"][0]["endMs"] = 1000
            data["targetDurationSeconds"] = 1.0
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
