"""Inspect *actual* generated mono narration PCM, independent of its label.

Every original short may use the same deterministic offline evidence. This
detects silent, truncated or wrong-rate output without guessing human
naturalness, recognizing phonemes, or relying on a paid voice API.
"""
from __future__ import annotations

from array import array
import hashlib
import math
from pathlib import Path
import sys
import wave

VERSION = "verified-real-pcm-narration-v1"
MAX_WAV_BYTES = 120_000_000


def inspect_narration(path: Path, *, engine: str) -> dict:
    """Check real WAV bytes and report reproducible, human-reviewable evidence."""
    if engine not in ("kokoro", "espeak"):
        raise ValueError("Unsupported narrator evidence engine")
    path = Path(path)
    if (not path.is_file() or path.is_symlink()
            or not 1024 <= path.stat().st_size <= MAX_WAV_BYTES):
        raise ValueError("Narration WAV is missing, unsafe or outside bounds")
    try:
        with wave.open(str(path), "rb") as source:
            rate = source.getframerate()
            nframes = source.getnframes()
            if (source.getnchannels() != 1 or source.getsampwidth() != 2
                    or source.getcomptype() != "NONE"
                    or not 8000 <= rate <= 48000
                    or (engine == "kokoro" and rate != 24000)
                    or not rate//2 <= nframes <= rate*180):
                raise ValueError("Narration must be bounded mono PCM16 at the expected rate")
            count = 0
            energy = 0
            peak = 0
            active = 0
            while True:
                data = source.readframes(8192)
                if not data:
                    break
                if len(data) % 2:
                    raise ValueError("Truncated PCM16 narration")
                values = array("h")
                values.frombytes(data)
                if sys.byteorder != "little":
                    values.byteswap()
                for sample in values:
                    value = abs(sample)
                    peak = max(peak, value)
                    energy += sample*sample
                    active += value >= 328
                count += len(values)
            if count != nframes:
                raise ValueError("Narration WAV frame count is inconsistent")
    except (EOFError, OSError, wave.Error) as exc:
        raise ValueError("Unreadable real narration WAV") from exc
    rms = math.sqrt(energy/count)/32768
    active_fraction = active/count
    if rms < .002 or active_fraction < .012:
        raise ValueError("Real narrator is effectively silent")
    with path.open("rb") as src:
        digest = hashlib.file_digest(src, "sha256").hexdigest()
    return {
        "version": VERSION,
        "engine": engine,
        "format": "PCM16-mono",
        "sampleRateHz": rate,
        "durationMs": round(count*1000/rate),
        "rmsDbfs": round(20*math.log10(rms), 2),
        "peakDbfs": round(20*math.log10(peak/32768), 2),
        "activeFraction": round(active_fraction, 4),
        "sha256": digest,
        "status": "verified-real-audio",
        "naturalnessVerified": False,
        "humanListeningRequired": True,
    }
