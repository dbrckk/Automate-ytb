"""Speech-measured short captions and safe, understated ASS video overlays.

This renderer does NOT invent word timings or claim forced alignment. Each
displayed caption is individually synthesized as a natural Kokoro phrase;
its boundaries come from the exact generated PCM sample count.
"""
from __future__ import annotations

import math
from pathlib import Path
import re

from .captions import srt_time

MAX_CAPTION_CHARS = 44
MAX_CAPTION_WORDS = 8
MAX_CAPTIONS = 80


def caption_fragments(text: str) -> list[str]:
    """Split written narration into short *speakable* phrases without edits."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Caption text must be nonempty")
    plain = " ".join(text.split())
    # Never interpret user script as libass override tags or FFmpeg syntax.
    if any(c in plain for c in ("{", "}", "\\")):
        raise ValueError("Caption text includes unsupported ASS control characters")
    if any(ord(c) < 32 for c in plain):
        raise ValueError("Caption text contains control characters")
    parts: list[str] = []
    current: list[str] = []
    for word in plain.split():
        if len(word) > MAX_CAPTION_CHARS:
            raise ValueError("An uninterrupted narration word exceeds subtitle width")
        candidate = " ".join((*current, word))
        if current and (len(candidate) > MAX_CAPTION_CHARS or
                        len(current) >= MAX_CAPTION_WORDS):
            parts.append(" ".join(current))
            current = []
        current.append(word)
        # Punctuation boundaries are prose events, not estimated timecodes.
        if word.endswith((".", "!", "?", "…", ",", ";", ":")) and len(current) >= 3:
            parts.append(" ".join(current))
            current = []
    if current:
        parts.append(" ".join(current))
    if not parts or " ".join(parts) != plain:
        raise RuntimeError("Short caption segmentation changed the original script")
    return parts


def _valid_int(value) -> bool:
    return type(value) is int


def verify_measured_beats(beats: list[dict], *, duration_ms: int) -> list[dict]:
    """Validate PCM-grounded timelines and exact source text round-trip."""
    if (not isinstance(beats, list) or not 2 <= len(beats) <= 12 or
            not _valid_int(duration_ms) or not 8000 <= duration_ms <= 180000):
        raise ValueError("Invalid natural narration timeline")
    previous = 0
    all_cues: list[dict] = []
    for beat_index, beat in enumerate(beats, 1):
        if not isinstance(beat, dict) or beat.get("index") != beat_index:
            raise ValueError("Invalid narration beat numbering")
        start, end, text = (beat.get("startMs"), beat.get("endMs"),
                            beat.get("text"))
        if (not _valid_int(start) or not _valid_int(end) or
                not 0 <= previous <= start < end <= duration_ms or
                not isinstance(text, str)):
            raise ValueError("Invalid narration beat boundaries")
        parts = beat.get("captionSegments")
        if not isinstance(parts, list) or not parts:
            raise ValueError("Missing speech-measured caption segments")
        transcript: list[str] = []
        cursor = start
        for segment in parts:
            if not isinstance(segment, dict):
                raise ValueError("Invalid caption timing entry")
            a, b, words = (segment.get("startMs"), segment.get("endMs"),
                           segment.get("text"))
            if (not _valid_int(a) or not _valid_int(b) or
                    not cursor <= a < b <= end or
                    not isinstance(words, str) or not words.strip()):
                raise ValueError("Caption crosses a speaking or scene boundary")
            if any(c in words for c in ("{", "}", "\\", "\r", "\n")):
                raise ValueError("Unsafe caption characters")
            transcript.append(words.strip())
            all_cues.append({"startMs": a, "endMs": b, "text": words,
                             "beatIndex": beat_index})
            cursor = b
        if (" ".join(transcript) != " ".join(text.split())
                or parts[0]["startMs"] != start or parts[-1]["endMs"] != end):
            raise ValueError("Displayed captions do not preserve synthesized words")
        previous = end
    if len(all_cues) > MAX_CAPTIONS:
        raise ValueError("Too many caption overlays for safe video rendering")
    return all_cues


def _ass_time(milliseconds: int) -> str:
    cs = max(0, milliseconds) // 10
    hours, rem = divmod(cs, 360000)
    minutes, rem = divmod(rem, 6000)
    seconds, centiseconds = divmod(rem, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


_ASS_HEADER = """[Script Info]
Title: Original narrated mobile documentary
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Spoken,DejaVu Sans,61,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,145,190,565,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def export_caption_assets(beats: list[dict], *, duration_ms: int,
                          directory: Path) -> dict:
    """Export one SRT and per-shot ASS files with real speech phrase markers.

    FFmpeg can burn each scene's local ASS directly during its normal encode;
    no second 1080p re-encode or external caption web service is required.
    """
    cues = verify_measured_beats(beats, duration_ms=duration_ms)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    srt = directory / "speech-measured.srt"
    pieces = []
    for i, cue in enumerate(cues, 1):
        pieces.append(
            f"{i}\n{srt_time(cue['startMs'])} --> "
            f"{srt_time(cue['endMs'])}\n{cue['text']}\n"
        )
    srt.write_text("\n".join(pieces) + "\n", encoding="utf-8")

    ass_paths = []
    for i, beat in enumerate(beats):
        # The first scene starts at the video's initial black-free frame.
        # Later scene starts are the true next-beat PCM boundaries.
        scene_start = 0 if i == 0 else beat["startMs"]
        scene_end = (beats[i + 1]["startMs"]
                     if i + 1 < len(beats) else duration_ms)
        if not 0 <= scene_start < scene_end <= duration_ms:
            raise ValueError("Invalid scene-relative caption boundaries")
        dialogue: list[str] = []
        for cue in cues:
            if cue["beatIndex"] != i + 1:
                continue
            local_start = cue["startMs"] - scene_start
            local_end = cue["endMs"] - scene_start
            if not 0 <= local_start < local_end <= scene_end - scene_start:
                raise ValueError("Caption extends beyond the encoded shot")
            text = cue["text"]
            dialogue.append(
                f"Dialogue: 0,{_ass_time(local_start)},"
                f"{_ass_time(local_end + 9)},Spoken,,0,0,0,,"
                r"{\fad(85,100)}" + text
            )
        path = directory / f"scene-{i+1:02}.ass"
        path.write_text(_ASS_HEADER + "\n".join(dialogue) + "\n",
                        encoding="utf-8")
        ass_paths.append(path)
    return {
        "srtPath": str(srt),
        "assPaths": [str(p) for p in ass_paths],
        "captionCount": len(cues),
        "timestampMethod": "individual-Kokoro-PCM-phrase-samples",
        "wordLevelAligned": False,
        "burnedInCaptions": True,
        "captionSafeZoneNeedsHumanReview": True,
    }
