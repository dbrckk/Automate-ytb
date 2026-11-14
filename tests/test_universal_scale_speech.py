"""Source PCM phrase-timed quantitative visuals, foley and provenance tests."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.captions import caption_phrases
from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_kinetic import (
    frame_image,read_story,timeline_for)
from automate_ytb.universal_scale_camera import (
    camera_pose,render_cinematic_scale_frame)
from automate_ytb.universal_scale_speech import (
    VERSION,METHOD,build_pcm_scale_timing,measured_phase,
    measured_reveal,scale_speech_event)

HERE=Path(__file__).resolve().parents[1]
SOURCE=HERE/"examples/universal_pcm_phrase_scale_story.en.txt"
TITLE="How a glowing thread changes scale"


def encoded(story):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"source-story.json"
        path.write_text(json.dumps(story,ensure_ascii=False),encoding="utf8")
        return read_story(path)


def transcript(story):
    """Synthetic sample boundaries for unit tests; production uses real TTS."""
    beats=story["beats"]
    bounds=[180*i for i in range(len(beats)+1)]
    cues=[]
    for i,beat in enumerate(beats):
        parts=caption_phrases(beat["narration"])
        spacing=round(162/(len(parts)+1))
        for j,phrase in enumerate(parts):
            at=bounds[i]+spacing*j
            cues.append({"beatIndex":i,"text":phrase,
                         "startFrame":at,"endFrame":at+max(2,spacing-1)})
    return cues,bounds


class SourcePCMPhraseTimingTests(unittest.TestCase):
    def prepared(self):
        data=compile_original_script(
            topic=TITLE,script=SOURCE.read_text(encoding="utf8"),
            language="en")
        return encoded(data)

    def test_source_only_opt_in_and_distinct_phrase_anchors(self):
        source=self.prepared()
        self.assertEqual(source["proceduralScaleSpeechEngine"],VERSION)
        self.assertEqual(len(source["beats"]),4)
        cues,bounds=transcript(source)
        timing=build_pcm_scale_timing(source,cues,bounds)
        self.assertEqual(timing["engine"],VERSION)
        self.assertEqual(timing["method"],METHOD)
        self.assertIs(timing["wordLevelAligned"],False)
        self.assertEqual(len(timing["events"]),4)
        self.assertEqual([e["sourceSpan"] for e in timing["events"]],
                         ["1 mm","2 cm","2 m","1 km"])
        self.assertEqual([e["landmark"] for e in timing["events"]],
                         ["human","tree","tower","mountain"])
        for i,e in enumerate(timing["events"]):
            self.assertEqual(e["beatIndex"],i)
            self.assertGreater(e["valueStartFrame"],bounds[i])
            self.assertGreater(e["landmarkStartFrame"],e["valueStartFrame"])
            self.assertIn(e["sourceSpan"],e["valuePhrase"])
            self.assertNotEqual(e["valuePhrase"],e["landmarkPhrase"])
            self.assertEqual(scale_speech_event(timing,i,bounds),e)

    def test_camera_and_milestones_wait_for_real_phrase_start(self):
        story=self.prepared()
        cues,bounds=transcript(story)
        timing=build_pcm_scale_timing(story,cues,bounds)
        journey=story["proceduralScaleJourney"]
        for i,e in enumerate(timing["events"]):
            start,end=bounds[i:i+2]
            at=e["valueStartFrame"]
            self.assertEqual(measured_phase(start,end,at),0.)
            self.assertEqual(measured_phase(at,end,at),0.)
            self.assertGreater(measured_phase(at+2,end,at),0.)
            self.assertAlmostEqual(measured_phase(end-1,end,at),
                                   (end-1-at)/(end-at))
            self.assertEqual(measured_reveal(
                e["landmarkStartFrame"],end,e["landmarkStartFrame"]),0.)
            self.assertEqual(measured_reveal(
                min(end-1,e["landmarkStartFrame"]+15),end,
                e["landmarkStartFrame"]),1.)
            previous=(camera_pose(journey,i,0.)["progress"]
                      if i else None)
            if i:
                self.assertEqual(previous,camera_pose(journey,i-1,1.)["progress"])
        with self.assertRaises(ValueError):
            measured_phase(-1,180,20)

    def test_foley_events_are_at_measured_PCM_frames_and_48khz_samples(self):
        source=self.prepared()
        cues,bounds=transcript(source)
        timing=build_pcm_scale_timing(source,cues,bounds)
        actual=timeline_for(source,bounds,timing)
        got=actual.audio_events()
        self.assertEqual(len(got),8)
        self.assertEqual(len([c for c in got if c["family"]=="scale-transition"]),4)
        self.assertEqual(len([c for c in got if c["family"]=="reveal"]),4)
        self.assertFalse(any(c["id"].startswith("story-cue-") for c in got))
        for i,e in enumerate(timing["events"]):
            tones=[c for c in got if c["id"]==f"source-scale-tone-{i:02d}"]
            chimes=[c for c in got if c["id"]==f"source-landmark-tone-{i:02d}"]
            self.assertEqual(len(tones),len(chimes))
            self.assertEqual(tones[0]["atFrame"],e["valueStartFrame"])
            self.assertEqual(chimes[0]["atFrame"],e["landmarkStartFrame"])
            self.assertEqual(tones[0]["atSample"],e["valueStartFrame"]*1600)
            self.assertEqual(chimes[0]["atSample"],e["landmarkStartFrame"]*1600)
        legacy=timeline_for(source,bounds)
        self.assertEqual(len(legacy.audio_events()),4)
        self.assertTrue(all(c["id"].startswith("story-cue")
                            for c in legacy.audio_events()))

    def test_actual_rgb_art_changes_at_synthesized_phrase_events(self):
        story=self.prepared()
        cues,bounds=transcript(story)
        timing=build_pcm_scale_timing(story,cues,bounds)
        timeline=timeline_for(story,bounds,timing)
        at=timing["events"][0]["valueStartFrame"]
        before=frame_image(story,timeline,bounds,at-1,360,640,
                           scale_speech_timing=timing)
        after=frame_image(story,timeline,bounds,at+15,360,640,
                          scale_speech_timing=timing)
        self.assertEqual((before.mode,before.size),("RGB",(360,640)))
        self.assertNotEqual(before.tobytes(),after.tobytes())
        self.assertEqual(after.tobytes(),frame_image(
            story,timeline,bounds,at+15,360,640,
            scale_speech_timing=timing).tobytes())
        no_timing=render_cinematic_scale_frame(
            story["proceduralScaleJourney"],TITLE,at-1,bounds,
            0,360,640)
        authored=render_cinematic_scale_frame(
            story["proceduralScaleJourney"],TITLE,at-1,bounds,
            0,360,640,speech_timing=timing)
        # The previous renderer displays 1 mm from the start; the v23
        # renderer leaves the numeric area empty until its voiced phrase.
        self.assertNotEqual(no_timing.crop((0,70,360,145)).tobytes(),
                            authored.crop((0,70,360,145)).tobytes())

    def test_invalid_or_forged_audio_phrase_anchors_fail_closed(self):
        story=self.prepared()
        cues,bounds=transcript(story)
        tamper=[
            lambda c:c[0].__setitem__("text","an invented narration phrase"),
            lambda c:c[0].__setitem__("beatIndex",2),
            lambda c:c[0].__setitem__("startFrame",-1),
            lambda c:c[1].__setitem__("startFrame",c[0]["startFrame"]),
            lambda c:c.pop(),
        ]
        for change in tamper:
            mutated=deepcopy(cues)
            change(mutated)
            with self.subTest(change=str(change)),self.assertRaises(ValueError):
                build_pcm_scale_timing(story,mutated,bounds)
        timing=build_pcm_scale_timing(story,cues,bounds)
        forged=deepcopy(timing)
        forged["events"][0]["valueStartFrame"]=bounds[1]+1
        with self.assertRaises(ValueError):
            scale_speech_event(forged,0,bounds)
        forged=deepcopy(timing)
        forged["wordLevelAligned"]=True
        with self.assertRaises(ValueError):
            scale_speech_event(forged,0,bounds)

    def test_previous_v22_story_has_no_new_timing_claims(self):
        # Reopen authored compiler output; read_story's normalized beats
        # have "items" rather than compiler-side concept "nodes".
        old=compile_original_script(
            topic=TITLE,script=SOURCE.read_text(encoding="utf8"),
            language="en")
        old.pop("proceduralScaleSpeechEngine")
        restored=encoded(old)
        self.assertNotIn("proceduralScaleSpeechEngine",restored)
        cues,bounds=transcript(restored)
        with self.assertRaises(ValueError):
            build_pcm_scale_timing(restored,cues,bounds)
        for bad in ("fabricated-aligner-v1",None,True):
            forge=deepcopy(old)
            forge["proceduralScaleSpeechEngine"]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                encoded(forge)
        forge=deepcopy(old)
        forge["proceduralScaleSpeechEngine"]=VERSION
        forge.pop("proceduralScaleCameraEngine")
        with self.assertRaises(ValueError):
            encoded(forge)


if __name__=="__main__":
    unittest.main()
