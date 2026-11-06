"""Auditable optical shot diversity for actual decoded video (not semantic matching).

Measures neighboring scene samples on the final MP4, including the effects
of reframing, subtitles and editing. A similarity warning is NOT a claim that
two scenes depict the same subject. Never blocks artistic choices by default.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

WIDTH, HEIGHT = 96, 54
PIXELS = WIDTH * HEIGHT
MAX_SCENES = 150


def _frame(video: Path, second: float) -> bytes:
    command = [
        "ffmpeg", "-nostdin", "-v", "error",
        "-ss", f"{second:.3f}", "-i", str(video),
        "-frames:v", "1", "-an",
        "-vf", f"scale={WIDTH}:{HEIGHT}:flags=fast_bilinear,format=gray",
        "-f", "rawvideo", "pipe:1",
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=35)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Final video optical sampling timed out") from exc
    if result.returncode or len(result.stdout) != PIXELS:
        raise ValueError("Could not decode the final MP4 at an authored scene midpoint")
    return result.stdout


def _signature(frame: bytes) -> dict:
    if len(frame) != PIXELS:
        raise ValueError("Unexpected frame sample dimensions")
    mean = sum(frame) / PIXELS
    deviation = math.sqrt(max(0., sum(x*x for x in frame)/PIXELS - mean*mean))
    # Spatial 8x6 blocks avoid treating identical global luminance as
    # identical composition. They are NOT semantic object features.
    blocks = []
    for by in range(6):
        for bx in range(8):
            pixels = [
                frame[y*WIDTH+x]
                for y in range(by*9,(by+1)*9)
                for x in range(bx*12,(bx+1)*12)
            ]
            blocks.append(round(sum(pixels)/len(pixels), 2))
    return {"meanLuminance":round(mean,2),
            "contrastStdDev":round(deviation,2),
            "blocks":blocks,
            "frameSHA256":hashlib.sha256(frame).hexdigest()}


def compare_signatures(left: dict, right: dict) -> dict:
    a, b = left["blocks"], right["blocks"]
    if len(a) != 48 or len(b) != 48:
        raise ValueError("Invalid optical signature")
    # Mean absolute difference over spatial blocks, not just mean brightness.
    distance = sum(abs(x-y) for x,y in zip(a,b))/len(a)
    return {"spatialBlockDifference":round(distance,2),
            "nearDuplicateOpticalComposition":distance < 9}


def analyze_frames(frames: list[bytes], *, source_names: list[str]) -> dict:
    if not 2 <= len(frames) <= MAX_SCENES or len(frames) != len(source_names):
        raise ValueError("At least two aligned, distinct authored scenes required")
    signatures = [_signature(frame) for frame in frames]
    comparisons = []
    for i in range(1,len(frames)):
        measure = compare_signatures(signatures[i-1],signatures[i])
        comparisons.append({
            "previousScene":i,"scene":i+1,
            "sameSourceFile":source_names[i-1] == source_names[i],
            **measure,
        })
    warnings = [
        f"Adjacent scenes {x['previousScene']} and {x['scene']} have visually similar spatial blocks; editorial review recommended"
        for x in comparisons if x["nearDuplicateOpticalComposition"]
    ]
    warnings.extend(
        f"Scene {i+1} is near-black or very low contrast"
        for i,s in enumerate(signatures)
        if s["meanLuminance"] < 15 or s["contrastStdDev"] < 7
    )
    return {
        "schemaVersion":1,
        "method":"decoded-final-mp4-grayscale-spatial-blocks-v1",
        "sceneCount":len(frames),
        "distinctSourceFiles":len(set(source_names)),
        "adjacentNearDuplicateCount":sum(x["nearDuplicateOpticalComposition"] for x in comparisons),
        "adjacentSourceChangeCount":sum(not x["sameSourceFile"] for x in comparisons),
        "scenes":[{
            "scene":i+1,
            "sourceName":source_names[i],
            **{k:v for k,v in s.items() if k!="blocks"}
        } for i,s in enumerate(signatures)],
        "adjacentComparisons":comparisons,
        "warnings":warnings,
        "semanticMatchingPerformed":False,
        "editorialReviewRequired":True,
        "publicationApproved":False,
        "limitations":[
            "Similar color and composition do not prove repeated content.",
            "Different spatial blocks do not prove a different narrative event.",
            "Subtitles and camera motion can affect measured differences.",
            "No speech-to-image semantic alignment is inferred.",
        ],
    }


def audit(video: Path, plan: Path, edit_report: Path) -> dict:
    if not video.is_file() or video.is_symlink() or video.suffix.lower()!=".mp4":
        raise ValueError("Expected a local regular final MP4")
    storyboard = json.loads(plan.read_text(encoding="utf-8"))
    report = json.loads(edit_report.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]
    shots = report["shots"]
    if not 2 <= len(scenes) <= MAX_SCENES or len(scenes)!=len(shots):
        raise ValueError("Scene plan and real footage provenance mismatch")
    if report["sceneCount"]!=len(scenes):
        raise ValueError("Shot provenance count mismatch")
    if any(s["id"]!=sh["sceneId"] for s,sh in zip(scenes,shots)):
        raise ValueError("Scene provenance ordering mismatch")
    duration = float(scenes[-1]["endMs"])/1000
    if not math.isfinite(duration) or duration>180:
        raise ValueError("Unsupported final duration")
    times=[]
    previous=0
    for scene in scenes:
        start,end=scene["startMs"],scene["endMs"]
        if not previous <= start < end <= 180_000:
            raise ValueError("Invalid scene timing")
        times.append((start+end)/2000)
        previous=end
    frames=[_frame(video,second) for second in times]
    result=analyze_frames(frames,source_names=[s["sourceName"] for s in shots])
    result["videoSHA256"]=hashlib.sha256(video.read_bytes()).hexdigest()
    result["sampleSeconds"]=times
    return result


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Review shot-to-shot optical diversity in a real finished Short")
    parser.add_argument("--video",type=Path,required=True)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--edit-report",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args(argv)
    result=audit(args.video,args.plan,args.edit_report)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"scenes":result["sceneCount"],
                      "adjacentNearDuplicates":result["adjacentNearDuplicateCount"],
                      "warnings":result["warnings"],
                      "semanticMatchingPerformed":False}))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
