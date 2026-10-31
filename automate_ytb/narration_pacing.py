"""Measured post-TTS pacing gate for narrated native science Shorts.

Inspects exact PCM-derived scene tail padding, not text-based timing guesses.
It never edits the user's script or changes generated speech.
"""
from __future__ import annotations

MAX_SHORT_TAIL_MS = 1500
MAX_SHORT_TAIL_FRACTION = 0.20


def inspect(scene_pacing: list[dict], *, strict: bool = False) -> dict:
    if not isinstance(scene_pacing, list) or not 1 <= len(scene_pacing) <= 1200:
        raise ValueError("Narration pacing requires 1-1200 measured scenes")
    if type(strict) is not bool:
        raise ValueError("Strict pacing must be a boolean")

    rows = []
    for item in scene_pacing:
        if not isinstance(item, dict) or not isinstance(item.get("sceneId"), str):
            raise ValueError("Invalid measured scene pacing record")
        values = [item.get(key) for key in (
            "spokenAudioMs", "sceneDurationMs", "tailPaddingMs")]
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("Narration pacing must use non-negative integer milliseconds")
        spoken, duration, padding = values
        if spoken < 1 or duration < spoken or padding != duration - spoken:
            raise ValueError("Narration pacing record has inconsistent PCM durations")
        rows.append({
            "sceneId": item["sceneId"],
            "spokenAudioMs": spoken,
            "sceneDurationMs": duration,
            "tailPaddingMs": padding,
            "tailPaddingFraction": round(padding / duration, 4),
        })

    duration = sum(item["sceneDurationMs"] for item in rows)
    padding = sum(item["tailPaddingMs"] for item in rows)
    ratio = padding / duration
    too_long = [item["sceneId"] for item in rows
                if item["tailPaddingMs"] > MAX_SHORT_TAIL_MS]
    findings = []
    if too_long:
        findings.append(
            "Excessive digitally silent scene tails: " + ", ".join(too_long))
    if ratio > MAX_SHORT_TAIL_FRACTION:
        findings.append(
            "Narration leaves more than 20% of the selected video timeline as tail padding")
    return {
        "schemaVersion": 1,
        "method": "synthesized-pcm-scene-tail-silence-v1",
        "status": "failed" if strict and findings else
                  "review-recommended" if findings else "passed",
        "strictReleaseGate": strict,
        "maxAllowedSceneTailPaddingMs": MAX_SHORT_TAIL_MS,
        "maxAllowedTailPaddingFraction": MAX_SHORT_TAIL_FRACTION,
        "totalSceneDurationMs": duration,
        "totalTailPaddingMs": padding,
        "tailPaddingFraction": round(ratio, 4),
        "maxSceneTailPaddingMs": max(item["tailPaddingMs"] for item in rows),
        "scenes": rows,
        "errors": findings if strict else [],
        "warnings": [] if strict else findings,
        "recommendedAction": (
            "Write more original narration for sparse scenes, or choose a "
            "different authored duration; do not auto-invent factual claims."
            if findings else None),
        "limitations": [
            "This measures explicit PCM padding, not linguistic naturalness or word alignment.",
            "Punctuation and legitimate pauses inside synthesized speech are not counted.",
        ],
        "humanEditorialReviewRequired": True,
        "publicationApproved": False,
    }
