"""Prevent silent bypass of expensive real video and neural voice CI gates.

Changing shared framing code must trigger BOTH the ocean/Kokoro real footage
render and the universal genre render. The test intentionally reads the
workflow definitions without relying on PyYAML or internet services.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"

DEPENDENCIES = {
    "kokoro-short-voice.yml": {
        "automate_ytb/short_voice.py",
        "automate_ytb/deepsea_short.py",
        "automate_ytb/subject_reframe.py",
        "automate_ytb/soundtrack.py",
        "automate_ytb/media_qa.py",
        "tests/test_subject_reframe.py",
    },
    "universal-editorial-release-candidate.yml": {
        "automate_ytb/auto_edit.py",
        "automate_ytb/production.py",
        "automate_ytb/footage.py",
        "automate_ytb/subject_reframe.py",
        "tests/test_subject_reframe.py",
        "tests/test_real_footage.py",
        "tests/test_auto_edit.py",
    },
}


class WorkflowTriggerCoverageTests(unittest.TestCase):
    def test_video_regression_workflows_cover_shared_engine(self):
        for workflow, paths in DEPENDENCIES.items():
            with self.subTest(workflow=workflow):
                text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
                # Isolate pull_request path list: do not accept a filename
                # merely because it occurs in a comment or run command.
                self.assertIn("pull_request:", text)
                start = text.index("pull_request:")
                end = text.index("\n  workflow_dispatch:", start) if (
                    "\n  workflow_dispatch:" in text[start:]
                ) else text.index("\npermissions:", start)
                scope = text[start:end]
                for path in paths:
                    self.assertTrue(
                        any(line.strip().strip("- ").strip('"').strip("'") == path
                            for line in scope.splitlines()),
                        f"{workflow} will not run when {path} changes",
                    )


if __name__ == "__main__":
    unittest.main()
