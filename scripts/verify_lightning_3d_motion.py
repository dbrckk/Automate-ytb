"""Validate independently rendered 3D shot frames and the actual H.264 pilot.

This checks genuine per-frame visual change, immutable SHA256 evidence, five
causal beats and full playable-file decoding. A manifesto-only test cannot pass.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageChops, ImageStat

BEATS=("charge","leader","connection","return","thunder")


def verify(folder: Path, *, require_movie: bool=True) -> dict:
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Invalid 3D preview root")
    manifest=folder/"manifest.json"
    if (not manifest.is_file() or manifest.is_symlink() or
            not 100<manifest.stat().st_size<200_000):
        raise ValueError("Invalid or missing 3D motion manifest")
    data=json.loads(manifest.read_text(encoding="utf8"))
    if (type(data) is not dict or data.get("schemaVersion")!=1 or
            data.get("version")!="storm-3d-causal-motion-p54-v1" or
            data.get("generator")!="blender-cycles-cpu-animated" or
            data.get("beatOrder")!=list(BEATS)):
        raise ValueError("Invalid scene generation provenance")
    for key,low,high in (("width",320,720),("height",400,900),
                          ("fps",4,24),("framesPerBeat",2,12),
                          ("samples",4,32),("cloudVertices",1000,500000),
                          ("meshObjects",110,2000),
                          ("actual3dCloudMeshes",3,3)):
        value=data.get(key)
        if type(value) is not int or not low<=value<=high:
            raise ValueError("Invalid 3D motion metric: "+key)
    frame_count=5*data["framesPerBeat"]
    if (data.get("frameCount")!=frame_count or
            not isinstance(data.get("frameEvidence"),list) or
            len(data["frameEvidence"])!=frame_count):
        raise ValueError("Incomplete five-beat storm story")
    prior=None
    beat_first={}
    change_magnitudes=[]
    for i,record in enumerate(data["frameEvidence"]):
        if type(record) is not dict:
            raise ValueError("Invalid frame evidence row")
        filename="frame-%04d.png"%i
        beat=BEATS[i//data["framesPerBeat"]]
        if record.get("file")!=filename or record.get("beat")!=beat:
            raise ValueError("Wrong physical beat order or frame filename")
        progress=record.get("progress")
        power=record.get("electricalLightPower")
        fraction=record.get("visibleChannelFraction")
        if (type(progress) not in (float,int) or not 0<=progress<=1 or
                type(power) not in (float,int) or not 0<=power<=3 or
                type(fraction) not in (float,int) or not 0<=fraction<=1 or
                not isinstance(record.get("cameraPosition"),list) or
                len(record["cameraPosition"])!=3 or
                any(type(v) not in (float,int) or abs(v)>100
                    for v in record["cameraPosition"])):
            raise ValueError("Invalid causal staging data")
        if beat=="charge" and fraction!=0:
            raise ValueError("Charge separation cannot show a connected bolt")
        if beat in ("return","thunder") and fraction!=1:
            raise ValueError("The return channel must be physically complete")
        digest=record.get("sha256")
        if (type(digest) is not str or
                not re.fullmatch("[0-9a-f]{64}",digest)):
            raise ValueError("Missing source frame SHA256")
        file=folder/filename
        if (not file.is_file() or file.is_symlink() or
                not 10_000<=file.stat().st_size<=40_000_000):
            raise ValueError("Missing/corrupted Cycles frame")
        if hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
            raise ValueError("Altered 3D frame")
        with Image.open(file) as picture:
            if (picture.format!="PNG" or
                    picture.size!=(data["width"],data["height"])):
                raise ValueError("Incorrect source frame dimensions")
            picture.load()
            rgb=picture.convert("RGB")
        stat=ImageStat.Stat(rgb)
        if min(stat.stddev)<5 or max(stat.mean)<14:
            raise ValueError("Flat/dark unusable 3D frame")
        if beat not in beat_first:
            beat_first[beat]=rgb.copy()
        if prior is not None:
            difference=ImageChops.difference(rgb,prior)
            magnitude=sum(ImageStat.Stat(difference).mean)/3
            change_magnitudes.append(round(magnitude,3))
            # Reject frozen-frame export even when time metadata advances.
            if magnitude<.25:
                raise ValueError("3D animation contains a frozen frame")
        prior=rgb
    if len({hashlib.sha256(im.tobytes()).hexdigest()
            for im in beat_first.values()})!=5:
        raise ValueError("Five different action shots not present")
    result={"version":data["version"],"frames":frame_count,
            "beats":list(BEATS),"minChange":min(change_magnitudes),
            "meanChange":round(sum(change_magnitudes)/len(change_magnitudes),3),
            "width":data["width"],"height":data["height"],
            "samples":data["samples"],"fps":data["fps"]}
    if require_movie:
        movie=folder/"storm-3d-motion-proof.mp4"
        if (not movie.is_file() or movie.is_symlink() or
                not 30_000<=movie.stat().st_size<=100_000_000):
            raise ValueError("No playable 3D animation")
        probe=subprocess.run(
            ["ffprobe","-v","error","-select_streams","v:0",
             "-show_entries",
             "stream=codec_name,width,height,avg_frame_rate,nb_frames:format=duration",
             "-of","json",str(movie)],
            check=True,timeout=35,capture_output=True,text=True)
        meta=json.loads(probe.stdout)
        streams=meta.get("streams",[])
        if len(streams)!=1:
            raise ValueError("3D H264 video stream missing")
        st=streams[0]
        length=float(meta["format"]["duration"])
        if (st["codec_name"]!="h264" or
                (st["width"],st["height"])!=
                (data["width"],data["height"]) or
                Fraction(st["avg_frame_rate"])!=data["fps"] or
                abs(length-frame_count/data["fps"])>.08 or
                int(st.get("nb_frames",0))!=frame_count):
            raise ValueError("Rendered movie contradicts original frame sequence")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror",
                        "-i",str(movie),"-f","null","-"],
                       check=True,timeout=90,capture_output=True)
        result["movieSizeBytes"]=movie.stat().st_size
        result["movieSHA256"]=hashlib.sha256(movie.read_bytes()).hexdigest()
        result["durationSeconds"]=length
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--folder",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(verify(args.folder.resolve()),sort_keys=True))


if __name__=="__main__":
    main()
