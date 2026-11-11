"""New original 2026-11-11 ocean heat-engine Short: five distinct real scenes."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

from automate_ytb.scene_plan import beats
from automate_ytb.science_storyboards import BEATS, classify
from automate_ytb.science_portrait import PortraitScienceScene

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/ocean-heat-engine-original-short.yml"
TOPIC="Can Ocean Currents Move Heat Across the Planet?"


def lines():
    raw=WORKFLOW.read_text(encoding="utf-8")
    match=re.search(r"(?m)^      original_script: >-\n((?:^        .+\n){5})",raw)
    if match is None:
        raise AssertionError("Missing five source-authored lines in video workflow")
    return tuple(beats(" ".join(row.strip() for row in
                                match.group(1).splitlines())))


class OriginalOceanHeatEngineVideoTests(unittest.TestCase):
    def test_all_five_mechanisms_are_distinct_and_true(self):
        scripts=lines()
        self.assertEqual(len(scripts),5)
        self.assertEqual(len(set(scripts)),5)
        self.assertEqual(tuple(classify(TOPIC,s) for s in scripts),BEATS)
        self.assertIn("regional climates",scripts[-1])
        self.assertIn("rotation",scripts[2])

    def test_actual_source_scenes_are_native_animated(self):
        for i,(beat,script) in enumerate(zip(BEATS,lines()),1):
            with self.subTest(beat=beat):
                scene=PortraitScienceScene(
                    topic=TOPIC,narration=script,scene_index=i)
                self.assertEqual(scene.beat,beat)
                image=scene.frame(1.2,6.6)
                self.assertEqual(image.size,(1080,1920))
                self.assertEqual(image.mode,"RGB")

    def test_video_is_real_english_kokoro_full_resolution_and_retained(self):
        raw=WORKFLOW.read_text(encoding="utf-8")
        for expected in (
            "uses: ./.github/workflows/one-click-preview.yml",
            "voice: kokoro","voice_name: af_heart",
            "language: en","resolution: shorts",
            "render_profile: high","caption_timing: audio",
            "duration_seconds: 34",
            "soundtrack: ambient",
            "shot_seconds: 6.8",
            "branches: [main]",
        ):
            self.assertIn(expected,raw)
        release=(ROOT/".github/workflows/science-preview-download.yml").read_text(encoding="utf-8")
        self.assertIn("ocean-heat-engine",release)
        self.assertIn("Produce new original ocean heat-engine science Short",release)
        self.assertNotIn("placeholder",raw.lower())
        self.assertNotIn("publish-to-youtube",raw.lower())


if __name__=="__main__":
    unittest.main()
