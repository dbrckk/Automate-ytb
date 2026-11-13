"""Actual narrator WAV evidence: bounded PCM samples, rate, source hash, silence."""
from __future__ import annotations

from array import array
import math
from pathlib import Path
import sys
import tempfile
import unittest
import wave

from automate_ytb.universal_voice_evidence import inspect_narration


def _wav(target: Path, *, rate: int=24000, seconds: float=1.0,
         audible: bool=True, channels: int=1) -> None:
    n=round(rate*seconds)
    samples=array("h", (
        round(4600*math.sin(2*math.pi*440*i/rate)) if audible else 0
        for i in range(n*channels)
    ))
    if sys.byteorder!="little":
        samples.byteswap()
    with wave.open(str(target),"wb") as dst:
        dst.setnchannels(channels)
        dst.setsampwidth(2)
        dst.setframerate(rate)
        dst.writeframes(samples.tobytes())


class OriginalNarrationEvidenceTests(unittest.TestCase):
    def test_real_voiced_pcm_has_reproducible_integrity_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"real.wav"
            _wav(src)
            proof=inspect_narration(src,engine="kokoro")
            again=inspect_narration(src,engine="kokoro")
            self.assertEqual(proof,again)
            self.assertEqual(proof["status"],"verified-real-audio")
            self.assertEqual(proof["sampleRateHz"],24000)
            self.assertEqual(proof["format"],"PCM16-mono")
            self.assertEqual(proof["durationMs"],1000)
            self.assertEqual(len(proof["sha256"]),64)
            self.assertLess(proof["rmsDbfs"],0)
            self.assertGreater(proof["activeFraction"],.5)
            self.assertFalse(proof["naturalnessVerified"])
            self.assertTrue(proof["humanListeningRequired"])
            _wav(src,rate=24000,seconds=1.5)
            other=inspect_narration(src,engine="kokoro")
            self.assertNotEqual(other["sha256"],proof["sha256"])

    def test_real_wav_silence_and_invalid_headers_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"voice.wav"
            _wav(src,audible=False)
            with self.assertRaisesRegex(ValueError,"silent"):
                inspect_narration(src,engine="kokoro")
            _wav(src,rate=22050)
            with self.assertRaisesRegex(ValueError,"expected rate"):
                inspect_narration(src,engine="kokoro")
            self.assertEqual(inspect_narration(src,engine="espeak")["sampleRateHz"],
                             22050)
            _wav(src,rate=24000,seconds=.2)
            with self.assertRaises(ValueError):
                inspect_narration(src,engine="kokoro")
            _wav(src,channels=2)
            with self.assertRaises(ValueError):
                inspect_narration(src,engine="kokoro")
            src.write_bytes(b"definitely not a WAV file"*90)
            with self.assertRaises(ValueError):
                inspect_narration(src,engine="kokoro")
            with self.assertRaises(ValueError):
                inspect_narration(src,engine="unknown")

    def test_symlink_and_missing_voice_are_never_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/"original.wav"
            _wav(src)
            pointer=root/"pointer.wav"
            pointer.symlink_to(src)
            with self.assertRaises(ValueError):
                inspect_narration(pointer,engine="kokoro")
            with self.assertRaises(ValueError):
                inspect_narration(root/"missing.wav",engine="kokoro")


if __name__=="__main__":
    unittest.main()
