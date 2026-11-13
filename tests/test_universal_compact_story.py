"""Guard against oversized pretty-printed original vector storyboards.

The bounded read_story validator remains unchanged; the universal script
compiler's portable JSON encoding must fit its existing byte cap.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch

from automate_ytb.universal_kinetic import main, read_story


class CompactOriginalTikTokStoryTests(TestCase):
    def test_original_five_scene_script_remains_readable_under_size_cap(self):
        script=Path(__file__).resolve().parents[1]/(
            "examples/tiktok_coastal_storm_2026_11_13.en.txt")
        self.assertTrue(script.is_file())
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"tiktok.mp4"
            capture={}
            def fake_produce(brief, filename, **kwargs):
                capture["brief"]=brief
                capture["filename"]=filename
                capture["params"]=kwargs
                parsed=read_story(brief)
                capture["parsed"]=parsed
                return {"delivery":{"status":"passed"}}
            with patch("automate_ytb.universal_kinetic.produce",
                       side_effect=fake_produce):
                with redirect_stdout(StringIO()):
                    status=main([
                        "--topic","What if a storm hit a coastal railway?",
                        "--script-file",str(script),"--language","en",
                        "--voice","kokoro","--voice-name","af_heart",
                        "--width","1080","--output",str(output)])
            self.assertEqual(status,0)
            self.assertEqual(capture["brief"],output.with_suffix(".story.json"))
            self.assertLess(capture["brief"].stat().st_size,120001)
            self.assertEqual(capture["params"]["width"],1080)
            data=capture["parsed"]
            self.assertEqual(len(data["beats"]),5)
            self.assertEqual([e["kind"] for e in data["proceduralVisualInteractions"]
                              if e],["rain-waters-plant","wave-hits-train"])
            self.assertEqual(data["language"],"en")
            self.assertEqual(json.loads(capture["brief"].read_text())["topic"],
                             "What if a storm hit a coastal railway?")
