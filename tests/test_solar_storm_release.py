"""No-network regression checks for public Solar Storm release provenance.

The actual embedded shell and Python of the checked-in GitHub Actions workflow
are parsed, syntax-checked, and the run-authorization code executed locally.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github" / "workflows" /
            "publish-solar-storm-video.yml")


def scripts():
    contents = WORKFLOW.read_text(encoding="utf-8")
    lines = contents.splitlines()
    blocks = []
    for i, line in enumerate(lines):
        if line != "        run: |":
            continue
        body = []
        for following in lines[i + 1:]:
            if following.startswith("          ") or not following.strip():
                body.append(following)
            else:
                break
        blocks.append(textwrap.dedent("\n".join(body)) + "\n")
    return contents, blocks


def python_heredocs(bash_script):
    return re.findall(r"(?ms)^python3 - [^\n]+ <<'PY'\n(.*?)^PY$", bash_script)


class PublicReleaseSafetyTests(unittest.TestCase):
    def test_embedded_workflow_scripts_are_valid_shell_and_python(self):
        source, blocks = scripts()
        self.assertEqual(len(blocks), 3)
        self.assertEqual(sum(len(python_heredocs(b)) for b in blocks), 2)
        self.assertIn("workflow_dispatch:", source)
        self.assertNotIn("\n  push:", source)
        for block in blocks:
            checked = subprocess.run(["bash", "-n"], input=block,
                                     text=True, capture_output=True, timeout=10)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            for snippet in python_heredocs(block):
                compile(snippet, str(WORKFLOW), "exec")

    def test_release_always_uses_selected_source_and_unique_tag(self):
        source, _ = scripts()
        self.assertIn("--workflow solar-storm-documentary.yml --branch main --limit 1", source)
        self.assertIn('gh run download "$SOURCE_RUN"', source)
        self.assertIn('TAG="solar-storm-en-run-$SOURCE_RUN"', source)
        self.assertIn("release-provenance.json", source)
        self.assertIn('qa.get("shot_count") != 13', source)
        self.assertIn('shot.get("sampled_shots") != 13', source)
        self.assertIn('scene.get("sampled_scenes") != 6', source)
        self.assertNotRegex(source, r"gh run download [0-9]{5,}")

    def test_run_provenance_rejects_failed_wrong_branch_and_wrong_workflow(self):
        _, blocks = scripts()
        script = python_heredocs(blocks[0])[0]
        good = {
            "databaseId": 41240018536,
            "status": "completed",
            "conclusion": "success",
            "headBranch": "main",
            "headSha": "a" * 40,
            "workflowName": "Produce Solar Storm short — NASA + Kokoro",
            "url": "https://github.com/dbrckk/Automate-ytb/actions/runs/41240018536",
        }
        with tempfile.TemporaryDirectory() as temp:
            metadata = Path(temp) / "run.json"
            outputs = Path(temp) / "outputs.txt"
            for changes, accepted in (
                    ({}, True), ({"conclusion": "failure"}, False),
                    ({"status": "in_progress"}, False),
                    ({"headBranch": "feature"}, False),
                    ({"workflowName": "Validate production pipeline"}, False),
                    ({"headSha": "wrong"}, False)):
                info = {**good, **changes}
                metadata.write_text(json.dumps(info), encoding="utf-8")
                outputs.unlink(missing_ok=True)
                run = subprocess.run(
                    [sys.executable, "-c", script, str(metadata), str(outputs)],
                    text=True, capture_output=True, timeout=10)
                self.assertEqual(run.returncode == 0, accepted, run.stderr)
                if accepted:
                    self.assertIn("run_id=41240018536", outputs.read_text())
                else:
                    self.assertFalse(outputs.exists())


if __name__ == "__main__":
    unittest.main()
