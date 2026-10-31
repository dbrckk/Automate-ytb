"""Ensure a science release cannot report success before real MP4 QA finishes.

No external action or GitHub API is required; this checks the contractual
relationship between two real repository workflows, not a simulated video.
"""
from __future__ import annotations

import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / ".github/workflows/one-click-preview.yml"
RELEASE = ROOT / ".github/workflows/science-shorts-release-candidate.yml"


class ScienceReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.production = PRODUCTION.read_text(encoding="utf-8")
        self.release = RELEASE.read_text(encoding="utf-8")

    def test_one_click_is_reusable_without_losing_android_dispatch(self):
        self.assertIn("  workflow_call:\n    inputs:\n", self.production)
        self.assertIn("  workflow_dispatch:\n    inputs:\n", self.production)
        call = self.production.split("  workflow_call:\n", 1)[1].split(
            "  workflow_dispatch:\n", 1)[0]
        dispatch = self.production.split("  workflow_dispatch:\n", 1)[1].split(
            "\npermissions:\n", 1)[0]
        names = re.findall(r"(?m)^      ([a-z][a-z_]*):\s*$", call)
        android = re.findall(r"(?m)^      ([a-z][a-z_]*):\s*$", dispatch)
        expected = {
            "topic", "original_script", "character", "style", "language",
            "voice", "voice_style", "voice_name", "soundtrack", "transition",
            "caption_timing", "duration_seconds", "shot_seconds",
            "resolution", "render_profile",
        }
        self.assertEqual(set(names), expected)
        self.assertEqual(len(names), len(expected))
        self.assertEqual(set(android), expected)
        for name in expected:
            self.assertRegex(
                call, rf"(?m)^      {name}:\n        type: (?:string|number)\n        required: true$")
        for name in ("duration_seconds", "shot_seconds"):
            self.assertRegex(call, rf"(?m)^      {name}:\n        type: number$")
        self.assertIn("  contents: read", self.production)

    def test_release_status_is_the_production_job_result_not_a_dispatch(self):
        self.assertIn(
            "uses: ./.github/workflows/one-click-preview.yml", self.release)
        self.assertRegex(
            self.release, r"(?m)^  confirm:\n    name: .*\n    needs: render-and-verify$")
        self.assertNotIn("gh workflow run", self.release)
        self.assertNotIn("actions: write", self.release)
        self.assertNotIn("GH_TOKEN", self.release)
        self.assertNotIn("continue-on-error:", self.release)
        self.assertIn("  contents: read", self.release)
        self.assertIn("    paths:\n      - .github/workflows/science-shorts-release-candidate.yml",
                      self.release)
        called = self.release.split("    with:\n", 1)[1].split(
            "\n  confirm:\n", 1)[0]
        keys = re.findall(r"(?m)^      ([a-z][a-z_]*):", called)
        self.assertEqual(set(keys), {
            "topic", "original_script", "character", "style", "language",
            "voice", "voice_style", "voice_name", "soundtrack", "transition",
            "caption_timing", "duration_seconds", "shot_seconds",
            "resolution", "render_profile",
        })
        self.assertEqual(len(keys), 15)

    def test_release_parameters_require_real_full_quality_video(self):
        required = (
            "      style: science", "      language: en",
            "      voice: kokoro", "      voice_name: af_heart",
            "      caption_timing: audio", "      soundtrack: ambient",
            "      duration_seconds: 30", "      shot_seconds: 6",
            "      resolution: shorts", "      render_profile: high",
        )
        for item in required:
            with self.subTest(value=item):
                self.assertIn(item, self.release)
        self.assertRegex(
            self.production,
            r"python -m automate_ytb\.episode[\s\S]*?--render-profile")
        for command in (
            "python -m automate_ytb.quality",
            "python -m automate_ytb.media_qa",
            "python -m automate_ytb.review_board",
            "python -m automate_ytb.qa_bundle",
            "name: automate-ytb-free-preview",
        ):
            with self.subTest(command=command):
                self.assertIn(command, self.production)
        # The real encoder and media gates must finish before this workflow
        # can claim success; uploading failure artifacts alone cannot pass it.
        self.assertIn('    needs: render-and-verify', self.release)
        self.assertIn('human', self.release.casefold())


if __name__ == "__main__":
    unittest.main()
