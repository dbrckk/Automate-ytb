#!/usr/bin/env python3
"""A NEW English science short about solar storms: original narration + NASA motion.

Source videos: SDO observations (real, false-color), CIL Earth magnetosphere
simulation, NASA space-weather satellite illustrations and Alaska aurora footage.
No graphics from a slideshow, no credits or paid services, no source audio reused.
"""
import json
from pathlib import Path
import subprocess
import time

import numpy as np
if __package__:
    from .camera_motion import build_portrait_camera, camera_metadata
else:
    from camera_motion import build_portrait_camera, camera_metadata

HERE=Path(__file__).resolve().parent
OUT=HERE/"out"
CACHE=HERE/".cache"
OUT.mkdir(parents=True,exist_ok=True)
CACHE.mkdir(parents=True,exist_ok=True)

MEDIA={
    "sun131":"https://svs.gsfc.nasa.gov/vis/a010000/a014500/a014536/20240222_XFlare_131A_2048p30.webm",
    "sun171":"https://svs.gsfc.nasa.gov/vis/a010000/a014500/a014536/20240222_XFlare_171A_2048p30.webm",
    "sun304":"https://svs.gsfc.nasa.gov/vis/a010000/a014500/a014536/20240222_XFlare_304A_2048p30.webm",
    # CME launch is a NASA conceptual animation showing the Sun, not Earth.
    "cme_launch":"https://svs.gsfc.nasa.gov/vis/a010000/a013000/a013003/CME.webm",
    "magnetosphere":"https://svs.gsfc.nasa.gov/vis/a020000/a020200/a020297/H_0219_VC_Animation_Earth_Only.mp4",
    "satellite":"https://svs.gsfc.nasa.gov/vis/a010000/a014900/a014956/14956_SatelliteImpact01_4K_YouTube.mp4",
    "satellite2":"https://svs.gsfc.nasa.gov/vis/a010000/a014900/a014956/14956_SatelliteImpact02_4K_YouTube.mp4",
    "aurora":"https://svs.gsfc.nasa.gov/vis/a010000/a015000/a015077/15077_AuroraTimelapse_4K_YouTube.mp4",
}

SCENES=[
    "Our Sun can launch a storm that travels all the way to Earth.",
    "These are real solar eruptions, recorded by NASA in extreme ultraviolet light.",
    "Some eruptions also throw enormous clouds of charged plasma into space.",
    "When one reaches Earth, our magnetic field takes the hit and bends.",
    "The result can be breathtaking auroras. Strong storms can also disrupt satellites and navigation.",
    "That's space weather: a reminder that Earth is connected to its star.",
]
# Real footage does not depict a single sequential historical storm. Use it for
# educational explanation only, with explicit contextual credit in metadata.
SHOT_PLAN=[
    [("sun131",1.0,.61),("sun304",11.0,.39)],
    [("sun171",8.0,.52),("sun131",17.0,.48)],
    [("sun304",24.0,.49),("cme_launch",1.5,.51)],
    [("magnetosphere",5.5,.60),("magnetosphere",12.0,.40)],
    [("aurora",9.0,.35),("satellite",2.0,.34),("satellite2",3.0,.31)],
    [("aurora",21.0,.56),("sun171",24.0,.44)],
]
# Role metadata prevents confusing a solar launch with Earth's magnetosphere.
VISUAL_ROLE={
    "sun131":"solar_observation",
    "sun171":"solar_observation",
    "sun304":"solar_observation",
    "cme_launch":"solar_cme_animation",
    "magnetosphere":"earth_magnetosphere_animation",
    "aurora":"aurora_footage",
    "satellite":"space_technology_animation",
    "satellite2":"space_technology_animation",
}
SCENE_ALLOWED_ROLES=(
    frozenset({"solar_observation"}),
    frozenset({"solar_observation"}),
    frozenset({"solar_observation","solar_cme_animation"}),
    frozenset({"earth_magnetosphere_animation"}),
    frozenset({"aurora_footage","space_technology_animation"}),
    frozenset({"aurora_footage","solar_observation"}),
)


def validate_storyboard():
    """Reject scientifically mismatched footage before expensive rendering."""
    if len(SHOT_PLAN)!=len(SCENES) or len(SCENE_ALLOWED_ROLES)!=len(SCENES):
        raise ValueError("Narrated scene and NASA storyboard length mismatch")
    if set(VISUAL_ROLE)!=set(MEDIA):
        raise ValueError("NASA source role catalog does not match sources")
    for index,(scene,allowed) in enumerate(zip(SHOT_PLAN,SCENE_ALLOWED_ROLES)):
        roles=set()
        if len(scene)<2:
            raise ValueError(f"Scene {index+1} needs two or more shots")
        if abs(sum(share for _,_,share in scene)-1)>1e-7:
            raise ValueError(f"Invalid source proportions in scene {index+1}")
        for key,seek,share in scene:
            if key not in MEDIA or VISUAL_ROLE[key] not in allowed:
                raise ValueError(f"Scientifically mismatched source in scene {index+1}: {key}")
            if not 0<=seek<900 or not 0<share<1:
                raise ValueError(f"Invalid offset or fraction in scene {index+1}")
            roles.add(VISUAL_ROLE[key])
        if index==2 and "solar_cme_animation" not in roles:
            raise ValueError("Scene 3 must show a Sun-origin CME animation")
        if index==4 and not {"aurora_footage","space_technology_animation"}<=roles:
            raise ValueError("Scene 5 must show both aurora and satellite impacts")


VOICE="am_michael"
VOICE_SPEEDS=[1.04,.97,1.00,.96,1.02,.93]

def run(cmd):
    print("RUN"," ".join(str(x) for x in cmd)[:260],flush=True)
    subprocess.run([str(x) for x in cmd],check=True)

def duration(path):
    result=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nokey=1:noprint_wrappers=1",str(path)],
        check=True,capture_output=True,text=True)
    return float(result.stdout.strip())

def download(url):
    # The storyboard contract is importable by lightweight repository tests.
    # HTTP is required only during the real source download.
    import requests
    path=CACHE/Path(url).name
    if path.is_file() and path.stat().st_size>100_000:
        duration(path)
        return path
    partial=path.with_suffix(path.suffix+".part")
    for retry in range(3):
        try:
            with requests.get(url,stream=True,timeout=(20,160),
                              headers={"User-Agent":"Mozilla/5.0 NASA-SVS-educational-reel"}) as resp:
                resp.raise_for_status()
                with partial.open("wb") as stream:
                    for block in resp.iter_content(1<<20):
                        if block: stream.write(block)
            if partial.stat().st_size<100_000:
                raise RuntimeError("Tiny download")
            duration(partial)
            partial.replace(path)
            print("SOURCE_OK",path.name,path.stat().st_size,flush=True)
            return path
        except Exception as err:
            print("SOURCE_RETRY",retry,str(err)[:180],flush=True)
            time.sleep(retry+1)
    raise RuntimeError(f"NASA source inaccessible: {url}")

def voice():
    import soundfile as sf
    from kokoro import KPipeline
    pipe=KPipeline(lang_code="a")
    wavs=[]
    timing=[]
    frame=0
    sr=24000
    for index,text in enumerate(SCENES):
        pieces=[np.asarray(a,dtype=np.float32) for _,_,a in
                pipe(text,voice=VOICE,speed=VOICE_SPEEDS[index],split_pattern=r"\n+")]
        if not pieces: raise RuntimeError(f"Speech synthesis failed on {index}")
        samples=np.concatenate(pieces)
        a=frame/sr
        b=(frame+len(samples))/sr
        timing.append({"text":text,"start":a,"end":b,"speech_duration":b-a})
        wavs.extend([samples,np.zeros(int(.21*sr),dtype=np.float32)])
        frame+=len(samples)+int(.21*sr)
    final=np.concatenate(wavs)
    sf.write(OUT/"narration.wav",final,sr,subtype="PCM_16")
    return timing,len(final)/sr

def clip(key,index,scene,offset,length):
    source=CACHE/Path(MEDIA[key]).name
    source_duration=duration(source)
    seek=max(0,min(offset,source_duration-length-.1))
    dest=OUT/f"shot_{index:02}.mp4"
    # Cinematic motion on genuine NASA source imagery without time stretching.
    vf=build_portrait_camera(key,index)
    run(["ffmpeg","-y","-v","error","-ss",f"{seek:.3f}","-i",source,
        "-t",f"{length:.3f}","-an","-vf",vf,"-r","30",
        "-c:v","libx264","-crf","19","-preset","veryfast",
        "-pix_fmt","yuv420p","-movflags","+faststart",dest])
    if abs(duration(dest)-length)>.25:
        raise RuntimeError(f"Shot time mismatch {dest}")
    return dest,{"scene":scene,"source":key,"start":seek,"duration":length,
                 "camera":camera_metadata(key,index),
                 "visual_role":VISUAL_ROLE[key],
                 "source_type":("observation" if key.startswith("sun") or key=="aurora"
                                else "NASA conceptual animation")}

def main():
    validate_storyboard()
    for name,url in MEDIA.items():
        src=download(url)
        print("SOURCE",name,src.name,"duration",round(duration(src),2),flush=True)
    segments,total=voice()
    clips=[];report=[]
    for scene,(plan,seg) in enumerate(zip(SHOT_PLAN,segments)):
        if abs(sum(fraction for _,_,fraction in plan)-1)>1e-7:
            raise RuntimeError("Invalid shot plan proportions")
        length=(seg["end"]-seg["start"])+.21
        elapsed=0
        for j,(key,seek,fraction) in enumerate(plan):
            span=length-elapsed if j==len(plan)-1 else length*fraction
            if span<.85:raise RuntimeError(f"Shot too short: {span}")
            path,data=clip(key,len(clips),scene,seek,span)
            clips.append(path);report.append(data);elapsed+=span
    listing=OUT/"shots.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in clips),encoding="utf-8")
    base=OUT/"visuals.mp4"
    run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",listing,
         "-c","copy","-an",base])
    out=OUT/"Solar_Storm_Base_EN.mp4"
    run(["ffmpeg","-y","-v","error","-i",base,"-i",OUT/"narration.wav",
         "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac",
         "-b:a","192k","-ar","48000","-af","highpass=f=70,lowpass=f=10500",
         "-t",f"{total:.3f}","-movflags","+faststart",out])
    run(["ffmpeg","-v","error","-i",out,"-f","null","-"])
    qa={"title":"The Sun Can Hit Earth With a Solar Storm",
        "video":out.name,"language":"en","source":"NASA SVS",
        "voice":VOICE,"voice_speeds":VOICE_SPEEDS,"duration":duration(out),
        "shot_count":len(clips),"shot_plan":report,"segments":segments,
        "references":list(MEDIA.values()),
        "note":"SDO false-color observations, NASA conceptual CME launch and magnetosphere animations, and independent aurora footage; not one historical storm"}
    (OUT/"production_report.json").write_text(json.dumps(qa,indent=2),encoding="utf-8")
    (OUT/"publication.txt").write_text(
        "Title: Can a Storm on the Sun Reach Earth?\n"
        "Description: Watch NASA observations of the Sun, visualizations of "
        "Earth's magnetic shield, and aurora footage. Solar flares and "
        "coronal mass ejections are distinct phenomena. Clips illustrate "
        "the physics; they do not show one continuous historical storm. "
        "Credits: NASA Goddard Space Flight Center/SDO, NASA GSFC Conceptual "
        "Image Lab/Bailee DesRocher, NASA GSFC/CIL/Krystofer Kim, NASA/Mike Toillion. "
        "NASA SVS 14536, 13029, 20297, 14956, 15077.\n"
        "Hashtags: #Sun #SpaceWeather #SolarStorm #ScienceShorts\n",
        encoding="utf-8")
    print("BASE_OK",out,round(duration(out),3),len(clips),flush=True)

if __name__=="__main__":
    main()
