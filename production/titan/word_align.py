#!/usr/bin/env python3
"""Align known English Kokoro narration against the actual spoken WAV.

Whisper timestamps are derived from audio, not estimated from character count.
When recognition omits a word, interpolate it between *verified* neighbours and
report it. A poor or incoherent alignment is an error, never a claimed success.
"""
import difflib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def normalize(word):
    return re.sub(r"[^a-z0-9]", "", word.lower().replace("’", "'"))


def recover_words(script, observations, start, end):
    """Return words with monotonic timing; unmatched tokens are disclosed."""
    original = script.split()
    labels = [normalize(w) for w in original]
    audible = [normalize(x["word"]) for x in observations]
    matcher = difflib.SequenceMatcher(None, labels, audible, autojunk=False)
    matches = {}
    for m in matcher.get_matching_blocks():
        for step in range(m.size):
            i, j = m.a + step, m.b + step
            word = observations[j]
            a = max(start, min(end, float(word["start"])))
            b = max(start, min(end, float(word["end"])))
            if b > a and b-a < 2.0:
                matches[i] = (a, b)
    coverage = len(matches) / max(1, len(original))
    if coverage < 0.62:
        raise RuntimeError(
            f"Poor audio alignment ({coverage:.0%} matching): {script!r}; "
            f"transcript={' '.join(x['word'] for x in observations)!r}"
        )

    result = [None] * len(original)
    for index, (a, b) in matches.items():
        result[index] = {"word": original[index], "start": a, "end": b, "recognized": True}

    # Fill a mismatched word only between real speech anchors; mark it inferred.
    # Interpolate within bounded time rather than inventing an exact word boundary.
    pos = 0
    while pos < len(result):
        if result[pos] is not None:
            pos += 1
            continue
        last = pos
        while last < len(result) and result[last] is None:
            last += 1
        left = result[pos-1]["end"] if pos > 0 else start
        right = result[last]["start"] if last < len(result) else end
        if right <= left:
            left = result[pos-1]["start"] if pos > 0 else start
            right = result[last]["end"] if last < len(result) else end
        if right <= left:
            raise RuntimeError("Audio anchors not monotonic")
        weights = [max(1, len(normalize(original[k]))) for k in range(pos, last)]
        span = right-left
        running = left
        for k, weight in zip(range(pos, last), weights):
            finish = min(right, running + span * weight / sum(weights))
            result[k] = {"word": original[k], "start": running, "end": finish, "recognized": False}
            running = finish
        pos = last

    # Guard against recognizer words overlapping, while preserving whole sentences.
    previous = start
    for item in result:
        item["start"] = max(start, min(end, item["start"]))
        item["end"] = max(item["start"]+0.015, min(end, item["end"]))
        if item["start"] < previous - 0.12:
            raise RuntimeError("Word timestamps run backwards")
        item["start"] = max(previous, item["start"])
        item["end"] = max(item["start"]+.015, item["end"])
        previous = item["start"]
    return result, coverage


def align_narration(narration_wav, segments, folder, model_name="base.en"):
    from faster_whisper import WhisperModel

    folder = Path(folder)
    folder.mkdir(exist_ok=True, parents=True)
    pcm = folder / "voice_16khz.wav"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(narration_wav),
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(pcm)
    ], check=True)
    audio, rate = sf.read(pcm, dtype="float32")
    if rate != 16000 or audio.ndim != 1:
        raise RuntimeError("Resampled audio has wrong format")

    model = WhisperModel(model_name, device="cpu", compute_type="int8",
                         cpu_threads=4, num_workers=1)
    all_words = []
    report = []
    for index, seg in enumerate(segments):
        start, end = float(seg["start"]), float(seg["end"])
        clip = np.array(audio[round(start*rate):round(end*rate)], dtype=np.float32)
        if clip.size < rate // 3:
            raise RuntimeError(f"Empty speech segment {index}")
        sections, _ = model.transcribe(
            clip, language="en", beam_size=4, temperature=0.0,
            word_timestamps=True, condition_on_previous_text=False,
            vad_filter=False, initial_prompt="Titan. Saturn. Methane. Ethane. Celsius.",
        )
        observed = []
        for section in sections:
            for word in (section.words or []):
                observed.append({"word": word.word.strip(),
                                 "start": start+float(word.start),
                                 "end": start+float(word.end)})
        words, coverage = recover_words(seg["text"], observed, start, end)
        all_words.extend(words)
        report.append({"scene": index, "matching_word_fraction": round(coverage, 3),
                       "whisper_transcript": " ".join(x["word"] for x in observed),
                       "source_word_count": len(words),
                       "estimated_words": sum(not w["recognized"] for w in words)})
    overall = sum(x["recognized"] for x in all_words) / max(1,len(all_words))
    if overall < 0.76:
        raise RuntimeError(f"Audio/English script mismatch; verified words={overall:.1%}")

    (folder/"word_timestamps.json").write_text(
        json.dumps({"model": model_name, "measured_coverage": round(overall,3),
                    "method": "Whisper acoustic word timing + script/ASR matching",
                    "caveat": "Unrecognized words interpolated; see recognized flags",
                    "words": all_words, "scenes": report}, indent=2), encoding="utf-8")
    print("ALIGN_OK", f"verified={overall:.1%}", "words=", len(all_words), flush=True)
    return all_words, report
