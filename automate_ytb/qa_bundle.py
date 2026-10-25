"""Consolidate independent MP4 quality checks without losing their evidence.

A draft can only be described as technically ready if BOTH validation reports
pass; this never grants permission to publish to YouTube.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .production import _write_json, _sha

MAX_REPORT_BYTES = 2_000_000
MAX_VIDEO_BYTES = 2_000_000_000


def _load(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_REPORT_BYTES:
        raise ValueError("Quality report missing or unexpectedly large: " + path.name)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Quality report must be a JSON object")
    return data


def consolidate(*, structural_report: Path, media_report: Path,
                video: Path, srt: Path, vtt: Path,
                output: Path, visual_report: Path | None = None,
                story_report: Path | None = None,
                plan: Path | None = None) -> dict:
    structural = _load(structural_report)
    media = _load(media_report)
    if not video.is_file() or not 2048 <= video.stat().st_size <= MAX_VIDEO_BYTES:
        raise ValueError("Missing or oversized MP4 output")
    if not srt.is_file() or not vtt.is_file():
        raise ValueError("Both SRT and VTT subtitle formats are required")
    problems = []
    if structural.get("status") != "passed" or structural.get("errors"):
        problems.append("Structural video quality gate did not pass")
    if media.get("status") not in ("pass", "pass-with-warnings") or media.get("errors"):
        problems.append("Media/audio/subtitle validation did not pass")
    if structural.get("publicationApproved") is not False:
        problems.append("Unexpected approval flag in structural quality report")
    if media.get("publicationApproved") is not False:
        problems.append("Unexpected approval flag in media quality report")
    stream = media.get("media", {})
    if not isinstance(stream, dict):
        problems.append("Missing media metadata")
        stream = {}
    if stream.get("fileBytes") != video.stat().st_size:
        problems.append("Media report does not describe the present MP4 size")
    video_hash = _sha(video)
    if (story_report is None) != (plan is None):
        raise ValueError("Story preflight needs both a report and the source plan")
    story = _load(story_report) if story_report is not None else None
    if story is not None:
        if not plan.is_file() or story.get("sourcePlanSha256") != _sha(plan):
            problems.append("Story preflight does not describe current storyboard")
        if story.get("publicationApproved") is not False:
            problems.append("Story preflight unexpectedly approved publication")
        if story.get("factChecked") is not False:
            problems.append("Story preflight incorrectly claims fact checking")
        if story.get("status") not in (
                "sampled-clean", "review-recommended", "needs-editorial-revision"):
            problems.append("Story preflight has invalid status")
        if not isinstance(story.get("exactRepeatCount"), int) or (
                isinstance(story.get("exactRepeatCount"), bool)):
            problems.append("Story repetition evidence is incomplete")
    visual = _load(visual_report) if visual_report is not None else None
    if visual is not None:
        if visual.get("status") == "failed" or visual.get("technicalVisualCheckPassed") is not True:
            problems.append("Visual frame sampling reported invalid or black scenes")
        if visual.get("errors"):
            problems.append("Visual review includes blocking errors")
        if visual.get("schemaVersion", 1) >= 2:
            compared = visual.get("motionPairsCompared")
            frozen = visual.get("frozenAnimatedSceneCount")
            if (not isinstance(compared, int) or isinstance(compared, bool)
                    or compared != visual.get("sampledSceneCount")):
                problems.append("Visual motion analysis is incomplete")
            if not isinstance(frozen, int) or isinstance(frozen, bool) or frozen < 0:
                problems.append("Visual motion freezing count is invalid")
            elif frozen:
                problems.append("Frozen original animation detected in encoded MP4")
        if visual.get("publicationApproved") is not False:
            problems.append("Unexpected visual publication approval flag")
        if visual.get("videoSha256") != video_hash:
            problems.append("Visual review does not describe the current video")
        if not isinstance(visual.get("sampledSceneCount"), int) or visual.get("sampledSceneCount", 0) < 1:
            problems.append("Visual review did not verify any frames")
    # Structural gate hashes the MP4 independently.
    claimed = structural.get("checks", {})
    if not isinstance(claimed, dict):
        problems.append("Missing structural metrics")
        claimed = {}
    try:
        encoded_duration = float(claimed.get("actualDurationSeconds"))
        independent_duration = float(stream.get("durationSeconds"))
        if abs(encoded_duration - independent_duration) > 0.1:
            problems.append("Independent media duration reports disagree")
    except (ValueError, TypeError):
        problems.append("Quality reports lack comparable MP4 duration")
    if not vtt.read_text(encoding="utf-8").startswith("WEBVTT\n"):
        problems.append("VTT subtitles do not have the required signature")
    if not srt.read_text(encoding="utf-8-sig").strip():
        problems.append("SRT is empty")
    report = {
        "schemaVersion": 1,
        "status": "failed" if problems else "passed",
        "technicalPreviewReady": not problems,
        "editorialRevisionRecommended": (
            story.get("status") == "needs-editorial-revision"
            if story is not None else None),
        "publicationApproved": False,
        "humanEditorialReviewRequired": True,
        "checks": {
            "structural": structural.get("status"),
            "media": media.get("status"),
            "mp4DurationSeconds": stream.get("durationSeconds"),
            "mp4Width": stream.get("width"),
            "mp4Height": stream.get("height"),
            "mp4Sha256": video_hash,
            "subtitleCues": media.get("subtitleCues"),
            "visualScenesSampled": visual.get("sampledSceneCount") if visual is not None else None,
            "nearBlackVisualSamples": visual.get("nearBlackSceneCount") if visual is not None else None,
            "visualMotionPairs": visual.get("motionPairsCompared") if visual is not None else None,
            "frozenAnimatedScenes": visual.get("frozenAnimatedSceneCount") if visual is not None else None,
            "narrationExactRepeatCount": (
                story.get("exactRepeatCount") if story is not None else None),
            "narrationNearRepeatNeighborCount": (
                story.get("nearRepeatNeighborCount") if story is not None else None),
            "narrationPaceWarnings": (
                story.get("speakingPaceWarningCount") if story is not None else None),
            "integratedLufs": media.get("integratedLufs"),
            "truePeakDbtp": media.get("truePeakDbtp"),
            "masteringTargetLufs": media.get("targetLufs"),
            "srtSha256": _sha(srt),
            "vttSha256": _sha(vtt),
        },
        "sourceReports": {
            "structural": structural_report.name,
            "media": media_report.name,
            "visual": visual_report.name if visual_report is not None else None,
            "story": story_report.name if story_report is not None else None,
        },
        "errors": problems,
        "warnings": list(dict.fromkeys(
            list(structural.get("warnings") or []) +
            list(media.get("warnings") or []) +
            list(visual.get("warnings") or [] if visual is not None else []) +
            list(story.get("warnings") or [] if story is not None else []))),
        "limitations": [
            "Both checks assess technical validity, not narrative quality.",
            "No human fact-checking, originality or publication permission is implied.",
            "Narration timing is not word-level forced alignment.",
            "EBU R128 loudness measurements do not replace listening-based review.",
            "Visual inspection samples at most 24 scenes twice; it is not a full video quality guarantee.",
            "Near-static motion may be sampled at coincident poses; manual review remains required.",
            "Narration repetition/pace heuristics are not fact checking or story coherence review.",
        ],
    }
    _write_json(output.resolve(), report)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Combine independent MP4 QA evidence")
    p.add_argument("--structural", required=True, type=Path)
    p.add_argument("--media", required=True, type=Path)
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--srt", required=True, type=Path)
    p.add_argument("--vtt", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--visual", type=Path,
                   help="Optional sampled real-frame review required to pass when supplied")
    p.add_argument("--story", type=Path,
                   help="Optional original-script editorial repetition review")
    p.add_argument("--plan", type=Path,
                   help="Source storyboard used to verify the editorial report")
    a = p.parse_args(argv)
    try:
        report = consolidate(structural_report=a.structural,
                             media_report=a.media, video=a.video,
                             srt=a.srt, vtt=a.vtt, output=a.output,
                             visual_report=a.visual,
                             story_report=a.story, plan=a.plan)
        print(json.dumps({"status": report["status"],
                          "technicalPreviewReady": report["technicalPreviewReady"],
                          "errors": report["errors"]}, ensure_ascii=False))
        return 0 if report["technicalPreviewReady"] else 2
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
