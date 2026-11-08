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

from automate_ytb.forest25d import frame, FPS, SECONDS, SIZE, ORIGIN_X, SPEED, TORSO_Y, KINDS
from automate_ytb.rig25d import UPPER, LOWER, PERIOD, GROUND, walking_leg
from automate_ytb.forest_contact25d import IMPACT_TIME, contact_at, VERSION as FLOWER_VERSION
from automate_ytb.forest_butterfly25d import VERSION as BUTTERFLY_VERSION
from automate_ytb.forest_story25d import STORY, VERSION as STORY_VERSION
from automate_ytb.forest_cinematic_world25d import VERSION as ART_VERSION
from automate_ytb.forest_cinematic_framing25d import VERSION as CAMERA_VERSION
from automate_ytb.forest_reactive_meadow25d import VERSION as MEADOW_VERSION, ROOTS as MEADOW_ROOTS
from automate_ytb.forest_character_art25d import VERSION as CHARACTER_VERSION
from automate_ytb.forest_organic_mesh25d import VERSION as ORGANIC_VERSION
from automate_ytb.forest_anatomical_limb25d import VERSION as ANATOMY_VERSION
from automate_ytb.forest_head_sculpt25d import VERSION as HEAD_VERSION



def framing_provenance(story: bool) -> dict | None:
    """Never claim event-directed optical crops for a legacy-camera pilot."""
    if type(story) is not bool:
        raise ValueError("Story-mode camera provenance requires a real flag")
    if not story:
        return None
    return {"version":CAMERA_VERSION,
            "mobileGroundClearOfCaptions":True,
            "actorAndButterflyTracking":True}


def score(path: Path, *, interaction: bool = False) -> None:
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
        signal=value*.10*envelope*pulse
        if interaction and 0 <= t-IMPACT_TIME <= .35:
            # Original, quiet impact chime exactly when the real right paw
            # plants on the flower; finite 48kHz PCM and no external media.
            dt=t-IMPACT_TIME
            signal+=.12*math.exp(-15*dt)*(
                math.sin(2*math.pi*590*dt)
                +.32*math.sin(2*math.pi*1180*dt))
        pcm.append(round(max(-1.,min(1.,signal))*32767))
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        if sys.byteorder!="little":
            pcm.byteswap()
        wav.writeframes(pcm.tobytes())


def render(output: Path, *, kind: str = "fox",
           interaction: bool = False, story: bool = False) -> dict:
    if type(story) is not bool or (story and not interaction):
        raise ValueError("Event-directed story requires interaction")
    if kind not in KINDS or type(interaction) is not bool:
        raise ValueError("Unsupported original 2.5D animal or interaction")
    if not isinstance(output,Path) or output.suffix.lower()!=".mp4":
        raise ValueError("Motion-pilot output requires an MP4 path")
    if not 0 < SECONDS <= 20 or FPS != 30:
        raise ValueError("Invalid bounded 2.5D production profile")
    output.parent.mkdir(parents=True,exist_ok=True)
    pad=output.parent/"original-score.wav"
    score(pad,interaction=interaction)
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
                preview=frame(t,kind=kind,interaction=interaction,story=story)
                preview.resize((540,960)).save(key,quality=88)
                rendered=preview
            else:
                rendered=frame(t,kind=kind,interaction=interaction,story=story)
            for side in ("left","right"):
                pose=walking_leg(t,side=side,origin_x=ORIGIN_X,
                                 speed=SPEED,torso_y=TORSO_Y,ground_y=GROUND)
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
                                    actorX=round(ORIGIN_X+SPEED*t,2)))
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
    event=(contact_at(IMPACT_TIME+.01,origin_x=ORIGIN_X,
                      speed=SPEED,torso_y=TORSO_Y) if interaction else None)
    if event is not None and (not event.planted or
                              event.y != GROUND or
                              not 0 < event.x < SIZE[0]):
        raise RuntimeError("Authored interaction lost real paw contact")
    report={
        "schemaVersion":3,"type":"original-25d-animated-animal-ik-motion-pilot",
        "status":"passed","scene":f"{kind}-meadow-grounded-walk",
        "animal":kind,"interactionEnabled":interaction,
        "causalButterfly":(
            {"trigger":"rig-verified paw impact",
             "firstVisibleSeconds":round(IMPACT_TIME+.12,3),
             "flightPhases":["approach","hover","retreat"],
             "wingAndFlightVersion":BUTTERFLY_VERSION,
             "target":"world-space responsive flower",
             "wings":"independently animated 9Hz original artwork"}
            if interaction else None),
        "eventDirectedStory":(
            {"version":STORY_VERSION,
             "beats":[{"name":name,"startSeconds":start,
                       "endSeconds":end,"title":title,"subtitle":subtitle}
                      for name,start,end,title,subtitle in STORY],
             "narration":"not generated — visual story preview only"}
            if story else None),
        "groundedFlowerContact":(
            {"version":FLOWER_VERSION,
             "releasedPetals":7,
             "motion":"outward fan avoids face",
             "eventSeconds":round(event.time,5),
             "pawWorldX":round(event.x,3),
             "pawGroundY":event.y,
             "source":"verified right-foot landing of real IK rig",
             "synchronizedOriginalChime":True,
             "independentWorldSpacePetals":True}
            if event is not None else None),
        "headSculpt":{"version":HEAD_VERSION,"originalEyeMouthPreserved":True,"worldFootIKUnchanged":True},
        "anatomicalLimbs":{"version":ANATOMY_VERSION,"curvedVolumes":True,"originalIKUnchanged":True},
        "organicSoftBody":{
            "version":ORGANIC_VERSION,
            "source":"continuous inverse-mapped Pillow strip mesh",
            "realBreathing":True,
            "gaitMassTransfer":True,
            "actualIKPawPositionsWarped":False,
            "postContactDampedRecoil":bool(interaction),
            "inertialTail":True,
            "attachedScarfDeformedWithTorso":True},
        "characterMaterials":{
            "version":CHARACTER_VERSION,
            "originalFurLightWrap":True,
            "exactIKWorldContact":True,
            "expressions":["body","look-down","surprise","follow","blink"],
            "animatedScarfTip":True},
        "livingMeadow":{"version":MEADOW_VERSION,
                        "worldSpaceRootedPlants":len(MEADOW_ROOTS),
                        "windAlwaysAnimated":True,
                        "causalPawWave":bool(interaction),
                        "wavePropagationPxPerSecond":300},
        "cinematicFraming":framing_provenance(story),
        "artDirection":{"version":ART_VERSION,
                        "staticPlates":9,"independentlyMovingAtmosphere":True,
                        "originalAssets":True,"layeredSunlight":True,
                        "physicalOpticalCuts":bool(story)},
        "frames":frames,"fps":FPS,"size":list(SIZE),
        "durationSeconds":round(duration,3),
        "animation":"fresh per-frame authored geometry; no image interpolation",
        "layers":["sky","clouds","ridges","sunbeams","trees",
                  "understory","meadow","grounded-shadow",
                  * (["responsive-flower"] if interaction else []),
                  "ik-"+kind,"contact-reactions",
                  * (["released-petals","reactive-butterfly"]
                     if interaction else []),
                  "living-light","grass-foreground","filmic-grade"],
        "actualTwoBoneInverseKinematics":True,
        "maximumBoneLengthErrorPx":round(worst_bone_error,5),
        "maximumPlantedFootWorldDriftPx":round(planted_contact_drift,5),
        "renderSeconds":round(elapsed,2),
        "voice":"none — motion demonstration, not narrated final episode",
        "audio":("original ambient score and rig-synchronized impact chime, AAC"
                 if interaction else "original locally synthesized ambient score, AAC"),
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
    parser.add_argument("--animal",choices=KINDS,default="fox",
                        help="Original fox, rabbit or cat artwork with grounded IK")
    parser.add_argument("--story",action="store_true",
                        help="Event-directed four-shot original visual story; requires --interaction")
    parser.add_argument("--interaction",action="store_true",
                        help="Add authored paw-to-flower contact, moving petals and original chime")
    args=parser.parse_args()
    print(json.dumps(render(args.output,kind=args.animal,
                            interaction=args.interaction,story=args.story),ensure_ascii=False))


if __name__=="__main__":
    main()
