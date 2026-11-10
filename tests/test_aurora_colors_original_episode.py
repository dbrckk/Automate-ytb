"""Production-original aurora color episode and verified permanent MP4 contract."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

from automate_ytb.science_aurora import classify, supports_topic
from automate_ytb.science_portrait import PortraitScienceScene

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/".github/workflows/aurora-colors-original-short.yml"
DELIVERY=ROOT/".github/workflows/science-preview-download.yml"
TITLE="Why Do Northern Lights Glow in Different Colors?"
EXPECTED=("solar_wind","magnetic_field","collisions","emission","curtains")


def episode_lines() -> tuple[str,...]:
    """Read the actual production script from the workflow, never a mock."""
    data=SOURCE.read_text(encoding="utf8")
    region=data.split("      original_script: >-\n",1)[1].split(
        "\n      character:",1)[0]
    return tuple(x.strip() for x in region.splitlines() if x.strip())


class OriginalAuroraColorEpisodeTests(unittest.TestCase):
    def test_five_causal_original_science_scenes_match_real_visual_engine(self):
        self.assertTrue(supports_topic(TITLE))
        scenes=episode_lines()
        self.assertEqual(len(scenes),5)
        self.assertEqual(tuple(classify(TITLE,line) for line in scenes),
                         EXPECTED)
        for index,(line,action) in enumerate(zip(scenes,EXPECTED),start=1):
            with self.subTest(action=action):
                scene=PortraitScienceScene(topic=TITLE,narration=line,
                                           scene_index=index)
                self.assertEqual(scene.aurora_beat,action)
                frame=scene.frame(.4,6.)
                self.assertEqual(frame.size,(1080,1920))
                self.assertEqual(frame.mode,"RGB")

    def test_new_narration_is_not_repeated_old_aurora_dance_script(self):
        lines=episode_lines()
        full=" ".join(lines).casefold()
        self.assertIn("oxygen",full)
        self.assertIn("nitrogen",full)
        self.assertIn("green",full)
        self.assertIn("red light",full)
        self.assertIn("pink",full)
        self.assertGreater(len(set(lines)),4)
        self.assertTrue(all(line.endswith(".") for line in lines))
        self.assertTrue(all(9<=len(line.split())<=26 for line in lines))
        self.assertIn("different colors",TITLE.casefold())

    def test_production_uses_neural_english_9_16_and_automatic_history(self):
        job=SOURCE.read_text(encoding="utf8")
        delivery=DELIVERY.read_text(encoding="utf8")
        for required in (
            "      style: science","      language: en",
            "      voice: kokoro","      voice_name: af_heart",
            "      caption_timing: audio","      duration_seconds: 30",
            "      shot_seconds: 6","      resolution: shorts",
            "      render_profile: high",
            "uses: ./.github/workflows/one-click-preview.yml",
        ):
            with self.subTest(required=required):
                self.assertIn(required,job)
        self.assertIn('Verify original aurora-colors science Short',delivery)
        self.assertIn("aurora-colors",delivery)
        self.assertIn('gh run download "$SOURCE_RUN_ID"',delivery)
        self.assertIn("python scripts/update_video_history.py",delivery)
        self.assertIn("cmp -s",delivery)
        self.assertIn('      - "Verify original aurora-colors science Short"',
                      delivery)


if __name__=="__main__":
    unittest.main()
