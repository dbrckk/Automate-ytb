"""Contract tests for real-PCM-directed forest short pacing."""
import math
import unittest

from automate_ytb.forest_voice_timeline import (
    ENGLISH_SCRIPT, FRENCH_SCRIPT, measured_timeline,
)


def report(language="en",seconds=3.):
    lines=ENGLISH_SCRIPT if language=="en" else FRENCH_SCRIPT
    spans=[]
    for i,text in enumerate(lines):
        start=round((.17+i*(seconds+.17))*1000)
        spans.append({"index":i+1,"text":text,"startMs":start,
                      "endMs":start+round(seconds*1000)})
    return {"engine":"kokoro-natural","language":language,
            "durationSeconds":round(spans[-1]["endMs"]/1000+.4,3),
            "beats":spans}


class MeasuredVoiceTimelineTests(unittest.TestCase):
    def test_measured_english_physical_shots(self):
        timeline=measured_timeline(report())
        self.assertEqual(len(timeline.beats),4)
        self.assertGreater(timeline.duration,12.)
        self.assertEqual([b.name for b in timeline.beats],
                         ["discovery","contact","arrival","departure"])
        for i,beat in enumerate(timeline.beats):
            self.assertGreater(beat.speech_start,beat.start)
            self.assertLess(beat.speech_end,beat.end)
            if i:
                self.assertAlmostEqual(beat.start,timeline.beats[i-1].end)
            middle=(beat.start+beat.end)/2
            source,actual=timeline.at(middle)
            self.assertEqual(actual.name,beat.name)
            self.assertTrue(beat.source_start<=source<=beat.source_end)

    def test_french_supported_without_english_mismatch(self):
        self.assertEqual(len(measured_timeline(report("fr"),language="fr").beats),4)
        with self.assertRaises(ValueError):
            measured_timeline(report("fr"),language="en")

    def test_rejects_fabricated_or_inconsistent_voice_reports(self):
        data=report()
        data["engine"]="espeak"
        with self.assertRaises(ValueError):
            measured_timeline(data)
        data=report()
        data["beats"][2]["text"]="fabricated subtitle"
        with self.assertRaises(ValueError):
            measured_timeline(data)
        data=report()
        data["beats"][1]["startMs"]=0
        with self.assertRaises(ValueError):
            measured_timeline(data)

    def test_no_invalid_video_clock(self):
        t=measured_timeline(report())
        for invalid in (-1.,t.duration+.1,math.nan,math.inf,True):
            with self.assertRaises(ValueError):
                t.at(invalid)


if __name__=="__main__":
    unittest.main()
