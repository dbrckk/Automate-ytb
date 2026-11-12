"""Regression tests for the reusable non-science kinetic Short production route."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw
import shutil
import tempfile
import unittest

from automate_ytb.universal_kinetic import (
    VERSION, _single_line, frame_image, produce, read_story, timeline_for)


def story():
    return {
        "schemaVersion": 1, "topic": "How a web request works", "language": "en",
        "beats": [
            {"kind": "concept", "title": "Who participates?",
             "narration": "The browser contacts a service through several network components.",
             "nodes": ["Browser", "DNS", "Server"]},
            {"kind": "sequence", "title": "The path of a request",
             "narration": "First resolve the name, establish a connection, then ask for content.",
             "steps": ["Resolve", "Connect", "Request", "Respond"]},
            {"kind": "measure", "title": "Illustrative time budget",
             "narration": "This example uses a hypothetical budget of five hundred milliseconds.",
             "label": "Example budget", "value": "500", "scaleMax": "1000", "unit": "ms"},
            {"kind": "compare", "title": "Illustrative scenarios",
             "narration": "These invented example timings show how different two requests can be.",
             "left": "Cached", "right": "Uncached",
             "leftValue": "45", "rightValue": "300", "unit": "ms"},
        ],
    }


class UniversalKineticTests(unittest.TestCase):
    def _load(self, data):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "story.json"
            path.write_text(json.dumps(data), encoding="utf8")
            return read_story(path)

    def test_four_generic_motion_grammars(self):
        data = self._load(story())
        self.assertIn("universal-kinetic", VERSION)
        self.assertEqual([x["kind"] for x in data["beats"]],
                         ["concept", "sequence", "measure", "compare"])
        times = [0, 60, 120, 180, 240]
        motion = timeline_for(data, times)
        self.assertAlmostEqual(motion.state_at(120)["objects"]["progress"]["value"], .5)
        self.assertEqual(len(motion.audio_events()), 4)
        self.assertEqual(motion.audio_events()[0]["atSample"], 0)
        for frame in (0, 59, 60, 119, 120, 179, 180, 239):
            self.assertEqual(frame_image(data,motion,times,frame,360,640).size,
                             (360,640))
        first = frame_image(data,motion,times,15,360,640)
        second = frame_image(data,motion,times,50,360,640)
        self.assertNotEqual(first.tobytes(),second.tobytes())

    def test_bad_values_and_unreviewed_sources(self):
        for field, bad in (
            ("value", "NaN"), ("value", "-1"), ("value", "1e100"),
            ("scaleMax", "0"), ("scaleMax", True),
        ):
            data = story()
            data["beats"][2][field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                self._load(data)
        data=story()
        data["beats"][0]["sources"]=["file:///etc/passwd"]
        with self.assertRaises(ValueError):
            self._load(data)
        data=story()
        data["beats"][0]["nodes"]=["Just one node"]
        with self.assertRaises(ValueError):
            self._load(data)
        data=story()
        data["beats"][0]["narration"]="a"
        with self.assertRaises(ValueError):
            self._load(data)

    def test_mobile_long_visual_labels_never_overflow(self):
        draw=ImageDraw.Draw(Image.new("RGB",(360,640)))
        for width in (90,150,230,320):
            text,font=_single_line(
                draw,"A very long original historical location label in French",
                width,30,bold=True)
            self.assertLessEqual(draw.textbbox((0,0),text,font=font)[2],width)
        current=story()
        current["topic"]="An extremely long topic about economic history and technology"
        current["beats"][1]["steps"]=[
            "Cryptographic verification", "Authorization workflow",
            "Cross-platform compatibility", "Status tracking",
        ]
        content=self._load(current)
        track=timeline_for(content,[0,60,120,180,240])
        image=frame_image(content,track,[0,60,120,180,240],80,360,640)
        self.assertEqual(image.size,(360,640))

    def test_numeric_values_arent_made_up_from_topic(self):
        data=story()
        data["topic"]="A different and unrelated subject"
        result=self._load(data)
        self.assertEqual(str(result["beats"][2]["value"]), "500")
        self.assertEqual(str(result["beats"][3]["rightValue"]), "300")
        self.assertFalse(result["beats"][0]["sources"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak-ng") or shutil.which("espeak")),
                         "Real external free media binaries unavailable")
    def test_real_video_with_narration_music_and_event_sfx(self):
        data=story()
        data["beats"]=data["beats"][:2]
        with tempfile.TemporaryDirectory() as td:
            brief=Path(td)/"brief.json"
            out=Path(td)/"short.mp4"
            brief.write_text(json.dumps(data),encoding="utf8")
            manifest=produce(brief,out,voice="espeak",width=720)
            self.assertTrue(out.is_file())
            self.assertGreater(out.stat().st_size,10000)
            self.assertEqual(manifest["delivery"]["status"],"passed")
            self.assertEqual(manifest["voiceEngine"],"espeak")
            self.assertEqual(manifest["sound"],"original-event-locked-foley")
            self.assertFalse(manifest["publicationApproved"])
            self.assertTrue(out.with_suffix(".json").is_file())


if __name__ == "__main__":
    unittest.main()
