"""A genuinely new rainbow-chase episode with five authored optical actions."""
from __future__ import annotations

import re
from pathlib import Path
import unittest

from PIL import ImageChops

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.science_rainbow import BEATS, classify, supports_topic
from automate_ytb.scene_plan import beats


ROOT=Path(__file__).resolve().parents[1]
TOPIC="Why Can't You Reach the End of a Rainbow?"
WORKFLOW=ROOT/".github/workflows/rainbow-chase-original-short.yml"
DELIVERY=ROOT/".github/workflows/science-preview-download.yml"


def production_sentences() -> tuple[str, ...]:
    raw=WORKFLOW.read_text(encoding="utf-8")
    matched=re.search(
        r"(?m)^      original_script: >-\n((?:^        .+\n){5})",raw)
    if matched is None:
        raise AssertionError("Original five-scene script missing from real video workflow")
    return tuple(beats(" ".join(row.strip() for row in
                                 matched.group(1).splitlines())))


class RainbowChaseOriginalVideoTests(unittest.TestCase):
    def test_original_episode_is_distinct_and_semantically_correct(self):
        self.assertTrue(supports_topic(TOPIC))
        self.assertNotEqual(TOPIC,"How Do Rainbows Form?")
        scripts=production_sentences()
        self.assertEqual(len(scripts),5)
        self.assertEqual(tuple(classify(TOPIC,s) for s in scripts),BEATS)
        self.assertEqual(len(set(scripts)),5)
        self.assertTrue("when you move" in scripts[-1].lower())
        self.assertTrue("observer" in scripts[-1].lower())
        self.assertTrue("looks perfectly white" in scripts[0])
        self.assertFalse(any("magic" in s.lower() for s in scripts))

    def test_real_portrait_subjects_are_dynamic_and_caption_safe(self):
        for i,(beat,phrase) in enumerate(zip(BEATS,production_sentences()),1):
            with self.subTest(beat=beat):
                scene=PortraitScienceScene(
                    topic=TOPIC,narration=phrase,scene_index=i)
                self.assertEqual(scene.rainbow_beat,beat)
                self.assertTrue(scene.english)
                early=scene.frame(.3,8.)
                later=scene.frame(1.4,8.)
                self.assertEqual(early.size,(1080,1920))
                self.assertEqual(early.mode,"RGB")
                self.assertIsNotNone(ImageChops.difference(
                    early.crop((80,695,1000,1480)),
                    later.crop((80,695,1000,1480))).getbbox())
                # Stable subtitle layout at unchanged narration text.
                self.assertEqual(
                    early.crop((65,1522,1015,1722)).tobytes(),
                    later.crop((65,1522,1015,1722)).tobytes())

    def test_production_is_real_kokoro_and_release_is_strictly_gated(self):
        original=WORKFLOW.read_text(encoding="utf-8")
        delivery=DELIVERY.read_text(encoding="utf-8")
        for expected in (
            'name: Produce original rainbow-chase science Short',
            "topic: \"Why Can't You Reach the End of a Rainbow?\"",
            "voice: kokoro","voice_name: af_heart","voice_style: natural",
            "duration_seconds: 33","shot_seconds: 6.6",
            "resolution: shorts","render_profile: high",
            "caption_timing: audio",
            'uses: ./.github/workflows/one-click-preview.yml',
        ):
            self.assertIn(expected,original)
        self.assertIn('if: github.event_name != \'pull_request\'',original)
        self.assertIn('"Produce original rainbow-chase science Short"',delivery)
        self.assertIn('$slug == "rainbow-chase"',delivery)
        self.assertIn('[[ "$PREVIEW_SLUG" == "rainbow-chase"',delivery)
        self.assertIn('cmp -s "delivered/${PREVIEW_SLUG}.mp4"',delivery)
        self.assertIn('scripts/update_video_history.py',delivery)
        self.assertIn('github.event.workflow_run.conclusion == \'success\'',delivery)


if __name__=="__main__":
    unittest.main()
