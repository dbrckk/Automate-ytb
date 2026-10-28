"""Listenability-oriented objective regressions for the free original music bed."""
from __future__ import annotations

from array import array
import json
from pathlib import Path
import tempfile
import unittest
import wave

from automate_ytb.scene_plan import plan
from automate_ytb.soundtrack import (
    SAMPLERATE, CHANNELS, LOOP_SECONDS, VERSION, create_bed,
)


class StereoSoundtrackTests(unittest.TestCase):
    def test_stereo_loudness_headroom_and_continuous_scene_change(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            scene_plan = plan(
                topic="Lumière et forêt originale",
                script=("La chouette se promène au matin. "
                        "Puis la nuit commence dans la vallée. "
                        "Elle voit une lumière près de la rivière. "
                        "Un nouvel ami arrive. "
                        "La chouette retrouve son chemin."),
                duration=30, shot_seconds=6,
                character="Une chouette originale")
            for index, scene in enumerate(scene_plan["scenes"]):
                direction = scene.get("direction")
                if direction:
                    direction["weather"] = "night" if index % 2 else "day"
            source = root/"plan.json"
            source.write_text(json.dumps(scene_plan, ensure_ascii=False), encoding="utf-8")
            output = root/"music.wav"
            result = create_bed(plan_path=source, output=output)
            self.assertEqual(result["engine"], VERSION)
            self.assertEqual(result["channels"], CHANNELS)
            self.assertEqual(result["sampleRate"], SAMPLERATE)
            self.assertGreaterEqual(result["moodTransitions"], 1)
            self.assertTrue(result["seamlessHarmonicLoop"])
            with wave.open(str(output), "rb") as wav:
                self.assertEqual(wav.getnchannels(), 2)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertEqual(wav.getframerate(), 48000)
                self.assertEqual(wav.getnframes(), 30 * 48000)
                def values(frame, frames=512):
                    wav.setpos(frame)
                    raw = wav.readframes(frames)
                    if len(raw) != 4*frames:
                        raise AssertionError("Unexpected PCM frame length")
                    samples = array("h")
                    samples.frombytes(raw)
                    return samples
                # No fade to silence at a narration scene boundary.
                boundary = round(scene_plan["scenes"][0]["endMs"]*SAMPLERATE/1000)
                after = values(boundary)
                self.assertGreater(max(abs(x) for x in after), 120)
                # Different channels preserve some spatial width.
                stereo = values(SAMPLERATE*3)
                self.assertTrue(any(stereo[2*i] != stereo[2*i+1]
                                    for i in range(100)))
                # At an ordinary repeat of the 8s bed, the harmonic
                # oscillators are phase-continuous rather than jumping.
                before = values(LOOP_SECONDS*SAMPLERATE-1, 1)
                after_loop = values(LOOP_SECONDS*SAMPLERATE, 1)
                self.assertLess(abs(before[0]-after_loop[0]), 1200)
                self.assertLess(abs(before[1]-after_loop[1]), 1200)
                self.assertLess(max(abs(v) for v in stereo), 32767)

    def test_invalid_scene_limit_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sample = plan(topic="original music", script="A. B. C. D. E.",
                          character="Original owl", duration=30,shot_seconds=6)
            source=root/"plan.json"
            source.write_text(json.dumps(sample),encoding="utf-8")
            with self.assertRaises(ValueError):
                create_bed(plan_path=source,output=root/"no.wav",limit=0)
