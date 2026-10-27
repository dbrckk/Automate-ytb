"""A real Android-viewable V2 animation reel from the production animal rigs.

Four original animated scene clips, subtitles and procedural score. Nothing is
downloaded, reused from third-party videos or published to a video platform.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import wave

from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_motion_clip as owl_clip
from automate_ytb.soundtrack import _loop, SAMPLERATE

FPS = 24
SCENE_SECONDS = 4.25
SCENES = (
    ("fox", "river", "day", "jump", "Le renard saute près de la rivière."),
    ("rabbit", "meadow", "wind", "run", "Le lapin court dans une prairie."),
    ("cat", "village", "night", "talk", "Le chat raconte une histoire au village."),
    ("owl", "forest", "cloudy", "fly", "La chouette vole au-dessus de la forêt."),
)
THEMES = ("warm", "wonder", "night", "wonder")


def _call(command: list[str]) -> None:
    subprocess.run(command, check=True, timeout=900)


def _stamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    h, remainder = divmod(milliseconds, 3600000)
    m, remainder = divmod(remainder, 60000)
    s, ms = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_captions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (_, _, _, _, narration) in enumerate(SCENES):
        start = index * SCENE_SECONDS
        end = (index + 1) * SCENE_SECONDS - 0.08
        rows.append(f"{index+1}\n{_stamp(start)} --> {_stamp(end)}\n{narration}\n")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_original_score(path: Path) -> None:
    """A rights-clean, soft synthesized score with fades at scene boundaries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    loops = {theme: _loop(theme) for theme in set(THEMES)}
    frames_per_scene = round(SCENE_SECONDS * SAMPLERATE)
    global_total = frames_per_scene * len(SCENES)
    fade = round(SAMPLERATE * .35)
    with wave.open(str(path), "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(SAMPLERATE)
        for index, theme in enumerate(THEMES):
            source = loops[theme]
            samples = array("h")
            for n in range(frames_per_scene):
                pos = index * frames_per_scene + n
                local_fade = min(1., n/max(1,fade),
                                 (frames_per_scene-1-n)/max(1,fade))
                full_fade = min(1., pos/(SAMPLERATE*.8),
                                 (global_total-1-pos)/(SAMPLERATE*.8))
                gain = max(0., min(local_fade,full_fade))
                samples.append(round(source[n % len(source)] * gain))
            if sys.byteorder != "little":
                samples.byteswap()
            sound.writeframes(samples.tobytes())


def make_showcase(destination: Path) -> dict:
    if not isinstance(destination, Path) or destination.suffix.lower() != ".mp4":
        raise ValueError("Showcase destination must be an MP4 file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    clips = destination.parent / "clips"
    clips.mkdir(exist_ok=True)
    video_paths = []
    for index, (actor, biome, weather, action, narration) in enumerate(SCENES):
        video = clips / f"{index+1:02d}-{actor}-{action}.mp4"
        common = dict(
            topic="Le monde des petits animaux — démonstration V2",
            narration=narration, scene_index=index+1,
            scene_count=len(SCENES), style="cartoon",
            duration=SCENE_SECONDS,width=1280,height=720,fps=FPS,
            destination=video,landscape=biome,
            direction=dict(weather=weather,action=action,emotion="happy",
                           shot="wide"),
        )
        if actor == "owl":
            owl_clip(**common)
        else:
            forest_clip(kind=actor,**common)
        video_paths.append(video.resolve())
    listfile = destination.parent/"clips.ffconcat"
    listfile.write_text("ffconcat version 1.0\n" +
                        "".join(f"file '{p}'\n" for p in video_paths),
                        encoding="utf-8")
    srt = destination.parent/"subtitles.srt"
    write_captions(srt)
    score = destination.parent/"original-score.wav"
    write_original_score(score)
    # These are real encoded scene clips, not a Ken-Burns montage of posters.
    # Burn readable subtitles for mobile so a separate player is unnecessary.
    subtitle_filter = (
        f"subtitles={srt.resolve()}:"
        "force_style='FontName=DejaVu Sans,FontSize=24,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00202020,BackColour=&H99000000,"
        "BorderStyle=3,Outline=1,Shadow=0,MarginV=40,Alignment=2'"
    )
    _call([
        "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-safe","0","-f","concat","-i",str(listfile),
        "-i",str(score),"-map","0:v:0","-map","1:a:0",
        "-vf",subtitle_filter,
        "-r",str(FPS),"-c:v","libx264","-preset","veryfast",
        "-crf","20","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k",
        "-af","loudnorm=I=-24:TP=-2:LRA=8",
        "-shortest","-movflags","+faststart",str(destination)
    ])
    probe = subprocess.run(
        ["ffprobe","-v","error","-show_entries",
         "format=duration:stream=codec_name,width,height",
         "-of","json",str(destination)],
        capture_output=True,text=True,check=True,timeout=45)
    streams = json.loads(probe.stdout)["streams"]
    fmt = json.loads(probe.stdout)["format"]
    if not any(s.get("codec_name")=="h264" and
               (s.get("width"),s.get("height"))==(1280,720) for s in streams):
        raise RuntimeError("No real 720p H264 stream")
    if not any(s.get("codec_name")=="aac" for s in streams):
        raise RuntimeError("No encoded AAC soundtrack")
    if abs(float(fmt["duration"])-len(SCENES)*SCENE_SECONDS)>1.2:
        raise RuntimeError("Invalid final reel duration")
    # Fully decode to catch invalid FFmpeg layer graphs or short inputs.
    _call(["ffmpeg","-nostdin","-hide_banner","-loglevel","error",
           "-i",str(destination),"-f","null","-"])
    cover = destination.parent / "cover.png"
    _call(["ffmpeg","-nostdin","-v","error","-y","-ss","1.1",
           "-i",str(destination),"-frames:v","1",str(cover)])
    report = {
        "source":"Real production 2D rigs from dbrckk/Automate-ytb",
        "type":"original-animation-showcase",
        "sceneCount":len(SCENES),"fps":FPS,
        "durationSeconds":round(float(fmt["duration"]),3),
        "resolution":"1280x720","codec":"h264",
        "audio":"original procedural score (no narrated voice)",
        "publicationApproved":False,"externalApiCalls":0,
        "sha256":hashlib.sha256(destination.read_bytes()).hexdigest(),
        "scenes":[dict(actor=a,landscape=l,weather=w,action=act,narration=n)
                  for a,l,w,act,n in SCENES],
    }
    (destination.parent/"showcase-report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report


def main() -> None:
    parser=argparse.ArgumentParser(description="Generate a real original 2D animation reel")
    parser.add_argument("--output",default="out/v2-animated-showcase/showcase.mp4")
    args=parser.parse_args()
    print(json.dumps(make_showcase(Path(args.output)),ensure_ascii=False))


if __name__=="__main__":
    main()
