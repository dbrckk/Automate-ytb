"""Original, event-locked 48 kHz stereo Foley for authored MasterTimeline.

Every cue originates from an approved visual PropertyEvent. The synthesis is
pure mathematics: no downloaded samples, third-party licenses or online APIs.
It writes PCM in bounded chunks rather than holding an entire episode in RAM.
Only explicit opted-in science timelines activate this module in production.
"""
from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

from .encoding_profiles import aac_args
from .master_timeline import MasterTimeline

VERSION = "causal-foley-stereo-48k-v1"
RATE = 48000
BLOCK = 4096
TAU = math.tau
# Each sound has a distinct envelope and frequency trajectory.
PROFILES = {
    "count": (.13, 640., 12.),
    "growth": (.50, 350., 5.),
    "contact": (.21, 185., 12.),
    "whoosh": (.58, 140., 3.),
    "reveal": (.69, 510., 4.),
    "water": (.76, 115., 3.),
    "electrical": (.26, 425., 11.),
    "scale-transition": (.62, 230., 3.5),
}


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sfx(index: int, profile: tuple[float, float, float], seed: int,
         family: str) -> float:
    """Time-domain deterministic transient, with no random global state."""
    duration, base, decay = profile
    t = index / RATE
    if t < 0 or t >= duration:
        return 0.
    attack = min(1., t / (.024 if family in {"whoosh", "water"} else .006))
    fade = min(1., (duration - t) / .018)
    envelope = attack * fade * math.exp(-decay * t)
    # Low-frequency movement is shaped to create real but restrained accents;
    # fractional frequency slope creates rises for growth/scale/reveals.
    sweep = 160 if family in {"growth", "scale-transition", "reveal"} else -40
    phase = TAU * (base*t + .5*sweep*t*t)
    detune = (seed % 29) * .004
    tone = math.sin(phase + detune) + .23 * math.sin(phase*1.98 + detune)
    airy = .32 * math.sin(TAU * (base * 1.43*t + .17 * math.sin(27*t)) +
                          seed % 19)
    return envelope * (tone*.69 + airy)


def create_causal_foley(*, timeline: MasterTimeline, output: Path,
                        duration_seconds: float) -> dict:
    """Render a bounded, true stereo WAV with sample-exact event anchors.

    Media duration is taken from the actual PCM-adjusted scene plan, not
    inferred from the rounded number of video frames. The gap is at most
    half a frame; events outside the real duration are rejected.
    """
    if type(timeline) is not MasterTimeline or timeline.fps != 30:
        raise ValueError("Foley requires a validated 30 fps MasterTimeline")
    if (type(duration_seconds) not in (int, float)
            or not math.isfinite(duration_seconds)
            or not .1 <= duration_seconds <= 180):
        raise ValueError("Original Foley is limited to 0.1–180-second episodes")
    if timeline.audio_sample_rate != RATE:
        raise ValueError("Foley requires an exact 48 kHz PCM timeline")
    events = timeline.audio_events()
    if not 1 <= len(events) <= 64:
        raise ValueError("Foley requires 1–64 genuinely authored visual cues")
    total = round(duration_seconds * RATE)
    profiles = []
    for cue in events:
        if type(cue.get("atSample")) is not int or not 0 <= cue["atSample"] < total:
            raise ValueError("An event lies outside the actual PCM episode")
        if cue["family"] not in PROFILES:
            raise ValueError("Unsupported causal sound family")
        seed = int.from_bytes(hashlib.sha256(cue["id"].encode("utf-8")).digest()[:4],
                              "big")
        seconds, _, _ = PROFILES[cue["family"]]
        profiles.append({
            "cue": cue, "profile": PROFILES[cue["family"]],
            "start": cue["atSample"],
            "end": min(total, cue["atSample"] + round(seconds * RATE)),
            "seed": seed,
            "pan": ((seed % 11) - 5) * .025,
            "gain": min(.22, .20 * 10**(cue["gainDb"] / 20)),
        })
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    peak = 0
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        for first in range(0, total, BLOCK):
            count = min(BLOCK, total-first)
            left, right = [0.]*count, [0.]*count
            for e in profiles:
                lo, hi = max(first, e["start"]), min(first+count, e["end"])
                if lo >= hi:
                    continue
                for absolute in range(lo, hi):
                    j = absolute - first
                    local = absolute - e["start"]
                    signal = (e["gain"] * _sfx(local, e["profile"], e["seed"],
                                              e["cue"]["family"]))
                    left[j] += signal * (1.-e["pan"])
                    right[j] += signal * (1.+e["pan"])
            pcm = array("h")
            for l, r in zip(left, right):
                for sample in (l, r):
                    v = int(round(max(-.9, min(.9, sample)) * 32767))
                    peak = max(peak, abs(v))
                    pcm.append(v)
            if sys.byteorder != "little":
                pcm.byteswap()
            wav.writeframesraw(pcm.tobytes())
    report = {
        "version": VERSION,
        "source": "procedural-original-no-third-party-assets",
        "sampleRateHz": RATE, "channels": 2,
        "durationSeconds": total / RATE, "samplesPerChannel": total,
        "peakSampleDbfs": (round(20*math.log10(peak / 32767), 2)
                           if peak else -120.),
        "containsThirdPartyAudio": False, "externalApiCalls": 0,
        "cueCount": len(events), "events": events,
        "wavSha256": _digest(output),
        "humanReviewed": False, "publicationApproved": False,
    }
    report_file = output.parent / "foley-report.json"
    report_file.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return report


def mix_causal_foley(*, silent_video: Path, foley: Path, output: Path,
                     duration_seconds: float, profile: str,
                     voice: Path | None = None,
                     music: Path | None = None) -> str:
    """Combine causal SFX with actual voice/music and master the encoded AAC.

    The existing legacy FFmpeg mix remains entirely unchanged for episodes
    without explicit MasterTimeline cues. A voice or music base is required
    because silent QA previews intentionally remain video-only.
    """
    if voice is None and music is None:
        raise ValueError("Foley mix requires a real narration or music stem")
    if (type(duration_seconds) not in (int, float)
            or not math.isfinite(duration_seconds)
            or not 0 < duration_seconds <= 180):
        raise ValueError("Invalid bounded Foley mix duration")
    paths = [silent_video]
    if voice is not None:
        paths.append(voice)
    if music is not None:
        paths.append(music)
    paths.append(foley)
    if any(not isinstance(p, Path) or not p.is_file() for p in paths):
        raise ValueError("Causal mix requires existing local media files")
    inputs = []
    for p in paths:
        inputs.extend(("-i", str(p.resolve())))
    has_voice, has_music = voice is not None, music is not None
    parts: list[str] = []
    channels: list[str] = []
    if has_voice:
        voice_index = 1
        speech = (f"[{voice_index}:a]aresample=48000,highpass=f=70,"
                  "acompressor=threshold=0.15:ratio=2:attack=12:release=160")
        if has_music:
            parts.append(speech + ",asplit=2[spoken][control]")
        else:
            parts.append(speech + "[spoken]")
        channels.append("[spoken]")
    if has_music:
        music_index = 2 if has_voice else 1
        parts.append(f"[{music_index}:a]aresample=48000,highpass=f=70,"
                     "volume=0.24[bed]")
        if has_voice:
            parts.append("[bed][control]sidechaincompress="
                         "threshold=0.02:ratio=7:attack=25:release=350[ducked]")
            channels.append("[ducked]")
        else:
            channels.append("[bed]")
    index = len(paths)-1
    parts.append(f"[{index}:a]aresample=48000,highpass=f=60,"
                 "volume=0.58[causal]")
    channels.append("[causal]")
    target = -16 if has_voice else -24
    parts.append("".join(channels) +
                 f"amix=inputs={len(channels)}:duration=longest:normalize=0,"
                 "alimiter=limit=0.92,"
                 f"loudnorm=I={target}:LRA=11:TP=-1.5[out]")
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        *inputs, "-filter_complex", ";".join(parts),
        "-map", "0:v:0", "-map", "[out]",
        "-c:v", "copy", *aac_args(profile, music_only=not has_voice),
        "-ac", "2", "-t", f"{duration_seconds:.3f}",
        "-movflags", "+faststart", str(output),
    ]
    try:
        done = subprocess.run(command, capture_output=True, text=True,
                              timeout=1200, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Free FFmpeg causal audio mix is unavailable") from exc
    if done.returncode:
        raise RuntimeError("Causal Foley final mix failed: " + done.stderr[-1500:])
    return ("ducked-narration-plus-original-bed" if has_voice and has_music
            else "narration-only" if has_voice else "original-bed-only"
            ) + "+causal-foley"
