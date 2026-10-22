"""CLI with honest offline drafts and optional official YouTube API discovery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .studio import build
from .youtube import discover_niches


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="automate-ytb", description=
        "Original YouTube drafts from your own facts and visual assets.")
    commands = p.add_subparsers(dest="cmd", required=True)
    create = commands.add_parser("create", help="Script, storyboard, voice, thumbnails, MP4 draft")
    create.add_argument("--topic", default="", help="Topic/question (overrides brief topic)")
    create.add_argument("--angle", default="", help="Creative angle")
    create.add_argument("--brief", type=Path, help="JSON file containing sourced facts")
    create.add_argument("--script", type=Path, help="Optional original script, one scene per paragraph")
    create.add_argument("--assets", type=Path, help="Optional owned/licensed image assets scene-01.png...")
    create.add_argument("--voice-file", type=Path, help="Optional existing recording WAV, MP3, M4A, FLAC")
    create.add_argument("--reference", default="", help="YouTube reference URL, never downloaded")
    create.add_argument("--duration", type=int, default=90, help="Minimum target duration (seconds)")
    create.add_argument("--style", choices=["cinematic", "cartoon", "documentary"], default="cinematic")
    create.add_argument("--language", choices=["fr", "en"], default="fr")
    create.add_argument("--tts", choices=["espeak", "off"], default="espeak")
    create.add_argument("--plan-only", action="store_true", help="Create assets without FFmpeg")
    create.add_argument("--output", type=Path, default=Path("outputs"))
    discovery = commands.add_parser("discover", help="Find candidate niches using official YouTube API")
    discovery.add_argument("--queries", nargs="+", required=True,
                           help="Starting topics to search (each quoted if multiple words)")
    discovery.add_argument("--days", type=int, default=90, help="Age of video window")
    discovery.add_argument("--min-views", type=int, default=20000)
    discovery.add_argument("--max-subscribers", type=int, default=100000)
    discovery.add_argument("--limit", type=int, default=20)
    discovery.add_argument("--output", type=Path, default=Path("outputs/niches.json"))
    args = p.parse_args(argv)
    try:
        if args.cmd == "create":
            result = build(
                args.topic, args.output, brief_path=args.brief,
                angle=args.angle, script_path=args.script, assets_dir=args.assets,
                audio_file=args.voice_file, reference=args.reference,
                style=args.style, language=args.language, duration=args.duration,
                plan_only=args.plan_only, tts=args.tts,
            )
            manifest = result["manifest"]
            print(json.dumps({
                "directory": result["folder"],
                "renderMode": manifest["renderMode"],
                "scenes": len(manifest["scenes"]),
                "durationSeconds": manifest["plannedDurationSeconds"],
                "voiceStatus": manifest["voiceStatus"],
                "manualReviewRequired": True,
            }, ensure_ascii=False))
        elif args.cmd == "discover":
            result = discover_niches(
                args.queries, days=args.days, min_views=args.min_views,
                max_subscribers=args.max_subscribers, limit=args.limit
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps({"output": str(args.output),
                              "channels": len(result["results"]),
                              "method": result["method"]}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
