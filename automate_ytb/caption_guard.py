"""Check that exported SRT captions exactly preserve the authored scene script.

This is a deterministic integrity check, NOT speech recognition or forced
alignment. It deliberately refuses gaps, text edits and misplaced scene cues.
"""
from __future__ import annotations

import re

_TIME = re.compile(
    r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3})"
    r"\s+-->\s+"
    r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3})"
)


def _ms(parts: tuple[str, ...]) -> int:
    h, m, s, ms = map(int, parts)
    return ((h * 60 + m) * 60 + s) * 1000 + ms


def _normalized(value: str) -> str:
    return " ".join(value.split())


def audit_caption_text(srt: str, scenes: list[dict]) -> dict:
    """Validate cue ownership, continuity and full narration round-trip.

    Reports which scene failed without echoing potentially private narration.
    Input is the actual exported SRT, not the in-memory caption generator.
    """
    errors: list[str] = []
    if not scenes:
        return {"passed": False, "scenesVerified": 0, "cueCount": 0,
                "errors": ["No storyboard scenes to verify"]}

    normalized = srt.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    blocks = re.split(r"\n[ \t]*\n+", normalized) if normalized else []
    collected: list[list[str]] = [[] for _ in scenes]
    previous: int | None = None
    scene_index = 0

    for index, block in enumerate(blocks, start=1):
        lines = block.split("\n")
        if len(lines) < 3 or lines[0].strip() != str(index):
            errors.append(f"Subtitle cue {index} has invalid numbering or text")
            continue
        times = _TIME.fullmatch(lines[1].strip())
        if times is None:
            errors.append(f"Subtitle cue {index} has an invalid timestamp")
            continue
        start, end = _ms(times.groups()[:4]), _ms(times.groups()[4:])
        if end <= start:
            errors.append(f"Subtitle cue {index} has nonpositive duration")
        if previous is not None and start != previous:
            errors.append(f"Subtitle cue {index} has a gap or overlap")
        if previous is None and start != scenes[0]["startMs"]:
            errors.append("First subtitle does not start with the first scene")
        previous = end
        while scene_index < len(scenes) and start >= scenes[scene_index]["endMs"]:
            scene_index += 1
        if scene_index >= len(scenes):
            errors.append(f"Subtitle cue {index} falls after the storyboard")
            continue
        scene = scenes[scene_index]
        if start < scene["startMs"] or end > scene["endMs"]:
            errors.append(f"Subtitle cue {index} crosses a scene boundary")
        content = _normalized(" ".join(lines[2:]))
        if not content:
            errors.append(f"Subtitle cue {index} has no visible narration")
        collected[scene_index].append(content)

    verified = 0
    for index, (scene, text_parts) in enumerate(zip(scenes, collected), start=1):
        if _normalized(" ".join(text_parts)) != _normalized(scene["narration"]):
            errors.append(f"Subtitle text differs from original scene {index}")
        else:
            verified += 1
    if not blocks:
        errors.append("SRT contains no subtitle cues")
    if previous != scenes[-1]["endMs"]:
        errors.append("Subtitles do not reach the final storyboard boundary")
    return {"passed": not errors, "scenesVerified": verified,
            "cueCount": len(blocks), "errors": errors}
