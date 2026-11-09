"""Gate for durable public video links: never publish an unverified MP4.

GitHub Actions artifacts expire. A GitHub Release asset is a public HTTPS file
with no chat-session dependency. The corresponding release workflow must
publish only after this strict media/manifest check, then fetch the public URL.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


def verify_release_video(video: Path, report: Path) -> dict:
    if not isinstance(video, Path) or video.suffix.lower() != ".mp4":
        raise ValueError("Release asset must be an MP4")
    if not isinstance(report, Path) or report.suffix.lower() != ".json":
        raise ValueError("Release provenance must be JSON")
    if not video.is_file() or video.stat().st_size < 100000:
        raise ValueError("Release video is missing or suspiciously small")
    qa = json.loads(report.read_text(encoding="utf-8"))
    digest = hashlib.sha256(video.read_bytes()).hexdigest()
    if qa.get("videoSha256") != digest:
        raise ValueError("Video SHA-256 differs from signed render manifest")
    if (qa.get("voiceEngine") != "kokoro-natural"
            or qa.get("soundscape", {}).get("clippedSamples") != 0
            or qa.get("size") != [1080, 1920]
            or qa.get("fps") != 30
            or qa.get("frames", 0) < 240
            or qa.get("publicationApproved") is not False):
        raise ValueError("Unverified or socially-approved production metadata")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True, timeout=40)
    media = json.loads(probe.stdout)
    streams = media.get("streams", [])
    video_stream = next((x for x in streams if x.get("codec_type") == "video"), {})
    audio_stream = next((x for x in streams if x.get("codec_type") == "audio"), {})
    if (video_stream.get("codec_name") != "h264"
            or video_stream.get("width") != 1080
            or video_stream.get("height") != 1920
            or audio_stream.get("codec_name") != "aac"
            or abs(float(media["format"]["duration"]) -
                   float(qa["durationSeconds"])) > .2):
        raise ValueError("Release asset is not the validated narrated Short")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror",
                    "-i", str(video), "-f", "null", "-"],
                   capture_output=True, check=True, timeout=180)
    return {"sha256": digest, "sizeBytes": video.stat().st_size,
            "durationSeconds": qa["durationSeconds"],
            "releaseVerified": True}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: verify_release_video.py VIDEO.mp4 MANIFEST.json")
    print(json.dumps(verify_release_video(Path(sys.argv[1]),
                                          Path(sys.argv[2])), indent=2))
