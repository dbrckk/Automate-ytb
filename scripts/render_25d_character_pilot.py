"""Produce an actual 1080x1920/30fps original 2.5D fox motion pilot.

Uses the existing original sprite art and the shared Scene25D compositor.
Pipes independent frames into FFmpeg (not a slideshow or interpolated stills),
creates a small *original* score without external sounds, fully decodes the
MP4 and reports objective IK bone-length/contact checks. No Kokoro narration
is claimed for this dedicated motion study; it is not auto-published.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import wave

from automate_ytb.forest25d import frame, character_plate, FPS, SECONDS, SIZE
from automate_ytb.rig25d import UPPER, LOWER, PERIOD


def score(path: Path) -> None:
    """Deterministic quiet wind-like tonal pad, original PCM no rights issues."""
    rate=48000
    pcm=array("h")
    notes=(196.,220.,246.94,220.)
    for n in range(round(SECONDS*rate)):
        t=n/rate
        note=notes[min(len(notes)-1,int(t/(SECONDS/len(notes))))]
        envelope=min(1.,t/.7,(SECONDS-t)/.9)
        envelope=max(0.,envelope)
        pulse=.80+.20*math.sin(2*math.pi*.36*t)
        value=(math.sin(2*math.pi*note*t)*
               .55+math.sin(2*math.pi*note*1.5*t)*.19+
               math.sin(2*math.pi*note*.5*t)*.25)
        pcm.append(round(max(-1.,min(1.,value*.10*envelope*pulse))*32767))
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        if sys.byteorder!="little":
            pcm.byteswap()
        wav.writeframes(pcm.tobytes())


def render(output: Path) -> dict:
    if not isinstance(output,Path) or output.suffix.lower()!=".mp4":
        raise ValueError("Motion-pilot output requires an MP4 path")
    if not 0 < SECONDS <= 20 or FPS != 30:
        raise ValueError("Invalid bounded 2.5D production profile")
    output.parent.mkdir(parents=True,exist_ok=True)
    pad=output.parent/"original-score.wav"
    score(pad)
    command=[
        "ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
        "-f","rawvideo","-pixel_format","rgb24",
        "-video_size",f"{SIZE[0]}x{SIZE[1]}",
        "-framerate",str(FPS),"-i","pipe:0",
        "-i",str(pad),
        "-map","0:v:0","-map","1:a:0",
        "-c:v","libx264","-preset","veryfast","-crf","22",
        "-pix_fmt","yuv420p","-r",str(FPS),"-g","60",
        "-c:a","aac","-b:a","128k","-ar","48000",
        "-shortest","-movflags","+faststart",str(output),
    ]
    started=time.perf_counter()
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    frames=round(SECONDS*FPS)
    worst_bone_error=0.
    planted_contact_drift=0.
    last_contact={"left":None,"right":None}
    samples=[]
    try:
        assert process.stdin is not None
        for i in range(frames):
            t=i/FPS
            if i in (30,99,171):
                key=output.parent/f"frame-{i:03d}.jpg"
                preview=frame(t)
                preview.resize((540,960)).save(key,quality=88)
                rendered=preview
            else:
                rendered=frame(t)
            for side,pose in ((s,character_plate(t)[1][s])
                              for s in ("left","right")):
                a=math.dist(pose.hip,pose.knee)
                b=math.dist(pose.knee,pose.foot)
                worst_bone_error=max(worst_bone_error,
                                     abs(a-UPPER),abs(b-LOWER))
                prev=last_contact[side]
                if pose.planted:
                    if prev is not None and prev[0]==math.floor(
                            (t-(0 if side=="left" else PERIOD*.5))/PERIOD):
                        planted_contact_drift=max(planted_contact_drift,
                             math.dist(prev[1],pose.foot))
                    last_contact[side]=(
                        math.floor((t-(0 if side=="left" else PERIOD*.5))/PERIOD),
                        pose.foot)
                else:
                    last_contact[side]=None
            if i % FPS == 0:
                samples.append(dict(second=i//FPS,
                                    foxX=round(character_plate(t)[1]["bodyX"],2)))
            process.stdin.write(rendered.tobytes())
        process.stdin.close()
        code=process.wait(timeout=120)
        if code:
            raise RuntimeError(f"FFmpeg 2.5D encoder exited with {code}")
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    elapsed=time.perf_counter()-started
    if worst_bone_error>.001 or planted_contact_drift>.001:
        raise RuntimeError("Rig IK geometry or world foot lock regressed")
    probe=subprocess.run([
        "ffprobe","-v","error","-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of","json",str(output)],capture_output=True,text=True,
        check=True,timeout=40)
    meta=json.loads(probe.stdout)
    image=next((s for s in meta["streams"]
                if s.get("codec_type")=="video"),{})
    audio=next((s for s in meta["streams"]
                if s.get("codec_type")=="audio"),{})
    duration=float(meta["format"]["duration"])
    if (image.get("codec_name")!="h264"
            or (image.get("width"),image.get("height"))!=SIZE
            or image.get("r_frame_rate")!="30/1"
            or audio.get("codec_name")!="aac"
            or abs(duration-SECONDS)>.2):
        raise RuntimeError("Native motion-pilot MP4 technical contract failed")
    subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror","-i",
                    str(output),"-f","null","-"],check=True,
                   capture_output=True,timeout=180)
    report={
        "schemaVersion":1,"type":"original-25d-animated-fox-ik-motion-pilot",
        "status":"passed","scene":"fox-meadow-grounded-walk",
        "frames":frames,"fps":FPS,"size":list(SIZE),
        "durationSeconds":round(duration,3),
        "animation":"fresh per-frame authored geometry; no image interpolation",
        "layers":["sky","clouds","ridges","trees","meadow",
                  "grounded-shadow","ik-fox","contact-reactions",
                  "grass-foreground"],
        "actualTwoBoneInverseKinematics":True,
        "maximumBoneLengthErrorPx":round(worst_bone_error,5),
        "maximumPlantedFootWorldDriftPx":round(planted_contact_drift,5),
        "renderSeconds":round(elapsed,2),
        "voice":"none — motion demonstration, not narrated final episode",
        "audio":"original locally synthesized ambient score, AAC",
        "videoSha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "publicationApproved":False,"humanVisualReviewRequired":True,
        "oneSecondMovementSamples":samples,
    }
    (output.parent/"pilot-qa.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",
        encoding="utf-8")
    return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,
                        default=Path("out/p3-fox-25d/fox-grounded.mp4"))
    args=parser.parse_args()
    print(json.dumps(render(args.output),ensure_ascii=False))


if __name__=="__main__":
    main()
