"""Validate a real narrated forest Actions artifact before permanent delivery.

Distribution invariant:
  temporary Actions ZIP -> SHA-256 / codec / full decode -> immutable GitHub
  Release assets -> unauthenticated direct download with identical checksum.
This script never uploads or publishes, and never accepts a fabricated QA
manifest as sufficient evidence of a real decodable movie.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

SOURCE_VIDEO = "forest-narrated-en.mp4"
SOURCE_QA = "forest-narrated-en.json"
ASSET_VIDEO = "forest-discovery.mp4"
ASSET_QA = "forest-discovery-manifest.json"
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024 - 1


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(piece)
    return hasher.hexdigest()


def _unique_file(base: Path, name: str) -> Path:
    files = list(base.rglob(name))
    if len(files) != 1:
        raise ValueError(f"Expected one original artifact {name}, found {len(files)}")
    path = files[0].resolve(strict=True)
    if not path.is_file() or not path.is_relative_to(base.resolve(strict=True)):
        raise ValueError("Artifact path escapes trusted extraction directory")
    return path


def prepare(source: Path, output: Path, run_id: int) -> dict:
    """Return independent QA evidence and copy bit-identical final asset."""
    if type(run_id) is not int or not 1 <= run_id <= 10**15:
        raise ValueError("Invalid successful source workflow run")
    if not isinstance(source, Path) or not isinstance(output, Path):
        raise ValueError("Use concrete artifact and delivery directories")
    base = source.resolve(strict=True)
    if not base.is_dir():
        raise ValueError("Actions artifact must be an extracted directory")
    video = _unique_file(base, SOURCE_VIDEO)
    qa_path = _unique_file(base, SOURCE_QA)
    if video.stat().st_size < 100_000 or video.stat().st_size >= MAX_VIDEO_SIZE:
        raise ValueError("Video must be a real bounded-size MP4 Release asset")
    manifest = json.loads(qa_path.read_text(encoding="utf-8"))
    if (manifest.get("type") != "original-25d-measured-kokoro-narrated-short"
            or manifest.get("animal") != "fox"
            or manifest.get("language") != "en"
            or manifest.get("voiceEngine") != "kokoro-natural"
            or manifest.get("publicationApproved") is not False
            or manifest.get("requiresListeningReview") is not True
            or manifest.get("fps") != 30
            or manifest.get("size") != [1080, 1920]
            or not isinstance(manifest.get("soundscape"), dict)
            or not manifest["soundscape"].get("version", "").startswith(
                "forest-original-voice-ducked-causal-soundscape-p47")
            or manifest["soundscape"].get("clippedSamples") != 0
            or not isinstance(manifest.get("frames"), int)
            or manifest["frames"] < 240):
        raise ValueError("Narrated artifact fails production provenance or sound QA")
    digest = sha256_file(video)
    if digest != manifest.get("videoSha256"):
        raise ValueError("MP4 SHA-256 differs from actual encoding QA")
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(video),
    ], capture_output=True, text=True, timeout=45, check=True)
    media = json.loads(probe.stdout)
    v = next((s for s in media.get("streams", [])
              if s.get("codec_type") == "video"), {})
    a = next((s for s in media.get("streams", [])
              if s.get("codec_type") == "audio"), {})
    duration = float(media["format"]["duration"])
    if (v.get("codec_name") != "h264"
            or (v.get("width"), v.get("height")) != (1080, 1920)
            or v.get("r_frame_rate") != "30/1"
            or a.get("codec_name") != "aac"
            or not 8 <= duration <= 90
            or abs(duration - float(manifest.get("durationSeconds", -999))) > .2):
        raise ValueError("Generated video is not valid audio/video Shorts format")
    subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(video),
        "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-",
    ], check=True, capture_output=True, timeout=300)
    output.mkdir(parents=True, exist_ok=True)
    delivered = output / ASSET_VIDEO
    shutil.copyfile(video, delivered)
    if sha256_file(delivered) != digest:
        raise RuntimeError("Delivered copy differs from verified original")
    result = {
        "schemaVersion": 1,
        "type": "public-github-release-unreviewed-original-short",
        "sourceRunId": run_id,
        "sourceEngine": "kokoro-natural",
        "sourceArtifact": "p35-real-kokoro-narrated-forest-en",
        "video": ASSET_VIDEO,
        "videoSha256": digest,
        "videoBytes": delivered.stat().st_size,
        "durationSeconds": round(duration, 3),
        "width": 1080, "height": 1920, "fps": 30,
        "videoCodec": "h264", "audioCodec": "aac",
        "soundscape": manifest["soundscape"]["version"],
        "technicalQA": "passed-full-decode-and-sha256",
        "humanEditorialReviewRequired": True,
        "publicationApproved": False,
        "notPublishedOnSocialNetworks": True,
        "delivery": "GitHub Release direct asset, not expiring Actions ZIP",
    }
    (output / ASSET_QA).write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    options = parser.parse_args()
    print("FOREST_RELEASE_QA_OK", json.dumps(
        prepare(options.artifact, options.output, options.run_id)))


if __name__ == "__main__":
    main()
