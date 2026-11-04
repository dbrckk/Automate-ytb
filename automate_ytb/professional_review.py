"""Professional editorial scorecard built from verified, real MP4 QA evidence.

This is a prioritised REVIEW aid, not an AI aesthetic rating or publication approval.
No external API, credentials, expensive inference or extra video decoding.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .production import _write_json

MAX_BYTES = 2_000_000


def _load(path: Path) -> dict:
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError("Missing or oversized review evidence: " + path.name)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Review evidence must be a JSON object")
    return value


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def assess(*, summary: dict, visual: dict, media: dict,
           pacing: dict | None = None) -> dict:
    if not all(isinstance(item, dict) for item in (summary, visual, media)):
        raise ValueError("Expected three complete QA reports")
    if summary.get("status") != "passed" or summary.get("technicalPreviewReady") is not True:
        raise ValueError("Professional review requires passed consolidated MP4 QA")
    if visual.get("technicalVisualCheckPassed") is not True:
        raise ValueError("Professional review requires decoded MP4 frame sampling")
    if media.get("status") not in ("pass", "pass-with-warnings"):
        raise ValueError("Professional review requires encoded audio/video QA")
    if pacing is not None and not isinstance(pacing, dict):
        raise ValueError("Invalid narration pacing evidence")
    rows = visual.get("frames")
    if not isinstance(rows, list) or not rows or len(rows) > 24:
        raise ValueError("Missing or excessive real MP4 frame evidence")
    movement = []
    luminance = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid sampled frame")
        motion = row.get("motion")
        if not isinstance(motion, dict):
            raise ValueError("Missing actual decoded motion pair")
        delta = _finite(motion.get("changedPixelFraction"))
        luma = _finite(row.get("meanLuminance"))
        if delta is None or not 0 <= delta <= 1 or luma is None or not 0 <= luma <= 255:
            raise ValueError("Invalid measured video frame metrics")
        movement.append(delta)
        luminance.append(luma)
    loudness = _finite(media.get("integratedLufs"))
    peak = _finite(media.get("truePeakDbtp"))
    target = _finite(media.get("targetLufs"))
    tasks = []

    def add(priority: str, domain: str, reason: str, action: str) -> None:
        tasks.append({"priority": priority, "domain": domain,
                      "evidence": reason, "action": action})

    # These are conservative review prompts, not arbitrary 'premium scores'.
    if any(delta < .012 for delta in movement):
        add("P0", "animation",
            "At least one sampled scene changes fewer than 1.2% of decoded pixels",
            "Review that scene in the MP4; add motivated foreground, subject and camera motion if appropriate")
    if len(movement) >= 3 and max(movement) - min(movement) < .015:
        add("P1", "editing",
            "Scene-to-scene sampled motion intensity varies by less than 1.5 percentage points",
            "Review pacing; vary shot scales and motion rhythm without arbitrary camera shake")
    if visual.get("nearDuplicateNeighborCount", 0) > 0:
        add("P0", "graphics",
            "Adjacent scene thumbnails are nearly identical",
            "Introduce different subjects, 3D compositions and causal interactions between scenes")
    if visual.get("suspectedBandedPortraitSceneCount", 0):
        add("P1", "composition",
            "At least one portrait sample resembles a narrow sharp strip",
            "Use full-height 9:16 staging; verify title, caption and safe areas")
    if any(v < 22 for v in luminance):
        add("P1", "lighting",
            "At least one scene has low average decoded luminance",
            "Inspect on a phone; raise subject separation rather than brightening all blacks")
    if loudness is None or peak is None:
        add("P0", "audio", "Missing measured encoded loudness or true peak",
            "Restore FFmpeg EBU R128 measurements before release")
    else:
        if target is not None and abs(loudness-target) > 2:
            add("P1", "audio",
                f"Encoded integrated loudness {loudness:.1f} LUFS differs from target {target:.1f}",
                "Rebalance narration and background bed; measure the final AAC again")
        if peak > -1:
            add("P0", "audio", f"Encoded true peak is {peak:.1f} dBTP",
                "Use a true-peak limiter and remeasure the final AAC")
    if pacing is not None:
        if pacing.get("status") == "failed":
            add("P0", "voice", "Synthesized scene pacing gate failed",
                "Rewrite scene narration or adjust authored shot durations; do not time-stretch speech")
        elif pacing.get("status") == "review-recommended":
            add("P1", "voice", "Synthesized speech leaves excessive scene tail padding",
                "Balance spoken duration across scenes and rerender with real Kokoro timings")
    if visual.get("nearBlackSceneCount", 0):
        add("P1", "lighting", "Some MP4 frames are nearly black",
            "Inspect night scenes on mobile; retain intended darkness while exposing the main subject")
    tasks.sort(key=lambda item: (item["priority"], item["domain"]))
    return {
        "schemaVersion": 1,
        "status": "editorial-review-required",
        "technicalPreviewReady": True,
        "publicationApproved": False,
        "humanListeningRequired": True,
        "humanVisualReviewRequired": True,
        "metrics": {
            "sampledScenes": len(rows),
            "meanChangedPixelFraction": round(sum(movement)/len(movement), 4),
            "minChangedPixelFraction": round(min(movement), 4),
            "maxChangedPixelFraction": round(max(movement), 4),
            "meanLuminance": round(sum(luminance)/len(luminance), 1),
            "integratedLufs": loudness,
            "truePeakDbtp": peak,
            "narrationPacing": pacing.get("status") if pacing else "not-measured",
        },
        "priorities": tasks,
        "mandatoryHumanChecks": [
            "Listen for synthetic pronunciation, emphasis and unpleasant transitions",
            "Watch the complete MP4 on an actual phone for scene clarity and rhythm",
            "Verify scientific claims, rights and appropriate source attribution",
        ],
        "limitations": [
            "Pixel motion is not equivalent to animation quality or storytelling",
            "Mean brightness is not a measure of cinematic lighting",
            "Loudness cannot establish naturalness or speech intelligibility",
            "Only the sampled MP4 frames are assessed; no subjective professional score is claimed",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Prioritised editorial review of a real encoded Short")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--visual", type=Path, required=True)
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--pacing", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = assess(
            summary=_load(args.summary),
            visual=_load(args.visual),
            media=_load(args.media),
            pacing=_load(args.pacing) if args.pacing and args.pacing.exists() else None,
        )
        _write_json(args.output, report)
        print(json.dumps({"status": report["status"],
                          "priorities": report["priorities"],
                          "metrics": report["metrics"]}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
