"""Release request preflight: real compiler constraints before torch install."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.premium_request import validate_request

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/universal-premium-release.yml"
SCRIPT = (
    "How does a lightning storm form? Warm rising air lifts moisture high "
    "into the clouds. Ice particles collide inside the clouds, and "
    "electrical charge separates until lightning can strike."
)


@contextmanager
def in_dir(path):
    original = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original)


class PremiumReleaseRequestTests(unittest.TestCase):
    def test_dispatch_accepts_original_multiple_beats_without_media_dependencies(self):
        value = validate_request(event_name="workflow_dispatch",
                                 topic="How lightning works",
                                 script=SCRIPT, language="en")
        self.assertEqual(value["script"], SCRIPT)
        self.assertEqual(value["language"], "en")

    def test_invalid_narration_rejected_before_downloading_models(self):
        invalid = (
            "Only one sentence can be quite long but cannot form a two beat story",
            "word " * 241,
            "word " * 361,
            "Beginning a story.\x00 But it contains a control byte.",
            "Just two words. Then two.",
        )
        for script in invalid:
            with self.subTest(script=script[:40]), self.assertRaises(ValueError):
                validate_request(event_name="workflow_dispatch",
                                 topic="Original science short",
                                 script=script, language="en")
        with self.assertRaises(ValueError):
            validate_request(event_name="workflow_dispatch",
                             topic="Original science short",
                             script=SCRIPT, language="de")
        with self.assertRaises(ValueError):
            validate_request(event_name="workflow_dispatch",
                             topic="Original\nshort",
                             script=SCRIPT, language="en")
        with self.assertRaises(ValueError):
            validate_request(event_name="schedule",
                             topic="Original science short",
                             script=SCRIPT, language="en")

    def test_push_is_exactly_one_new_safe_request(self):
        with tempfile.TemporaryDirectory() as temp, in_dir(Path(temp)):
            root = Path("video_requests")
            root.mkdir()
            (root / "new-short.json").write_text(json.dumps({
                "topic": "How lightning works", "script": SCRIPT,
                "language": "en",
            }), encoding="utf-8")
            valid = "A\tvideo_requests/new-short.json\n"
            sha1, sha2 = "a" * 40, "b" * 40
            with patch("automate_ytb.premium_request.subprocess.check_output",
                       return_value=valid):
                result = validate_request(event_name="push", before=sha1, head=sha2)
            self.assertEqual(result["topic"], "How lightning works")
            for changes in (
                "M\tvideo_requests/new-short.json\n",
                valid + "M\tvideo_requests/old.json\n",
                valid + "A\tvideo_requests/other.json\n",
                "A\tvideo_requests/../../bad.json\n",
            ):
                with self.subTest(changes=changes), patch(
                    "automate_ytb.premium_request.subprocess.check_output",
                    return_value=changes,
                ), self.assertRaises(ValueError):
                    validate_request(event_name="push", before=sha1, head=sha2)
            with self.assertRaises(ValueError):
                validate_request(event_name="push", before="nope", head=sha2)

    def test_push_rejects_duplicate_fields_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as temp, in_dir(Path(temp)):
            root = Path("video_requests")
            root.mkdir()
            source = root / "one.json"
            sha1, sha2 = "a" * 40, "b" * 40
            with patch("automate_ytb.premium_request.subprocess.check_output",
                       return_value="A\tvideo_requests/one.json\n"):
                source.write_text('{"topic":"a","topic":"b","script":"c","language":"en"}',
                                  encoding="utf-8")
                with self.assertRaises(ValueError):
                    validate_request(event_name="push", before=sha1, head=sha2)
                source.write_text(json.dumps({
                    "topic": "How lightning works", "script": SCRIPT,
                    "language": "en", "execute": "true",
                }), encoding="utf-8")
                with self.assertRaises(ValueError):
                    validate_request(event_name="push", before=sha1, head=sha2)
                source.unlink()
                source.symlink_to(root / "missing.json")
                with self.assertRaises(ValueError):
                    validate_request(event_name="push", before=sha1, head=sha2)

    def test_workflow_preflight_precedes_paid_time_and_release_is_gated(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertLess(
            workflow.index("python -m automate_ytb.premium_request"),
            workflow.index("python -m pip install"),
        )
        self.assertIn("--voice kokoro", workflow)
        self.assertIn("--width 1080", workflow)
        self.assertIn("--full-decode", workflow)
        self.assertIn('test "$local_hash" = "$remote_hash"', workflow)
        self.assertNotIn("continue-on-error: true\n      - name: Publish", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)


if __name__ == "__main__":
    unittest.main()
