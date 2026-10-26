"""Generate an Android-friendly real-motion quality-control contact sheet.

Unlike the still-image visual gallery this script encodes actual clips from
the production character rigs, decodes fixed frame positions, and publishes
four temporal snapshots plus small raw MP4 files for manual art review.
No copyrighted assets, external inference, audio generation or publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageStat

from automate_ytb.animated_forest import render_motion_clip as forest_clip
from automate_ytb.animated_owl import render_motion_clip as owl_clip
from automate_ytb.studio import font


EXAMPLES = {
    "fox": ("forest", "day", "jump",
            "Le renard saute au-dessus du ruisseau."),
    "rabbit": ("meadow", "wind", "run",
               "Le lapin court dans la prairie."),
    "cat": ("village", "night", "talk",
            "Le chat parle à son ami."),
    "owl": ("river", "cloudy", "fly",
            "La chouette vole au-dessus de la rivière."),
}
FPS = 24
DURATION = 1.45
SAMPLE_FRAMES = (4, 11, 19, 28)
CELL = (480, 270)
TITLE_HEIGHT = 52
ROW_HEIGHT = 302


def _capture_four_frames(video: Path) -> list[Image.Image]:
    """Decode only four selected real frames in one bounded FFmpeg process."""
    selectors = "+".join(f"eq(n\\,{idx})" for idx in SAMPLE_FRAMES)
    process = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
         "-i", str(video),
         "-vf", f"select={selectors},scale={CELL[0]}:{CELL[1]}:flags=lanczos",
         "-frames:v", str(len(SAMPLE_FRAMES)), "-fps_mode", "passthrough",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True, check=True, timeout=90,
    )
    frame_bytes = CELL[0] * CELL[1] * 3
    if len(process.stdout) != frame_bytes * len(SAMPLE_FRAMES):
        raise RuntimeError("The real video did not provide all four frames")
    return [
        Image.frombytes("RGB", CELL,
                        process.stdout[n*frame_bytes:(n+1)*frame_bytes])
        for n in range(len(SAMPLE_FRAMES))
    ]


def _verify_clip(video: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name,width,height,nb_frames",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True, timeout=40,
    )
    info = json.loads(out.stdout)["streams"][0]
    if info["codec_name"] != "h264" or (info["width"], info["height"]) != (1280, 720):
        raise RuntimeError("Unexpected original animation codec or dimensions")
    if int(info["nb_frames"]) != round(DURATION * FPS):
        raise RuntimeError("The motion sample has a non-contiguous timeline")
    return info


def render_motion_gallery(output: Path, *, actors: tuple[str, ...] | None = None
                          ) -> dict:
    if not isinstance(output, Path):
        raise ValueError("Output must be a file path")
    actors = tuple(EXAMPLES) if actors is None else actors
    if not actors or any(a not in EXAMPLES for a in actors) or len(set(actors)) != len(actors):
        raise ValueError("Choose one or more distinct supported characters")
    if len(actors) > len(EXAMPLES):
        raise ValueError("Too many characters")

    report = {"format": "real-encoded-motion-v1", "fps": FPS,
              "durationSeconds": DURATION, "frameIndices": SAMPLE_FRAMES,
              "motionScoreIsNotPerceptualQuality": True, "characters": []}
    sheet = Image.new("RGB", (4 * CELL[0],
                             TITLE_HEIGHT + len(actors) * ROW_HEIGHT),
                      (17, 26, 42))
    pen = ImageDraw.Draw(sheet)
    pen.text((18, 12), "ORIGINAL CHARACTER MOTION | 4 REAL VIDEO FRAMES",
             font=font(23), fill=(231, 243, 247))
    clips_dir = output.parent / "motion-clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    for row, actor in enumerate(actors):
        biome, weather, action, narration = EXAMPLES[actor]
        clip = clips_dir / f"{actor}-{action}.mp4"
        shared = dict(topic=f"Original animated {actor} in {biome}",
                      narration=narration, scene_index=row + 1,
                      scene_count=len(actors), style="cartoon",
                      direction={"action": action, "emotion": "happy",
                                 "weather": weather, "shot": "wide"},
                      duration=DURATION, width=1280, height=720, fps=FPS,
                      landscape=biome, destination=clip)
        if actor == "owl":
            owl_clip(**shared)
        else:
            forest_clip(kind=actor, **shared)
        info = _verify_clip(clip)
        frames = _capture_four_frames(clip)
        changes = []
        for left, right in zip(frames, frames[1:]):
            changes.append(round(sum(ImageStat.Stat(
                ImageChops.difference(left, right)).mean), 3))
        if max(changes) <= 0.4:
            raise RuntimeError(f"Frozen character preview: {actor}")
        for col, frame in enumerate(frames):
            x, y = col * CELL[0], TITLE_HEIGHT + row * ROW_HEIGHT
            sheet.paste(frame, (x, y))
            pen.text((x+10, y+CELL[1]+8),
                     f"{actor.upper()} | {action} | {SAMPLE_FRAMES[col] / FPS:.2f}s",
                     font=font(19), fill=(222, 232, 241))
        report["characters"].append({
            "actor": actor, "biome": biome, "weather": weather,
            "action": action, "file": str(clip.name),
            "codec": info["codec_name"],
            "frames": int(info["nb_frames"]),
            "sampleDeltaScores": changes,
            "meanDeltaScore": round(statistics.mean(changes), 3),
        })
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)
    report_path = output.with_suffix(".json")
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline original animal animation review on Android")
    parser.add_argument("--output", default="out/motion-gallery.png")
    parser.add_argument("--actor", choices=tuple(EXAMPLES),
                        action="append", dest="actors")
    args = parser.parse_args()
    report = render_motion_gallery(
        Path(args.output), actors=tuple(args.actors) if args.actors else None)
    print(json.dumps({"gallery": args.output,
                      "characters": len(report["characters"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
