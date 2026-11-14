"""Fail-closed, dependency-light request gate for public premium Shorts.

Runs before installing heavyweight Kokoro/torch dependencies. A push must
introduce exactly one new request, never modify or overwrite an old request.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

from .universal_script import _chunks, _concepts

_SAFE_REQUEST = re.compile(r"video_requests/[a-z0-9][a-z0-9_-]{0,70}\.json\Z")
_SHA = re.compile(r"[0-9a-f]{40}\Z")
MAX_SCRIPT_CHARS = 1800
MAX_SCRIPT_WORDS = 240


def _unique_fields(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("Duplicate JSON field: " + str(key))
        data[key] = value
    return data


def _new_push_request(before: str, head: str) -> dict:
    if not _SHA.fullmatch(before) or not _SHA.fullmatch(head):
        raise ValueError("Cannot prove valid source commits")
    changed = subprocess.check_output(
        ["git", "diff", "--name-status", "--no-renames", before, head,
         "--", "video_requests"], text=True
    ).splitlines()
    # Every change in this directory matters, including modifications and
    # deletions. Do not accept a new request plus a modified existing request.
    if len(changed) != 1 or not changed[0].startswith("A\t"):
        raise ValueError("Push must add exactly one new request, with no other request edits")
    relative = changed[0][2:]
    if not _SAFE_REQUEST.fullmatch(relative):
        raise ValueError("Unsafe request filename")
    source = Path(relative)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 12000:
        raise ValueError("Missing, linked or oversized request file")
    return json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_unique_fields)


def validate_request(*, event_name: str, before: str = "", head: str = "",
                     topic=None, script=None, language=None) -> dict:
    """Return a clean source-only request, or raise before expensive render."""
    if event_name == "push":
        request = _new_push_request(before, head)
        if type(request) is not dict or set(request) != {"topic", "script", "language"}:
            raise ValueError("Request JSON must contain only topic, script and language")
        topic, script, language = (request["topic"], request["script"], request["language"])
    elif event_name != "workflow_dispatch":
        raise ValueError("Unsupported event type")
    if any(type(value) is not str for value in (topic, script, language)):
        raise ValueError("Request fields must all be strings")
    topic, script = topic.strip(), script.strip()
    if not 3 <= len(topic) <= 120 or any(ord(c) < 32 or ord(c) == 127 for c in topic):
        raise ValueError("Topic must be a safe one-line title of 3–120 characters")
    if not 40 <= len(script) <= MAX_SCRIPT_CHARS:
        raise ValueError("Premium narration must be 40–1800 characters")
    if len(script.split()) > MAX_SCRIPT_WORDS:
        raise ValueError("Premium narration exceeds 240 words")
    if any((ord(c) < 32 and c not in "\r\n\t") or ord(c) == 127 for c in script):
        raise ValueError("Narration contains unsafe control characters")
    if language not in ("en", "fr"):
        raise ValueError("Narration language must be en or fr")
    # Apply the same first-pass story constraints as the real compiler, so
    # a one-sentence or malformed narration fails before pip/torch/model IO.
    for beat in _chunks(script):
        _concepts(beat, topic)
    # Rendering arbitrary generic circles is technically possible but was
    # rejected by human review (0/20). Premium production now refuses to
    # release a falsely advertised visual if the source vocabulary cannot
    # ground an original scene pack or continuous sourced scale world.
    from .universal_script import compile_original_script
    compiled=compile_original_script(topic=topic,script=script,language=language)
    has_scale=compiled.get("proceduralScaleJourney") is not None
    if not has_scale and any(not beat.get("visualVectors") for beat in compiled["beats"]):
        raise ValueError(
            "Premium artwork unavailable for one or more narrated scenes. "
            "Author an original visual pack for this subject before release; "
            "generic circle-and-label fallback is not premium.")
    if compiled.get("proceduralVisualFamily")=="maglev":
        from .premium_story_cues import action_sequence
        cues=action_sequence(compiled["beats"])
        if None in cues or len(set(cues))<2:
            raise ValueError(
                "Premium maglev narration needs two or more grounded, "
                "distinct visual actions, not a repeated static scene")
    return {"topic": topic, "script": script, "language": language}


def main() -> int:
    request = validate_request(
        event_name=os.environ.get("GITHUB_EVENT_NAME", ""),
        before=os.environ.get("BEFORE_COMMIT", ""),
        head=os.environ.get("GITHUB_SHA", ""),
        topic=os.environ.get("VIDEO_TOPIC", ""),
        script=os.environ.get("VIDEO_SCRIPT", ""),
        language=os.environ.get("VIDEO_LANGUAGE", ""),
    )
    root = Path("build/premium")
    root.mkdir(parents=True, exist_ok=True)
    (root / "topic.txt").write_text(request["topic"], encoding="utf-8")
    (root / "original-script.txt").write_text(request["script"] + "\n", encoding="utf-8")
    (root / "language.txt").write_text(request["language"], encoding="utf-8")
    print("Premium request preflight passed before dependency installation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
