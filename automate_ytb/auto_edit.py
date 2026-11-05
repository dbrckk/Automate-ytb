"""One-command offline multi-video edit, from licensed footage to real MP4.

Purposefully separates verifiable technical selection (nonblack frames,
contrast, basic motion) from semantic editing. No fictional AI transcript,
automatic source rights assumption, third-party downloads or publication.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .footage import VIDEO_SUFFIXES, probe_video
from .production import _sha, _write_json, PROVIDER, ingest_video, load_plan, render
from .scene_plan import plan as create_plan

VERSION = "licensed-multivideo-autoedit-v1"
MAX_SOURCES = 32
PIXELS = 96 * 54
MAX_SAMPLE_FRAMES = 6

GENRES = frozenset((
    "documentary", "cinematic", "product", "fitness", "education",
    "gaming", "travel", "personal"
))


def assign_sources(scene_ms: list[int], capacity_ms: list[int]) -> tuple[int, ...]:
    """Assign consecutive scene groups in source order, with NO repeated time.

    When feasible, maximize the number of different provided source files.
    Requires whole scenes in one source, never freezes a short file to fill
    an authored beat or silently loops it. Empty sources may be skipped.
    """
    if (not scene_ms or not capacity_ms or len(scene_ms) > 150
            or not 1 <= len(capacity_ms) <= MAX_SOURCES
            or any(type(x) is not int or x < 500 for x in scene_ms)
            or any(type(x) is not int or x < 0 for x in capacity_ms)):
        raise ValueError("Invalid original footage source capacity/scene timeline")
    n, m = len(scene_ms), len(capacity_ms)

    @lru_cache(maxsize=None)
    def solve(source_index: int, scene_index: int):
        if scene_index == n:
            return (0,) * (m - source_index)
        if source_index == m:
            return None
        best = None
        best_key = None
        total = 0
        for count in range(n - scene_index + 1):
            if count:
                total += scene_ms[scene_index + count - 1]
                if total > capacity_ms[source_index]:
                    break
            rest = solve(source_index + 1, scene_index + count)
            if rest is None:
                continue
            candidate = (count,) + rest
            # Use different recordings for visual variety. On ties favor
            # earlier input videos and balanced scene counts.
            used = sum(k > 0 for k in candidate)
            key = (used, -sum(j for j,k in enumerate(candidate) if k),
                   -max(candidate))
            if best_key is None or key > best_key:
                best_key, best = key, candidate
        return best

    chosen = solve(0, 0)
    if chosen is None:
        raise ValueError(
            "Not enough continuous original footage for these scenes "
            "in source order. Provide longer recordings, fewer scenes "
            "or shorter shot lengths (no looping/fabricated footage).")
    return chosen


def _sample_quality(source: Path, start: float, seconds: float) -> dict:
    """Bounded local FFmpeg sample: diagnostics, never a beauty/semantic score."""
    duration = min(1.60, seconds * .65)
    offset = start + (seconds - duration) / 2
    cmd = [
        "ffmpeg","-nostdin","-hide_banner","-loglevel","error",
        "-threads","1","-filter_threads","1",
        "-protocol_whitelist","file,pipe",
        "-ss",f"{offset:.3f}","-i",str(source),"-t",f"{duration:.3f}",
        "-vf","fps=3,scale=96:54:flags=fast_bilinear,format=gray",
        "-frames:v",str(MAX_SAMPLE_FRAMES),"-an",
        "-c:v","rawvideo","-pix_fmt","gray","-f","rawvideo","pipe:1"]
    try:
        response = subprocess.run(
            cmd, capture_output=True, check=False, timeout=35)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Timed out inspecting real source footage") from exc
    raw=response.stdout
    if response.returncode or not raw or len(raw) % PIXELS or (
            len(raw) > MAX_SAMPLE_FRAMES * PIXELS):
        raise ValueError(
            "Could not decode bounded real footage sample: " +
            response.stderr.decode("utf-8","replace")[-300:])
    images = [memoryview(raw)[i:i+PIXELS]
              for i in range(0,len(raw),PIXELS)]
    means = [sum(row) / PIXELS for row in images]
    luma = sum(means) / len(means)
    contrast = sum(
        math.sqrt(max(0, sum(p*p for p in row) / PIXELS - avg*avg))
        for row,avg in zip(images,means)) / len(images)
    differences = [
        sum(abs(x-y) for x,y in zip(a,b))/PIXELS
        for a,b in zip(images,images[1:])
    ]
    change = sum(differences)/len(differences) if differences else 0.
    # Optical quality proxies only. Excessive motion saturates rather than
    # winning forever; near-black or clipped-white scenes are penalized.
    exposure = max(0,1-abs(luma-120)/120)
    visual_score = (.45*min(contrast/48,1)
                    +.28*min(change/18,1)
                    +.27*exposure)
    if luma < 22 or luma > 234:
        visual_score -= .65
    return {
        "sampledFrames":len(images),
        "meanLuminance":round(luma,2),
        "contrastStdDev":round(contrast,2),
        "meanFrameChange":round(change,3),
        "technicalSelectionScore":round(visual_score,5),
        "requiresVisualReview":luma < 28 or luma > 232 or contrast < 8,
    }


def select_excerpts(
    sources: list[Path], scene_ms: list[int], capacities: list[int],
    counts: tuple[int, ...],
) -> list[dict]:
    """Choose nonoverlapping chronological excerpt starts, with local QA."""
    if len(sources) != len(capacities) or len(sources) != len(counts):
        raise ValueError("Original source allocation mismatch")
    result=[]
    scene_index=0
    for source,capacity,count in zip(sources,capacities,counts):
        if not count:
            continue
        lengths=scene_ms[scene_index:scene_index+count]
        slack=capacity-sum(lengths)
        if slack < 0:
            raise ValueError("Selected footage source is too short")
        cursor=0
        nominal_prefix=0
        for j,length in enumerate(lengths):
            remaining=sum(lengths[j+1:])
            latest=capacity-length-remaining
            ideal=nominal_prefix + slack*(j+1)/(count+1)
            ideal=min(latest,max(cursor,ideal))
            # Sample three nearby candidate windows only where source
            # slack permits. All samples are inside the assigned source
            # and never overlap a previously selected scene.
            spread=min(10000,slack/(count+1)*.75)
            candidate_ms=sorted(set(
                max(cursor,min(latest,int(round(
                    min(latest,max(cursor,ideal+delta))/100))*100))
                for delta in (-spread,0,spread)))
            evaluated=[]
            for start_ms in candidate_ms:
                metrics=_sample_quality(
                    source,start_ms/1000,length/1000)
                evaluated.append((metrics["technicalSelectionScore"],
                                  -abs(start_ms-ideal),start_ms,metrics))
            score, _, start_ms, metrics=max(evaluated)
            result.append({
                "sceneIndex":scene_index+j,
                "source":source,
                "startSeconds":round(start_ms/1000,3),
                "durationSeconds":round(length/1000,3),
                "sourceCapacitySeconds":round(capacity/1000,3),
                "candidateCount":len(evaluated),
                "technicalReview":metrics,
            })
            cursor=start_ms+length
            nominal_prefix+=length
        scene_index+=count
    if scene_index!=len(scene_ms):
        raise ValueError("Automatic edit did not fill the complete story")
    return result


def auto_edit(*, video_paths: list[Path], destination: Path,
              script_path: Path | None = None, plan_path: Path | None = None,
              topic: str = "", duration: int = 30,
              shot_seconds: float = 6.0, genre: str = "documentary",
              rights_note: str, rights_confirmed: bool,
              provider: str = "original-camera",
              resolution: str = "shorts", fps: int = 30,
              transition: str = "adaptive", render_profile: str = "preview",
              audio: Path | None = None, music: Path | None = None) -> dict:
    """Publish an inspectable project folder only after actual MP4 succeeds."""
    if not rights_confirmed:
        raise ValueError("Explicit --confirm-rights required for every source")
    if (not PROVIDER.fullmatch(provider)
            or not isinstance(rights_note,str)
            or not 12 <= len(rights_note.strip()) <= 1000):
        raise ValueError("Invalid video source or rights declaration")
    if genre not in GENRES:
        raise ValueError("Unsupported original footage genre")
    if (script_path is None) == (plan_path is None):
        raise ValueError("Choose exactly one of --script or --plan")
    if not 1 <= len(video_paths) <= MAX_SOURCES:
        raise ValueError("Provide 1 to 32 owned local source videos")
    if resolution not in ("shorts","720p","1080p") or fps not in (24,30):
        raise ValueError("Invalid original video export size or frame rate")
    if transition not in ("cut","dissolve","adaptive") or render_profile not in ("preview","high"):
        raise ValueError("Invalid transition or render profile")
    destination=Path(destination).expanduser().resolve()
    if destination.exists():
        raise ValueError("Destination already exists; choose a new output folder")
    destination.parent.mkdir(parents=True,exist_ok=True)

    if script_path is not None:
        source_text=Path(script_path).read_text(encoding="utf8")
        storyboard=create_plan(
            topic=topic, script=source_text, duration=duration,
            shot_seconds=shot_seconds,
            character="Original licensed camera footage, no fictional avatar",
            style=f"Authentic {genre} storytelling from approved real footage")
    else:
        storyboard=load_plan(Path(plan_path))
    if any(scene.get("renderStyle") == "science"
           or scene.get("motionRig") is not None
           for scene in storyboard["scenes"]):
        raise ValueError("Batch footage cannot replace validated science/cartoon rigs")
    durations=[scene["endMs"]-scene["startMs"]
               for scene in storyboard["scenes"]]
    sources=[]
    seen=set()
    profiles=[]
    for raw in video_paths:
        path=Path(raw).expanduser()
        if (not path.is_file() or path.is_symlink() or
                path.suffix.lower() not in VIDEO_SUFFIXES):
            raise ValueError("Sources must be local regular video files")
        resolved=path.resolve()
        if resolved in seen:
            raise ValueError("Duplicate source video; each input is used once")
        seen.add(resolved)
        sources.append(resolved)
        profiles.append(probe_video(resolved,start=0,seconds=.5))
    capacities=[math.floor(x["sourceDurationSeconds"]*1000)
                for x in profiles]
    # Bind rendered excerpts to exact source bytes, not just filenames.
    source_hashes={source:_sha(source) for source in sources}
    groups=assign_sources(durations,capacities)
    excerpts=select_excerpts(sources,durations,capacities,groups)
    staging=Path(tempfile.mkdtemp(
        prefix=".automate-ytb-autoedit-",dir=destination.parent))
    try:
        staged_plan=staging/"scene-plan.json"
        _write_json(staged_plan,storyboard)
        imported=[]
        for item in excerpts:
            scene_id=storyboard["scenes"][item["sceneIndex"]]["id"]
            proof=ingest_video(
                plan_path=staged_plan,scene_id=scene_id,
                video_path=item["source"],provider=provider,
                rights_note=rights_note,cost_usd="0",
                rights_confirmed=True,
                clip_start_seconds=item["startSeconds"])
            if _sha(item["source"]) != source_hashes[item["source"]]:
                raise ValueError("Original footage changed during import")
            imported.append({
                "sceneId":scene_id,
                "sourceName":item["source"].name,
                "sourceSHA256":source_hashes[item["source"]],
                "startSeconds":item["startSeconds"],
                "durationSeconds":item["durationSeconds"],
                "candidateCount":item["candidateCount"],
                "normalizedVideoSHA256":proof["videoSha256"],
                "posterSHA256":proof["posterSha256"],
                "technicalReview":item["technicalReview"],
            })
        edited=render(
            plan_path=staged_plan,output=staging/"render",
            resolution=resolution,fps=fps,transition=transition,
            render_profile=render_profile,audio=audio,music=music)
        preview=staging/"render"/"preview.mp4"
        if (not preview.is_file() or preview.stat().st_size < 10000
                or edited["scenesRendered"] != len(excerpts)):
            raise RuntimeError("Complete original multi-video render did not succeed")
        warnings=[
            f"Scene {item['sceneId']}: poor exposure/low-contrast source requires review"
            for item in imported if item["technicalReview"]["requiresVisualReview"]
        ]
        report={
            "schemaVersion":1,"algorithm":VERSION,
            "status":"rendered-for-human-review",
            "topic":storyboard["topic"],"genre":genre,
            "sceneCount":len(excerpts),"sourcesProvided":len(sources),
            "sourcesUsed":sum(k>0 for k in groups),
            "sourceAllocationCounts":list(groups),
            "sourceOrderPreserved":True,
            "sourceSegmentsNonoverlapping":True,
            "semanticMatchingPerformed":False,
            "voiceGenerated":False,
            "hasUserProvidedNarration":audio is not None,
            "sourceAudioIncluded":False,
            "outputVideo":str(destination/"render"/"preview.mp4"),
            "resolution":resolution,"fps":fps,
            "rightsConfirmedByUser":True,
            "publicationApproved":False,
            "shots":imported,
            "warnings":warnings,
            "limitations":[
                "Only technical exposure/contrast/motion indicators; no subject understanding.",
                "Footage stays in provided order; no semantic script-to-footage matching.",
                "This command does not synthesize narration or publish the video.",
                "An editor must review story coherence, claims, rights and audio.",
            ],
        }
        _write_json(staging/"auto-edit-report.json",report)
        # Normal render reports use absolute working paths. Rebase them to
        # the final location so reports remain usable after atomic delivery.
        render_report=staging/"render"/"render-report.json"
        if render_report.is_file():
            data=render_report.read_text(encoding="utf8")
            render_report.write_text(
                data.replace(str(staging),str(destination)),encoding="utf8")
        if destination.exists():
            raise ValueError("Destination appeared during edit; refusing overwrite")
        os.replace(staging,destination)
        return report
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(
        description="Make a reviewable mixed-video MP4 from owned source clips")
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--script",type=Path)
    mode.add_argument("--plan",type=Path)
    parser.add_argument("--videos",nargs="+",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--topic",default="")
    parser.add_argument("--duration",type=int,default=30)
    parser.add_argument("--shot-seconds",type=float,default=6)
    parser.add_argument("--genre",choices=sorted(GENRES),default="documentary")
    parser.add_argument("--rights-note",required=True)
    parser.add_argument("--confirm-rights",action="store_true")
    parser.add_argument("--provider",default="original-camera")
    parser.add_argument("--resolution",choices=("shorts","720p","1080p"),
                        default="shorts")
    parser.add_argument("--fps",type=int,choices=(24,30),default=30)
    parser.add_argument("--transition",choices=("adaptive","dissolve","cut"),
                        default="adaptive")
    parser.add_argument("--render-profile",choices=("preview","high"),
                        default="preview")
    parser.add_argument("--audio",type=Path)
    parser.add_argument("--music",type=Path)
    args=parser.parse_args(argv)
    try:
        report=auto_edit(
            video_paths=args.videos,destination=args.output,
            script_path=args.script,plan_path=args.plan,
            topic=args.topic,duration=args.duration,
            shot_seconds=args.shot_seconds,genre=args.genre,
            rights_note=args.rights_note,
            rights_confirmed=args.confirm_rights,provider=args.provider,
            resolution=args.resolution,fps=args.fps,
            transition=args.transition,render_profile=args.render_profile,
            audio=args.audio,music=args.music)
        print(json.dumps({
            "status":report["status"],"video":report["outputVideo"],
            "scenes":report["sceneCount"],"warnings":report["warnings"],
            "publicationApproved":False},ensure_ascii=False))
        return 0
    except (ValueError,RuntimeError,OSError) as error:
        parser.exit(2,f"ERROR: {error}\n")


if __name__=="__main__":
    raise SystemExit(main())
