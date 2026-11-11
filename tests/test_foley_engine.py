"""Real, encoded audiovisual proof of original MasterTimeline Foley mixing."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave

from automate_ytb.master_timeline import (
    Beat, MasterTimeline, PropertyEvent, SoundCue, WorldObject)
from automate_ytb.foley_engine import (
    create_causal_foley, mix_causal_foley, RATE, VERSION)


def timeline(*, cues: bool = True) -> MasterTimeline:
    return MasterTimeline(
        fps=30, audio_sample_rate=RATE, total_frames=60,
        objects=[WorldObject("parcel", {"x": 0., "value": 1}, unit="units")],
        beats=[Beat("start", 0, 30), Beat("outcome", 30, 60)],
        events=[PropertyEvent("parcel-grow", "parcel", "value", 16, 53, 1, 20),
                PropertyEvent("parcel-shift", "parcel", "x", 24, 55, 0, 25)],
        cues=[SoundCue("grow-sound", "parcel-grow", "growth", gain_db=-16),
              SoundCue("move-sound", "parcel-shift", "whoosh", offset_frames=1)]
        if cues else [],
    )


class CausalFoleyUnitTests(unittest.TestCase):
    def test_original_stereo_wav_has_sample_exact_onsets_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            first = root / "a" / "foley-original.wav"
            second = root / "b" / "foley-original.wav"
            one = create_causal_foley(timeline=timeline(), output=first,
                                      duration_seconds=2.)
            two = create_causal_foley(timeline=timeline(), output=second,
                                      duration_seconds=2.)
            self.assertEqual(one["version"], VERSION)
            self.assertEqual(one, two)
            self.assertEqual(one["cueCount"], 2)
            self.assertEqual(one["events"][0]["atFrame"], 16)
            self.assertEqual(one["events"][0]["atSample"], 25600)
            self.assertEqual(one["events"][1]["atSample"], 40000)
            self.assertFalse(one["containsThirdPartyAudio"])
            self.assertFalse(one["humanReviewed"])
            self.assertFalse(one["publicationApproved"])
            self.assertEqual(one["wavSha256"], hashlib.sha256(first.read_bytes()).hexdigest())
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with wave.open(str(first), "rb") as wav:
                self.assertEqual((wav.getframerate(), wav.getnchannels(),
                                  wav.getsampwidth(), wav.getnframes()),
                                 (48000, 2, 2, 96000))
                before = wav.readframes(25500)
                onset = wav.readframes(14500)
                self.assertTrue(all(sample == 0 for sample in before))
                stereo = list(struct.iter_unpack("<hh", onset))
                self.assertGreater(max(abs(left)+abs(right)
                                       for left,right in stereo), 200)
                self.assertTrue(any(left != right for left,right in stereo))
            manifest = json.loads((first.parent / "foley-report.json").read_text())
            self.assertEqual(manifest, one)

    def test_fail_closed_for_missing_cues_invalid_durations_rates_and_bools(self):
        with tempfile.TemporaryDirectory() as workspace:
            f = Path(workspace) / "foley-original.wav"
            for invalid in (True, float("nan"), float("inf"), 0, 181):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    create_causal_foley(timeline=timeline(), output=f,
                                        duration_seconds=invalid)
            with self.assertRaises(ValueError):
                create_causal_foley(timeline=timeline(cues=False), output=f,
                                    duration_seconds=2)
            with self.assertRaises(ValueError):
                create_causal_foley(timeline=timeline(), output=f,
                                    duration_seconds=.3)
            self.assertFalse(f.exists())

    def test_silent_non_authored_episodes_are_not_given_random_soundtracks(self):
        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaises(ValueError):
                mix_causal_foley(
                    silent_video=Path(workspace) / "no.mp4",
                    foley=Path(workspace) / "no.wav",
                    output=Path(workspace) / "out.mp4",
                    duration_seconds=2, profile="preview")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Real free FFmpeg required to test encoded AAC mix")
class CausalFoleyRealMediaTests(unittest.TestCase):
    def test_real_final_aac_stems_music_voice_and_foley_survive(self):
        with tempfile.TemporaryDirectory(prefix="foley-real-encoded-") as workspace:
            root = Path(workspace)
            raw = root / "raw-video.mp4"
            narration = root / "real-voice.wav"
            music = root / "original-bed.wav"
            foley = root / "foley-original.wav"
            output = root / "final-audiovisual.mp4"
            subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=#193348:size=288x512:rate=30:duration=2",
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                "-an", str(raw)], check=True, timeout=40)
            for target, frequency in ((narration, 260), (music, 135)):
                subprocess.run([
                    "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration=2",
                    "-ar", "48000", str(target)], check=True, timeout=40)
            report = create_causal_foley(timeline=timeline(), output=foley,
                                         duration_seconds=2.)
            self.assertEqual(report["cueCount"], 2)
            from automate_ytb.media_qa import _audio_measurements
            for voice, bed, expected, target in (
                (narration, music, "ducked-narration-plus-original-bed+causal-foley", -16),
                (narration, None, "narration-only+causal-foley", -16),
                (None, music, "original-bed-only+causal-foley", -24),
            ):
                with self.subTest(mode=expected):
                    mode = mix_causal_foley(
                        silent_video=raw, voice=voice, music=bed,
                        foley=foley, output=output,
                        duration_seconds=2, profile="preview")
                    self.assertEqual(mode, expected)
                    probe = json.loads(subprocess.run([
                        "ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,codec_name,width,height,"
                        "sample_rate,channels", "-of", "json", str(output)],
                        capture_output=True, text=True, check=True,
                        timeout=40).stdout)
                    video = [x for x in probe["streams"] if x["codec_type"]=="video"]
                    audio = [x for x in probe["streams"] if x["codec_type"]=="audio"]
                    self.assertEqual((video[0]["width"],video[0]["height"],
                                      video[0]["codec_name"]), (288,512,"h264"))
                    self.assertEqual((audio[0]["codec_name"],audio[0]["sample_rate"],
                                      audio[0]["channels"]), ("aac","48000",2))
                    self.assertAlmostEqual(float(probe["format"]["duration"]),2.,delta=.07)
                    measured = _audio_measurements(output)
                    self.assertAlmostEqual(measured["integratedLufs"],target,delta=4.)
                    self.assertLessEqual(measured["truePeakDbtp"], -1.)
                    self.assertGreater(output.stat().st_size, 8000)


if __name__ == "__main__":
    unittest.main()
