"""Fast visual-only QA for seven narrated Earth-stop motion scenes.

Produces an actual H.264 MP4 and decoded-frame motion evidence, without
requiring neural speech, NASA downloads, paid services or network access.
The full Kokoro workflow remains the separate release quality gate.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageStat

from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.science_earth_stop import classify

TOPIC = "What If Earth Suddenly Stopped Spinning?"
STORY = (
    ("stop", "What if Earth suddenly stopped spinning?"),
    ("inertia", "At the equator, inertia would carry moving objects onward."),
    ("wind", "The atmosphere would keep moving, sending violent winds over cities."),
    ("ocean", "The oceans would keep moving, producing enormous coastal waves."),
    ("poles", "Over longer timescales, ocean water could redistribute toward the poles."),
    ("day", "Day and night could last for months, with a dramatically changed solar cycle."),
    ("astronaut", "Astronauts and other survivors would face severe new challenges."),
)
FPS = 30
BEAT_FRAMES = 30
DURATION = BEAT_FRAMES / FPS
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "outputs" / "earth-motion-visual-qa"


def decode(video: Path, second: float) -> Image.Image:
    cmd = [
        "ffmpeg", "-nostdin", "-v", "error", "-ss", f"{second:.3f}",
        "-i", str(video), "-frames:v", "1", "-vf",
        "scale=180:320:flags=bilinear", "-pix_fmt", "rgb24",
        "-f", "rawvideo", "pipe:1",
    ]
    result = subprocess.run(cmd, capture_output=True, check=True, timeout=30)
    if len(result.stdout) != 180*320*3:
        raise RuntimeError("Actual H264 motion sample is incomplete")
    return Image.frombytes("RGB", (180,320), result.stdout)


def main() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("FFmpeg and FFprobe are required")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    movie = OUTPUT / "earth-motion-7-scene-1080x1920.mp4"
    cmd = [
        "ffmpeg", "-y", "-nostdin", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", "1080x1920", "-r", str(FPS), "-i", "pipe:0",
        "-an", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(movie),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i, (expected, narration) in enumerate(STORY, 1):
            if classify(TOPIC, narration) != expected:
                raise RuntimeError(f"Unexpected illustrated story beat {expected}")
            shot = PortraitScienceScene(
                topic=TOPIC, narration=narration, scene_index=i)
            for n in range(BEAT_FRAMES):
                # Match on-screen animated clock to the H264 frame time;
                # no fake zooms, still-card repeats or artificial frame interpolation.
                frame = shot.frame(n / FPS, DURATION)
                if frame.size != (1080,1920) or frame.mode != "RGB":
                    raise RuntimeError("Invalid native portrait frame")
                proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        if proc.wait(timeout=300):
            raise RuntimeError("H264 motion preview encoding failed")
    except BaseException:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        movie.unlink(missing_ok=True)
        raise

    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,nb_frames",
        "-of", "json", str(movie)
    ], capture_output=True, text=True, check=True, timeout=20)
    meta = json.loads(probe.stdout)["streams"][0]
    if ((meta["width"],meta["height"]) != (1080,1920)
            or meta["avg_frame_rate"] != "30/1"
            or int(meta["nb_frames"]) != len(STORY)*BEAT_FRAMES):
        raise RuntimeError(f"Unexpected encoded MP4 video stream {meta}")

    sheet=Image.new("RGB",(1080,1020),(8,18,34))
    sd=ImageDraw.Draw(sheet)
    motion=[]
    for i,(beat,_) in enumerate(STORY):
        a=decode(movie,i*DURATION+.2*DURATION)
        b=decode(movie,i*DURATION+.76*DURATION)
        diff=ImageChops.difference(a.crop((15,93,165,250)),
                                   b.crop((15,93,165,250)))
        change=ImageStat.Stat(diff).mean
        value=round(sum(change)/3,3)
        if value < .20:
            raise RuntimeError(f"Encoded story beat {beat} appears frozen: {value}")
        motion.append({"beat":beat,"meanAbsoluteRgbChange":value,
                       "source":"actual H264 decoded frames"})
        x=(i%4)*270
        y=(i//4)*510
        frame=decode(movie,i*DURATION+.5*DURATION).resize((270,480))
        sheet.paste(frame,(x,y))
        sd.rectangle((x,y+480,x+270,y+510),fill=(10,26,43))
        sd.text((x+12,y+485),beat.upper(),fill=(249,211,148))
    sheet.save(OUTPUT/"seven-scene-contact-sheet.jpg",quality=89)
    report={
        "video":movie.name,"frameSize":[1080,1920],"fps":FPS,
        "totalFrames":len(STORY)*BEAT_FRAMES,
        "verifiedMotion":motion,"source":"seven original schematic 2D animations",
        "audio":"not included; full Kokoro production is a separate workflow",
        "publicationApproved":False
    }
    (OUTPUT/"visual-motion-qa.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf8")
    print("EARTH_SCENE_MOTION_PREVIEW_OK",json.dumps(report),flush=True)


if __name__=="__main__":
    main()
