"""Render a real narrated vertical forest short with Kokoro-synchronized cuts.

Requires the existing optional open-source speech extra. No eSpeak fallback.
All cut timing is derived from actual generated PCM; no estimated speech.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import wave

from automate_ytb.forest25d import frame, FPS, SIZE
from automate_ytb.forest_voice_timeline import (
    ENGLISH_SCRIPT, FRENCH_SCRIPT, measured_timeline,
)
from automate_ytb.short_voice import synthesize
from automate_ytb.forest_captions25d import caption_plate,VERSION as CAPTION_VERSION
from automate_ytb.forest_butterfly25d import VERSION as BUTTERFLY_VERSION
from automate_ytb.forest_cinematic_world25d import VERSION as ART_VERSION
from automate_ytb.forest_character_art25d import VERSION as CHARACTER_VERSION
from automate_ytb.forest_organic_mesh25d import VERSION as ORGANIC_VERSION
from automate_ytb.forest_anatomical_limb25d import VERSION as ANATOMY_VERSION
from automate_ytb.forest_head_sculpt25d import VERSION as HEAD_VERSION


def render(destination: Path, *, language: str="en", animal: str="fox") -> dict:
    if language not in ("en","fr") or animal not in ("fox","rabbit","cat"):
        raise ValueError("Unsupported narrated animal or language")
    if not isinstance(destination,Path) or destination.suffix.lower()!=".mp4":
        raise ValueError("Output must be an MP4")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p35-narrated-") as temp:
        folder=Path(temp)
        script=folder/"script.txt"
        script.write_text("\n".join(ENGLISH_SCRIPT if language=="en"
                                   else FRENCH_SCRIPT)+"\n",encoding="utf-8")
        voice=folder/"kokoro.wav"
        report=synthesize(script_path=script,destination=voice,
                          language=language,style="natural")
        timeline=measured_timeline(report,language=language)
        aligned=folder/"aligned.wav"
        with wave.open(str(voice),"rb") as wav:
            if (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())!=(1,2,24000):
                raise RuntimeError("Kokoro WAV must be mono signed 16bit 24kHz")
            samples=wav.readframes(wav.getnframes())
        target=bytearray(b"\0\0"*round(timeline.duration*24000))
        for beat,span in zip(timeline.beats,report["beats"]):
            start,end=span["startMs"],span["endMs"]
            begin=round(start*24)*2
            finish=round(end*24)*2
            payload=samples[begin:finish]
            offset=round(beat.speech_start*24000)*2
            if len(payload)==0 or offset+len(payload)>len(target):
                raise RuntimeError("Voice alignment exceeded narrated film duration")
            target[offset:offset+len(payload)]=payload
        with wave.open(str(aligned),"wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(target)
        command=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                 "-f","rawvideo","-pixel_format","rgb24",
                 "-video_size",f"{SIZE[0]}x{SIZE[1]}",
                 "-framerate",str(FPS),"-i","pipe:0",
                 "-i",str(aligned),"-map","0:v:0","-map","1:a:0",
                 "-c:v","libx264","-preset","veryfast","-crf","22",
                 "-pix_fmt","yuv420p","-r",str(FPS),"-g","60",
                 "-c:a","aac","-b:a","128k","-ar","48000",
                 "-shortest","-movflags","+faststart",str(destination)]
        proc=subprocess.Popen(command,stdin=subprocess.PIPE)
        count=round(timeline.duration*FPS)
        try:
            assert proc.stdin is not None
            for index in range(count):
                source_t,beat=timeline.at(index/FPS)
                # Real frame-by-frame animation, never duplicated still frames.
                visual=frame(source_t,kind=animal,interaction=True,story=True,
                             show_story_titles=False)
                captions=caption_plate(index/FPS,timeline)
                visual.paste(captions,(0,0),captions)
                proc.stdin.write(visual.tobytes())
            proc.stdin.close()
            if proc.wait(timeout=120):
                raise RuntimeError("FFmpeg narrated story encoding failed")
        except BaseException:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            raise
        probe=subprocess.run(["ffprobe","-v","error","-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of","json",str(destination)],capture_output=True,text=True,
            check=True,timeout=40)
        media=json.loads(probe.stdout)
        video=next((s for s in media["streams"] if s.get("codec_type")=="video"),{})
        audio=next((s for s in media["streams"] if s.get("codec_type")=="audio"),{})
        duration=float(media["format"]["duration"])
        if (video.get("codec_name")!="h264"
            or (video.get("width"),video.get("height"))!=SIZE
            or video.get("r_frame_rate")!="30/1"
            or audio.get("codec_name")!="aac"
            or abs(duration-timeline.duration)>.2):
            raise RuntimeError("Narrated MP4 media contract failed")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror","-i",
                        str(destination),"-f","null","-"],
                       check=True,capture_output=True,timeout=180)
        result={"type":"original-25d-measured-kokoro-narrated-short",
                "language":language,"animal":animal,
                "voice":report["voice"],"voiceEngine":report["engine"],
                "captions":"actual-PCM-timed mobile-safe original text",
                "captionPresentation":CAPTION_VERSION,
                "artDirection":ART_VERSION,
                "characterMaterials":CHARACTER_VERSION,
                "organicSoftBody":ORGANIC_VERSION,
                "anatomicalLimbs":ANATOMY_VERSION,
                "headSculpt":HEAD_VERSION,
                "causalButterfly":BUTTERFLY_VERSION,
                "editorialTitles":False,
                "fps":FPS,"size":list(SIZE),"frames":count,
                "durationSeconds":round(duration,3),
                "beats":[{"name":b.name,"start":b.start,"end":b.end,
                          "speechStart":b.speech_start,"speechEnd":b.speech_end,
                          "text":b.narration} for b in timeline.beats],
                "videoSha256":hashlib.sha256(destination.read_bytes()).hexdigest(),
                "publicationApproved":False,"requiresListeningReview":True}
        destination.with_suffix(".json").write_text(
            json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--language",choices=("en","fr"),default="en")
    parser.add_argument("--animal",choices=("fox","rabbit","cat"),default="fox")
    args=parser.parse_args()
    print(json.dumps(render(args.output,language=args.language,
                            animal=args.animal),ensure_ascii=False))


if __name__=="__main__":
    main()
