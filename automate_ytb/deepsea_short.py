"""Reproducible real-footage original deep-ocean Short with measured Kokoro speech.

Exact publicly documented NOAA footage checksums protect the editorial source.
No invented bioluminescent footage, no source camera audio, no automatic upload.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import wave

from .soundtrack import _loop, SAMPLERATE
from .subject_reframe import track_crop, crop_expression
from .short_captions import export_caption_assets

SOURCES = {
    "crossota": "72053267ced4a58c9c28e865937d00c0a35bb667da010b9b115558fbcfd12595",
    "medusa": "35fecdb5b5df9bb7398eda107abf284e75b7e1c94ddbc9b5f80676f2ad6ca173",
}
SHOTS = (
    ("medusa", 39.0, 452, "THE DEEP SEA IS ALIVE"),
    ("crossota", 20.7, 400, "LIGHT FROM WITHIN"),
    ("medusa", 12.2, 420, "A SIGNAL IN THE DARK"),
    ("medusa", 44.6, 520, "SURVIVAL IN THE DEEP"),
)


def _run(cmd: list[str], *, timeout: int = 300, cwd: Path | None = None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, cwd=cwd)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise RuntimeError("FFmpeg processing unavailable or timed out") from exc
    if result.returncode:
        raise RuntimeError("FFmpeg failure: " + result.stderr[-500:])


def _sha(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            d.update(chunk)
    return d.hexdigest()


def _probe(path: Path) -> dict:
    output = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True)
    return json.loads(output.stdout)


def _srt(ms: int) -> str:
    hours, rest = divmod(ms, 3600000)
    minutes, rest = divmod(rest, 60000)
    seconds, millis = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def build(*, crossota: Path, medusa: Path, voice: Path,
          report: Path, output: Path) -> dict:
    paths = {"crossota": crossota.resolve(), "medusa": medusa.resolve()}
    for name, source in paths.items():
        if not source.is_file() or _sha(source) != SOURCES[name]:
            raise ValueError(f"Unexpected source checksum: {name}")
    data = json.loads(report.read_text(encoding="utf-8"))
    if data.get("engine") != "kokoro-natural" or data.get("language") != "en":
        raise ValueError("A true English Kokoro natural narrator is required")
    if data.get("sha256") != _sha(voice):
        raise ValueError("Narration WAV checksum disagrees with the beat report")
    with wave.open(str(voice), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 24000:
            raise ValueError("Narration must be 24kHz mono PCM")
        duration = wav.getnframes() / wav.getframerate()
    beats = data.get("beats")
    if not isinstance(beats, list) or len(beats) != 4 or not 8 <= duration <= 90:
        raise ValueError("The original four-beat 8–90s narrator is required")
    start = [0.0] + [float(row["startMs"])/1000 for row in beats[1:]]
    lengths = [start[i+1] - start[i] for i in range(3)] + [duration - start[3]]
    if any(x < 1 or x > 16 for x in lengths):
        raise ValueError("Unsafe or invalid narration beat lengths")
    for name, source in paths.items():
        probe = _probe(source)
        videos = [s for s in probe["streams"] if s.get("codec_type") == "video"]
        expected = (1920, 1080) if name == "crossota" else (1280, 720)
        if len(videos) != 1 or tuple(videos[0].get(k) for k in ("width","height")) != expected:
            raise ValueError("Unexpected original footage frame dimensions")
    for (name, offset, _crop, _title), length in zip(SHOTS, lengths):
        source_duration = float(_probe(paths[name])["format"]["duration"])
        if offset + length > source_duration - .05:
            raise ValueError("Source cannot cover the actual spoken segment")

    output = output.resolve()
    if output.exists():
        raise ValueError("Refusing to overwrite an existing finished video")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="deepsea-master-",dir=output.parent) as td:
        work = Path(td)
        captions = export_caption_assets(
            beats, duration_ms=round(duration * 1000), directory=work)
        clips = []
        shot_tracking = []
        for i, ((name, offset, _old_x, _old_title), length) in enumerate(zip(SHOTS,lengths),1):
            w,h = (1920,1080) if name=="crossota" else (1280,720)
            cw = (608 if name=="crossota" else 406)
            # Inspect only the footage used by this sentence. The moving
            # vertical window is synchronized to *measured* speech beats.
            # No fake animated creatures or full-screen PowerPoint headings.
            track = track_crop(
                source=paths[name], start=offset, seconds=length,
                source_width=w, crop_width=cw)
            x_expr = crop_expression(track)
            shot_tracking.append({
                "sceneIndex": i, "footage": name,
                "startSeconds": round(offset, 3),
                "durationSeconds": round(length, 3),
                **track,
            })
            vf = ",".join([
                "setpts=PTS-STARTPTS",
                f"crop={cw}:{h}:x='{x_expr}':y=0",
                "scale=1080:1920:flags=lanczos",
                "fps=30",
                "eq=contrast=1.045:saturation=1.06:brightness=-0.005",
                f"ass=filename=scene-{i:02}.ass",
                "format=yuv420p",
            ])
            clip=work/f"scene-{i:02}.mp4"
            _run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                  "-ss",f"{offset:.3f}","-i",str(paths[name]),"-t",f"{length:.3f}",
                  "-vf",vf,"-an","-r","30","-c:v","libx264",
                  "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(clip)],
                 cwd=work)
            if not clip.is_file() or clip.stat().st_size < 30000:
                raise RuntimeError("Encoded real-footage video scene is missing")
            clips.append(clip)
        ffconcat = work / "scenes.ffconcat"
        ffconcat.write_text("ffconcat version 1.0\n" +
                            "".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
        silent=work/"silent.mp4"
        _run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
              "-f","concat","-safe","0","-i",str(ffconcat),
              "-c","copy",str(silent)])

        # Reuse the repo's fully procedural original chord loops; no licensed song.
        motifs = _loop("night")
        needed = round(duration*SAMPLERATE)
        music=work/"original-ambient.wav"
        with wave.open(str(music),"wb") as dst:
            dst.setnchannels(1);dst.setsampwidth(2);dst.setframerate(SAMPLERATE)
            samples=array("h")
            for j in range(needed):
                gain=min(1.0,j/(SAMPLERATE*.4),(needed-j)/(SAMPLERATE*.6))
                samples.append(round(motifs[j%len(motifs)]*max(0,gain)))
            dst.writeframes(samples.tobytes())
        mix=(
            "[1:a]aresample=48000,highpass=f=65,"
            "acompressor=threshold=0.14:ratio=2:attack=15:release=175,asplit=2[speech][control];"
            "[2:a]aresample=48000,highpass=f=45,volume=0.17[bed];"
            "[bed][control]sidechaincompress=threshold=0.012:ratio=7:attack=24:release=350[duck];"
            "[speech][duck]amix=inputs=2:duration=first:normalize=0,"
            "alimiter=limit=0.92,loudnorm=I=-16:LRA=9:TP=-1.5[out]"
        )
        rendered=work/"final.mp4"
        _run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
              "-i",str(silent),"-i",str(voice),"-i",str(music),
              "-filter_complex",mix,"-map","0:v:0","-map","[out]",
              "-c:v","copy","-c:a","aac","-b:a","192k",
              "-ac","2","-ar","48000","-t",f"{duration:.3f}",
              "-movflags","+faststart",str(rendered)],timeout=200)
        # Real decode, not metadata alone, required for acceptance.
        _run(["ffmpeg","-nostdin","-v","error","-i",str(rendered),
              "-f","null","-"],timeout=300)
        output_srt=output.with_suffix(".srt")
        # Same audio-sourced phrase cues in the portable SRT companion.
        output_srt.write_bytes(Path(captions["srtPath"]).read_bytes())
        result={
            "status": "rendered",
            "video": str(output),
            "sha256": _sha(rendered),
            "fps": 30, "resolution": [1080, 1920],
            "durationSeconds": round(duration,3),
            "sourceRights": "NOAA public-domain, verified SHA256 and attribution docs",
            "voiceEngine": "kokoro-natural",
            "voice": data.get("voice"),
            "sceneCount": len(SHOTS),
            "footageType": "real-recorded-jellyfish",
            "portraitTracking": shot_tracking,
            "staticTitleCards": False,
            "opticalSubjectDetection": False,
            "captionMode": "speech-measured-ass-mobile-overlay-plus-srt",
            "captionTimingMethod": captions["timestampMethod"],
            "captionCount": captions["captionCount"],
            "burnedInCaptions": True,
            "wordLevelAligned": False,
            "captionSafeZoneNeedsHumanReview": True,
            "bioluminescenceActuallyRecorded": False,
            "copyrightedMusic": False,
            "publicationApproved": False,
            "humanReviewRequired": True
        }
        rendered.replace(output)
        output.with_suffix(".json").write_text(json.dumps(result,indent=2)+"\n",
                                               encoding="utf-8")
    return result


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description="Original real-jellyfish footage plus actual neural voice")
    p.add_argument("--crossota",type=Path,required=True)
    p.add_argument("--medusa",type=Path,required=True)
    p.add_argument("--voice",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        result=build(crossota=args.crossota,medusa=args.medusa,voice=args.voice,
                     report=args.report,output=args.output)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
