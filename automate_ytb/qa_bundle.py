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
                output: Path) -> dict:
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
            "integratedLufs": media.get("integratedLufs"),
            "truePeakDbtp": media.get("truePeakDbtp"),
            "masteringTargetLufs": media.get("targetLufs"),
            "srtSha256": _sha(srt),
            "vttSha256": _sha(vtt),
        },
        "sourceReports": {
            "structural": structural_report.name,
            "media": media_report.name,
        },
        "errors": problems,
        "warnings": list(dict.fromkeys(
            list(structural.get("warnings") or []) +
            list(media.get("warnings") or []))),
        "limitations": [
            "Both checks assess technical validity, not narrative quality.",
            "No human fact-checking, originality or publication permission is implied.",
            "Narration timing is not word-level forced alignment.",
            "EBU R128 loudness measurements do not replace listening-based review.",
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
    a = p.parse_args(argv)
    try:
        report = consolidate(structural_report=a.structural,
                             media_report=a.media, video=a.video,
                             srt=a.srt, vtt=a.vtt, output=a.output)
        print(json.dumps({"status": report["status"],
                          "technicalPreviewReady": report["technicalPreviewReady"],
                          "errors": report["errors"]}, ensure_ascii=False))
        return 0 if report["technicalPreviewReady"] else 2
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
