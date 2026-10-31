"""Inspect a rendered video and export a portable pre-publication quality report."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys

def _run(args):
    proc = subprocess.run(args, capture_output=True, text=True, timeout=120, check=False)
    if proc.returncode:
        raise RuntimeError("Media validation failed: " + proc.stderr[-500:])
    return proc.stdout

def probe_media(path: Path) -> dict:
    path = path.resolve()
    if not path.is_file() or path.stat().st_size < 2048:
        raise ValueError("Output MP4 does not exist or is empty")
    raw = _run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate",
                "-of", "json", str(path)])
    data = json.loads(raw)
    streams = data.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if len(videos) != 1 or len(audios) > 1:
        raise ValueError("Preview must have one video stream and at most one audio stream")
    duration = float(data.get("format", {}).get("duration", 0))
    if not math.isfinite(duration) or duration <= 0 or duration > 7200:
        raise ValueError("Invalid MP4 duration")
    video = videos[0]
    dims = (int(video.get("width", 0)), int(video.get("height", 0)))
    if min(dims) < 240:
        raise ValueError("Invalid video dimensions")
    return {"durationSeconds": round(duration, 3),
            "width": dims[0], "height": dims[1],
            "videoCodec": video.get("codec_name"),
            "audioCodec": audios[0].get("codec_name") if audios else None,
            "hasAudio": bool(audios),
            "fileBytes": path.stat().st_size}

def _parse_srt(path: Path):
    if not path.is_file():
        raise ValueError("Missing SRT subtitles")
    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    groups = re.split(r"\n\s*\n", content.strip())
    output = []
    for item in groups:
        lines = item.strip().splitlines()
        if not lines:
            continue
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError("Invalid SRT cue")
        match = re.fullmatch(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", lines[1].strip())
        if not match:
            raise ValueError("Invalid SRT timecode")
        t = [int(n) for n in match.groups()]
        if t[1] > 59 or t[2] > 59 or t[5] > 59 or t[6] > 59 or t[3] > 999 or t[7] > 999:
            raise ValueError("Invalid subtitle timestamp fields")
        start = ((t[0]*60+t[1])*60+t[2])*1000+t[3]
        end = ((t[4]*60+t[5])*60+t[6])*1000+t[7]
        if start >= end or not any(text.strip() for text in lines[2:]):
            raise ValueError("Invalid or empty SRT cue")
        output.append((start, end, lines[2:]))
    if not output:
        raise ValueError("SRT has no captions")
    return output

def _stamp(ms):
    hours, remainder = divmod(ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

def generate_vtt(srt: Path, destination: Path, *, max_duration_ms: int | None = None) -> dict:
    entries = _parse_srt(srt)
    previous = 0
    lines = ["WEBVTT", ""]
    for start, end, text in entries:
        if start < previous:
            raise ValueError("Overlapping or unsorted subtitle cues")
        if max_duration_ms is not None and end > max_duration_ms + 750:
            raise ValueError("Subtitle cue exceeds video duration")
        previous = end
        lines += [f"{_stamp(start)} --> {_stamp(end)}", *text, ""]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"cues": len(entries), "lastCueMs": previous, "file": str(destination)}

def _audio_measurements(path: Path) -> dict:
    """EBU R128 integrated loudness and true peak, plus legacy sample peak.

    Measures the *encoded output*, not the input voice or source soundtrack.
    All three measurements are obtained in a single FFmpeg decoding pass.
    """
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "info",
         "-i", str(path), "-map", "0:a:0", "-vn",
         "-af", "ebur128=peak=true,volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=600, check=False)
    if proc.returncode:
        raise RuntimeError("Unable to inspect encoded MP4 audio")
    tail = proc.stderr.rsplit("Summary:", 1)
    if len(tail) < 2:
        raise RuntimeError("FFmpeg EBU R128 meter did not return a summary")
    summary = tail[-1]
    number = r"(-?(?:\d+(?:\.\d+)?|inf))"
    integrated = re.search(r"Integrated loudness:\s+I:\s*" + number +
                           r"\s*LUFS", summary)
    true_peak = re.search(r"True peak:\s+Peak:\s*" + number +
                          r"\s*dBFS", summary)
    sample_peaks = re.findall(r"max_volume:\s*" + number +
                              r"\s*dB", proc.stderr)
    if not integrated or not true_peak or not sample_peaks:
        raise RuntimeError("FFmpeg audio loudness analysis is incomplete")
    def finite(value):
        parsed = float(value)
        return round(parsed, 2) if math.isfinite(parsed) else None
    return {
        "integratedLufs": finite(integrated.group(1)),
        "truePeakDbtp": finite(true_peak.group(1)),
        "samplePeakDbfs": finite(sample_peaks[-1]),
        "method": "FFmpeg ebur128=peak=true + volumedetect",
    }


def assess(*, video: Path, captions: Path | None = None,
           expected_duration: float | None = None,
           require_audio: bool = False,
           destination: Path | None = None,
           target_lufs: float | None = None) -> dict:
    media = probe_media(video)
    problems, warnings = [], []
    if target_lufs is not None and (
            not math.isfinite(target_lufs) or not -30 <= target_lufs <= -9):
        raise ValueError("Target loudness must be finite between -30 and -9 LUFS")
    if require_audio and not media["hasAudio"]:
        problems.append("Narration audio is missing")
    if expected_duration is not None:
        if not math.isfinite(expected_duration) or expected_duration <= 0:
            raise ValueError("Invalid expected duration")
        if abs(media["durationSeconds"] - expected_duration) > 0.85:
            problems.append("Actual duration differs from requested timeline")
    if (media["width"], media["height"]) not in {(1280, 720), (1920, 1080), (1080, 1920)}:
        warnings.append("Unexpected video resolution or aspect ratio")
    if media["videoCodec"] != "h264":
        warnings.append("Video codec is not H.264")
    levels = _audio_measurements(video) if media["hasAudio"] else None
    peak = levels["samplePeakDbfs"] if levels else None
    integrated = levels["integratedLufs"] if levels else None
    true_peak = levels["truePeakDbtp"] if levels else None
    if levels and integrated is None:
        (problems if require_audio else warnings).append(
            "Encoded audio is effectively silent; check the narration or soundtrack")
    if integrated is not None:
        if integrated < -29:
            warnings.append("Encoded audio is unusually quiet; review playback")
        if integrated > -9:
            warnings.append("Encoded audio is unusually loud; review playback")
        if target_lufs is not None:
            difference = abs(integrated - target_lufs)
            if difference > 8:
                problems.append("Encoded loudness is far from the intended mastering target")
            elif difference > 4:
                warnings.append("Encoded loudness differs from the mastering target")
    if true_peak is not None and true_peak > -0.2:
        warnings.append("True peak approaches digital full scale; check distortion")
    if peak is not None and peak > -0.2:
        warnings.append("Sample peak approaches digital full scale; check clipping")
    if captions is not None:
        try:
            subs = _parse_srt(captions)
            last = 0
            for start, end, _ in subs:
                if start < last:
                    raise ValueError("Overlapping caption cues")
                last = end
            if last > round(media["durationSeconds"] * 1000) + 750:
                problems.append("Subtitles extend beyond video duration")
            caption_count = len(subs)
        except ValueError as exc:
            problems.append("Invalid subtitles: " + str(exc))
            caption_count = 0
    else:
        caption_count = 0
    report = {
        "status": "fail" if problems else "pass-with-warnings" if warnings else "pass",
        "publicationApproved": False, "humanReviewRequired": True,
        "media": media, "peakDbfs": peak,
        "integratedLufs": integrated,
        "truePeakDbtp": true_peak,
        "targetLufs": target_lufs,
        "audioMeasurement": levels["method"] if levels else None,
        "subtitleCues": caption_count, "errors": problems, "warnings": warnings,
        "limitations": ["No listening-based speech review or factual verification",
                        "No automated copyrighted-media rights verification",
                        "Objective LUFS and true peak measurements do not replace listening-based review",
                        "Subtitle boundaries are scene-based, not forced word alignment"],
    }
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate YouTube draft media")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--srt", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--vtt", type=Path)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--require-audio", action="store_true")
    parser.add_argument("--target-lufs", type=float,
                        help="Optional expected integrated loudness target in LUFS")
    args = parser.parse_args(argv)
    try:
        report = assess(video=args.video, captions=args.srt,
                        expected_duration=args.duration, require_audio=args.require_audio,
                        destination=args.report, target_lufs=args.target_lufs)
        if args.vtt:
            if not args.srt:
                raise ValueError("--vtt requires --srt")
            generate_vtt(args.srt, args.vtt,
                         max_duration_ms=round(report["media"]["durationSeconds"]*1000))
        print(json.dumps({"status": report["status"], "media": report["media"],
                          "errors": report["errors"], "warnings": report["warnings"]}))
        return 2 if report["errors"] else 0
    except (ValueError, OSError, RuntimeError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
