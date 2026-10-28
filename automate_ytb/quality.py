"""Objective, offline quality gate for the actual exported YouTube MP4 preview.

Checks structure, media playback, requested audio streams and caption timing.
It does NOT certify originality, factual correctness or editorial quality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from .production import _write_json, load_plan
from .caption_guard import audit_caption_text

CUE = re.compile(
    r"(?m)^(?P<n>\d+)\s*\n"
    r"(?P<a>\d{2}:\d{2}:\d{2},\d{3}) --> "
    r"(?P<b>\d{2}:\d{2}:\d{2},\d{3})\s*\n"
)
MAX_REPORT_BYTES = 1_000_000


def _probe(path: Path) -> dict:
    done = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
         "-of", "json", str(path)], capture_output=True, text=True,
        timeout=60, check=False,
    )
    if done.returncode:
        raise RuntimeError("FFprobe could not inspect the rendered preview")
    return json.loads(done.stdout)


def _stamp(value: str) -> int:
    hh, mm, other = value.split(":")
    ss, ms = other.split(",")
    return ((int(hh) * 60 + int(mm)) * 60 + int(ss)) * 1000 + int(ms)


def _digest(path: Path) -> str:
    hash_ = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hash_.update(chunk)
    return hash_.hexdigest()


def _picture_decodes(path: Path, second: float) -> bool:
    # Extraction produces an actual PNG only if the decoder returns a frame.
    done = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{second:.3f}",
         "-i", str(path), "-frames:v", "1", "-f", "image2pipe",
         "-c:v", "png", "-"], capture_output=True, timeout=75, check=False)
    return done.returncode == 0 and done.stdout.startswith(b"\x89PNG\r\n\x1a\n")


def check(*, plan: Path, output: Path, expected_voice: str,
          expected_soundtrack: str, report_path: Path | None = None,
          decode_frames: bool = True, expected_render_profile: str = "preview") -> dict:
    if expected_voice not in ("none", "espeak", "kokoro"):
        raise ValueError("Expected voice must be none, espeak or kokoro")
    if expected_soundtrack not in ("none", "ambient"):
        raise ValueError("Expected soundtrack must be none or ambient")
    from .encoding_profiles import settings
    codec = settings(expected_render_profile)
    data = load_plan(plan)
    output = output.resolve()
    expected_audio = expected_voice != "none" or expected_soundtrack != "none"
    errors, warnings = [], []
    video = output / "preview.mp4"
    srt = output / "draft-captions.srt"
    manifest = output / "episode-report.json"
    render_report = output / "render-report.json"
    result = {
        "status": "failed",
        "publicationApproved": False,
        "expectedVoice": expected_voice,
        "expectedSoundtrack": expected_soundtrack,
        "checks": {},
        "errors": errors,
        "warnings": warnings,
    }
    metrics = result["checks"]
    try:
        for file in (video, srt, manifest, render_report):
            if not file.is_file() or not file.stat().st_size:
                errors.append(f"Required deliverable missing or empty: {file.name}")
        if errors:
            return result
        for file in (manifest, render_report):
            if file.stat().st_size > MAX_REPORT_BYTES:
                errors.append(f"Report unexpectedly large: {file.name}")
        if errors:
            return result
        episode = json.loads(manifest.read_text(encoding="utf-8"))
        rendered = json.loads(render_report.read_text(encoding="utf-8"))
        if episode.get("publicationApproved") is not False or rendered.get("publicationApproved") is not False:
            errors.append("No preview may be automatically approved for publication")
        if episode.get("factChecked") is not False:
            errors.append("Fact-checking must not be falsely marked as complete")
        metrics["renderProfile"] = rendered.get("renderProfile")
        if rendered.get("renderProfile") != expected_render_profile:
            errors.append("Rendered MP4 profile disagrees with the requested quality")
        if episode.get("renderProfile") != expected_render_profile:
            errors.append("Episode report lacks the requested delivery profile")
        if rendered.get("videoEncodingPreset") != codec["preset"]:
            errors.append("Reported H.264 encoder preset disagrees with the selected profile")
        if rendered.get("videoEncodingCrf") != codec["crf"]:
            errors.append("Reported H.264 CRF disagrees with the selected profile")
        if not rendered.get("previewOnly"):
            errors.append("Export must remain a preview")
        count = rendered.get("scenesRendered")
        if not isinstance(count, int) or isinstance(count, bool) or not (1 <= count <= len(data["scenes"])):
            errors.append("Rendered scene count is invalid")
            return result
        planned_duration = data["scenes"][count-1]["endMs"] / 1000
        metrics["plannedDurationSeconds"] = planned_duration
        metrics["sceneCount"] = count
        # Crossfades are image-only: they may not shorten scenes or shift
        # the separately narrated timeline and SRT boundaries.
        transitions = rendered.get("transitions", {})
        mode = transitions.get("mode") if isinstance(transitions, dict) else None
        expected_transitions = count - 1 if mode == "dissolve" else 0
        metrics["transitionMode"] = mode
        metrics["transitionCount"] = (
            transitions.get("count") if isinstance(transitions, dict) else None)
        metrics["transitionTimelineShiftMs"] = (
            transitions.get("timelineShiftMs") if isinstance(transitions, dict) else None)
        if (mode not in ("cut", "dissolve")
                or transitions.get("count") != expected_transitions
                or transitions.get("timelineShiftMs") != 0):
            errors.append("Visual scene transitions changed or misstated the planned timeline")
        metrics["renderedDurationSeconds"] = rendered.get("targetDurationSeconds")
        if abs(float(rendered.get("targetDurationSeconds", -999)) - planned_duration) > 0.01:
            errors.append("Rendered timeline does not match scene plan")
        if rendered.get("videoSha256") != _digest(video):
            errors.append("Rendered video checksum mismatch")
        wanted_speech = expected_voice != "none"
        wanted_music = expected_soundtrack == "ambient"
        if rendered.get("hasNarrationAudio") is not wanted_speech:
            errors.append("Requested narration does not match final render report")
        if rendered.get("hasBackgroundMusic") is not wanted_music:
            errors.append("Requested soundtrack does not match final render report")
        expected_mix = ("ducked-narration-plus-original-bed" if wanted_speech and wanted_music else
                        "narration-only" if wanted_speech else
                        "original-bed-only" if wanted_music else "silent")
        if rendered.get("audioMixMode") != expected_mix:
            errors.append("Unexpected audio mixing mode")
        voice_engine = {"none": "none", "espeak": "espeak-draft",
                        "kokoro": "kokoro-natural"}[expected_voice]
        if episode.get("voice", {}).get("engine") != voice_engine:
            errors.append("Incorrect narration engine in episode report")
        if wanted_speech and not (output / "narration.wav").is_file():
            errors.append("Narration WAV missing")
        if wanted_music and not (output / "background-original.wav").is_file():
            errors.append("Requested original music WAV missing")
        if episode.get("soundtrack", {}).get("engine") != (
                "ambient-original-v1" if wanted_music else "none"):
            errors.append("Incorrect soundtrack source in episode report")
        info = _probe(video)
        streams = info.get("streams", [])
        kinds = [s.get("codec_type") for s in streams]
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        metrics["streams"] = kinds
        if len(video_streams) != 1 or len(audio_streams) != int(expected_audio):
            errors.append("MP4 does not contain exactly the expected audio/video tracks")
        if video_streams:
            dimensions = (video_streams[0].get("width"), video_streams[0].get("height"))
            metrics["resolution"] = list(dimensions)
            if dimensions not in ((1280, 720), (1920, 1080)):
                errors.append("Unexpected video resolution")
            if video_streams[0].get("codec_name") != "h264":
                errors.append("Unexpected video codec")
        if audio_streams and audio_streams[0].get("codec_name") != "aac":
            errors.append("Unexpected audio codec")
        if expected_audio and audio_streams:
            # A technically present AAC stream can still be completely silent.
            # Sample the beginning without analyzing or retaining private speech.
            peak_check = subprocess.run(
                ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(video),
                 "-t", "4", "-map", "0:a:0", "-vn", "-af", "volumedetect",
                 "-f", "null", "-"], capture_output=True, text=True,
                timeout=45, check=False)
            if peak_check.returncode:
                errors.append("Could not decode the output audio for loudness check")
            else:
                peak_match = re.search(
                    r"max_volume:\s*(-inf|-?\d+(?:\.\d+)?) dB",
                    peak_check.stderr)
                if not peak_match:
                    errors.append("No decoded audio peak could be measured")
                else:
                    peak = float(peak_match[1])
                    metrics["initialAudioPeakDbFS"] = peak if peak != float("-inf") else None
                    if peak < -58:
                        errors.append("The exported audio stream is effectively silent")
                    elif peak > -0.1:
                        warnings.append("Audio peak approaches digital clipping; listen to output")
        try:
            duration = float(info["format"]["duration"])
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append("Could not determine video duration")
            return result
        metrics["actualDurationSeconds"] = round(duration, 3)
        if not 0 < duration <= 3602 or abs(duration - planned_duration) > 0.55:
            errors.append("MP4 duration does not match storyboard")
        text = srt.read_text(encoding="utf-8")
        caption_audit = audit_caption_text(text, data["scenes"][:count])
        metrics["captionTextMatchesPlan"] = caption_audit["passed"]
        metrics["captionScenesVerified"] = caption_audit["scenesVerified"]
        errors.extend(caption_audit["errors"])
        matches = list(CUE.finditer(text))
        metrics["subtitleCues"] = len(matches)
        if not matches or len(matches) != rendered.get("captionGeneration", {}).get("cueCount"):
            errors.append("Subtitle count mismatch")
        previous = 0
        for index, match in enumerate(matches, start=1):
            begin, end = _stamp(match["a"]), _stamp(match["b"])
            if (int(match["n"]) != index or begin < previous or end <= begin
                    or end > round(planned_duration*1000)+10):
                errors.append(f"Invalid subtitle timing at cue {index}")
                break
            previous = end
        if matches and abs(previous - round(planned_duration*1000)) > 10:
            errors.append("Subtitles do not cover the end of the planned timeline")
        if decode_frames and duration > 0:
            samples = (0.1, max(0.1, duration - 0.7))
            for second in samples:
                if not _picture_decodes(video, second):
                    errors.append(f"MP4 cannot decode a frame near {second:.1f}s")
            metrics["sampledFramesDecoded"] = len(samples) if not any(
                "cannot decode" in item for item in errors) else 0
        if not rendered.get("captionsPreciselyAligned") and wanted_speech:
            warnings.append("SRT timings are approximate; not force-aligned to spoken words")
        warnings.append("Editorial accuracy, pronunciation, music fit and video quality require human review")
        return result
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, RuntimeError) as exc:
        errors.append(f"Quality gate could not complete ({type(exc).__name__})")
        return result
    finally:
        result["status"] = "passed" if not errors else "failed"
        if report_path is not None:
            _write_json(report_path.resolve(), result)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Objective QA of rendered YouTube preview")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--expect-voice", choices=["none", "espeak", "kokoro"], required=True)
    p.add_argument("--expect-soundtrack", choices=["none", "ambient"], required=True)
    p.add_argument("--report", type=Path)
    p.add_argument("--expect-render-profile", choices=["preview", "high"],
                   default="preview")
    args = p.parse_args(argv)
    try:
        result = check(plan=args.plan, output=args.output,
                       expected_voice=args.expect_voice,
                       expected_soundtrack=args.expect_soundtrack,
                       expected_render_profile=args.expect_render_profile,
                       report_path=args.report)
    except (OSError, ValueError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
