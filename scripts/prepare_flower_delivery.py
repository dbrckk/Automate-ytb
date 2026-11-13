"""Decode and package the actual flower MP4; never publishes by itself."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw
from automate_ytb.media_qa import _parse_srt
from automate_ytb.shorts_delivery import validate_short
from benchmark_audiovisual import measure


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify_package(folder):
    manifest=json.loads((folder/"flower-manifest.json").read_text(encoding="utf8"))
    expected={"flower.mp4","flower.srt","flower-production.json","flower-contact-sheet.jpg"}
    if (manifest.get("status")!="passed" or manifest.get("releaseEligible") is not True
            or set(manifest.get("files",{}))!=expected):
        raise ValueError("Expected verified neural flower release package")
    for name, record in manifest["files"].items():
        source=folder/name
        if (source.is_symlink() or source.stat().st_size!=record["bytes"]
                or digest(source)!=record["sha256"]):
            raise ValueError("Release asset differs from its verified digest")


def prepare(video: Path, output: Path, *, release=False):
    video=video.resolve(strict=True)
    report_path=video.with_suffix(".json")
    if not report_path.is_file() and video.name=="flower.mp4":
        verify_package(video.parent)
        report_path=video.parent/"flower-production.json"
    report=json.loads(report_path.read_text(encoding="utf8"))
    srt=video.with_suffix(".srt")
    for key,source in (("videoSha256",video),("subtitleSha256",srt)):
        expected=report.get(key)
        if (release or expected is not None) and expected!=digest(source):
            raise ValueError("Production digest does not match final media")
    delivery=validate_short(video,require_audio=True)
    if delivery["status"]!="passed":
        raise ValueError("Encoded flower video failed technical delivery")
    if (report.get("publicationApproved") is not False or report.get("language")!="fr"
            or report.get("actorCueCount")!=7 or report.get("beats")!=3
            or report.get("artwork",{}).get("originalVectorLayers")!=30):
        raise ValueError("Expected the unreviewed three-beat articulated flower pilot")
    if release and (report.get("voiceEngine")!="kokoro" or report.get("voiceName")!="ff_siwis"
                    or report.get("resolution")!=[1080,1920]):
        raise ValueError("Release requires French Kokoro and native 1080p, never eSpeak")
    media=delivery["media"]
    if (report.get("resolution")!=[media["width"],media["height"]]
            or media["fps"]!=30 or abs(report["durationSeconds"]-media["durationSeconds"])>.1):
        raise ValueError("Production report does not match encoded media")
    cues=_parse_srt(srt)
    previous=0
    for cue in cues:
        start,end,_=cue
        if start<previous or end>media["durationSeconds"]*1000+34:
            raise ValueError("Subtitles overlap or exceed the final video")
        previous=end
    if len(cues)!=report.get("subtitleCues"):
        raise ValueError("Subtitle count differs from production evidence")
    decoded=subprocess.run([
        "ffmpeg","-nostdin","-hide_banner","-v","info","-xerror","-i",str(video),
        "-map","0:v:0","-map","0:a:0","-vf","blackdetect=d=0.10:pix_th=0.02:pic_th=0.98",
        "-f","null","-"],capture_output=True,text=True,check=True,timeout=360)
    if "black_start:" in decoded.stderr:
        raise ValueError("Near-black interval detected in encoded flower video")
    measurement=measure(video,"articulated-flower")
    audio=measurement["audio"]
    if (not -17<=audio["integratedLufs"]<=-15 or audio["truePeakDbtp"]>-1.3
            or measurement["media"]["audioChannels"]!=2
            or measurement["media"]["audioSampleRateHz"]!=48000):
        raise ValueError("Final AAC mix failed stereo/loudness/peak checks")
    # 0.2 dB tolerance is for AAC reconstruction; mastering target is -1.5 dBTP.
    output.mkdir(parents=True,exist_ok=True)
    sheet=Image.new("RGB",(1080,1320),(12,19,32))
    bounds=report["beatBoundariesFrames"]
    times=[]
    for first,last in zip(bounds,bounds[1:]):
        times.extend(((first+.15*(last-first))/30,(first+.85*(last-first))/30))
    for index,seconds in enumerate(times):
        frame=subprocess.run(["ffmpeg","-nostdin","-v","error","-ss",str(seconds),
            "-i",str(video),"-frames:v","1","-vf","scale=360:640","-f","image2pipe",
            "-vcodec","png","-"],capture_output=True,check=True,timeout=60)
        with Image.open(io.BytesIO(frame.stdout)) as image:
            sheet.paste(image.convert("RGB"),((index%3)*360,(index//3)*660))
        ImageDraw.Draw(sheet).text(((index%3)*360+8,(index//3)*660+643),
                                  f"{seconds:.2f} s",fill="white")
    sheet_path=output/"flower-contact-sheet.jpg"
    sheet.save(sheet_path,quality=90)
    files={}
    for source,name in ((video,"flower.mp4"),(srt,"flower.srt"),
                        (report_path,"flower-production.json")):
        target=output/name
        if source!=target.resolve(): shutil.copyfile(source,target)
        files[name]={"sha256":digest(target),"bytes":target.stat().st_size}
    files[sheet_path.name]={"sha256":digest(sheet_path),"bytes":sheet_path.stat().st_size}
    evidence={"schemaVersion":1,"status":"passed","fullDecode":True,
        "nearBlackIntervals":0,"releaseEligible":release,"files":files,
        "subtitleCues":len(cues),"measurement":measurement,"audioEvents":report["audioEvents"],
        "voiceEngine":report["voiceEngine"],"humanReviewed":False,"publicationApproved":False,
        "masteringTargetDbtp":-1.5,"aacPeakToleranceDb":.2}
    (output/"flower-manifest.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf8")
    return evidence


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--video",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--release",action="store_true")
    args=cli.parse_args()
    print(json.dumps(prepare(args.video,args.output,release=args.release),indent=2))
