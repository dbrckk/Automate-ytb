"""Guardrails for stable, user-downloadable forest MP4 releases.

Unlike an expiring Actions artifact or session-local sandbox path, a release
asset is a fixed publicly accessible URL. The workflow must reject unverified
source runs and only advertise a video after an anonymous SHA-matched GET.
"""
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_forest_release import (
    ASSET_VIDEO, ASSET_QA, SOURCE_VIDEO, SOURCE_QA,
    prepare, sha256_file,
)

ROOT=Path(__file__).resolve().parents[1]
DISTRIBUTION=ROOT/".github/workflows/forest-stable-video-download.yml"
NARRATION=ROOT/".github/workflows/p3-5-narrated-forest.yml"


class PermanentForestDeliveryTests(unittest.TestCase):
    def test_workflow_produces_only_real_public_release_downloads(self):
        workflow=DISTRIBUTION.read_text(encoding="utf-8")
        self.assertIn("  workflow_run:",workflow)
        self.assertIn("  workflow_dispatch:",workflow)
        self.assertIn("  push:",workflow)
        self.assertIn('    branches: [main]',workflow)
        self.assertIn('  contents: write',workflow)
        self.assertIn('  actions: read',workflow)
        self.assertIn('head_branch == \'main\'',workflow)
        self.assertIn('head_repository.full_name == github.repository',workflow)
        self.assertIn('.head_repository.full_name == $repo',workflow)
        self.assertIn('.conclusion == "success"',workflow)
        self.assertIn('gh run download "$SOURCE_RUN_ID"',workflow)
        self.assertIn('python scripts/prepare_forest_release.py',workflow)
        self.assertIn('gh release create "$tag"',workflow)
        self.assertIn('--prerelease --latest=false',workflow)
        self.assertIn('curl --fail --show-error --silent --location',workflow)
        self.assertIn('diff -u "$RUNNER_TEMP/expected.sha"',workflow)
        self.assertIn('anonymous.mp4',workflow)
        self.assertNotIn('youtube upload',workflow.lower())

    def test_every_successful_trusted_main_kokoro_video_can_trigger_release(self):
        narration=NARRATION.read_text(encoding="utf-8")
        self.assertIn("  push:\n    branches: [main]\n",narration)
        self.assertIn('"automate_ytb/forest_soundscape25d.py"',narration)
        self.assertIn('"scripts/render_25d_narrated_story.py"',narration)
        self.assertIn('name: p35-real-kokoro-narrated-forest-en',narration)
        self.assertIn('retention-days: 7',narration) # staging is temporary
        self.assertIn('"publicationApproved"',narration) # no social publish

    def test_delivery_refuses_missing_or_duplicate_original_assets(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)/"source"
            base.mkdir()
            with self.assertRaises(ValueError):
                prepare(base,Path(root)/"out",42593121306)
            (base/SOURCE_VIDEO).write_bytes(b"not a video")
            (base/SOURCE_QA).write_text("{}",encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(base,Path(root)/"out",42593121306)
            (base/"duplicate").mkdir()
            (base/"duplicate"/SOURCE_VIDEO).write_bytes(b"duplicate")
            with self.assertRaises(ValueError):
                prepare(base,Path(root)/"out",42593121306)

    def test_delivery_guards_against_symlinks_escape_and_invalid_ids(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)/"source"
            base.mkdir()
            (Path(root)/SOURCE_VIDEO).write_bytes(b"outside")
            (base/SOURCE_VIDEO).symlink_to(Path(root)/SOURCE_VIDEO)
            (base/SOURCE_QA).write_text("{}",encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(base,Path(root)/"out",42593121306)
            for wrong_id in (True,-1,0,10**20,"42593121306"):
                with self.assertRaises(ValueError):
                    prepare(base,Path(root)/"out",wrong_id)
            self.assertEqual(len(sha256_file(Path(root)/SOURCE_VIDEO)),64)


if __name__=="__main__":
    unittest.main()
