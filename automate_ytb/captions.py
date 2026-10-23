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


def subtitles_for_scenes(scenes: list[dict]) -> tuple[str, dict]:
    output: list[str] = []
    cue = 0
    warnings = []
    for scene in scenes:
        text = " ".join(scene["narration"].split())
        parts = _chunks(text)
        start, stop = scene["startMs"], scene["endMs"]
        if not 0 <= start < stop:
            raise ValueError("Invalid scene subtitle boundaries")
        duration = stop - start
        if duration < len(parts):
            raise ValueError("Too little time for nonempty subtitle cues")
        weights = [max(1, len(part.replace("\n", " ").split())) for part in parts]
        total = sum(weights)
        stamp = start
        used = 0
        for i, (part, weight) in enumerate(zip(parts, weights)):
            used += weight
            next_stamp = (stop if i == len(parts) - 1
                          else min(stop - len(parts) + i + 1,
                                   start + round(duration * used / total)))
            if next_stamp <= stamp:
                next_stamp = stamp + 1
            cue += 1
            output.append(f"{cue}\n{srt_time(stamp)} --> {srt_time(next_stamp)}\n{part}\n")
            if next_stamp - stamp < 650:
                warnings.append(f"Short subtitle cue {cue}: check script pacing")
            stamp = next_stamp
    return "\n".join(output), {
        "cueCount": cue,
        "method": "estimated-proportional-phrases",
        "wordLevelAligned": False,
        "maxLines": MAX_LINES,
        "maxLineCharsForOrdinaryWords": MAX_LINE_CHARS,
        "warnings": warnings[:20],
    }
