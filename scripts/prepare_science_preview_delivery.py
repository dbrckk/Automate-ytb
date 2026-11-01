"""Prepare verifiable, permanent-downloadable science video preview assets.

Runs on a successful Actions artifact from the same repository. It NEVER
publishes videos, changes release status or relies on secret credentials;
the GitHub workflow independently decides if a preview may be attached.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(source: Path, destination: Path, slug: str, run_id: int) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,49}", slug):
        raise ValueError("Invalid safe preview slug")
    if type(run_id) is not int or not 1 <= run_id <= 10**15:
        raise ValueError("Invalid source Actions run ID")
    base = source.resolve(strict=True)
    video = (base / "video" / "preview.mp4").resolve(strict=True)
    qa_file = (base / "video" / "qa-summary.json").resolve(strict=True)
    captions = (base / "video" / "draft-captions.srt").resolve(strict=True)
    if not all(p.is_relative_to(base) for p in (video, qa_file, captions)):
        raise ValueError("Video source contains escaping path")
    if not 100_000 <= video.stat().st_size <= 500_000_000:
        raise ValueError("Unexpected preview video size")
    qa = json.loads(qa_file.read_text(encoding="utf-8"))
    checks = qa.get("checks") or {}
    if (qa.get("status") != "passed" or
            qa.get("technicalPreviewReady") is not True or
            qa.get("publicationApproved") is not False or
            qa.get("humanEditorialReviewRequired") is not True or
            qa.get("errors") or
            checks.get("structural") != "passed" or
            checks.get("media") != "pass" or
            checks.get("frozenAnimatedScenes") != 0 or
            checks.get("nearBlackVisualSamples") != 0 or
            checks.get("reviewOrientation") != "portrait" or
            checks.get("mp4Width") != 1080 or checks.get("mp4Height") != 1920):
        raise ValueError("Preview has not passed required safety and media QA")
    if not checks.get("contactSheetsVerified") or checks.get("subtitleCues", 0) < 1:
        raise ValueError("Preview needs valid subtitles and visual evidence")
    digest = _sha(video)
    if digest != checks.get("mp4Sha256"):
        raise ValueError("Video bytes differ from verified QA digest")
    if _sha(captions) != checks.get("srtSha256"):
        raise ValueError("Subtitle bytes differ from verified QA digest")
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(video)
    ], capture_output=True, text=True, timeout=45, check=True)
    meta = json.loads(result.stdout)
    streams = meta.get("streams", [])
    image = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    seconds = float(meta["format"]["duration"])
    if (image.get("codec_name") != "h264" or
            (image.get("width"), image.get("height")) != (1080, 1920) or
            image.get("r_frame_rate") != "30/1" or
            audio.get("codec_name") != "aac" or
            not 20 <= seconds <= 900):
        raise ValueError("Preview is not supported native H264/AAC portrait MP4")
    if abs(seconds - float(checks.get("mp4DurationSeconds", -100))) > .25:
        raise ValueError("Duration differs from signed-off QA measurement")
    # Validate complete H264/AAC decode; do not only check MP4 container header.
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-xerror",
                    "-i", str(video), "-map", "0:v:0", "-map", "0:a:0",
                    "-f", "null", "-"],
                   check=True, capture_output=True, timeout=360)
    destination.mkdir(parents=True, exist_ok=True)
    mp4 = destination / f"{slug}.mp4"
    srt = destination / f"{slug}.srt"
    shutil.copyfile(video, mp4)
    shutil.copyfile(captions, srt)
    report = {
        "schemaVersion": 1,
        "type": "public-accessible-unreviewed-science-video-preview",
        "sourceRunId": run_id,
        "technicalChecksPassed": True,
        "humanEditorialReviewRequired": True,
        "publicationApproved": False,
        "video": mp4.name,
        "videoSha256": digest,
        "subtitles": srt.name,
        "subtitlesSha256": _sha(srt),
        "durationSeconds": round(seconds, 3),
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "audio": "AAC; narration and original soundtrack",
        "source": "Existing successful Actions movie; original media bytes unchanged",
    }
    (destination / f"{slug}-manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    report = prepare(args.artifact, args.output, args.slug, args.run_id)
    print("SCIENCE_PREVIEW_DELIVERY_QA_OK", json.dumps(report))


if __name__ == "__main__":
    main()
