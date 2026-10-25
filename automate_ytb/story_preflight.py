"""Offline editorial preflight for user-authored original YouTube scripts.

Flags objective text repetition and potentially mismatched planned speaking
pace. It does NOT measure storytelling quality, check facts, replace an
editor, or silently rewrite a creator's narration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import sys
import unicodedata

from .production import load_plan, _write_json

VERSION = "story-preflight-v1"
MAX_FINDINGS = 30
# These short, non-topical words carry little information when comparing
# French and English scene descriptions. Numeric identifiers are not content.
STOP = frozenset("""
a an and are as at be by for from has have in into is it of on or
the their there these this to was were with you your then after before
un une de du des le la les et en dans sur au aux pour par avec qui que
est sont il elle ils elles son sa ses ce cette ces puis alors
""".split())


def _tokens(value: str) -> list[str]:
    clean = unicodedata.normalize("NFKD", value.casefold())
    clean = "".join(c for c in clean if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", clean)


def _signature(value: str) -> str:
    return " ".join(_tokens(value))


def _meaningful(value: str) -> set[str]:
    return {t for t in _tokens(value)
            if t not in STOP and not t.isdecimal() and len(t) > 2}


def _similarity(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def analyze(data: dict) -> dict:
    """Audit an already-validated plan, retaining only bounded excerpts."""
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise ValueError("Expected a valid storyboard plan")
    scenes = data["scenes"]
    if not 1 <= len(scenes) <= 1200:
        raise ValueError("Unexpected scene count")
    signatures: dict[str, str] = {}
    repeated = []
    near = []
    pace = []
    previous_content: set[str] = set()
    scene_lengths = []
    shots = Counter()
    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError("Scene must be an object")
        name, line = scene.get("id"), scene.get("narration")
        start, end = scene.get("startMs"), scene.get("endMs")
        if (not isinstance(name, str) or not isinstance(line, str)
                or not line.strip() or not isinstance(start, int)
                or not isinstance(end, int) or isinstance(start, bool)
                or isinstance(end, bool) or end <= start):
            raise ValueError("Invalid authored narration or scene timing")
        words = _tokens(line)
        scene_lengths.append(len(words))
        wpm = round(len(words) * 60000 / (end-start), 1)
        if wpm > 230 or (wpm < 55 and len(words) >= 3):
            pace.append({"sceneId": name, "wordsPerMinute": wpm,
                         "type": "fast" if wpm > 230 else "slow"})
        normalized = _signature(line)
        if normalized in signatures:
            repeated.append({"sceneId": name,
                             "firstSeenSceneId": signatures[normalized],
                             "excerpt": line[:140]})
        else:
            signatures[normalized] = name
        content = _meaningful(line)
        if idx and len(content) >= 4 and len(previous_content) >= 4:
            score = _similarity(content, previous_content)
            if score >= 0.82 and normalized != _signature(scenes[idx-1]["narration"]):
                near.append({"sceneId": name, "previousSceneId": scenes[idx-1]["id"],
                             "tokenSimilarity": round(score, 3),
                             "excerpt": line[:140]})
        previous_content = content
        shots[scene.get("camera", "unspecified")] += 1
    exact_fraction = len(repeated) / len(scenes)
    high_repetition = (len(scenes) >= 3
                       and (exact_fraction >= 0.35
                            or len(repeated) >= 3 and exact_fraction >= 0.25))
    warnings = []
    if repeated:
        warnings.append(
            f"{len(repeated)} scenes repeat a previous narration beat exactly")
    if near:
        warnings.append(
            f"{len(near)} adjacent pairs use nearly identical content words")
    if pace:
        warnings.append(
            f"{len(pace)} scenes have potentially awkward estimated speaking pace")
    if high_repetition:
        warnings.append(
            "Systematic exact narration repetition; revise the authored script")
    return {
        "schemaVersion": 1, "version": VERSION,
        "status": "needs-editorial-revision" if high_repetition else
                  "review-recommended" if warnings else "sampled-clean",
        "humanEditorialReviewRequired": True,
        "publicationApproved": False,
        "factChecked": False,
        "sceneCount": len(scenes),
        "exactRepeatCount": len(repeated),
        "nearRepeatNeighborCount": len(near),
        "speakingPaceWarningCount": len(pace),
        "repeatFraction": round(exact_fraction, 4),
        "averageWordsPerScene": round(sum(scene_lengths) / len(scenes), 1),
        "cameraShotTypesUsed": len(shots),
        "exactRepeats": repeated[:MAX_FINDINGS],
        "nearRepeatNeighbors": near[:MAX_FINDINGS],
        "speakingPaceFindings": pace[:MAX_FINDINGS],
        "findingsTruncated": any(len(items) > MAX_FINDINGS
                                 for items in (repeated, near, pace)),
        "warnings": warnings,
        "limitations": [
            "Text and pace heuristics cannot establish narrative coherence.",
            "Near-repetition flags may include intentional refrains or serial topics.",
            "Speaking pace is based on storyboard duration, not audible fluency.",
            "No automated fact-checking, originality proof, rights approval or publication.",
        ],
    }


def inspect(*, plan: Path, destination: Path | None = None) -> dict:
    data = load_plan(plan)
    report = analyze(data)
    report["sourcePlanSha256"] = hashlib.sha256(plan.read_bytes()).hexdigest()
    if destination is not None:
        _write_json(destination.resolve(), report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline storyboard repetition/pacing preflight")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = inspect(plan=args.plan, destination=args.report)
        print(json.dumps({
            "status": report["status"],
            "exactRepeatCount": report["exactRepeatCount"],
            "nearRepeatNeighborCount": report["nearRepeatNeighborCount"],
            "speakingPaceWarningCount": report["speakingPaceWarningCount"],
        }, ensure_ascii=False))
        # Editorial findings are review flags, not an arbitrary reason to
        # block an otherwise decodable draft MP4. Publication remains manual.
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
