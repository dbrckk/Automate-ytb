"""Deterministic interleaving and real-footage non-overlap regression gates."""
from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from automate_ytb.source_scheduler import (
    counts_for_schedule, interleave_sources,
)
from automate_ytb.auto_edit import select_interleaved_excerpts


class SchedulingTests(TestCase):
    def test_actual_nasa_footage_capacity_produces_four_source_changes(self):
        # Actual duration figures from checked NASA download FFprobe run.
        scene_ms=[7000]*5
        sources=interleave_sources(scene_ms, [49560,88033])
        self.assertEqual(len(sources),5)
        self.assertEqual(set(sources),{0,1})
        self.assertEqual(sum(x!=y for x,y in zip(sources,sources[1:])),4)
        counts=counts_for_schedule(sources,2)
        self.assertEqual(sum(counts),5)
        self.assertLessEqual(counts[0]*7000,49560)
        self.assertLessEqual(counts[1]*7000,88033)

    def test_single_source_falls_back_without_fabricated_alternation(self):
        self.assertEqual(interleave_sources([6000,6000],[12500]),(0,0))
        self.assertEqual(counts_for_schedule((0,0),1),(2,))

    def test_never_uses_source_beyond_capacity(self):
        with self.assertRaisesRegex(ValueError,"Insufficient"):
            interleave_sources([7000]*5,[14000,14000])
        schedule=interleave_sources([7000]*5,[14000,21000])
        counts=counts_for_schedule(schedule,2)
        self.assertEqual(counts,(2,3))

    def test_invalid_requests_fail_closed(self):
        for scenes, caps in (
            ([],[10000]), ([6000],[]), ([0],[10000]),
            ([6000],[-100]), ([6000],[1000]),
        ):
            with self.subTest(scenes=scenes,caps=caps):
                with self.assertRaises(ValueError):
                    interleave_sources(scenes,caps)
        with self.assertRaises(ValueError):
            interleave_sources([6000],[10000],beam_width=0)
        with self.assertRaises(ValueError):
            counts_for_schedule((0,2),2)

    def test_interleaved_candidate_extractors_preserve_each_source_timeline(self):
        # Two real source filenames stand in for approved local recordings.
        # Sampling is mocked to isolate planning; E2E production CI separately
        # downloads/decodes genuine NASA media, renders and validates the MP4.
        calls=[]
        def sample(source,start,length):
            calls.append((source.name,start,length))
            light=60 if source.name=="first.mp4" else 170
            return {
                "sampledFrames":3,
                "meanLuminance":light,
                "contrastStdDev":20,
                "meanFrameChange":10,
                "technicalSelectionScore":.7,
                "requiresVisualReview":False,
                "spatialSignature":[light]*48,
            }
        plan=interleave_sources([4000]*5,[16000,16000])
        with patch("automate_ytb.auto_edit._sample_quality",side_effect=sample):
            shots=select_interleaved_excerpts(
                [Path("first.mp4"),Path("second.mp4")],
                [4000]*5,[16000,16000],plan,
            )
        self.assertEqual(len(shots),5)
        self.assertEqual([x["sceneIndex"] for x in shots],list(range(5)))
        self.assertEqual(sum(plan[i]!=plan[i-1] for i in range(1,5)),4)
        for source in ("first.mp4","second.mp4"):
            selected=[s for s in shots if s["source"].name==source]
            self.assertTrue(all(
                prev["startSeconds"]+prev["durationSeconds"] <= nxt["startSeconds"]+.005
                for prev,nxt in zip(selected,selected[1:])
            ))
        self.assertTrue(all(x["candidateCount"]>=1 for x in shots))
        self.assertGreater(len(calls),5)
