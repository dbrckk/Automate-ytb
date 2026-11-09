"""Guard the durable Android/PC science preview delivery contract."""
from pathlib import Path
import unittest

WORKFLOW=(Path(__file__).resolve().parents[1]/
          ".github/workflows/science-preview-download.yml")


class PublicScienceDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow=WORKFLOW.read_text(encoding="utf-8")

    def test_no_public_url_without_anonymous_full_download(self):
        workflow=self.workflow
        self.assertIn('curl --fail --location --silent --show-error',workflow)
        self.assertIn('"$url" --output "$RUNNER_TEMP/public-science.mp4"',workflow)
        self.assertIn('cmp -s "delivered/${PREVIEW_SLUG}.mp4" "$RUNNER_TEMP/public-science.mp4"',workflow)
        self.assertIn('if [[ "$verified" != true ]]; then',workflow)
        self.assertIn('exit 1',workflow)
        self.assertLess(workflow.index('if [[ "$verified" != true ]]; then'),
                        workflow.index('echo "$url" >> "$GITHUB_STEP_SUMMARY"') if
                        'echo "$url" >> "$GITHUB_STEP_SUMMARY"' in workflow else
                        workflow.index('echo "$url"',workflow.index('if [[ "$verified" != true ]]; then')))

    def test_sha256_and_release_assets_are_bound_to_same_slug(self):
        workflow=self.workflow
        self.assertIn('sha256sum "delivered/${PREVIEW_SLUG}.mp4"',workflow)
        self.assertIn('sha256sum "$RUNNER_TEMP/public-science.mp4"',workflow)
        self.assertIn('[[ "$expected" == "$received" ]]',workflow)
        self.assertIn('gh release create "$tag"',workflow)
        self.assertIn('--prerelease --latest=false',workflow)
        self.assertNotIn('curl --head',workflow)

    def test_publication_remains_unreviewed(self):
        self.assertIn('Technical preview — human editorial review required.',self.workflow)
        self.assertNotIn('youtube-upload',self.workflow)


if __name__=="__main__":
    unittest.main()
