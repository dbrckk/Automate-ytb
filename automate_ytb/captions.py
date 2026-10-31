"""Readable SRT drafts split into short phrases without inventing word timing.

Proportional timings are *estimates*, not ASR-derived or forced alignment.
Source narration is never changed, summarized, or silently omitted.
"""
from __future__ import annotations

import re

MAX_LINE_CHARS = 40
MAX_LINES = 2


def srt_time(ms: int) -> str:
    h, remainder = divmod(ms, 3_600_000)
    m, remainder = divmod(remainder, 60_000)
    s, milli = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{milli:03d}"


def _chunks(text: str) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        raise ValueError("Cannot caption empty narration")
    result, lines, current = [], [], ""
    for word in words:
        if len(word) > MAX_LINE_CHARS:
            # Rare unbroken URLs or technical IDs cannot fit naturally:
            # return a standalone line rather than deleting any characters.
            if current:
                lines.append(current)
                current = ""
            if lines:
                result.append("\n".join(lines))
                lines = []
            result.append(word)
            continue
        candidate = (current + " " + word).strip()
        if len(candidate) <= MAX_LINE_CHARS:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) == MAX_LINES:
                result.append("\n".join(lines))
                lines = []
        if word.endswith((".", "!", "?", "…", ";", ":")) and len(lines) >= 1:
            if current:
                lines.append(current)
                current = ""
            result.append("\n".join(lines))
            lines = []
    if current:
        lines.append(current)
    if lines:
        result.append("\n".join(lines))
    return result


def caption_phrases(text: str) -> list[str]:
    """Exactly the visible, whitespace-normalized units shown in SRT cues."""
    return [" ".join(part.split()) for part in _chunks(text)]


def timed_cues_for_scene(scene: dict, *,
                         use_audio_boundaries: bool = False) -> list[dict]:
    """One canonical phrase timeline shared by SRT and baked portrait captions.

    Audio mode uses only the actual synthesized-phrase start/end markers,
    never invented word-level timings. Estimated mode uses the same
    proportional word weights as the historical SRT exporter.
    """
    text = " ".join(scene["narration"].split())
    parts = _chunks(text)
    start, stop = scene["startMs"], scene["endMs"]
    if not 0 <= start < stop:
        raise ValueError("Invalid scene subtitle boundaries")
    duration = stop - start
    timings = scene.get("captionSegments") if use_audio_boundaries else None
    if use_audio_boundaries:
        if not isinstance(timings, list) or len(timings) != len(parts):
            raise ValueError("Missing audio-derived caption timings for scene")
        previous = start
        for segment, part in zip(timings, parts):
            if not isinstance(segment, dict):
                raise ValueError("Invalid audio-derived caption entry")
            a, b = segment.get("startMs"), segment.get("endMs")
            if (not isinstance(a, int) or isinstance(a, bool)
                    or not isinstance(b, int) or isinstance(b, bool)
                    or a != previous or b <= a or b > stop):
                raise ValueError("Invalid audio-derived caption boundary")
            if " ".join(str(segment.get("text", "")).split()) != " ".join(part.split()):
                raise ValueError("Audio caption text differs from the original narration")
            previous = b
        if previous != stop:
            raise ValueError("Audio captions do not reach the scene end")
    if duration < len(parts):
        raise ValueError("Too little time for nonempty subtitle cues")
    weights = [max(1, len(part.replace("\n", " ").split())) for part in parts]
    total = sum(weights)
    stamp = start
    used = 0
    cues = []
    for i, (part, weight) in enumerate(zip(parts, weights)):
        used += weight
        next_stamp = (timings[i]["endMs"] if timings is not None else
                      stop if i == len(parts) - 1 else
                      min(stop - len(parts) + i + 1,
                          start + round(duration * used / total)))
        if next_stamp <= stamp:
            next_stamp = stamp + 1
        cues.append({"text": part, "startMs": stamp, "endMs": next_stamp})
        stamp = next_stamp
    return cues


def subtitles_for_scenes(scenes: list[dict], *,
                         use_audio_boundaries: bool = False) -> tuple[str, dict]:
    output: list[str] = []
    cue = 0
    warnings = []
    for scene in scenes:
        for segment in timed_cues_for_scene(
                scene, use_audio_boundaries=use_audio_boundaries):
            cue += 1
            start, stop = segment["startMs"], segment["endMs"]
            output.append(
                f"{cue}\\n{srt_time(start)} --> {srt_time(stop)}\\n"
                f"{segment['text']}\\n")
            if stop - start < 650:
                warnings.append(f"Short subtitle cue {cue}: check script pacing")
    return "\n".join(output), {
        "cueCount": cue,
        "method": ("audio-derived-synthesized-phrases" if use_audio_boundaries
                   else "estimated-proportional-phrases"),
        "wordLevelAligned": False,
        "maxLines": MAX_LINES,
        "maxLineCharsForOrdinaryWords": MAX_LINE_CHARS,
        "warnings": warnings[:20],
    }
